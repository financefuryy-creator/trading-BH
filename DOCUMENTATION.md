# Binance Trading Bot - Technical Documentation

## Overview
This bot scans Binance futures markets for trading opportunities based on Heikin-Ashi candle patterns and Bollinger Bands on the 1-hour timeframe.

## Signal Detection Logic

### Buy Signal Requirements:
1. **Previous Candle (n-1)**: Must be a RED Heikin-Ashi candle
2. **Bollinger Band Touch**: The red candle must touch or cross the LOWER Bollinger Band
   - Checked on both the candle body AND the wick (low)
3. **Current Candle (n)**: Must be a GREEN Heikin-Ashi candle
4. **Body Size**: The green candle must have at least 30% body size relative to its full range

### Sell Signal Requirements:
1. **Previous Candle (n-1)**: Must be a GREEN Heikin-Ashi candle
2. **Bollinger Band Touch**: The green candle must touch or cross the UPPER Bollinger Band
   - Checked on both the candle body AND the wick (high)
3. **Current Candle (n)**: Must be a RED Heikin-Ashi candle
4. **Body Size**: The red candle must have at least 30% body size relative to its full range

## Technical Indicators

### Heikin-Ashi Candles
Heikin-Ashi candles are calculated using the following formulas:

```
HA_Close = (Open + High + Low + Close) / 4
HA_Open = (Previous HA_Open + Previous HA_Close) / 2
HA_High = Max(High, HA_Open, HA_Close)
HA_Low = Min(Low, HA_Open, HA_Close)
```

Candle Color:
- GREEN (Bullish): HA_Close >= HA_Open
- RED (Bearish): HA_Close < HA_Open

Body Percentage:
```
Body = |HA_Close - HA_Open|
Range = HA_High - HA_Low
Body_Percentage = (Body / Range) * 100
```

### Bollinger Bands
Standard Bollinger Bands with:
- Period: 20
- Standard Deviation: 2

```
SMA = Simple Moving Average of Close (20 periods)
STD = Standard Deviation of Close (20 periods)
Upper_Band = SMA + (2 * STD)
Lower_Band = SMA - (2 * STD)
```

## Execution Schedule

The bot runs at **22 minutes past each hour** (XX:22) between:
- **Start**: 9:22 AM IST
- **End**: 10:22 PM IST

This provides 14 scan opportunities per day:
- 9:22, 10:22, 11:22, 12:22, 13:22, 14:22, 15:22, 16:22, 17:22, 18:22, 19:22, 20:22, 21:22, 22:22

## Trading Pairs

The bot scans all pairs listed in `binance pairs.csv`. Default pairs include:
- BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, XRP/USDT
- ADA/USDT, DOGE/USDT, AVAX/USDT, DOT/USDT, MATIC/USDT
- LINK/USDT, UNI/USDT, LTC/USDT, ATOM/USDT, ETC/USDT

## Telegram Notifications

When signals are detected, the bot sends formatted messages to configured Telegram chats:

```
1Hr BH - 2026-01-17 15:22:00 IST

BUY:
  • BTC
  • ETH

SELL:
  • SOL
```

## Files Structure

- `main.py` - Core trading bot with signal detection and scheduling
- `visualize_signals.py` - Visualization tool for manual validation
- `config.py` - Telegram bot credentials
- `binance pairs.csv` - List of trading pairs to scan
- `test_logic.py` - Logic validation tests
- `test_schedule.py` - Schedule validation tests

## Running the Bot

### Start the bot:
```bash
python main.py
```

### Test signal detection:
```bash
python test_logic.py
```

### Visualize signals for a pair:
```bash
python visualize_signals.py BTC/USDT
```

## Dependencies

- ccxt - Cryptocurrency exchange integration
- pandas - Data manipulation
- numpy - Numerical operations
- schedule - Task scheduling
- requests - HTTP requests for Telegram
- pytz - Timezone handling
- matplotlib - Chart visualization

Install all dependencies:
```bash
pip install -r requirements.txt
```

## Signal Accuracy Validation

The bot's signal detection logic has been designed to match visual chart analysis:

1. **Precise HA Calculation**: Uses the standard HA formulas with proper initialization
2. **BB Touch Detection**: Checks both body and wick contact with BB levels
3. **Body Size Validation**: Ensures minimum 30% body for confirmation candles
4. **Look-back Window**: Examines last 2-3 candles to catch all transitions

Visual validation can be performed using the `visualize_signals.py` tool which generates charts showing:
- Heikin-Ashi candles (color-coded)
- Bollinger Bands with shaded region
- Detected buy signals (green arrows)
- Detected sell signals (red arrows)

## Logging

All bot activities are logged to:
- Console (stdout)
- File: `trading_bot.log`

Log levels:
- INFO: Normal operations, signals detected, scans completed
- ERROR: API failures, data fetch issues, Telegram send failures

## Error Handling

The bot includes robust error handling for:
- Network failures
- API rate limits
- Invalid trading pairs
- Missing data
- Telegram sending failures

Each error is logged and the bot continues operation with remaining pairs.
