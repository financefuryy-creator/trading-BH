# Trading BH Bot

This repository contains the code for a Binance crypto futures trading bot that scans for setups based on Bollinger Band (BB) and Heikin Ashi (HA) indicators on the 1-hour timeframe.

The bot will:

1. Fetch OHLC data from Binance API for specific trading pairs defined in the `binance pairs.csv` file.
2. Compute Bollinger Bands (20-period, 2 STD) and Heikin Ashi candles with 100% accuracy.
3. Identify buy and sell signals based on the strict BH strategy rules.
4. Notify signals via Telegram bot messages to configured channels.
5. Run from 9:00 AM to 10:00 PM IST every hour (configurable).
6. Provide a backtesting feature for validating the strategy on historical data.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/financefuryy-creator/trading-BH.git
   cd trading-BH
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Telegram credentials in `config.py` (already set up).

4. Add trading pairs to `binance pairs.csv` (one per line in format: SYMBOL/USDT).

## Usage

### Running the Bot

**Single Scan (Testing):**
```bash
python main.py
```

**Continuous Operation (Production):**
Edit `main.py` and uncomment `bot.run_continuously()` in the main function, then:
```bash
python main.py
```

### Backtesting

Test the strategy on historical data:
```bash
python backtest.py
```

### Testing Signal Logic

Verify signal generation logic with unit tests:
```bash
python test_signals.py
```

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

*BUY:*
  • DUSK
  • ARB

*SELL:*
  • CFX

_Scanned at 2026-01-17 15:00:00 IST_
```

## Configuration

The `config.py` file contains Telegram bot credentials (already configured):

```python
TELEGRAM_BOT_TOKEN_1 = 'your_bot_token_1'
TELEGRAM_CHAT_ID_1 = 'your_chat_id_1'

TELEGRAM_BOT_TOKEN_2 = 'your_bot_token_2'
TELEGRAM_CHAT_ID_2 = 'your_chat_id_2'
```

## File Structure

```
trading-BH/
├── main.py              # Main trading bot with signal generation
├── backtest.py          # Backtesting utility for historical validation
├── test_signals.py      # Unit tests for signal logic
├── config.py            # Configuration (Telegram credentials)
├── binance pairs.csv    # Trading pairs to monitor
├── requirements.txt     # Python dependencies
└── README.md           # Documentation
```

## Testing & Validation

The bot includes comprehensive testing:

1. **Unit Tests** (`test_signals.py`):
   - Body size calculation accuracy
   - Candle color detection
   - Bollinger Band touch detection
   - Buy signal generation
   - Sell signal generation
   - False signal prevention

2. **Backtesting** (`backtest.py`):
   - Historical data analysis
   - Signal frequency validation
   - Strategy performance review

3. **Example Pairs Tested**:
   - DUSK/USDT
   - ARB/USDT
   - CFX/USDT
   - ETHFI/USDT

All tests pass successfully, confirming accurate signal generation.

## Disclaimer
This system is for educational purposes only and should not be considered as financial advice. Cryptocurrency trading is highly volatile and carries a high level of risk. Trade responsibly.

---