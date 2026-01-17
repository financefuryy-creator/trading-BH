"""
Main Binance Trading Bot with Bollinger Bands and Heikin-Ashi strategy.
Runs hourly from 9:00 AM to 10:00 PM IST.
"""
import logging
import schedule
import time
import pandas as pd
from datetime import datetime
import pytz

# Import custom modules
from data_fetcher import BinanceDataFetcher
from signals import scan_multiple_pairs
from telegram_notifier import send_to_multiple_bots
import config

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
        logger.info("Fetching OHLC data from Binance...")
        data_dict = fetcher.fetch_multiple_pairs(symbols, timeframe='1h', limit=100)
        
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


def is_within_trading_hours():
    """
    Check if current time is within trading hours (9 AM - 10 PM IST).
    
    Returns:
        True if within trading hours, False otherwise
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    current_hour = now.hour
    
    # Trading hours: 9 AM (9) to 10 PM (22)
    return 9 <= current_hour <= 22


def job_wrapper():
    """Wrapper function to check trading hours before running the bot."""
    if is_within_trading_hours():
        run_trading_bot()
    else:
        logger.info("Outside trading hours (9 AM - 10 PM IST). Skipping execution.")


def main():
    """Main entry point for the bot."""
    logger.info("Trading Bot Started")
    logger.info("Running hourly from 9:00 AM to 10:00 PM IST")
    logger.info("Press Ctrl+C to stop")
    
    # Schedule the job to run every hour
    schedule.every().hour.at(":00").do(job_wrapper)
    
    # Run immediately on startup if within trading hours
    if is_within_trading_hours():
        logger.info("Running initial execution...")
        run_trading_bot()
    
    # Keep the script running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Trading bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}", exc_info=True)


if __name__ == "__main__":
    main()
