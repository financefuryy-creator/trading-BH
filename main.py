#!/usr/bin/env python3
"""
Binance Trading Bot with Bollinger Bands and Heikin-Ashi Strategy
Detects buy/sell signals and sends notifications via Telegram
"""

import ccxt
import pandas as pd
import numpy as np
import schedule
import time
import logging
from datetime import datetime
import pytz
import requests
from config import TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1, TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BinanceTradingBot:
    """Trading bot for detecting BB + Heikin-Ashi signals on Binance"""
    
    # Configuration constants
    MIN_BODY_PERCENTAGE = 30  # Minimum body size as percentage of candle range for signal confirmation
    RATE_LIMIT_DELAY = 0.1    # Delay between API calls in seconds
    
    def __init__(self):
        """Initialize the trading bot"""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        self.timeframe = '1h'
        self.bb_period = 20
        self.bb_std = 2
        self.pairs = self.load_trading_pairs()
        
    def load_trading_pairs(self):
        """Load trading pairs from CSV file"""
        try:
            # Try to read from binance pairs.csv first
            try:
                df = pd.read_csv('binance pairs.csv')
                pairs = df.iloc[:, 0].tolist() if not df.empty else []
            except:
                # Fallback to pairs.csv
                df = pd.read_csv('pairs.csv')
                pairs = df.iloc[:, 0].tolist() if not df.empty else []
            
            # Filter out empty or invalid pairs
            pairs = [p.strip() for p in pairs if isinstance(p, str) and p.strip()]
            
            # If no pairs found, use a default list of popular pairs
            if not pairs:
                pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
                logger.warning(f"No pairs found in CSV, using default pairs: {pairs}")
            
            logger.info(f"Loaded {len(pairs)} trading pairs")
            return pairs
        except Exception as e:
            logger.error(f"Error loading trading pairs: {e}")
            # Return default pairs on error
            return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
    
    def fetch_ohlcv(self, symbol, limit=100):
        """Fetch OHLCV data from Binance"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_heikin_ashi(self, df):
        """Calculate Heikin-Ashi candles from regular OHLCV data"""
        ha_df = df.copy()
        
        # Initialize first HA candle
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_df['ha_open'] = (df['open'] + df['close']) / 2
        ha_df['ha_high'] = df['high']
        ha_df['ha_low'] = df['low']
        
        # Calculate subsequent HA candles
        for i in range(1, len(df)):
            ha_df.loc[i, 'ha_open'] = (ha_df.loc[i-1, 'ha_open'] + ha_df.loc[i-1, 'ha_close']) / 2
            ha_df.loc[i, 'ha_close'] = (df.loc[i, 'open'] + df.loc[i, 'high'] + 
                                        df.loc[i, 'low'] + df.loc[i, 'close']) / 4
            ha_df.loc[i, 'ha_high'] = max(df.loc[i, 'high'], ha_df.loc[i, 'ha_open'], ha_df.loc[i, 'ha_close'])
            ha_df.loc[i, 'ha_low'] = min(df.loc[i, 'low'], ha_df.loc[i, 'ha_open'], ha_df.loc[i, 'ha_close'])
        
        # Determine candle color (True = Green/Bullish, False = Red/Bearish)
        ha_df['ha_color'] = ha_df['ha_close'] >= ha_df['ha_open']
        
        # Calculate body size as percentage of candle range
        ha_range = ha_df['ha_high'] - ha_df['ha_low']
        ha_body = abs(ha_df['ha_close'] - ha_df['ha_open'])
        # Avoid division by zero - 0% body when range is zero (doji candle)
        ha_df['ha_body_pct'] = np.where(ha_range > 0, ha_body / ha_range * 100, 0)
        
        return ha_df
    
    def calculate_bollinger_bands(self, df):
        """Calculate Bollinger Bands"""
        # Use closing price for BB calculation
        df['sma'] = df['close'].rolling(window=self.bb_period).mean()
        df['std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['sma'] + (df['std'] * self.bb_std)
        df['bb_lower'] = df['sma'] - (df['std'] * self.bb_std)
        return df
    
    def check_buy_signal(self, ha_df):
        """
        Check for buy signal:
        - Red HA candle touches or crosses lower BB (on body or wick)
        - Next candle is green HA candle with at least 30% body size
        """
        if len(ha_df) < 3:
            return False
        
        # Look at last 3 candles
        for i in range(-3, -1):  # Check indices -3,-2 (comparing with -2,-1)
            try:
                prev_idx = ha_df.index[i]
                curr_idx = ha_df.index[i+1]
                
                prev_candle = ha_df.loc[prev_idx]
                curr_candle = ha_df.loc[curr_idx]
                
                # Check if previous candle is red (bearish)
                prev_is_red = not prev_candle['ha_color']
                
                # Check if previous red candle touches or crosses lower BB
                # Check both the low (wick) and the body
                prev_touches_lower_bb = (
                    prev_candle['ha_low'] <= prev_candle['bb_lower'] or
                    min(prev_candle['ha_open'], prev_candle['ha_close']) <= prev_candle['bb_lower']
                )
                
                # Check if current candle is green (bullish) with at least minimum body size
                curr_is_green = curr_candle['ha_color']
                curr_body_ok = curr_candle['ha_body_pct'] >= self.MIN_BODY_PERCENTAGE
                
                # Buy signal conditions
                if prev_is_red and prev_touches_lower_bb and curr_is_green and curr_body_ok:
                    return True
                    
            except (KeyError, IndexError):
                continue
        
        return False
    
    def check_sell_signal(self, ha_df):
        """
        Check for sell signal:
        - Green HA candle touches or crosses upper BB (on body or wick)
        - Next candle is red HA candle with at least 30% body size
        """
        if len(ha_df) < 3:
            return False
        
        # Look at last 3 candles
        for i in range(-3, -1):  # Check indices -3,-2 (comparing with -2,-1)
            try:
                prev_idx = ha_df.index[i]
                curr_idx = ha_df.index[i+1]
                
                prev_candle = ha_df.loc[prev_idx]
                curr_candle = ha_df.loc[curr_idx]
                
                # Check if previous candle is green (bullish)
                prev_is_green = prev_candle['ha_color']
                
                # Check if previous green candle touches or crosses upper BB
                # Check both the high (wick) and the body
                prev_touches_upper_bb = (
                    prev_candle['ha_high'] >= prev_candle['bb_upper'] or
                    max(prev_candle['ha_open'], prev_candle['ha_close']) >= prev_candle['bb_upper']
                )
                
                # Check if current candle is red (bearish) with at least minimum body size
                curr_is_red = not curr_candle['ha_color']
                curr_body_ok = curr_candle['ha_body_pct'] >= self.MIN_BODY_PERCENTAGE
                
                # Sell signal conditions
                if prev_is_green and prev_touches_upper_bb and curr_is_red and curr_body_ok:
                    return True
                    
            except (KeyError, IndexError):
                continue
        
        return False
    
    def scan_all_pairs(self):
        """Scan all trading pairs for buy/sell signals"""
        buy_signals = []
        sell_signals = []
        
        logger.info(f"Starting scan of {len(self.pairs)} pairs...")
        
        for symbol in self.pairs:
            try:
                # Fetch OHLCV data
                df = self.fetch_ohlcv(symbol)
                if df is None or len(df) < self.bb_period + 10:
                    continue
                
                # Calculate Bollinger Bands
                df = self.calculate_bollinger_bands(df)
                
                # Calculate Heikin-Ashi
                ha_df = self.calculate_heikin_ashi(df)
                
                # Check for signals
                if self.check_buy_signal(ha_df):
                    buy_signals.append(symbol)
                    logger.info(f"BUY signal detected for {symbol}")
                
                if self.check_sell_signal(ha_df):
                    sell_signals.append(symbol)
                    logger.info(f"SELL signal detected for {symbol}")
                
                # Small delay to respect rate limits
                time.sleep(self.RATE_LIMIT_DELAY)
                
            except Exception as e:
                logger.error(f"Error scanning {symbol}: {e}")
                continue
        
        logger.info(f"Scan complete. Buy signals: {len(buy_signals)}, Sell signals: {len(sell_signals)}")
        return buy_signals, sell_signals
    
    def send_telegram_message(self, message, bot_token, chat_id):
        """Send message via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"Telegram message sent successfully to {chat_id}")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def format_and_send_signals(self, buy_signals, sell_signals):
        """Format signals and send via Telegram"""
        # Get current time in IST
        ist_tz = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
        
        # Format message
        message = f"<b>1Hr BH - {current_time}</b>\n\n"
        
        if buy_signals:
            message += "<b>BUY:</b>\n"
            for symbol in buy_signals:
                # Extract coin name (e.g., BTC from BTC/USDT)
                coin = symbol.split('/')[0]
                message += f"  • {coin}\n"
        else:
            message += "<b>BUY:</b>\n  None\n"
        
        message += "\n"
        
        if sell_signals:
            message += "<b>SELL:</b>\n"
            for symbol in sell_signals:
                # Extract coin name
                coin = symbol.split('/')[0]
                message += f"  • {coin}\n"
        else:
            message += "<b>SELL:</b>\n  None\n"
        
        # Send to both configured Telegram bots
        logger.info(f"Sending signals to Telegram:\n{message}")
        self.send_telegram_message(message, TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1)
        self.send_telegram_message(message, TELEGRAM_BOT_TOKEN_2, TELEGRAM_CHAT_ID_2)
    
    def run_scan(self):
        """Main scan routine"""
        logger.info("=" * 60)
        logger.info("Starting scheduled scan...")
        
        try:
            buy_signals, sell_signals = self.scan_all_pairs()
            self.format_and_send_signals(buy_signals, sell_signals)
            logger.info("Scan completed successfully")
        except Exception as e:
            logger.error(f"Error during scan: {e}")
        
        logger.info("=" * 60)


def is_ist_time_in_range():
    """Check if current IST time is within operating hours"""
    ist_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_tz)
    current_hour = current_time.hour
    current_minute = current_time.minute
    
    # Check if we're at XX:22 and between 9:22 AM and 10:22 PM
    # Operating hours: 9 AM to 10 PM (22:00 in 24-hour format)
    if current_minute == 22:
        if 9 <= current_hour <= 22:
            return True
    return False


def scheduled_task():
    """Task to run at scheduled times"""
    if is_ist_time_in_range():
        bot = BinanceTradingBot()
        bot.run_scan()
    else:
        logger.info("Outside operating hours, skipping scan")


def main():
    """Main function to run the bot"""
    SCHEDULER_CHECK_INTERVAL = 30  # Check schedule every 30 seconds
    
    logger.info("Binance Trading Bot starting...")
    logger.info("Schedule: Every hour at XX:22 between 9:22 AM and 10:22 PM IST")
    
    # Schedule the job to run at 22 minutes past every hour
    schedule.every().hour.at(":22").do(scheduled_task)
    
    # Run immediately on start for testing
    logger.info("Running initial scan...")
    bot = BinanceTradingBot()
    bot.run_scan()
    
    # Keep running
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(SCHEDULER_CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
