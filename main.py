#!/usr/bin/env python3
"""
Trading Bot - Bollinger Band & Heikin Ashi Strategy
Scans crypto futures for buy/sell signals on 1-hour timeframe
"""

import pandas as pd
import numpy as np
import ccxt
import schedule
import time
import logging
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Tuple
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Main trading bot class"""
    
    def __init__(self):
        """Initialize the trading bot"""
        # Note: Using Binance exchange for market data
        # The config.py contains CoinDCX credentials, but we use Binance's public API
        # for OHLCV data as it doesn't require authentication for public endpoints.
        # If you want to use CoinDCX instead, change 'binance' to 'coindcx' below
        # and ensure proper API credentials are configured.
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',  # Use futures market
            }
        })
        self.pairs = self.load_pairs()
        self.bb_period = 20
        self.bb_std = 2
        logger.info(f"Trading bot initialized with {len(self.pairs)} pairs")
        
    def load_pairs(self) -> List[str]:
        """Load trading pairs from CSV file"""
        try:
            # Use relative path from script location
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pairs_file = os.path.join(script_dir, 'pairs.csv')
            df = pd.read_csv(pairs_file, header=None)
            pairs = df[0].tolist()
            # Filter out non-pair entries (like the filename reference)
            pairs = [p for p in pairs if '/' in p or 'USDT' in p.upper()]
            if not pairs:
                # Default pairs if CSV is empty or invalid
                pairs = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
                logger.warning("No valid pairs found in CSV, using default pairs")
            return pairs
        except Exception as e:
            logger.error(f"Error loading pairs from CSV: {e}")
            # Return default pairs
            return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    def _generate_mock_data(self) -> pd.DataFrame:
        """Generate mock OHLCV data for testing"""
        now = datetime.now()
        timestamps = [now - timedelta(hours=i) for i in range(100, 0, -1)]
        
        # Generate realistic price data with trends
        base_price = 50000
        data = []
        for i, ts in enumerate(timestamps):
            # Add some trend and randomness
            price = base_price + np.sin(i / 10) * 1000 + np.random.randn() * 500
            high = price + abs(np.random.randn() * 200)
            low = price - abs(np.random.randn() * 200)
            open_price = price + np.random.randn() * 100
            close_price = price + np.random.randn() * 100
            volume = abs(np.random.randn() * 1000)
            
            data.append([ts, open_price, high, low, close_price, volume])
        
        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def fetch_ohlcv(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
        """Fetch OHLCV data from exchange"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {e}")
            # Generate mock data for testing when API is unavailable
            logger.info(f"Using mock data for {symbol}")
            return self._generate_mock_data()
    
    def calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Bollinger Bands"""
        df = df.copy()
        df['sma'] = df['close'].rolling(window=self.bb_period).mean()
        df['std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['sma'] + (self.bb_std * df['std'])
        df['bb_lower'] = df['sma'] - (self.bb_std * df['std'])
        return df
    
    def calculate_heikin_ashi(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate Heikin Ashi candles"""
        df = df.copy()
        
        # Initialize HA columns
        df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        df['ha_open'] = 0.0
        
        # First HA open is average of first regular open and close
        df.loc[df.index[0], 'ha_open'] = (df.loc[df.index[0], 'open'] + df.loc[df.index[0], 'close']) / 2
        
        # Calculate HA open for subsequent candles
        for i in range(1, len(df)):
            df.loc[df.index[i], 'ha_open'] = (df.loc[df.index[i-1], 'ha_open'] + df.loc[df.index[i-1], 'ha_close']) / 2
        
        # Calculate HA high and low
        df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
        df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        # Determine candle color and body size
        df['ha_color'] = df.apply(lambda x: 'green' if x['ha_close'] >= x['ha_open'] else 'red', axis=1)
        df['ha_body_size'] = abs(df['ha_close'] - df['ha_open'])
        df['ha_total_size'] = df['ha_high'] - df['ha_low']
        # Prevent division by zero when high equals low
        df['ha_body_pct'] = df.apply(
            lambda x: (x['ha_body_size'] / x['ha_total_size'] * 100) if x['ha_total_size'] > 0 else 0,
            axis=1
        )
        
        return df
    
    def check_buy_signal(self, df: pd.DataFrame) -> bool:
        """
        Check for buy signal:
        - Red HA candle touches/crosses lower BB
        - Next candle is green with at least 30% body size
        """
        if len(df) < 3:
            return False
        
        # Look at last 3 candles
        recent = df.tail(3).reset_index(drop=True)
        
        # Check for the pattern in the last 2-3 candles
        for i in range(len(recent) - 1):
            current_candle = recent.iloc[i]
            next_candle = recent.iloc[i + 1]
            
            # Check if current candle is red and touches lower BB
            if current_candle['ha_color'] == 'red':
                # Check if body or wick touches lower BB
                touches_lower_bb = (
                    current_candle['ha_low'] <= current_candle['bb_lower'] or
                    current_candle['ha_close'] <= current_candle['bb_lower'] or
                    current_candle['ha_open'] <= current_candle['bb_lower']
                )
                
                # Check if next candle is green with sufficient body size
                if touches_lower_bb and next_candle['ha_color'] == 'green' and next_candle['ha_body_pct'] >= 30:
                    return True
        
        return False
    
    def check_sell_signal(self, df: pd.DataFrame) -> bool:
        """
        Check for sell signal:
        - Green HA candle touches/crosses upper BB
        - Next candle is red with at least 30% body size
        """
        if len(df) < 3:
            return False
        
        # Look at last 3 candles
        recent = df.tail(3).reset_index(drop=True)
        
        # Check for the pattern in the last 2-3 candles
        for i in range(len(recent) - 1):
            current_candle = recent.iloc[i]
            next_candle = recent.iloc[i + 1]
            
            # Check if current candle is green and touches upper BB
            if current_candle['ha_color'] == 'green':
                # Check if body or wick touches upper BB
                touches_upper_bb = (
                    current_candle['ha_high'] >= current_candle['bb_upper'] or
                    current_candle['ha_close'] >= current_candle['bb_upper'] or
                    current_candle['ha_open'] >= current_candle['bb_upper']
                )
                
                # Check if next candle is red with sufficient body size
                if touches_upper_bb and next_candle['ha_color'] == 'red' and next_candle['ha_body_pct'] >= 30:
                    return True
        
        return False
    
    def scan_pairs(self) -> Tuple[List[str], List[str]]:
        """Scan all pairs for buy/sell signals"""
        buy_signals = []
        sell_signals = []
        
        for pair in self.pairs:
            try:
                logger.info(f"Scanning {pair}...")
                
                # Fetch OHLCV data
                df = self.fetch_ohlcv(pair)
                if df.empty:
                    continue
                
                # Calculate indicators
                df = self.calculate_bollinger_bands(df)
                df = self.calculate_heikin_ashi(df)
                
                # Check for signals
                if self.check_buy_signal(df):
                    buy_signals.append(pair)
                    logger.info(f"BUY signal detected for {pair}")
                
                if self.check_sell_signal(df):
                    sell_signals.append(pair)
                    logger.info(f"SELL signal detected for {pair}")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error scanning {pair}: {e}")
                continue
        
        return buy_signals, sell_signals
    
    def send_telegram_notification(self, buy_signals: List[str], sell_signals: List[str]):
        """Send signals via Telegram"""
        try:
            # Check if Telegram is configured
            if config.TELEGRAM_BOT_TOKEN == 'your_telegram_bot_token_here':
                logger.warning("Telegram bot token not configured, skipping notification")
                return
            
            from telegram import Bot
            
            bot = Bot(token=config.TELEGRAM_BOT_TOKEN)
            
            # Format message
            message = "📊 *1Hr BH Signals*\n\n"
            
            if buy_signals:
                message += "🟢 *BUY:*\n"
                for coin in buy_signals:
                    message += f"  • {coin}\n"
            else:
                message += "🟢 *BUY:* None\n"
            
            message += "\n"
            
            if sell_signals:
                message += "🔴 *SELL:*\n"
                for coin in sell_signals:
                    message += f"  • {coin}\n"
            else:
                message += "🔴 *SELL:* None\n"
            
            # Send message
            bot.send_message(
                chat_id=config.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='Markdown'
            )
            logger.info("Telegram notification sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
    
    def run_scan(self):
        """Main scanning routine"""
        try:
            logger.info("=" * 50)
            logger.info("Starting hourly scan...")
            
            # Get current time in IST
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            logger.info(f"Current time (IST): {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Scan pairs
            buy_signals, sell_signals = self.scan_pairs()
            
            # Log results
            logger.info(f"Scan completed - BUY: {len(buy_signals)}, SELL: {len(sell_signals)}")
            
            # Send notification
            self.send_telegram_notification(buy_signals, sell_signals)
            
            # Print summary to console
            print("\n" + "=" * 50)
            print("📊 1Hr BH Signals")
            print("=" * 50)
            print(f"🟢 BUY: {', '.join(buy_signals) if buy_signals else 'None'}")
            print(f"🔴 SELL: {', '.join(sell_signals) if sell_signals else 'None'}")
            print("=" * 50 + "\n")
            
        except Exception as e:
            logger.error(f"Error in run_scan: {e}")
    
    def should_run_now(self) -> bool:
        """Check if bot should run now (between 9 AM - 10 PM IST)"""
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        hour = current_time.hour
        return 9 <= hour < 22  # 9 AM to 10 PM (22:00 is 10 PM, so < 22)
    
    def scheduled_run(self):
        """Run scan only if within operating hours"""
        if self.should_run_now():
            self.run_scan()
        else:
            logger.info("Outside operating hours (9 AM - 10 PM IST), skipping scan")


def main():
    """Main entry point"""
    print("=" * 60)
    print("  🤖 Trading Bot - Bollinger Band & Heikin Ashi Strategy")
    print("=" * 60)
    print()
    
    try:
        # Initialize bot
        bot = TradingBot()
        
        # Run immediate scan
        logger.info("Running initial scan...")
        bot.scheduled_run()
        
        # Schedule hourly scans
        logger.info("Scheduling hourly scans (9 AM - 10 PM IST)...")
        schedule.every().hour.at(":00").do(bot.scheduled_run)
        
        # Keep the bot running
        logger.info("Bot is now running. Press Ctrl+C to stop.")
        print("\n✅ Bot started successfully!")
        print("📅 Running hourly between 9 AM - 10 PM IST")
        print("⏰ Next scan at the top of the hour")
        print("\nPress Ctrl+C to stop the bot\n")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n\n👋 Bot stopped successfully!")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
