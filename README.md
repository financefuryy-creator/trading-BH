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

1. Clone the repository:
   ```bash
   git clone https://github.com/financefuryy-creator/trading-BH.git
   cd trading-BH
   ```
3. Configure the Telegram bot tokens and chat IDs in `config.py` (already configured).
4. Customize trading pairs in `trading_pairs.csv` if needed.
5. Run the bot:
   ```bash
   pip install -r requirements.txt
   ```

## Execution Schedule

The bot executes automatically at **30 minutes past every hour** from **9:30 AM to 10:30 PM IST**:

```
9:30 AM, 10:30 AM, 11:30 AM, 12:30 PM, 1:30 PM, 2:30 PM, 3:30 PM,
4:30 PM, 5:30 PM, 6:30 PM, 7:30 PM, 8:30 PM, 9:30 PM, 10:30 PM
```

- **Total executions:** 14 times per day
- **Timezone:** IST (India Standard Time, UTC+5:30)
- **Pattern:** Every hour at :30 minutes

The bot uses the `schedule` library with proper IST timezone handling to ensure accurate execution times. **Note:** The system timezone should be configured to IST for the schedule to work correctly.

## How It Works

The strategy uses:

- **Bollinger Bands**:
  - Default settings of 20-period moving average with a 2-standard deviations multiplier.
  
- **Heikin Ashi Candles**:
  - Calculated dynamically using OHLC data for accurate results.

### Signal Generation Logic (Strict Implementation)

#### Buy Signal Requirements (ALL must be met):
1. **Previous Candle**: Red Heikin Ashi candle (HA_Close < HA_Open)
2. **BB Touch**: Previous candle's body or wick touches or breaks the lower Bollinger Band
3. **Current Candle**: Green Heikin Ashi candle (HA_Close > HA_Open)
4. **Body Size**: Current candle has at least 30% body size
   - Body Size % = (|HA_Close - HA_Open| / (HA_High - HA_Low)) × 100
   - Must be ≥ 30%

#### Sell Signal Requirements (ALL must be met):
1. **Previous Candle**: Green Heikin Ashi candle (HA_Close > HA_Open)
2. **BB Touch**: Previous candle's body or wick touches or breaks the upper Bollinger Band
3. **Current Candle**: Red Heikin Ashi candle (HA_Close < HA_Open)
4. **Body Size**: Current candle has at least 30% body size
   - Body Size % = (|HA_Close - HA_Open| / (HA_High - HA_Low)) × 100
   - Must be ≥ 30%

#### Key Implementation Details:
- **Heikin Ashi Calculation**: Uses proper HA formula for accurate candle representation
- **BB Touch Detection**: Checks both candle body (close) and wick (high/low) for BB interaction
- **Body Size Verification**: Ensures meaningful reversal candles (not just small movements)
- **Error Handling**: Robust error handling for API failures and data issues

### Telegram Notifications

Signals are sent every hour to both configured Telegram bots in the format:

```
*1Hr BH*

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