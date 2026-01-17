#!/usr/bin/env python3
"""
Trading BH Bot - Bollinger Band & Heikin Ashi Strategy
Executes at 30 minutes past each hour from 9:30 AM to 10:30 PM IST
"""

import schedule
import time
import requests
import pandas as pd
import numpy as np
import talib
from datetime import datetime, timedelta
import pytz
from telegram import Bot
from telegram.error import TelegramError
import logging
from config import TELEGRAM_BOT_TOKEN_1, TELEGRAM_CHAT_ID_1

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')

class TradingBot:
    def __init__(self):
        """Initialize the trading bot"""
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN_1)
        self.chat_id = TELEGRAM_CHAT_ID_1
        self.pairs = self.load_pairs()
        logger.info(f"Trading bot initialized with {len(self.pairs)} pairs")
    
    def load_pairs(self):
        """Load trading pairs from pairs.csv"""
        try:
            with open('pairs.csv', 'r') as f:
                pairs = [line.strip() for line in f.readlines() if line.strip()]
            return pairs
        except Exception as e:
            logger.error(f"Error loading pairs: {e}")
            return []
    
    def fetch_ohlc_data(self, pair, timeframe='1h', limit=100):
        """
        Fetch OHLC data from CoinDCX API
        
        Args:
            pair: Trading pair symbol
            timeframe: Timeframe for candles (default: 1h)
            limit: Number of candles to fetch
        
        Returns:
            DataFrame with OHLC data
        """
        try:
            # TODO: Implement actual CoinDCX API integration
            # CoinDCX API documentation: https://docs.coindcx.com/
            # 
            # Example implementation approach:
            # 1. Use the CoinDCX REST API or WebSocket API
            # 2. Authenticate with API key and secret from config.py
            # 3. Request historical OHLC data for the specified pair and timeframe
            # 4. Parse the response and convert to pandas DataFrame
            #
            # The current implementation uses PLACEHOLDER DATA for demonstration.
            # This will NOT work in production and MUST be replaced with real API calls.
            
            logger.warning(f"Using placeholder data for {pair} - implement real API integration!")
            
            # PLACEHOLDER: Generate sample OHLC data
            # Replace this entire section with actual API calls
            dates = pd.date_range(end=datetime.now(), periods=limit, freq='1H')
            data = {
                'timestamp': dates,
                'open': np.random.uniform(100, 200, limit),
                'high': np.random.uniform(100, 200, limit),
                'low': np.random.uniform(100, 200, limit),
                'close': np.random.uniform(100, 200, limit),
                'volume': np.random.uniform(1000, 10000, limit)
            }
            df = pd.DataFrame(data)
            
            # Ensure high is highest and low is lowest
            df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
            df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLC data for {pair}: {e}")
            return None
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """
        Calculate Bollinger Bands using TA-Lib
        
        Args:
            df: DataFrame with OHLC data
            period: Period for moving average (default: 20)
            std_dev: Standard deviation multiplier (default: 2)
        
        Returns:
            DataFrame with BB columns added
        """
        try:
            close_prices = df['close'].values
            
            # Calculate Bollinger Bands
            upper, middle, lower = talib.BBANDS(
                close_prices,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev,
                matype=0
            )
            
            df['bb_upper'] = upper
            df['bb_middle'] = middle
            df['bb_lower'] = lower
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands: {e}")
            return df
    
    def calculate_heikin_ashi(self, df):
        """
        Calculate Heikin Ashi candles
        
        Args:
            df: DataFrame with OHLC data
        
        Returns:
            DataFrame with HA columns added
        """
        try:
            ha_df = df.copy()
            
            # Heikin Ashi calculations
            ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
            ha_df['ha_open'] = 0.0
            
            # First HA open is average of first regular open and close
            ha_df.loc[0, 'ha_open'] = (df.loc[0, 'open'] + df.loc[0, 'close']) / 2
            
            # Subsequent HA opens
            for i in range(1, len(df)):
                ha_df.loc[i, 'ha_open'] = (ha_df.loc[i-1, 'ha_open'] + ha_df.loc[i-1, 'ha_close']) / 2
            
            ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
            ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
            
            # Determine candle color (green = bullish, red = bearish)
            ha_df['ha_color'] = np.where(ha_df['ha_close'] >= ha_df['ha_open'], 'green', 'red')
            
            # Calculate body size percentage
            ha_df['ha_body_size'] = abs(ha_df['ha_close'] - ha_df['ha_open'])
            ha_df['ha_total_range'] = ha_df['ha_high'] - ha_df['ha_low']
            ha_df['ha_body_pct'] = (ha_df['ha_body_size'] / ha_df['ha_total_range']) * 100
            ha_df['ha_body_pct'] = ha_df['ha_body_pct'].fillna(0)
            
            return ha_df
            
        except Exception as e:
            logger.error(f"Error calculating Heikin Ashi: {e}")
            return df
    
    def check_buy_signal(self, df):
        """
        Check for buy signal:
        - Red HA candle touches/crosses lower BB
        - Next candle is green HA with >= 30% body size
        
        Args:
            df: DataFrame with all indicators
        
        Returns:
            Boolean indicating buy signal
        """
        try:
            if len(df) < 3:
                return False
            
            # Look at last 3 candles
            last_3 = df.tail(3).reset_index(drop=True)
            
            for i in range(len(last_3) - 1):
                current = last_3.iloc[i]
                next_candle = last_3.iloc[i + 1]
                
                # Check if current candle is red and touches/crosses lower BB
                if current['ha_color'] == 'red':
                    touches_lower_bb = (
                        current['ha_low'] <= current['bb_lower'] or
                        current['ha_close'] <= current['bb_lower'] or
                        current['ha_open'] <= current['bb_lower']
                    )
                    
                    # Check if next candle is green with >= 30% body
                    if touches_lower_bb and next_candle['ha_color'] == 'green' and next_candle['ha_body_pct'] >= 30:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking buy signal: {e}")
            return False
    
    def check_sell_signal(self, df):
        """
        Check for sell signal:
        - Green HA candle touches/crosses upper BB
        - Next candle is red HA with >= 30% body size
        
        Args:
            df: DataFrame with all indicators
        
        Returns:
            Boolean indicating sell signal
        """
        try:
            if len(df) < 3:
                return False
            
            # Look at last 3 candles
            last_3 = df.tail(3).reset_index(drop=True)
            
            for i in range(len(last_3) - 1):
                current = last_3.iloc[i]
                next_candle = last_3.iloc[i + 1]
                
                # Check if current candle is green and touches/crosses upper BB
                if current['ha_color'] == 'green':
                    touches_upper_bb = (
                        current['ha_high'] >= current['bb_upper'] or
                        current['ha_close'] >= current['bb_upper'] or
                        current['ha_open'] >= current['bb_upper']
                    )
                    
                    # Check if next candle is red with >= 30% body
                    if touches_upper_bb and next_candle['ha_color'] == 'red' and next_candle['ha_body_pct'] >= 30:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking sell signal: {e}")
            return False
    
    def analyze_pair(self, pair):
        """
        Analyze a trading pair for buy/sell signals
        
        Args:
            pair: Trading pair to analyze
        
        Returns:
            Dict with signal information
        """
        try:
            # Fetch OHLC data
            df = self.fetch_ohlc_data(pair)
            if df is None or len(df) < 50:
                return {'pair': pair, 'signal': None}
            
            # Calculate indicators
            df = self.calculate_bollinger_bands(df)
            df = self.calculate_heikin_ashi(df)
            
            # Check for signals
            buy_signal = self.check_buy_signal(df)
            sell_signal = self.check_sell_signal(df)
            
            if buy_signal:
                return {'pair': pair, 'signal': 'BUY'}
            elif sell_signal:
                return {'pair': pair, 'signal': 'SELL'}
            else:
                return {'pair': pair, 'signal': None}
                
        except Exception as e:
            logger.error(f"Error analyzing pair {pair}: {e}")
            return {'pair': pair, 'signal': None}
    
    def send_telegram_message(self, message):
        """
        Send message via Telegram
        
        Args:
            message: Message text to send
        """
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            logger.info("Telegram message sent successfully")
        except TelegramError as e:
            logger.error(f"Error sending Telegram message: {e}")
    
    def run_analysis(self):
        """
        Run analysis on all pairs and send notifications
        """
        try:
            current_time = datetime.now(IST)
            logger.info(f"Running analysis at {current_time.strftime('%Y-%m-%d %H:%M:%S IST')}")
            
            buy_signals = []
            sell_signals = []
            
            # Analyze each pair
            for pair in self.pairs:
                result = self.analyze_pair(pair)
                if result['signal'] == 'BUY':
                    buy_signals.append(pair)
                elif result['signal'] == 'SELL':
                    sell_signals.append(pair)
            
            # Format message
            message = "📊 *1Hr BH*\n\n"
            
            if buy_signals:
                message += "🟢 *BUY:*\n"
                message += ", ".join(buy_signals) + "\n\n"
            else:
                message += "🟢 *BUY:* None\n\n"
            
            if sell_signals:
                message += "🔴 *SELL:*\n"
                message += ", ".join(sell_signals) + "\n\n"
            else:
                message += "🔴 *SELL:* None\n\n"
            
            message += f"⏰ {current_time.strftime('%H:%M IST')}"
            
            # Send notification
            self.send_telegram_message(message)
            logger.info(f"Analysis complete: {len(buy_signals)} BUY, {len(sell_signals)} SELL signals")
            
        except Exception as e:
            logger.error(f"Error in run_analysis: {e}")


