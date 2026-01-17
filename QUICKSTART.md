# Quick Start Guide

## Running the Trading Bot

### 1. Installation
```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Edit `config.py` and add your Telegram credentials:
```python
TELEGRAM_BOT_TOKEN = 'your_bot_token_from_botfather'
TELEGRAM_CHAT_ID = 'your_chat_id'
```

### 3. Trading Pairs
Edit `pairs.csv` to include your desired trading pairs:
```
BTC/USDT
ETH/USDT
BNB/USDT
SOL/USDT
ADA/USDT
```

### 4. Run the Bot
```bash
python main.py
```

The bot will:
- Start immediately if within trading hours (9 AM - 10 PM IST)
- Scan all pairs for buy/sell signals
- Send Telegram notifications with results
- Continue running every hour automatically

### 5. Test the Bot
Run the test suite to verify everything works:
```bash
python test_bot.py
```

## How It Works

### Signal Detection Logic

**Buy Signal:**
1. Looks at last 2-3 candles
2. Finds red Heikin Ashi candle touching lower Bollinger Band
3. Next candle must be green with ≥30% body size
4. Generates buy signal

**Sell Signal:**
1. Looks at last 2-3 candles
2. Finds green Heikin Ashi candle touching upper Bollinger Band
3. Next candle must be red with ≥30% body size
4. Generates sell signal

### Indicators

- **Bollinger Bands**: 20-period SMA with 2 standard deviations
- **Heikin Ashi**: Smoothed candlestick calculation for trend identification

### Notification Format
```
📊 1Hr BH

🟢 BUY:
  • BTC/USDT
  • ETH/USDT

🔴 SELL:
  • BNB/USDT
```

## Troubleshooting

### Bot Not Fetching Data
- Check internet connection
- Verify Binance API is accessible
- The bot works without API keys for public data

### Telegram Not Working
- Verify bot token is correct
- Check chat ID is correct
- Test by sending a message manually to your bot

### No Signals Generated
- This is normal - signals are rare
- Verify pairs.csv has valid trading pairs
- Check that data is being fetched successfully

## Advanced Usage

### Custom Pairs
Add any Binance spot trading pair to `pairs.csv`:
```
BTC/USDT
ETH/USDT
DOT/USDT
LINK/USDT
```

### Running as a Service
Use systemd, supervisor, or screen to keep the bot running 24/7:
```bash
# Using screen
screen -S trading-bot
python main.py
# Press Ctrl+A then D to detach
```

### Logs
The bot prints all activity to stdout. Redirect to a file if needed:
```bash
python main.py >> bot.log 2>&1
```
