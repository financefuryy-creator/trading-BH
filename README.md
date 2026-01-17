# Trading BH Bot

This repository contains the code for creating a crypto futures trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 1-hour timeframe.

The bot will:

1. Fetch OHLC data from the Binance API for specific trading pairs defined in the `binance pairs.csv` file.
2. Compute Bollinger Bands and Heikin Ashi candles.
3. Identify buy and sell signals based on the provided strategy.
4. Notify signals via Telegram bot messages.
5. Run at 22 minutes past each hour (XX:22) from 9:22 AM to 10:22 PM IST.
6. Provide visualization tools for validating signal accuracy.

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
- Signals are sent every hour in the format:
  - **1Hr BH**:
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
- Deploy locally to run every hour between 9AM-10PM IST.

## Visualization

To validate signal accuracy visually, run:
```bash
python visualize_signals.py BTC/USDT
```

This will generate charts showing Heikin-Ashi candles, Bollinger Bands, and detected signals for manual validation.

## Configuration
Telegram bot credentials are configured in the `config.py` file. The bot uses Binance public API which doesn't require API keys for fetching market data.

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---