def setup_schedule():
    """
    Setup schedule to run at 30 minutes past each hour from 9:30 AM to 10:30 PM IST
    
    IMPORTANT: The schedule library uses the system's local time. 
    Ensure the system is configured to IST timezone, or adjust these times accordingly.
    For a system in UTC, subtract 5:30 hours from these IST times.
    
    Schedule times (IST):
    9:30, 10:30, 11:30, 12:30, 13:30, 14:30, 15:30, 16:30, 17:30, 18:30, 19:30, 20:30, 21:30, 22:30
    """
    bot = TradingBot()
    
    # Schedule for each hour at :30 minutes (IST times)
    # These times are interpreted in the system's local timezone by the schedule library
    schedule_times = [
        "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30",
        "16:30", "17:30", "18:30", "19:30", "20:30", "21:30", "22:30"
    ]
    
    for time_str in schedule_times:
        schedule.every().day.at(time_str).do(bot.run_analysis)
        logger.info(f"Scheduled job at {time_str} (local time)")
    
    logger.info(f"Total {len(schedule_times)} jobs scheduled")
    logger.info(f"NOTE: Ensure system timezone is set to IST for correct execution times")
    return bot


def get_next_run_time():
    """Get the next scheduled run time in IST"""
    next_run = schedule.next_run()
    if next_run:
        # Ensure next_run is timezone-aware and convert to IST
        # schedule.next_run() returns a naive datetime in local time
        # We need to make it timezone-aware before converting
        if next_run.tzinfo is None:
            # Assume it's in the system's local timezone
            local_tz = pytz.timezone('UTC')
            next_run = local_tz.localize(next_run)
        next_run_ist = next_run.astimezone(IST)
        return next_run_ist
    return None


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Trading BH Bot Starting")
    logger.info("Schedule: Every hour at :30 from 9:30 AM to 10:30 PM IST")
    logger.info("=" * 60)
    
    # Setup schedule
    bot = setup_schedule()
    
    # Display next run time
    next_run = get_next_run_time()
    if next_run:
        logger.info(f"Next scheduled run: {next_run.strftime('%Y-%m-%d %H:%M:%S IST')}")
    
    # Run immediately for testing (optional - comment out in production)
    # logger.info("Running immediate test analysis...")
    # bot.run_analysis()
    
    # Keep the script running
    logger.info("Bot is now running. Press Ctrl+C to stop.")
    
    try:
        while True:
            # Run pending scheduled jobs
            schedule.run_pending()
            time.sleep(30)  # Check every 30 seconds
            
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
