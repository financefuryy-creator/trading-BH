# Trading BH Bot

This repository contains the code for creating a crypto futures trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 2-hour timeframe.

The bot will:

1. Fetch OHLC data from the Binance API for specific trading pairs defined in the `binance pairs.csv` file.
2. Compute Bollinger Bands and Heikin Ashi candles.
3. Identify buy and sell signals based on the provided strategy.
4. Notify signals via Telegram bot messages.
5. Run every 2 hours at specific IST times: 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM.
6. Provide a backtesting feature for validating the strategy.

## Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the API keys and settings in `config.py`.
4. Run the bot:
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
- Signals are sent every 2 hours in the format:
  - **GHTB**
  - **2Hr BH**:
    - BUY:
      - List of coin names.
    - SELL:
      - List of coin names.

## Development Plan
- Fetch Data from CoinDCX API.
- Compute BB and HA indicators with 100% accuracy.
- Identify Buy/Sell signals accurately as per strategy.
- Notify signals via Telegram.
- Create a backtesting utility.
- Deploy locally to run every 2 hours at specific IST times: 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM.

## Configuration
You need to set up your Telegram bot tokens and chat IDs in the `config.py` file.

```python
TELEGRAM_BOT_TOKEN_1 = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID_1 = "your_chat_id_here"
TELEGRAM_BOT_TOKEN_2 = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID_2 = "your_chat_id_here"
```

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---