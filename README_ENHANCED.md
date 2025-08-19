# Daily Dashboard - Enhanced Edition

A powerful terminal dashboard that displays weather, financial markets, news, social media trends, and AI-generated briefings when you open your terminal.

## 🚀 New Features

### 📈 Financial Markets
- **Stock Market Tracking**: Monitor major indices (SPY, QQQ) and individual stocks
- **Cryptocurrency Prices**: Track Bitcoin, Ethereum, and other cryptocurrencies
- **Real-time Changes**: Shows daily price changes with color-coded indicators

### 🌡️ Enhanced Weather
- **Detailed Conditions**: Feels-like temperature, humidity, wind speed, UV index
- **Weather Alerts**: Automatic warnings for severe conditions
- **Astronomy Data**: Sunrise, sunset times, and moon phases
- **Precipitation Info**: Current and expected rainfall

### 🤖 AI Daily Briefing
- **Personalized Summary**: AI-generated analysis of the day's news and weather
- **Trend Detection**: Identifies patterns in news headlines
- **Motivational Insights**: Provides contextual daily thoughts
- **Powered by Claude**: Uses Anthropic's Claude AI for intelligent summaries

## 📦 Installation

1. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Set up environment variables**:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   ```

3. **Configure** (optional - for additional settings):
   ```bash
   cp config_enhanced.json config.json
   # Edit config.json for advanced preferences
   ```

4. **Run the dashboard**:
   ```bash
   python3 dashboard_enhanced.py
   ```

## ⚙️ Configuration Guide

### Environment Variables (.env)

The dashboard supports configuration through environment variables for sensitive data and quick customization:

```bash
# API Keys
ANTHROPIC_API_KEY=your-api-key-here

# Feature Toggles
FINANCE_ENABLED=true
AI_BRIEFING_ENABLED=true

# Custom Settings
WEATHER_HOME_CITY=San Francisco
FINANCE_STOCKS=AAPL,GOOGL,TSLA,SPY
FINANCE_CRYPTO=BTC-USD,ETH-USD,SOL-USD
REDDIT_SUBREDDITS=programming,webdev,technology
NEWS_SOURCES=https://feeds.bbci.co.uk/news/rss.xml,https://techcrunch.com/feed/
```

Environment variables take precedence over config.json settings.

### Finance Settings
```json
"finance": {
  "enabled": true,
  "stocks": ["SPY", "QQQ", "AAPL", "MSFT", "GOOGL"],
  "crypto": ["BTC-USD", "ETH-USD", "SOL-USD"]
}
```
- `stocks`: List of stock tickers to track (uses Yahoo Finance)
- `crypto`: List of cryptocurrency pairs (uses CoinGecko API)

### Enhanced Weather Settings
```json
"weather": {
  "home_city": "Shanghai",
  "units": "metric",
  "show_details": true,
  "show_alerts": true
}
```
- `show_details`: Display extended weather information
- `show_alerts`: Show weather warnings and advisories

### AI Briefing Settings
```json
"ai_briefing": {
  "enabled": true,
  "api_key": null,
  "model": "claude-3-haiku-20240307"
}
```
- `enabled`: Toggle AI briefing generation
- `api_key`: Your Anthropic API key (or use environment variable)
- `model`: Claude model to use (haiku is fast and affordable)

## 📊 Sample Output

```
======================================================================
    DAILY DASHBOARD - Tuesday, August 19, 2025
======================================================================

🌤️  WEATHER
Weather: ☀️  Shanghai: +29°C
  Feels like: 32°C
  Humidity: 65%
  Wind: 15 km/h
  UV Index: 8
  🌅 Sunrise: 05:22 AM
  🌇 Sunset: 06:33 PM
⚠️  High UV index - use sunscreen

📈 MARKETS
Stocks:
• SPY: $643.30 ↑ 5.21 (0.82%)
• QQQ: $485.50 ↑ 3.15 (0.65%)
• AAPL: $235.80 ↓ 1.20 (0.51%)
Crypto:
• BTC: $115,285.00 ↑ 2.35%
• ETH: $4,521.50 ↑ 1.82%

📰 NEWS HEADLINES
• Major tech breakthrough announced...
• Global climate summit reaches agreement...

🔥 TRENDING ON REDDIT
• r/technology: New AI model surpasses expectations...
• r/science: Breakthrough in quantum computing...

🤖 AI DAILY BRIEFING
Today's news highlights significant progress in technology and 
international cooperation, with clear skies providing perfect 
conditions for outdoor activities. Make the most of this 
productive Tuesday while staying protected from high UV levels.

======================================================================
```

## 🔧 Troubleshooting

### Stock data not showing
- Install yfinance: `pip3 install yfinance`
- Check internet connectivity
- Verify stock symbols are valid

### AI Briefing not working
- Ensure you have an Anthropic API key
- Check API key is correctly set in config or environment
- Verify you have sufficient API credits

### Weather details missing
- Some locations may not provide all weather details
- Check your internet connection
- Try a different city to verify functionality

## 🎯 Performance Tips

1. **Caching**: API responses are cached for 15 minutes to reduce load
2. **Selective Features**: Disable features you don't need in config.json
3. **API Limits**: Be mindful of rate limits, especially for Reddit
4. **Debug Mode**: Use `--debug` flag to troubleshoot issues

## 📝 Advanced Usage

### Running Multiple Configs
```bash
# Work dashboard
python3 dashboard_enhanced.py --config work_config.json

# Personal dashboard  
python3 dashboard_enhanced.py --config personal_config.json
```

### Scheduling with Cron
```bash
# Add to crontab for daily 8 AM run
0 8 * * * /usr/bin/python3 /path/to/dashboard_enhanced.py
```

### Integration with Terminal
```bash
# Add to ~/.zshrc or ~/.bashrc
alias morning="python3 ~/daily-dashboard/dashboard_enhanced.py"
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT License - feel free to use and modify as needed.