#!/usr/bin/env python3

import json
import os
import sys
import logging
import requests
import feedparser
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from colorama import init, Fore, Style
import tempfile
import pickle
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

init(autoreset=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path.home() / '.daily_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration values"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """Validate the configuration dictionary"""
        # Validate weather config
        weather = config.get('weather', {})
        if not weather.get('home_city'):
            raise ValueError("weather.home_city is required")
        if weather.get('units') not in ['metric', 'imperial', None]:
            raise ValueError("weather.units must be 'metric' or 'imperial'")
        
        # Validate news config
        news = config.get('news', {})
        max_headlines = news.get('max_headlines', 5)
        if not isinstance(max_headlines, int) or max_headlines < 1 or max_headlines > 20:
            raise ValueError("news.max_headlines must be between 1 and 20")
        
        sources = news.get('sources', [])
        for source in sources:
            if not source.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid RSS URL: {source}")
        
        # Validate reddit config
        reddit = config.get('reddit', {})
        max_posts = reddit.get('max_posts', 3)
        if not isinstance(max_posts, int) or max_posts < 1 or max_posts > 10:
            raise ValueError("reddit.max_posts must be between 1 and 10")
        
        # Validate timeout config
        timeout = config.get('timeout', {})
        api_timeout = timeout.get('api_timeout', 5)
        if not isinstance(api_timeout, (int, float)) or api_timeout < 1 or api_timeout > 30:
            raise ValueError("timeout.api_timeout must be between 1 and 30 seconds")
        
        # Validate finance config
        finance = config.get('finance', {})
        if finance.get('enabled', False):
            stocks = finance.get('stocks', [])
            crypto = finance.get('crypto', [])
            if not stocks and not crypto:
                raise ValueError("finance.stocks or finance.crypto must have at least one symbol when finance is enabled")

class APICache:
    """Simple cache for API responses"""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl_minutes: int = 15):
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / 'daily_dashboard_cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for a given key"""
        safe_key = "".join(c if c.isalnum() or c in '-_' else '_' for c in key)
        return self.cache_dir / f"{safe_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if it exists and is not expired"""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cached_data = pickle.load(f)
            
            if datetime.now() - cached_data['timestamp'] < self.ttl:
                logger.debug(f"Cache hit for key: {key}")
                return cached_data['data']
            else:
                logger.debug(f"Cache expired for key: {key}")
                cache_path.unlink()
                return None
        except Exception as e:
            logger.warning(f"Error reading cache for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Cache a value"""
        cache_path = self._get_cache_path(key)
        
        try:
            cached_data = {
                'timestamp': datetime.now(),
                'data': value
            }
            with open(cache_path, 'wb') as f:
                pickle.dump(cached_data, f)
            logger.debug(f"Cached data for key: {key}")
        except Exception as e:
            logger.warning(f"Error caching data for {key}: {e}")

class FinanceTracker:
    """Track stocks and cryptocurrency prices"""
    
    def __init__(self, config: Dict[str, Any], cache: APICache, timeout: float = 5):
        self.config = config
        self.cache = cache
        self.timeout = timeout
    
    def get_stock_data(self) -> List[str]:
        """Fetch stock market data"""
        stocks = self.config.get('stocks', ['SPY', 'QQQ'])
        results = []
        
        try:
            import yfinance as yf
            
            for symbol in stocks:
                cache_key = f"stock_{symbol}"
                cached_data = self.cache.get(cache_key)
                
                if cached_data:
                    results.append(cached_data)
                    continue
                
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.fast_info
                    
                    current_price = info.get('lastPrice', 0)
                    prev_close = info.get('previousClose', 0)
                    
                    if current_price and prev_close:
                        change = current_price - prev_close
                        change_pct = (change / prev_close) * 100
                        
                        arrow = "↑" if change >= 0 else "↓"
                        color = Fore.GREEN if change >= 0 else Fore.RED
                        
                        result = f"• {symbol}: ${current_price:.2f} {color}{arrow} {abs(change):.2f} ({abs(change_pct):.2f}%){Fore.WHITE}"
                        
                        self.cache.set(cache_key, result)
                        results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error fetching stock {symbol}: {e}")
                    
        except ImportError:
            logger.warning("yfinance not installed, skipping stocks")
            return ["Stock tracking requires: pip install yfinance"]
        
        return results
    
    def get_crypto_data(self) -> List[str]:
        """Fetch cryptocurrency data"""
        crypto = self.config.get('crypto', ['BTC-USD', 'ETH-USD'])
        results = []
        
        for symbol in crypto:
            cache_key = f"crypto_{symbol}"
            cached_data = self.cache.get(cache_key)
            
            if cached_data:
                results.append(cached_data)
                continue
            
            try:
                # Use CoinGecko API (free, no key required)
                coin_id = symbol.split('-')[0].lower()
                if coin_id == 'btc':
                    coin_id = 'bitcoin'
                elif coin_id == 'eth':
                    coin_id = 'ethereum'
                
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
                response = requests.get(url, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    if coin_id in data:
                        price = data[coin_id]['usd']
                        change_24h = data[coin_id].get('usd_24h_change', 0)
                        
                        arrow = "↑" if change_24h >= 0 else "↓"
                        color = Fore.GREEN if change_24h >= 0 else Fore.RED
                        
                        display_name = symbol.split('-')[0]
                        result = f"• {display_name}: ${price:,.2f} {color}{arrow} {abs(change_24h):.2f}%{Fore.WHITE}"
                        
                        self.cache.set(cache_key, result)
                        results.append(result)
                        
            except Exception as e:
                logger.warning(f"Error fetching crypto {symbol}: {e}")
        
        return results

class WeatherEnhanced:
    """Enhanced weather information with more details"""
    
    def __init__(self, config: Dict[str, Any], cache: APICache, timeout: float = 5):
        self.config = config
        self.cache = cache
        self.timeout = timeout
    
    def get_detailed_weather(self) -> Dict[str, Any]:
        """Get enhanced weather data including feels like, sunrise/sunset"""
        home_city = self.config.get('home_city', 'Shanghai')
        units = self.config.get('units', 'metric')
        
        cache_key = f"weather_detailed_{home_city}_{units}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        result = {
            'basic': '',
            'details': [],
            'alerts': []
        }
        
        try:
            # Get basic weather (as before)
            unit_param = "m" if units == "metric" else "u"
            
            # Current location
            current_url = f"https://wttr.in/?format=1&{unit_param}"
            current_response = requests.get(current_url, timeout=self.timeout)
            
            if current_response.status_code == 200:
                result['basic'] = current_response.text.strip()
            
            # Get detailed weather using format 2 (more detailed)
            detailed_url = f"https://wttr.in/{home_city}?format=%C+%t+%f+%w+%h+%P+%S+%s&{unit_param}"
            detailed_response = requests.get(detailed_url, timeout=self.timeout)
            
            if detailed_response.status_code == 200:
                # Parse the detailed format response
                parts = detailed_response.text.strip().split()
                if len(parts) >= 8:
                    result['details'] = [
                        f"Feels like: {parts[2]}" if len(parts) > 2 else "",
                        f"Wind: {parts[3]}" if len(parts) > 3 else "",
                        f"Humidity: {parts[4]}" if len(parts) > 4 else "",
                        f"Pressure: {parts[5]}" if len(parts) > 5 else "",
                        f"Sunrise: {parts[6]}" if len(parts) > 6 else "",
                        f"Sunset: {parts[7]}" if len(parts) > 7 else ""
                    ]
            
            # Get weather alerts using JSON format
            alert_url = f"https://wttr.in/{home_city}?format=j1"
            alert_response = requests.get(alert_url, timeout=self.timeout)
            
            if alert_response.status_code == 200:
                weather_data = alert_response.json()
                current = weather_data.get('current_condition', [{}])[0]
                
                # Extract detailed information
                if current:
                    temp_c = current.get('temp_C', '')
                    feels_like_c = current.get('FeelsLikeC', '')
                    humidity = current.get('humidity', '')
                    wind_speed = current.get('windspeedKmph', '')
                    precip = current.get('precipMM', '0')
                    uv_index = current.get('uvIndex', '')
                    
                    result['details'] = [
                        f"Feels like: {feels_like_c}°C" if feels_like_c else "",
                        f"Humidity: {humidity}%" if humidity else "",
                        f"Wind: {wind_speed} km/h" if wind_speed else "",
                        f"Precipitation: {precip}mm" if float(precip) > 0 else "No precipitation",
                        f"UV Index: {uv_index}" if uv_index else ""
                    ]
                    
                    # Weather alerts based on conditions
                    if float(precip) > 5:
                        result['alerts'].append("⚠️  Heavy rain expected")
                    if wind_speed and int(wind_speed) > 40:
                        result['alerts'].append("⚠️  Strong winds")
                    if uv_index and int(uv_index) > 7:
                        result['alerts'].append("⚠️  High UV index - use sunscreen")
                
                # Get astronomy data
                astronomy = weather_data.get('weather', [{}])[0].get('astronomy', [{}])[0]
                if astronomy:
                    sunrise = astronomy.get('sunrise', '')
                    sunset = astronomy.get('sunset', '')
                    moonrise = astronomy.get('moonrise', '')
                    moon_phase = astronomy.get('moon_phase', '')
                    
                    if sunrise and sunset:
                        result['details'].extend([
                            f"🌅 Sunrise: {sunrise}",
                            f"🌇 Sunset: {sunset}"
                        ])
                    if moon_phase:
                        result['details'].append(f"🌙 Moon: {moon_phase}")
                        
        except Exception as e:
            logger.error(f"Error fetching enhanced weather: {e}")
            result['basic'] = "Weather data unavailable"
        
        self.cache.set(cache_key, result)
        return result

class AIBriefing:
    """Generate AI-powered daily briefing"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        self.enabled = bool(self.api_key)
    
    def generate_briefing(self, news: List[str], weather: str, date_str: str) -> Optional[str]:
        """Generate personalized AI briefing based on collected data"""
        if not self.enabled:
            return None
        
        try:
            from anthropic import Anthropic
            
            client = Anthropic(api_key=self.api_key)
            
            # Prepare context
            news_text = "\n".join(news[:5]) if news else "No news available"
            
            prompt = f"""Based on today's information ({date_str}), create a brief 2-3 sentence daily briefing that:
1. Summarizes the key news themes
2. Mentions any important weather conditions
3. Provides a motivational or insightful closing thought

Today's weather: {weather}
Today's headlines:
{news_text}

Keep it concise, professional, and engaging. Format as a single paragraph."""
            
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except ImportError:
            logger.info("Anthropic library not installed")
            return "AI Briefing requires: pip install anthropic"
        except Exception as e:
            logger.warning(f"Error generating AI briefing: {e}")
            return None

class DailyDashboard:
    def __init__(self, config_path: Optional[str] = None):
        # Use pathlib for proper path handling
        self.base_dir = Path(__file__).parent
        config_file = Path(config_path) if config_path else self.base_dir / "config.json"
        
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            # Override config with environment variables if they exist
            self._load_env_overrides()
            
            # Validate configuration
            ConfigValidator.validate_config(self.config)
            
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
        except ValueError as e:
            logger.error(f"Configuration validation error: {e}")
            sys.exit(1)
        
        # Set up file paths
        self.last_run_file = self.base_dir / self.config.get('last_run_file', '.last_run')
        
        # Set up cache
        cache_ttl = self.config.get('cache', {}).get('ttl_minutes', 15)
        self.cache = APICache(ttl_minutes=cache_ttl)
        
        # Get timeout configuration
        timeout_config = self.config.get('timeout', {})
        self.api_timeout = timeout_config.get('api_timeout', 5)
        
        # Initialize enhanced components
        finance_config = self.config.get('finance', {})
        if finance_config.get('enabled', False):
            self.finance = FinanceTracker(finance_config, self.cache, self.api_timeout)
        else:
            self.finance = None
        
        self.weather_enhanced = WeatherEnhanced(
            self.config.get('weather', {}), 
            self.cache, 
            self.api_timeout
        )
        
        ai_config = self.config.get('ai_briefing', {})
        if ai_config.get('enabled', False):
            # Use API key from config or environment
            api_key = ai_config.get('api_key') or os.getenv('ANTHROPIC_API_KEY')
            self.ai_briefing = AIBriefing(api_key)
        else:
            self.ai_briefing = None
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        # Weather overrides
        if os.getenv('WEATHER_HOME_CITY'):
            if 'weather' not in self.config:
                self.config['weather'] = {}
            self.config['weather']['home_city'] = os.getenv('WEATHER_HOME_CITY')
        
        # Finance overrides
        if os.getenv('FINANCE_ENABLED'):
            if 'finance' not in self.config:
                self.config['finance'] = {}
            self.config['finance']['enabled'] = os.getenv('FINANCE_ENABLED').lower() == 'true'
        
        if os.getenv('FINANCE_STOCKS'):
            if 'finance' not in self.config:
                self.config['finance'] = {}
            self.config['finance']['stocks'] = [s.strip() for s in os.getenv('FINANCE_STOCKS').split(',')]
        
        if os.getenv('FINANCE_CRYPTO'):
            if 'finance' not in self.config:
                self.config['finance'] = {}
            self.config['finance']['crypto'] = [c.strip() for c in os.getenv('FINANCE_CRYPTO').split(',')]
        
        # AI Briefing overrides
        if os.getenv('AI_BRIEFING_ENABLED'):
            if 'ai_briefing' not in self.config:
                self.config['ai_briefing'] = {}
            self.config['ai_briefing']['enabled'] = os.getenv('AI_BRIEFING_ENABLED').lower() == 'true'
        
        if os.getenv('ANTHROPIC_API_KEY'):
            if 'ai_briefing' not in self.config:
                self.config['ai_briefing'] = {}
            self.config['ai_briefing']['api_key'] = os.getenv('ANTHROPIC_API_KEY')
        
        # Reddit overrides
        if os.getenv('REDDIT_SUBREDDITS'):
            if 'reddit' not in self.config:
                self.config['reddit'] = {}
            self.config['reddit']['subreddits'] = [r.strip() for r in os.getenv('REDDIT_SUBREDDITS').split(',')]
        
        # News overrides
        if os.getenv('NEWS_SOURCES'):
            if 'news' not in self.config:
                self.config['news'] = {}
            self.config['news']['sources'] = [s.strip() for s in os.getenv('NEWS_SOURCES').split(',')]
    
    def should_run_today(self) -> bool:
        """Check if dashboard should run today"""
        today = date.today().isoformat()
        
        if not self.last_run_file.exists():
            return True
        
        try:
            last_run = self.last_run_file.read_text().strip()
            return last_run != today
        except Exception as e:
            logger.warning(f"Error reading last run file: {e}")
            return True
    
    def mark_run_today(self) -> None:
        """Mark dashboard as run today"""
        today = date.today().isoformat()
        try:
            self.last_run_file.write_text(today)
        except Exception as e:
            logger.error(f"Error writing last run file: {e}")
    
    def get_weather(self) -> str:
        """Fetch basic weather information"""
        weather_config = self.config.get('weather', {})
        home_city = weather_config.get('home_city', 'Shanghai')
        units = weather_config.get('units', 'metric')
        
        # Check cache first
        cache_key = f"weather_{home_city}_{units}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            unit_param = "m" if units == "metric" else "u"
            
            # Get current location weather
            current_url = f"https://wttr.in/?format=1&{unit_param}"
            try:
                current_response = requests.get(current_url, timeout=self.api_timeout)
                if current_response.status_code == 200:
                    current_weather = current_response.text.strip()
                    
                    # Get home city weather
                    home_url = f"https://wttr.in/{home_city}?format=1&{unit_param}"
                    home_response = requests.get(home_url, timeout=self.api_timeout)
                    
                    if home_response.status_code == 200:
                        home_weather = home_response.text.strip()
                        
                        # Check if current location contains home city name
                        if home_city.lower() in current_weather.lower():
                            result = f"Weather: {current_weather}"
                        else:
                            result = f"Weather: {current_weather}\nHome ({home_city}): {home_weather}"
                    else:
                        result = f"Weather: {current_weather}"
                else:
                    logger.warning(f"Weather API returned status {current_response.status_code}")
                    result = "Weather: Unable to fetch data"
            except requests.exceptions.Timeout:
                logger.warning("Weather API request timed out")
                result = "Weather: Request timed out"
            except requests.exceptions.RequestException as e:
                logger.warning(f"Weather API request failed: {e}")
                result = "Weather: Connection error"
            
            # Cache the result
            self.cache.set(cache_key, result)
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return "Weather: Error fetching data"
    
    def get_news_headlines(self) -> List[str]:
        """Fetch news headlines from RSS feeds"""
        news_config = self.config.get('news', {})
        sources = news_config.get('sources', [])
        max_headlines = news_config.get('max_headlines', 5)
        
        headlines = []
        
        for source in sources:
            # Check cache
            cache_key = f"news_{source}"
            cached_headlines = self.cache.get(cache_key)
            
            if cached_headlines:
                headlines.extend(cached_headlines)
                continue
            
            try:
                logger.debug(f"Fetching news from {source}")
                # feedparser doesn't support timeout directly, so we use requests
                response = requests.get(source, timeout=self.api_timeout)
                feed = feedparser.parse(response.text)
                
                if feed.bozo:
                    logger.warning(f"Feed parsing error for {source}: {feed.bozo_exception}")
                    continue
                
                source_headlines = []
                for entry in feed.entries[:max_headlines]:
                    headline = f"• {entry.title}"
                    if hasattr(entry, 'link'):
                        headline += f"\n  {entry.link}"
                    source_headlines.append(headline)
                
                # Cache the headlines for this source
                self.cache.set(cache_key, source_headlines)
                headlines.extend(source_headlines)
                
                if len(headlines) >= max_headlines:
                    break
                    
            except Exception as e:
                logger.warning(f"Error fetching news from {source}: {e}")
                continue
        
        return headlines[:max_headlines]
    
    def get_reddit_posts(self) -> List[str]:
        """Fetch trending Reddit posts"""
        reddit_config = self.config.get('reddit', {})
        subreddits = reddit_config.get('subreddits', ['worldnews'])
        max_posts = reddit_config.get('max_posts', 3)
        
        posts = []
        
        for subreddit in subreddits:
            # Check cache
            cache_key = f"reddit_{subreddit}"
            cached_posts = self.cache.get(cache_key)
            
            if cached_posts:
                posts.extend(cached_posts)
                continue
            
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={max_posts}"
                headers = {'User-Agent': 'DailyDashboard/1.0'}
                
                logger.debug(f"Fetching Reddit posts from r/{subreddit}")
                response = requests.get(url, headers=headers, timeout=self.api_timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    subreddit_posts = []
                    for post in data['data']['children'][:max_posts]:
                        post_data = post['data']
                        reddit_url = f"https://reddit.com{post_data['permalink']}"
                        post_text = f"• r/{subreddit}: {post_data['title']}\n  {reddit_url}"
                        subreddit_posts.append(post_text)
                    
                    # Cache the posts for this subreddit
                    self.cache.set(cache_key, subreddit_posts)
                    posts.extend(subreddit_posts)
                    
                elif response.status_code == 429:
                    logger.warning(f"Rate limited by Reddit for r/{subreddit}")
                else:
                    logger.warning(f"Reddit API returned status {response.status_code} for r/{subreddit}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Reddit request timed out for r/{subreddit}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Reddit request failed for r/{subreddit}: {e}")
            except (KeyError, json.JSONDecodeError) as e:
                logger.warning(f"Error parsing Reddit response for r/{subreddit}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching Reddit posts from r/{subreddit}: {e}")
        
        return posts[:max_posts * len(subreddits)]
    
    def display_dashboard(self) -> None:
        """Display the enhanced dashboard"""
        date_str = datetime.now().strftime('%A, %B %d, %Y')
        
        print(f"\n{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}    DAILY DASHBOARD - {date_str}")
        print(f"{Fore.CYAN}{'='*70}\n")
        
        # Enhanced Weather
        print(f"{Fore.YELLOW}🌤️  WEATHER")
        weather_data = self.weather_enhanced.get_detailed_weather()
        print(f"{Fore.WHITE}{weather_data['basic']}")
        
        # Weather details
        if weather_data['details']:
            for detail in weather_data['details']:
                if detail:
                    print(f"{Fore.WHITE}  {detail}")
        
        # Weather alerts
        if weather_data['alerts']:
            for alert in weather_data['alerts']:
                print(f"{Fore.YELLOW}{alert}")
        print()
        
        # Financial Markets (if enabled)
        if self.finance:
            print(f"{Fore.CYAN}📈 MARKETS")
            
            # Stocks
            stocks = self.finance.get_stock_data()
            if stocks:
                print(f"{Fore.WHITE}Stocks:")
                for stock in stocks:
                    print(f"{Fore.WHITE}{stock}")
            
            # Crypto
            crypto = self.finance.get_crypto_data()
            if crypto:
                print(f"{Fore.WHITE}Crypto:")
                for coin in crypto:
                    print(f"{Fore.WHITE}{coin}")
            print()
        
        # News Headlines
        print(f"{Fore.GREEN}📰 NEWS HEADLINES")
        headlines = self.get_news_headlines()
        if headlines:
            for headline in headlines:
                print(f"{Fore.WHITE}{headline}")
        else:
            print(f"{Fore.WHITE}No news headlines available")
        print()
        
        # Reddit Posts
        print(f"{Fore.MAGENTA}🔥 TRENDING ON REDDIT")
        posts = self.get_reddit_posts()
        if posts:
            for post in posts:
                print(f"{Fore.WHITE}{post}")
        else:
            print(f"{Fore.WHITE}No Reddit posts available")
        print()
        
        # AI Daily Briefing (if enabled)
        if self.ai_briefing:
            print(f"{Fore.BLUE}🤖 AI DAILY BRIEFING")
            briefing = self.ai_briefing.generate_briefing(
                headlines, 
                weather_data['basic'],
                date_str
            )
            if briefing:
                # Wrap text for better display
                import textwrap
                wrapped = textwrap.fill(briefing, width=65)
                print(f"{Fore.WHITE}{wrapped}")
                print()
        
        print(f"{Fore.CYAN}{'='*70}\n")

def main():
    """Main entry point"""
    try:
        # Check for debug or force mode
        debug_mode = '--debug' in sys.argv
        force_mode = '--force' in sys.argv or debug_mode
        
        dashboard = DailyDashboard()
        
        # Check if we should run today (skip check in force/debug mode)
        if not force_mode and not dashboard.should_run_today():
            logger.info("Dashboard already run today, skipping")
            sys.exit(0)
        
        # Display the dashboard
        dashboard.display_dashboard()
        
        # Mark as run (unless in debug mode)
        if not debug_mode:
            dashboard.mark_run_today()
        
    except KeyboardInterrupt:
        logger.info("Dashboard interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Suppress logging to console for normal operation
    if '--debug' not in sys.argv:
        logging.getLogger().handlers = [h for h in logging.getLogger().handlers 
                                       if not isinstance(h, logging.StreamHandler)]
    main()