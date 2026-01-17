# Quick Start Guide

This guide will help you get the Binance trading bot up and running quickly.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Internet connection

## Installation Steps

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- ccxt (for Binance API)
- pandas and numpy (for data processing)
- schedule (for scheduling)
- python-telegram-bot (for notifications)
- pytz (for timezone handling)

### 2. Verify Configuration

The `config.py` file is already configured with Telegram bot credentials:
- Bot 1: Token and Chat ID for the first notification channel
- Bot 2: Token and Chat ID for the second notification channel

### 3. Customize Trading Pairs (Optional)

Edit `trading_pairs.csv` to add or remove trading pairs:

```csv
symbol
BTCUSDT
ETHUSDT
BNBUSDT
...
```

## Running the Bot

### Start the Trading Bot

```bash
python main.py
```

The bot will:
- Check if current time is within trading hours (9 AM - 10 PM IST)
- Run immediately if within hours
- Schedule hourly execution at the top of each hour
- Log all activities to `trading_bot.log` and console

### Stop the Bot

Press `Ctrl+C` to stop the bot gracefully.

## Running Backtests

### Basic Backtest

Test the strategy on all pairs in `trading_pairs.csv`:

```bash
python run_backtest.py
```

### Backtest Specific Pairs

```bash
python run_backtest.py --pairs BTC/USDT ETH/USDT BNB/USDT
```

### Customize Backtest Parameters

```bash
python run_backtest.py --limit 1000 --capital 20000
```

Options:
- `--limit`: Number of historical 1h candles (default: 500)
- `--capital`: Initial capital in USD (default: 10000)

## Understanding the Output

### Trading Bot Output

The bot will log:
- ✓ Trading pairs loaded
- ✓ Data fetched from Binance
- ✓ Signals generated (BUY/SELL)
- ✓ Telegram notifications sent

### Telegram Messages

Messages are sent in the format:

```
**1Hr BH**:

**BUY**:
  • BTC
  • ETH

**SELL**:
  • BNB
  • XRP
```

### Backtest Results

Backtests show:
- Initial and final capital
- Total profit/loss
- Returns percentage
- Win rate
- Number of trades

## Logs

All activities are logged to:
- **Console**: Real-time output
- **trading_bot.log**: Detailed file log

## Troubleshooting

### Network Errors

If you see network errors:
- Check your internet connection
- Binance API might be temporarily unavailable (bot will retry next hour)

### Telegram Errors

If notifications fail:
- Verify bot tokens and chat IDs in `config.py`
- Ensure bots are active and have permission to send messages

### No Signals Generated

This is normal! Signals are only generated when:
- Red HA candle touches lower BB + next candle is green with ≥30% body (BUY)
- Green HA candle touches upper BB + next candle is red with ≥30% body (SELL)

These conditions may not be met every hour.

## Next Steps

1. Monitor the `trading_bot.log` file for the first few runs
2. Check Telegram messages to verify notifications are working
3. Run backtests to understand the strategy's performance
4. Adjust trading pairs based on your preferences

## Support

For issues or questions, check the logs first:

```bash
tail -f trading_bot.log
```

This shows real-time log updates as the bot runs.
