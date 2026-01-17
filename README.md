# Trading BH Bot

This repository contains the code for a Binance crypto futures trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 1-hour timeframe.

The bot will:

1. Fetch OHLC data from the Binance API for specific trading pairs defined in the `binance pairs.csv` file.
2. Compute Bollinger Bands and Heikin Ashi candles.
3. Identify buy and sell signals based on the provided strategy.
4. Notify signals via Telegram bot messages.
5. **Execute at 30 minutes past every hour from 9:30 AM to 10:30 PM IST** (14 executions per day).
6. Provide a backtesting feature for validating the strategy.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/financefuryy-creator/trading-BH.git
   cd trading-BH
   ```
3. Configure the API keys and settings in `config.py`.
4. **Important:** Ensure your system timezone is set to IST (Asia/Kolkata) for correct schedule execution:
   ```bash
   # On Linux/Mac
   export TZ=Asia/Kolkata
   
   # Or set system timezone permanently
   sudo timedatectl set-timezone Asia/Kolkata
   ```
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

## Development Plan
- Fetch Data from CoinDCX API.
- Compute BB and HA indicators with 100% accuracy.
- Identify Buy/Sell signals accurately as per strategy.
- Notify signals via Telegram.
- Create a backtesting utility.
- **Deploy locally to run at :30 of every hour from 9:30 AM to 10:30 PM IST** (14 times daily).

*SELL:*
  • CFX

_Scanned at 2026-01-17 15:00:00 IST_
```

## Visualization

To validate signal accuracy visually, run:
```bash
python visualize_signals.py BTC/USDT
```

This will generate charts showing Heikin-Ashi candles, Bollinger Bands, and detected signals for manual validation.

## Configuration
Telegram bot credentials are configured in the `config.py` file. The bot uses Binance public API which doesn't require API keys for fetching market data.

**Security Note**: In production, it's recommended to move sensitive credentials (Telegram tokens) to environment variables instead of committing them to the repository.

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---