# Daily Dashboard

A powerful terminal dashboard that displays weather, financial markets, news, social media trends, and AI-generated briefings when you open your terminal.

## Features

- 🌤️ **Enhanced Weather** - Current conditions, feels-like temp, UV index, sunrise/sunset
- 📈 **Financial Markets** - Stock prices and cryptocurrency tracking with live changes
- 📰 **News Headlines** - Aggregated from multiple RSS feeds
- 🔥 **Reddit Trends** - Hot posts from your favorite subreddits
- 🤖 **AI Daily Briefing** - Personalized summary powered by Claude AI
- 📅 **Smart Scheduling** - Runs once per day (won't spam every terminal)
- 💾 **Intelligent Caching** - 15-minute cache to reduce API calls
- 🔐 **Secure Config** - Environment variables via .env file
- 🎨 **Beautiful Output** - Colorful, well-formatted terminal display

## Quick Start

1. **Clone and install**:
   ```bash
   git clone <repository>
   cd daily-dashboard
   pip3 install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   nano .env  # Add your API key and customize settings
   ```

3. **Run the dashboard**:
   ```bash
   python3 dashboard.py
   ```

4. **Auto-run on terminal open** (optional):
   ```bash
   ./install.sh
   ```

## Configuration

### Environment Variables (.env)

Create a `.env` file with your settings:

```bash
# API Keys
ANTHROPIC_API_KEY=your-api-key-here  # Get from console.anthropic.com

# Location
WEATHER_HOME_CITY=San Francisco

# Financial Markets
FINANCE_ENABLED=true
FINANCE_STOCKS=AAPL,GOOGL,TSLA,SPY
FINANCE_CRYPTO=BTC-USD,ETH-USD,SOL-USD

# AI Features
AI_BRIEFING_ENABLED=true

# Content Sources
REDDIT_SUBREDDITS=programming,technology,science
NEWS_SOURCES=https://feeds.bbci.co.uk/news/rss.xml,https://techcrunch.com/feed/
```

### Advanced Configuration (config.json)

For more detailed settings, edit `config.json`:

```json
{
  "weather": {
    "home_city": "Shanghai",
    "units": "metric"
  },
  "finance": {
    "enabled": true,
    "stocks": ["SPY", "QQQ"],
    "crypto": ["BTC-USD", "ETH-USD"]
  },
  "cache": {
    "ttl_minutes": 15
  },
  "timeout": {
    "api_timeout": 5
  }
}
```

*Note: Environment variables override config.json settings*

## Features in Detail

### 🤖 AI Daily Briefing
- Analyzes news trends and weather conditions
- Generates personalized insights and recommendations
- Powered by Claude 3 Haiku (fast and efficient)
- Requires Anthropic API key

### 📈 Financial Markets
- **Stocks**: Real-time prices with daily changes
- **Crypto**: Bitcoin, Ethereum, and more via CoinGecko
- Color-coded gains (green) and losses (red)
- Configurable symbols via .env

### 🌤️ Weather Enhancement
- Current temperature and conditions
- Feels-like temperature
- Wind speed, humidity, UV index
- Sunrise and sunset times
- Weather alerts for severe conditions
- Moon phase information

## Manual Commands

```bash
# Run dashboard manually
python3 dashboard.py

# Run with debug output
python3 dashboard.py --debug

# Force run (ignores daily limit)
rm .last_run && python3 dashboard.py
```

## API Requirements

- **Weather**: Uses wttr.in (no API key needed)
- **News**: RSS feeds (no API key needed)
- **Reddit**: Public API (no key needed, rate limited)
- **Stocks**: Yahoo Finance via yfinance
- **Crypto**: CoinGecko free API
- **AI Briefing**: Anthropic API key required

## Troubleshooting

### AI Briefing not showing
- Ensure `ANTHROPIC_API_KEY` is set in .env
- Check you have API credits at console.anthropic.com
- Verify `AI_BRIEFING_ENABLED=true`

### Stock data missing
- Install yfinance: `pip3 install yfinance`
- Check internet connectivity
- Verify stock symbols are valid

### Weather timeout
- Increase timeout in config.json
- Check internet connection
- Try different city name

## Privacy & Security

- API keys stored locally in `.env` (never committed)
- All data fetched fresh (minimal caching)
- No telemetry or tracking
- Open source and auditable

## Contributing

Pull requests welcome! Please ensure:
- Code follows existing style
- New features are configurable
- Environment variables documented
- Error handling included

## License

MIT License - Use freely in personal or commercial projects.