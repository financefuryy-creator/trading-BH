#!/usr/bin/env python3
"""
Binance Trading Bot - Bollinger Bands & Heikin-Ashi Strategy
Executes every 2 hours at specific IST times: 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM
"""

import ccxt
import pandas as pd
import numpy as np
import schedule
import time
import logging
import os
from datetime import datetime, timedelta
import pytz
from telegram import Bot
import asyncio
from config import TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1, TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Binance exchange
exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}  # Use futures market
})

# IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Set environment timezone to IST for schedule library
os.environ['TZ'] = 'Asia/Kolkata'
try:
    time.tzset()  # Available on Unix-like systems
except AttributeError:
    logger.warning("time.tzset() not available on this system. Ensure system timezone is set to IST.")

def load_pairs():
    """Load trading pairs from CSV file"""
    try:
        # Try with the actual filename (with space)
        pairs_file = 'binance pairs.csv'
        with open(pairs_file, 'r') as f:
            content = f.read().strip()
            # If the file just references itself, use defaults
            if content == 'binance pairs.csv' or content == '':
                logger.warning("pairs file is empty or self-referencing, using default pairs")
                return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            pairs = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
            if not pairs:
                logger.warning("No pairs found in file, using defaults")
                return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            logger.info(f"Loaded {len(pairs)} pairs from {pairs_file}")
            return pairs
    except FileNotFoundError:
        logger.warning("binance pairs.csv not found, using default pairs")
        return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']

