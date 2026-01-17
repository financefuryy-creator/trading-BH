"""
Main Binance Trading Bot with Bollinger Bands and Heikin-Ashi strategy.
Runs every 2 hours from 9:30 AM to 9:30 PM IST.
"""
import logging
import schedule
import time
import pandas as pd
from datetime import datetime
import pytz
import os

# Import custom modules
from data_fetcher import BinanceDataFetcher
from signals import scan_multiple_pairs
from telegram_notifier import send_to_multiple_bots
from visual_verification import verify_signals_visually
import config

# Constants
TRADING_SCHEDULE_TIMES = [
    (9, 30),   # 9:30 AM IST
    (11, 30),  # 11:30 AM IST
    (13, 30),  # 1:30 PM IST
    (15, 30),  # 3:30 PM IST
    (17, 30),  # 5:30 PM IST
    (19, 30),  # 7:30 PM IST
    (21, 30),  # 9:30 PM IST
]
TIMEFRAME = '2h'  # 2-hour timeframe for analysis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_trading_pairs(filepath='trading_pairs.csv'):
    """
    Load trading pairs from CSV file.
    
    Args:
        filepath: Path to CSV file with trading pairs
    
    Returns:
        List of trading pair symbols in CCXT format (e.g., 'BTC/USDT')
    """
    try:
        # Try to load from specified filepath, fallback to pairs.csv
        if not os.path.exists(filepath) and os.path.exists('pairs.csv'):
            filepath = 'pairs.csv'
            logger.info(f"Using pairs.csv instead of {filepath}")
        
        df = pd.read_csv(filepath)
        # Convert to CCXT format (e.g., BTCUSDT -> BTC/USDT)
        symbols = []
        for symbol in df['symbol'].tolist():
            if 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                symbols.append(f"{base}/USDT")
            else:
                symbols.append(symbol)
        
        logger.info(f"Loaded {len(symbols)} trading pairs from {filepath}")
        return symbols
    except Exception as e:
        logger.error(f"Error loading trading pairs: {e}")
        return []


def run_trading_bot():
    """Main function to run the trading bot."""
    logger.info("=" * 60)
    logger.info("Starting trading bot execution")
    logger.info("=" * 60)
    
    try:
        # Load trading pairs
        symbols = load_trading_pairs()
        if not symbols:
            logger.error("No trading pairs loaded. Exiting.")
            return
        
        logger.info(f"Trading pairs: {', '.join(symbols)}")
        
        # Initialize data fetcher
        fetcher = BinanceDataFetcher()
        
        # Fetch OHLC data for all pairs
        logger.info(f"Fetching OHLC data from Binance (timeframe: {TIMEFRAME})...")
        data_dict = fetcher.fetch_multiple_pairs(symbols, timeframe=TIMEFRAME, limit=100)
        
        if not data_dict:
            logger.error("Failed to fetch data for any trading pairs")
            return
        
        logger.info(f"Successfully fetched data for {len(data_dict)} pairs")
        
        # Generate signals
        logger.info("Scanning for buy/sell signals...")
        signals = scan_multiple_pairs(data_dict, min_body_size=30)
        
        logger.info(f"Signals generated - BUY: {len(signals['BUY'])}, SELL: {len(signals['SELL'])}")
        if signals['BUY']:
            logger.info(f"BUY signals: {', '.join(signals['BUY'])}")
        if signals['SELL']:
            logger.info(f"SELL signals: {', '.join(signals['SELL'])}")
        
        # Generate visual verification charts for signals
        if signals['BUY'] or signals['SELL']:
            logger.info("Generating visual verification charts...")
            chart_paths = verify_signals_visually(data_dict, signals)
            if chart_paths:
                logger.info(f"Visual verification complete. Charts saved: {len(chart_paths)}")
                for symbol, path in chart_paths.items():
                    logger.info(f"  {symbol}: {path}")
        
        # Send notifications to both Telegram bots
        bot_configs = [
            (config.TELEGRAM_BOT_TOKEN_1, config.TELEGRAM_CHAT_ID_1),
            (config.TELEGRAM_BOT_TOKEN_2, config.TELEGRAM_CHAT_ID_2)
        ]
        
        logger.info("Sending notifications to Telegram bots...")
        results = send_to_multiple_bots(signals, bot_configs)
        
        success_count = sum(results)
        logger.info(f"Telegram notifications sent: {success_count}/{len(bot_configs)} successful")
        
    except Exception as e:
        logger.error(f"Error in trading bot execution: {e}", exc_info=True)
    
    logger.info("Trading bot execution completed")
    logger.info("=" * 60)


def is_scheduled_time():
    """
    Check if current time matches one of the scheduled execution times.
    
    Returns:
        True if current time matches scheduled time, False otherwise
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_time = (now.hour, now.minute)
    
    # Check if current time matches any scheduled time (with 1-minute tolerance)
    for hour, minute in TRADING_SCHEDULE_TIMES:
        if now.hour == hour and abs(now.minute - minute) <= 1:
            return True
    return False


def job_wrapper():
    """Wrapper function to check scheduled time before running the bot."""
    if is_scheduled_time():
        run_trading_bot()
    else:
        logger.debug("Not a scheduled execution time. Skipping.")


def main():
    """Main entry point for the bot."""
    logger.info("Trading Bot Started")
    logger.info("Running every 2 hours: 9:30 AM, 11:30 AM, 1:30 PM, 3:30 PM, 5:30 PM, 7:30 PM, 9:30 PM IST")
    logger.info("Press Ctrl+C to stop")
    
    # Schedule the job to run at specific times
    for hour, minute in TRADING_SCHEDULE_TIMES:
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(run_trading_bot)
        logger.info(f"Scheduled execution at {hour:02d}:{minute:02d} IST")
    
    # Run immediately on startup if at scheduled time
    if is_scheduled_time():
        logger.info("Running initial execution...")
        run_trading_bot()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)


if __name__ == "__main__":
    main()
