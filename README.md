# Trading BH Bot

This repository contains the code for creating a crypto futures trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 1-hour timeframe.

The bot will:

1. Fetch OHLC data from the CoinDCX API for specific trading pairs defined in the `pairs.csv` file.
2. Compute Bollinger Bands and Heikin Ashi candles.
3. Identify buy and sell signals based on the provided strategy.
4. Notify signals via Telegram bot messages.
5. Run from 9:00 AM to 10:00 PM IST every hour.
6. Provide a backtesting feature for validating the strategy.

## Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the API keys and settings in `config.py`:
   ```python
   # Optional: Binance API credentials (only needed for private endpoints)
   BINANCE_API_KEY = 'your_api_key_here'
   BINANCE_SECRET_KEY = 'your_secret_key_here'
   
   # Required: Telegram bot credentials (for notifications)
   TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token_here'
   TELEGRAM_CHAT_ID = 'your_chat_id_here'
   ```
4. Update `pairs.csv` with your desired trading pairs (one per line, e.g., `BTC/USDT`)
5. Run the bot:
   ```bash
   python main.py
   ```

## How It Works

The strategy uses:

- **Bollinger Bands**:
  - Default settings of 20-period moving average with a 2-standard deviations multiplier.
  
- **Heikin Ashi Candles**:
  - Calculated dynamically using OHLC data for accurate results.

### Signal Generation Logic

#### Buy Signal:
- Look at the latest 2-3 candles.
- If the red HA candle (downward candle) touches or crosses the lower Bollinger Band on its body or wick, and the next candle is green (upward HA candle) with 30% body size, a buy signal is generated.

#### Sell Signal:
- Look at the latest 2-3 candles.
- If the green HA candle (upward candle) touches or crosses the upper Bollinger Band on its body or wick, and the next candle is red (downward HA candle) with 30% body size, a sell signal is generated.

### Telegram Notifications
- Signals are sent every hour in the format:
  - **1Hr BH**:
    - BUY:
      - List of coin names.
    - SELL:
      - List of coin names.

## Development Plan
- [x] Fetch Data from Binance API (using CCXT library)
- [x] Compute BB and HA indicators with 100% accuracy
- [x] Identify Buy/Sell signals accurately as per strategy
- [x] Notify signals via Telegram
- [x] Deploy locally to run every hour between 9AM-10PM IST
- [ ] Create a backtesting utility (future enhancement)

## Configuration
You need to set up your Telegram bot token in the `config.py` file. Binance API credentials are optional (only needed for private endpoints; public market data works without authentication).

```python
# Optional: Binance API credentials
BINANCE_API_KEY = ''
BINANCE_SECRET_KEY = ''

# Required: Telegram bot credentials
TELEGRAM_BOT_TOKEN = 'your_telegram_bot_token_here'
TELEGRAM_CHAT_ID = 'your_chat_id_here'
```

### Getting Telegram Credentials

1. Create a bot by chatting with [@BotFather](https://t.me/botfather) on Telegram
2. Use `/newbot` command and follow the instructions
3. Copy the bot token provided by BotFather
4. Get your chat ID by sending a message to your bot and visiting:
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

## Usage

Simply run:
```bash
python main.py
```

The bot will:
- Load trading pairs from `pairs.csv`
- Fetch hourly OHLCV data from Binance
- Calculate Bollinger Bands and Heikin Ashi indicators
- Identify buy/sell signals based on the strategy
- Send notifications via Telegram
- Run automatically every hour between 9 AM - 10 PM IST

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---