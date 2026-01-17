# Binance Trading Bot - Deployment Guide

## Overview
This bot scans Binance futures markets using Bollinger Bands and Heikin-Ashi indicators on 2-hour candles, then sends signals via Telegram.

## Schedule
The bot runs every 2 hours at these IST times:
- 9:30 AM
- 11:30 AM
- 1:30 PM
- 3:30 PM
- 5:30 PM
- 7:30 PM
- 9:30 PM

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Timezone (IMPORTANT)
For accurate scheduling, set your system timezone to IST (Asia/Kolkata):

**Linux/Mac:**
```bash
export TZ=Asia/Kolkata
# Or permanently: sudo timedatectl set-timezone Asia/Kolkata
```

**Windows:**
```powershell
# Set via Control Panel > Date and Time > Change time zone
# Or use: tzutil /s "India Standard Time"
```

**Verify timezone:**
```bash
python -c "from datetime import datetime; import pytz; print(datetime.now(pytz.timezone('Asia/Kolkata')))"
```

### 3. Configure Trading Pairs
Edit `binance pairs.csv` to add/remove trading pairs:
```
BTC/USDT
ETH/USDT
BNB/USDT
SOL/USDT
XRP/USDT
```

### 4. Configure Telegram (Already set in config.py)
The `config.py` file already contains your Telegram bot tokens and chat IDs:
- Bot 1: Token and Chat ID configured
- Bot 2: Token and Chat ID configured

### 5. Run the Bot
```bash
python main.py
```

The bot will:
1. Run an initial scan immediately
2. Schedule future runs at the specified IST times
3. Continue running 24/7

## Telegram Message Format
Every notification includes:

```
GHTB

2Hr BH:

BUY:
  • BTC
  • ETH

SELL:
  • SOL
  • XRP

Time: 2026-01-17 09:30 AM IST
```

## Technical Details

### Indicators
- **Bollinger Bands**: 20-period MA with 2 standard deviations
- **Heikin-Ashi**: Calculated dynamically from OHLCV data
- **Timeframe**: 2-hour candles

### Signal Logic
**BUY Signal:**
- Red HA candle touches/crosses lower Bollinger Band
- Next candle is green HA with ≥30% body size

**SELL Signal:**
- Green HA candle touches/crosses upper Bollinger Band
- Next candle is red HA with ≥30% body size

## Running as a Service

### Linux (systemd)
Create `/etc/systemd/system/trading-bot.service`:
```ini
[Unit]
Description=Binance Trading Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/trading-BH
Environment="TZ=Asia/Kolkata"
ExecStart=/usr/bin/python3 /path/to/trading-BH/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
sudo systemctl status trading-bot
```

### Using screen (Simple alternative)
```bash
screen -S trading-bot
export TZ=Asia/Kolkata
python main.py
# Press Ctrl+A, then D to detach
# Reattach: screen -r trading-bot
```

## Monitoring

### Check Logs
The bot logs to stdout. When running as a service:
```bash
sudo journalctl -u trading-bot -f
```

### Verify Schedule
The bot logs scheduled run times on startup:
```
Scheduled bot execution at 09:30 IST
Scheduled bot execution at 11:30 IST
...
```

## Troubleshooting

### Issue: Bot not running at correct times
- **Solution**: Verify system timezone is set to IST (Asia/Kolkata)
- Check: `date` command should show IST time

### Issue: Telegram messages not received
- **Solution**: Verify bot tokens and chat IDs in `config.py`
- Test: Send a test message using the Telegram Bot API

### Issue: Network errors when fetching data
- **Solution**: Check internet connection and Binance API status
- Binance API: https://api.binance.com/api/v3/ping

### Issue: No signals generated
- This is normal - signals only appear when specific conditions are met
- The bot will send "None" for both BUY and SELL when no setups exist

## Updates and Changes

### To modify schedule times:
Edit the `execution_times` list in `main.py` (lines 331-339)

### To change timeframe:
Modify the `timeframe='2h'` parameter in the `fetch_ohlcv` function

### To adjust Bollinger Bands:
Change `period=20` or `std_dev=2` in `calculate_bollinger_bands` calls

## Support
For issues or questions, check the code comments in `main.py` for detailed explanations of each function.