def fetch_ohlcv(symbol, timeframe='2h', limit=100):
    """
    Fetch OHLCV data from Binance
    
    Args:
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe (default: '2h' for 2-hour candles)
        limit: Number of candles to fetch
    
    Returns:
        pandas DataFrame with OHLCV data
    """
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    Calculate Bollinger Bands
    
    Args:
        df: DataFrame with OHLCV data
        period: Moving average period (default: 20)
        std_dev: Standard deviation multiplier (default: 2)
    
    Returns:
        DataFrame with BB columns added
    """
    df = df.copy()
    df['bb_middle'] = df['close'].rolling(window=period).mean()
    df['bb_std'] = df['close'].rolling(window=period).std()
    df['bb_upper'] = df['bb_middle'] + (std_dev * df['bb_std'])
    df['bb_lower'] = df['bb_middle'] - (std_dev * df['bb_std'])
    return df

def calculate_heikin_ashi(df):
    """
    Calculate Heikin-Ashi candles
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        DataFrame with HA columns added
    """
    df = df.copy()
    
    # HA Close
    df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    # HA Open (first candle uses regular open)
    df['ha_open'] = 0.0
    df.loc[df.index[0], 'ha_open'] = df.loc[df.index[0], 'open']
    
    for i in range(1, len(df)):
        df.loc[df.index[i], 'ha_open'] = (df.loc[df.index[i-1], 'ha_open'] + df.loc[df.index[i-1], 'ha_close']) / 2
    
    # HA High and Low
    df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
    df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
    
    # Calculate body size percentage
    df['ha_body_size'] = abs(df['ha_close'] - df['ha_open'])
    df['ha_range'] = df['ha_high'] - df['ha_low']
    df['ha_body_pct'] = (df['ha_body_size'] / df['ha_range']) * 100
    
    # Determine candle color (green = bullish, red = bearish)
    df['ha_color'] = np.where(df['ha_close'] > df['ha_open'], 'green', 'red')
    
    return df

def generate_signals(df):
    """
    Generate buy/sell signals based on BB and HA strategy
    
    Buy Signal:
    - Look at latest 2-3 candles
    - Red HA candle touches/crosses lower BB (body or wick)
    - Next candle is green HA with >= 30% body size
    
    Sell Signal:
    - Look at latest 2-3 candles
    - Green HA candle touches/crosses upper BB (body or wick)
    - Next candle is red HA with >= 30% body size
    
    Args:
        df: DataFrame with BB and HA indicators
    
    Returns:
        'BUY', 'SELL', or None
    """
    if len(df) < 3:
        return None
    
    # Get last 3 candles
    last_3 = df.tail(3).reset_index(drop=True)
    
    # Check for BUY signal
    for i in range(len(last_3) - 1):
        current = last_3.iloc[i]
        next_candle = last_3.iloc[i + 1]
        
        # Red candle touching lower BB
        if current['ha_color'] == 'red':
            touches_lower = (current['ha_low'] <= current['bb_lower']) or (current['ha_close'] <= current['bb_lower'])
            
            # Next candle is green with >= 30% body
            if touches_lower and next_candle['ha_color'] == 'green' and next_candle['ha_body_pct'] >= 30:
                return 'BUY'
    
    # Check for SELL signal
    for i in range(len(last_3) - 1):
        current = last_3.iloc[i]
        next_candle = last_3.iloc[i + 1]
        
        # Green candle touching upper BB
        if current['ha_color'] == 'green':
            touches_upper = (current['ha_high'] >= current['bb_upper']) or (current['ha_close'] >= current['bb_upper'])
            
            # Next candle is red with >= 30% body
            if touches_upper and next_candle['ha_color'] == 'red' and next_candle['ha_body_pct'] >= 30:
                return 'SELL'
    
    return None

def scan_pairs(pairs):
    """
    Scan all trading pairs for signals
    
    Args:
        pairs: List of trading pairs
    
    Returns:
        Dictionary with 'BUY' and 'SELL' lists
    """
    signals = {'BUY': [], 'SELL': []}
    
    for pair in pairs:
        try:
            logger.info(f"Scanning {pair}...")
            
            # Fetch 2-hour candle data
            df = fetch_ohlcv(pair, timeframe='2h', limit=50)
            if df is None or len(df) < 25:
                logger.warning(f"Insufficient data for {pair}")
                continue
            
            # Calculate indicators
            df = calculate_bollinger_bands(df)
            df = calculate_heikin_ashi(df)
            
            # Generate signal
            signal = generate_signals(df)
            
            if signal == 'BUY':
                signals['BUY'].append(pair)
                logger.info(f"BUY signal for {pair}")
            elif signal == 'SELL':
                signals['SELL'].append(pair)
                logger.info(f"SELL signal for {pair}")
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error scanning {pair}: {e}")
            continue
    
    return signals

async def send_telegram_message(bot_token, chat_id, message):
    """Send message via Telegram bot"""
    try:
        bot = Bot(token=bot_token)
        await bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
        logger.info(f"Message sent to chat_id {chat_id}")
    except Exception as e:
        logger.error(f"Error sending Telegram message to {chat_id}: {e}")

def format_telegram_message(signals):
    """
    Format signals for Telegram notification with GHTB header
    
    Args:
        signals: Dictionary with 'BUY' and 'SELL' lists
    
    Returns:
        Formatted message string
    """
    message = "<b>GHTB</b>\n\n"
    message += "<b>2Hr BH</b>:\n\n"
    
    # BUY signals
    message += "<b>BUY:</b>\n"
    if signals['BUY']:
        for pair in signals['BUY']:
            # Extract coin name (e.g., BTC from BTC/USDT)
            coin = pair.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "  • None\n"
    
    message += "\n"
    
    # SELL signals
    message += "<b>SELL:</b>\n"
    if signals['SELL']:
        for pair in signals['SELL']:
            # Extract coin name
            coin = pair.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "  • None\n"
    
    # Add timestamp in IST
    ist_time = datetime.now(IST)
    message += f"\n<i>Time: {ist_time.strftime('%Y-%m-%d %I:%M %p IST')}</i>"
    
    return message

async def notify_signals(signals):
    """Send signal notifications to all configured Telegram bots"""
    message = format_telegram_message(signals)
    logger.info(f"Notification message:\n{message}")
    
    # Send to both configured bots
    await send_telegram_message(TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1, message)
    await send_telegram_message(TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2, message)

def run_bot():
    """Main bot execution function"""
    try:
        ist_time = datetime.now(IST)
        logger.info(f"=== Bot execution started at {ist_time.strftime('%Y-%m-%d %I:%M %p IST')} ===")
        
        # Load trading pairs
        pairs = load_pairs()
        logger.info(f"Loaded {len(pairs)} trading pairs")
        
        # Scan for signals
        signals = scan_pairs(pairs)
        
        logger.info(f"Scan complete - BUY: {len(signals['BUY'])}, SELL: {len(signals['SELL'])}")
        
        # Send notifications
        asyncio.run(notify_signals(signals))
        
        logger.info("=== Bot execution completed ===\n")
        
    except Exception as e:
        logger.error(f"Error in bot execution: {e}", exc_info=True)

def schedule_bot():
    """
    Schedule bot to run at specific IST times every day:
    9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM
    
    The environment timezone is set to IST at module import to ensure
    the schedule library interprets times correctly.
    """
    # Define execution times in IST (24-hour format)
    execution_times = [
        "09:30",  # 9:30 AM
        "11:30",  # 11:30 AM
        "13:30",  # 1:30 PM
        "15:30",  # 3:30 PM
        "17:30",  # 5:30 PM
        "19:30",  # 7:30 PM
        "21:30",  # 9:30 PM
    ]
    
    # Schedule for each time
    for exec_time in execution_times:
        schedule.every().day.at(exec_time).do(run_bot)
        logger.info(f"Scheduled bot execution at {exec_time} IST")
    
    # Log current timezone for verification
    current_time = datetime.now(IST)
    logger.info(f"Current IST time: {current_time.strftime('%Y-%m-%d %I:%M %p IST')}")
    logger.info("Bot scheduler initialized. Waiting for scheduled times...")
    logger.info("Execution schedule: Every 2 hours at 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM IST")

def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Binance Trading Bot - Bollinger Bands & Heikin-Ashi Strategy")
    logger.info("Timeframe: 2-hour candles")
    logger.info("Schedule: Every 2 hours at specific IST times")
    logger.info("=" * 60)
    
    # Run once immediately for initial testing/verification
    logger.info("Running initial scan...")
    run_bot()
    
    # Set up scheduler
    schedule_bot()
    
    # Keep the script running and check for scheduled tasks
    while True:
        try:
            # Calculate next run time
            next_run = schedule.next_run()
            if next_run:
                # Convert to IST for display
                ist_next = next_run.astimezone(IST) if hasattr(next_run, 'astimezone') else datetime.now(IST) + timedelta(hours=1)
                logger.info(f"Next scheduled run: {ist_next.strftime('%Y-%m-%d %I:%M %p IST')}")
            
            # Run pending scheduled tasks
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    main()
