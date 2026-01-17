# Trading BH Bot

This repository contains the code for a Binance trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 1-hour timeframe.

The bot will:

1. Fetch OHLC data from the Binance API for specific trading pairs defined in the `trading_pairs.csv` file.
2. Compute Bollinger Bands and Heikin Ashi candles.
3. Identify buy and sell signals based on the provided strategy.
4. Notify signals via Telegram bot messages to two separate bots.
5. Run from 9:00 AM to 10:00 PM IST every hour.
6. Provide a backtesting feature for validating the strategy.

## Installation

1. Clone the repository.
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure the Telegram bot tokens and chat IDs in `config.py` (already configured).
4. Customize trading pairs in `trading_pairs.csv` if needed.
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

## Modules

The bot consists of the following modules:

- **`main.py`**: Main bot script with hourly scheduling (9 AM - 10 PM IST)
- **`data_fetcher.py`**: Fetches OHLC data from Binance API using CCXT
- **`indicators.py`**: Calculates Bollinger Bands and Heikin-Ashi candles
- **`signals.py`**: Generates buy/sell signals based on the strategy
- **`telegram_notifier.py`**: Sends notifications to multiple Telegram bots
- **`backtesting.py`**: Backtesting engine for strategy validation
- **`run_backtest.py`**: Utility script for running backtests
- **`config.py`**: Configuration file with Telegram credentials

## Running the Bot

To start the trading bot:
```bash
python main.py
```

The bot will:
- Run immediately if within trading hours (9 AM - 10 PM IST)
- Schedule hourly execution at the top of each hour
- Log all activities to `trading_bot.log` and console
- Send signals to both configured Telegram bots

## Backtesting

To run a backtest on the strategy:

```bash
# Backtest all pairs in trading_pairs.csv
python run_backtest.py

# Backtest specific pairs
python run_backtest.py --pairs BTC/USDT ETH/USDT

# Customize parameters
python run_backtest.py --limit 1000 --capital 20000
```

Parameters:
- `--pairs`: Trading pairs to backtest (space-separated)
- `--limit`: Number of historical candles to fetch (default: 500)
- `--capital`: Initial capital for backtesting (default: 10000)

## Configuration

The `config.py` file contains Telegram bot credentials:

```python
# Telegram Bot 1
TELEGRAM_BOT_TOKEN_1 = '8182721422:AAEiSsPsKlKB3reWGA5DvJTSulxPOAbNBrQ'
TELEGRAM_CHAT_ID_1 = '7515010163'

# Telegram Bot 2
TELEGRAM_BOT_TOKEN_2 = '8557523608:AAHGJ_UOKEZaJc6iPfW0DITreuQ1Nx2mVv4'
TELEGRAM_CHAT_ID_2 = '7650632969'
```

## Trading Pairs

Edit `trading_pairs.csv` to customize the trading pairs:

```csv
symbol
BTCUSDT
ETHUSDT
BNBUSDT
...
```

The bot will automatically convert symbols to CCXT format (e.g., `BTCUSDT` → `BTC/USDT`).

## Error Handling

The bot includes comprehensive error handling:
- Network errors during data fetching are logged and gracefully handled
- Failed Telegram notifications are logged without stopping execution
- Exchange errors are caught and logged with details
- All errors are logged to `trading_bot.log` for debugging

## Logs

All bot activities are logged to:
- **Console**: Real-time output
- **File**: `trading_bot.log` with detailed information

Log levels:
- INFO: Normal operations, signals generated, notifications sent
- WARNING: Non-critical issues (e.g., no data for a pair)
- ERROR: Critical issues that need attention

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---