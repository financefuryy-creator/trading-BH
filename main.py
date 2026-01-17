#!/usr/bin/env python3
"""
Binance Trading Bot - BH Strategy
Scans for setups based on Bollinger Bands and Heikin Ashi indicators on 1-hour timeframe.
"""

import ccxt
import pandas as pd
import numpy as np
import time
import schedule
from datetime import datetime, timezone
import pytz
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import config

# Constants
TIMEFRAME = '1h'
BB_PERIOD = 20
BB_STD = 2
MIN_BODY_SIZE_PERCENT = 30  # Minimum body size for signal confirmation


class TradingBot:
    """Main trading bot class for BH strategy."""
    
    def __init__(self):
        """Initialize the trading bot with Binance exchange and Telegram bots."""
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'  # Use futures market
            }
        })
        
        # Initialize Telegram bots
        self.telegram_bot_1 = Bot(token=config.TELEGRAM_BOT_TOKEN_1)
        self.telegram_bot_2 = Bot(token=config.TELEGRAM_BOT_TOKEN_2)
        
        print(f"[{self.get_timestamp()}] Trading bot initialized")
    
    def get_timestamp(self):
        """Get current timestamp in IST."""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    
    def load_pairs(self, filename='binance pairs.csv'):
        """Load trading pairs from CSV file."""
        try:
            df = pd.read_csv(filename, header=None)
            pairs = df[0].str.strip().tolist() if not df.empty else []
            # Filter out empty strings and ensure proper format
            pairs = [p.strip() for p in pairs if p.strip()]
            print(f"[{self.get_timestamp()}] Loaded {len(pairs)} trading pairs")
            return pairs
        except FileNotFoundError:
            print(f"[{self.get_timestamp()}] Error: {filename} not found")
            return []
        except Exception as e:
            print(f"[{self.get_timestamp()}] Error loading pairs: {e}")
            return []
    
    def fetch_ohlcv(self, symbol, limit=100):
        """
        Fetch OHLCV data from Binance.
        
        Args:
            symbol: Trading pair symbol (e.g., 'DUSK/USDT')
            limit: Number of candles to fetch
            
        Returns:
            DataFrame with OHLCV data or None on error
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"[{self.get_timestamp()}] Error fetching data for {symbol}: {e}")
            return None
    
    def calculate_bollinger_bands(self, df):
        """
        Calculate Bollinger Bands.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added BB columns (bb_upper, bb_middle, bb_lower)
        """
        df = df.copy()
        df['bb_middle'] = df['close'].rolling(window=BB_PERIOD).mean()
        bb_std = df['close'].rolling(window=BB_PERIOD).std()
        df['bb_upper'] = df['bb_middle'] + (BB_STD * bb_std)
        df['bb_lower'] = df['bb_middle'] - (BB_STD * bb_std)
        return df
    
    def calculate_heikin_ashi(self, df):
        """
        Calculate Heikin Ashi candles.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added HA columns (ha_open, ha_high, ha_low, ha_close)
        """
        df = df.copy()
        
        # HA Close = (Open + High + Low + Close) / 4
        df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        
        # HA Open
        df['ha_open'] = 0.0
        df.loc[0, 'ha_open'] = (df.loc[0, 'open'] + df.loc[0, 'close']) / 2
        
        for i in range(1, len(df)):
            df.loc[i, 'ha_open'] = (df.loc[i-1, 'ha_open'] + df.loc[i-1, 'ha_close']) / 2
        
        # HA High and Low
        df['ha_high'] = df[['high', 'ha_open', 'ha_close']].max(axis=1)
        df['ha_low'] = df[['low', 'ha_open', 'ha_close']].min(axis=1)
        
        return df
    
    def calculate_body_size_percent(self, ha_open, ha_close, ha_high, ha_low):
        """
        Calculate body size as percentage of total candle range.
        
        Args:
            ha_open: HA open price
            ha_close: HA close price
            ha_high: HA high price
            ha_low: HA low price
            
        Returns:
            Body size percentage (0-100)
        """
        total_range = ha_high - ha_low
        if total_range == 0:
            return 0
        
        body_size = abs(ha_close - ha_open)
        body_percent = (body_size / total_range) * 100
        return body_percent
    
    def is_red_candle(self, ha_open, ha_close):
        """Check if Heikin Ashi candle is red (bearish)."""
        return ha_close < ha_open
    
    def is_green_candle(self, ha_open, ha_close):
        """Check if Heikin Ashi candle is green (bullish)."""
        return ha_close > ha_open
    
    def touches_or_breaks_lower_bb(self, ha_low, ha_close, bb_lower):
        """
        Check if candle touches or breaks lower Bollinger Band.
        Checks both body and wick.
        """
        return ha_low <= bb_lower or ha_close <= bb_lower
    
    def touches_or_breaks_upper_bb(self, ha_high, ha_close, bb_upper):
        """
        Check if candle touches or breaks upper Bollinger Band.
        Checks both body and wick.
        """
        return ha_high >= bb_upper or ha_close >= bb_upper
    
    def check_buy_signal(self, df):
        """
        Check for buy signal based on BH strategy.
        
        Buy Signal Conditions:
        1. A red HA candle touches or breaks the lower Bollinger Band
        2. The next candle is green and has at least 30% body size
        
        Args:
            df: DataFrame with OHLCV, BB, and HA data
            
        Returns:
            Tuple (has_signal: bool, details: dict)
        """
        if len(df) < 2:
            return False, {}
        
        # Get the last two candles
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]
        
        # Check if previous candle is red
        prev_is_red = self.is_red_candle(prev_candle['ha_open'], prev_candle['ha_close'])
        
        # Check if previous candle touches/breaks lower BB
        prev_touches_bb = self.touches_or_breaks_lower_bb(
            prev_candle['ha_low'], 
            prev_candle['ha_close'], 
            prev_candle['bb_lower']
        )
        
        # Check if current candle is green
        current_is_green = self.is_green_candle(current_candle['ha_open'], current_candle['ha_close'])
        
        # Calculate current candle body size
        current_body_percent = self.calculate_body_size_percent(
            current_candle['ha_open'],
            current_candle['ha_close'],
            current_candle['ha_high'],
            current_candle['ha_low']
        )
        
        # Check if body size meets minimum requirement
        body_size_ok = current_body_percent >= MIN_BODY_SIZE_PERCENT
        
        # Buy signal is valid if all conditions are met
        has_signal = prev_is_red and prev_touches_bb and current_is_green and body_size_ok
        
        details = {
            'prev_candle_red': prev_is_red,
            'prev_touches_lower_bb': prev_touches_bb,
            'current_candle_green': current_is_green,
            'current_body_percent': round(current_body_percent, 2),
            'body_size_ok': body_size_ok,
            'prev_ha_close': prev_candle['ha_close'],
            'prev_bb_lower': prev_candle['bb_lower'],
            'current_ha_close': current_candle['ha_close'],
            'timestamp': current_candle['timestamp']
        }
        
        return has_signal, details
    
    def check_sell_signal(self, df):
        """
        Check for sell signal based on BH strategy.
        
        Sell Signal Conditions:
        1. A green HA candle touches or breaks the upper Bollinger Band
        2. The next candle is red and has at least 30% body size
        
        Args:
            df: DataFrame with OHLCV, BB, and HA data
            
        Returns:
            Tuple (has_signal: bool, details: dict)
        """
        if len(df) < 2:
            return False, {}
        
        # Get the last two candles
        prev_candle = df.iloc[-2]
        current_candle = df.iloc[-1]
        
        # Check if previous candle is green
        prev_is_green = self.is_green_candle(prev_candle['ha_open'], prev_candle['ha_close'])
        
        # Check if previous candle touches/breaks upper BB
        prev_touches_bb = self.touches_or_breaks_upper_bb(
            prev_candle['ha_high'],
            prev_candle['ha_close'],
            prev_candle['bb_upper']
        )
        
        # Check if current candle is red
        current_is_red = self.is_red_candle(current_candle['ha_open'], current_candle['ha_close'])
        
        # Calculate current candle body size
        current_body_percent = self.calculate_body_size_percent(
            current_candle['ha_open'],
            current_candle['ha_close'],
            current_candle['ha_high'],
            current_candle['ha_low']
        )
        
        # Check if body size meets minimum requirement
        body_size_ok = current_body_percent >= MIN_BODY_SIZE_PERCENT
        
        # Sell signal is valid if all conditions are met
        has_signal = prev_is_green and prev_touches_bb and current_is_red and body_size_ok
        
        details = {
            'prev_candle_green': prev_is_green,
            'prev_touches_upper_bb': prev_touches_bb,
            'current_candle_red': current_is_red,
            'current_body_percent': round(current_body_percent, 2),
            'body_size_ok': body_size_ok,
            'prev_ha_close': prev_candle['ha_close'],
            'prev_bb_upper': prev_candle['bb_upper'],
            'current_ha_close': current_candle['ha_close'],
            'timestamp': current_candle['timestamp']
        }
        
        return has_signal, details
    
    def scan_pair(self, symbol):
        """
        Scan a single trading pair for signals.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dict with signal information
        """
        result = {
            'symbol': symbol,
            'buy_signal': False,
            'sell_signal': False,
            'buy_details': {},
            'sell_details': {},
            'error': None
        }
        
        try:
            # Fetch OHLCV data
            df = self.fetch_ohlcv(symbol)
            if df is None or len(df) < BB_PERIOD + 2:
                result['error'] = "Insufficient data"
                return result
            
            # Calculate indicators
            df = self.calculate_bollinger_bands(df)
            df = self.calculate_heikin_ashi(df)
            
            # Check for signals
            buy_signal, buy_details = self.check_buy_signal(df)
            sell_signal, sell_details = self.check_sell_signal(df)
            
            result['buy_signal'] = buy_signal
            result['sell_signal'] = sell_signal
            result['buy_details'] = buy_details
            result['sell_details'] = sell_details
            
            if buy_signal:
                print(f"[{self.get_timestamp()}] BUY signal for {symbol}")
                print(f"  Details: {buy_details}")
            
            if sell_signal:
                print(f"[{self.get_timestamp()}] SELL signal for {symbol}")
                print(f"  Details: {sell_details}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"[{self.get_timestamp()}] Error scanning {symbol}: {e}")
        
        return result
    
    def scan_all_pairs(self):
        """
        Scan all trading pairs for signals.
        
        Returns:
            Dict with lists of buy and sell signals
        """
        pairs = self.load_pairs()
        
        if not pairs:
            print(f"[{self.get_timestamp()}] No pairs to scan")
            return {'buy': [], 'sell': []}
        
        buy_signals = []
        sell_signals = []
        
        print(f"[{self.get_timestamp()}] Scanning {len(pairs)} pairs...")
        
        for pair in pairs:
            # Add delay to respect rate limits
            time.sleep(0.5)
            
            result = self.scan_pair(pair)
            
            if result['buy_signal']:
                buy_signals.append(pair)
            
            if result['sell_signal']:
                sell_signals.append(pair)
        
        return {
            'buy': buy_signals,
            'sell': sell_signals
        }
    
    async def send_telegram_message(self, message):
        """
        Send message to Telegram bots.
        
        Args:
            message: Message text to send
        """
        try:
            # Send to first bot
            await self.telegram_bot_1.send_message(
                chat_id=config.TELEGRAM_CHAT_ID_1,
                text=message,
                parse_mode='Markdown'
            )
            print(f"[{self.get_timestamp()}] Message sent to Telegram bot 1")
        except TelegramError as e:
            print(f"[{self.get_timestamp()}] Error sending to Telegram bot 1: {e}")
        
        try:
            # Send to second bot
            await self.telegram_bot_2.send_message(
                chat_id=config.TELEGRAM_CHAT_ID_2,
                text=message,
                parse_mode='Markdown'
            )
            print(f"[{self.get_timestamp()}] Message sent to Telegram bot 2")
        except TelegramError as e:
            print(f"[{self.get_timestamp()}] Error sending to Telegram bot 2: {e}")
    
    def format_telegram_message(self, signals):
        """
        Format signals into Telegram message.
        
        Args:
            signals: Dict with buy and sell signal lists
            
        Returns:
            Formatted message string
        """
        message = "*1Hr BH*\n\n"
        
        # Buy signals
        message += "*BUY:*\n"
        if signals['buy']:
            for pair in signals['buy']:
                # Remove /USDT suffix for display
                coin_name = pair.replace('/USDT', '')
                message += f"  • {coin_name}\n"
        else:
            message += "  None\n"
        
        message += "\n"
        
        # Sell signals
        message += "*SELL:*\n"
        if signals['sell']:
            for pair in signals['sell']:
                # Remove /USDT suffix for display
                coin_name = pair.replace('/USDT', '')
                message += f"  • {coin_name}\n"
        else:
            message += "  None\n"
        
        message += f"\n_Scanned at {self.get_timestamp()}_"
        
        return message
    
    def run_scan(self):
        """Run a complete scan and send notifications."""
        print(f"\n{'='*60}")
        print(f"[{self.get_timestamp()}] Starting scan...")
        print(f"{'='*60}\n")
        
        try:
            # Scan all pairs
            signals = self.scan_all_pairs()
            
            # Format and send message
            message = self.format_telegram_message(signals)
            
            print(f"\n[{self.get_timestamp()}] Scan complete")
            print(f"Buy signals: {len(signals['buy'])}")
            print(f"Sell signals: {len(signals['sell'])}")
            
            # Send telegram notification
            asyncio.run(self.send_telegram_message(message))
            
        except Exception as e:
            print(f"[{self.get_timestamp()}] Error during scan: {e}")
    
    def run_continuously(self):
        """Run the bot continuously with hourly scans between 9 AM - 10 PM IST."""
        ist = pytz.timezone('Asia/Kolkata')
        
        # Schedule scans every hour between 9 AM and 10 PM IST
        for hour in range(9, 23):  # 9 AM to 10 PM (22:00)
            time_str = f"{hour:02d}:00"
            schedule.every().day.at(time_str).do(self.run_scan)
        
        print(f"[{self.get_timestamp()}] Bot scheduled to run hourly from 9 AM to 10 PM IST")
        print(f"[{self.get_timestamp()}] Next run: {schedule.next_run()}")
        
        # Run immediately on start
        self.run_scan()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    """Main entry point for the trading bot."""
    print("="*60)
    print("Binance Trading Bot - BH Strategy")
    print("="*60)
    
    bot = TradingBot()
    
    # For testing, run a single scan
    # For production, use bot.run_continuously()
    bot.run_scan()


if __name__ == "__main__":
    main()
