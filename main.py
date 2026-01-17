#!/usr/bin/env python3
"""
Trading BH Bot - Bollinger Bands & Heikin Ashi Trading Bot
Scans for setups on 1-hour timeframe and sends Telegram notifications
"""

import ccxt
import pandas as pd
import numpy as np
import schedule
import time
from datetime import datetime
import pytz
from telegram import Bot
import asyncio
import config


class TradingBot:
    def __init__(self):
        """Initialize the trading bot with API connections"""
        # Use Binance exchange (CCXT doesn't have CoinDCX)
        self.exchange = ccxt.binance({
            'apiKey': getattr(config, 'BINANCE_API_KEY', ''),
            'secret': getattr(config, 'BINANCE_SECRET_KEY', ''),
            'enableRateLimit': True,
        })
        self.telegram_token = config.TELEGRAM_BOT_TOKEN
        self.telegram_chat_id = config.TELEGRAM_CHAT_ID
        self.pairs = self.load_pairs()
        
    def load_pairs(self):
        """Load trading pairs from pairs.csv file"""
        try:
            pairs = []
            with open('pairs.csv', 'r') as f:
                for line in f:
                    pair = line.strip()
                    # Skip empty lines and comments
                    if pair and not pair.startswith('#'):
                        pairs.append(pair)
            return pairs if pairs else ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
        except FileNotFoundError:
            print("Warning: pairs.csv not found, using default pairs")
            return ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """Fetch OHLCV data from Binance API"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def calculate_bollinger_bands(self, df, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        df['middle_band'] = df['close'].rolling(window=period).mean()
        df['std'] = df['close'].rolling(window=period).std()
        df['upper_band'] = df['middle_band'] + (std_dev * df['std'])
        df['lower_band'] = df['middle_band'] - (std_dev * df['std'])
        return df
    
    def calculate_heikin_ashi(self, df):
        """Calculate Heikin Ashi candles"""
        ha_df = df.copy()
        
        # Calculate HA close
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # Calculate HA open
        ha_df['ha_open'] = 0.0
        ha_df.loc[0, 'ha_open'] = df.loc[0, 'open']
        
        for i in range(1, len(ha_df)):
            ha_df.loc[i, 'ha_open'] = (ha_df.loc[i-1, 'ha_open'] + ha_df.loc[i-1, 'ha_close']) / 2
        
        # Calculate HA high and low
        ha_df['ha_high'] = ha_df[['high', 'ha_open', 'ha_close']].max(axis=1)
        ha_df['ha_low'] = ha_df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        # Determine candle color (True = green/bullish, False = red/bearish)
        ha_df['ha_color'] = ha_df['ha_close'] > ha_df['ha_open']
        
        # Calculate body size percentage
        ha_df['ha_body_size'] = abs(ha_df['ha_close'] - ha_df['ha_open'])
        ha_df['ha_full_size'] = ha_df['ha_high'] - ha_df['ha_low']
        # Avoid division by zero - set to 0 if candle has no size
        ha_df['ha_body_pct'] = ha_df.apply(
            lambda row: (row['ha_body_size'] / row['ha_full_size'] * 100) if row['ha_full_size'] > 0 else 0,
            axis=1
        )
        
        return ha_df
    
    def check_buy_signal(self, df):
        """
        Check for buy signal:
        - Red HA candle touches/crosses lower BB
        - Next candle is green with >= 30% body size
        """
        if len(df) < 3:
            return False
        
        # Look at the last 3 candles
        for i in range(-3, -1):
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Check if current candle is red (bearish)
            if not current_candle['ha_color']:
                # Check if the red candle touches or crosses lower BB (body or wick)
                touches_lower_bb = (
                    current_candle['ha_low'] <= current_candle['lower_band'] or
                    current_candle['ha_close'] <= current_candle['lower_band'] or
                    current_candle['ha_open'] <= current_candle['lower_band']
                )
                
                # Check if next candle is green with >= 30% body size
                if touches_lower_bb and next_candle['ha_color'] and next_candle['ha_body_pct'] >= 30:
                    return True
        
        return False
    
    def check_sell_signal(self, df):
        """
        Check for sell signal:
        - Green HA candle touches/crosses upper BB
        - Next candle is red with >= 30% body size
        """
        if len(df) < 3:
            return False
        
        # Look at the last 3 candles
        for i in range(-3, -1):
            current_candle = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Check if current candle is green (bullish)
            if current_candle['ha_color']:
                # Check if the green candle touches or crosses upper BB (body or wick)
                touches_upper_bb = (
                    current_candle['ha_high'] >= current_candle['upper_band'] or
                    current_candle['ha_close'] >= current_candle['upper_band'] or
                    current_candle['ha_open'] >= current_candle['upper_band']
                )
                
                # Check if next candle is red with >= 30% body size
                if touches_upper_bb and not next_candle['ha_color'] and next_candle['ha_body_pct'] >= 30:
                    return True
        
        return False
    
    def scan_all_pairs(self):
        """Scan all pairs for buy/sell signals"""
        buy_signals = []
        sell_signals = []
        
        for pair in self.pairs:
            try:
                print(f"Scanning {pair}...")
                
                # Fetch OHLCV data
                df = self.fetch_ohlcv(pair)
                if df is None or len(df) < 30:
                    continue
                
                # Calculate indicators
                df = self.calculate_bollinger_bands(df)
                df = self.calculate_heikin_ashi(df)
                
                # Check for signals
                if self.check_buy_signal(df):
                    buy_signals.append(pair)
                    print(f"  ✓ BUY signal detected for {pair}")
                
                if self.check_sell_signal(df):
                    sell_signals.append(pair)
                    print(f"  ✓ SELL signal detected for {pair}")
                
            except Exception as e:
                print(f"Error processing {pair}: {str(e)}")
        
        return buy_signals, sell_signals
    
    async def send_telegram_message(self, message):
        """Send message via Telegram bot"""
        try:
            if not self.telegram_token or self.telegram_token == 'your_telegram_bot_token_here':
                print("Telegram token not configured, skipping notification")
                print(f"Would have sent: {message}")
                return
            
            bot = Bot(token=self.telegram_token)
            await bot.send_message(chat_id=self.telegram_chat_id, text=message)
            print("Telegram notification sent successfully")
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")
    
    def format_signals_message(self, buy_signals, sell_signals):
        """Format signals into Telegram message"""
        message = "📊 *1Hr BH*\n\n"
        
        message += "🟢 *BUY:*\n"
        if buy_signals:
            for pair in buy_signals:
                message += f"  • {pair}\n"
        else:
            message += "  • None\n"
        
        message += "\n🔴 *SELL:*\n"
        if sell_signals:
            for pair in sell_signals:
                message += f"  • {pair}\n"
        else:
            message += "  • None\n"
        
        return message
    
    def run_scan(self):
        """Main scanning function - runs every hour"""
        print(f"\n{'='*50}")
        print(f"Running scan at {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}")
        print(f"{'='*50}")
        
        # Scan all pairs
        buy_signals, sell_signals = self.scan_all_pairs()
        
        # Format and send Telegram message
        message = self.format_signals_message(buy_signals, sell_signals)
        print("\nSignal Summary:")
        print(message)
        
        # Send to Telegram
        asyncio.run(self.send_telegram_message(message))
        
        print(f"{'='*50}\n")
    
    def is_trading_hours(self):
        """Check if current time is within trading hours (9 AM - 10 PM IST)"""
        ist = pytz.timezone('Asia/Kolkata')
        now = datetime.now(ist)
        current_hour = now.hour
        return 9 <= current_hour < 22
    
    def scheduled_scan(self):
        """Wrapper for run_scan that checks trading hours"""
        if self.is_trading_hours():
            self.run_scan()
        else:
            print(f"Outside trading hours. Current time: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M:%S IST')}")
    
    def start(self):
        """Start the bot with hourly scheduling"""
        print("="*50)
        print("Trading BH Bot Starting...")
        print("="*50)
        print(f"Loaded {len(self.pairs)} trading pairs")
        print("Schedule: Every hour from 9:00 AM to 10:00 PM IST")
        print("="*50)
        
        # Run immediately if within trading hours
        if self.is_trading_hours():
            print("\nRunning initial scan...")
            self.run_scan()
        
        # Schedule to run every hour
        schedule.every().hour.at(":00").do(self.scheduled_scan)
        
        print("\nBot is now running. Press Ctrl+C to stop.")
        
        # Keep the bot running
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n\nBot stopped by user.")


def main():
    """Main entry point"""
    try:
        bot = TradingBot()
        bot.start()
    except Exception as e:
        print(f"Error starting bot: {str(e)}")
        raise


if __name__ == "__main__":
    main()
