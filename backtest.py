#!/usr/bin/env python3
"""
Backtesting utility for the BH strategy.
Tests the strategy on historical data to validate signal accuracy.
"""

import pandas as pd
from datetime import datetime, timedelta
from main import TradingBot
import pytz


class Backtester:
    """Backtesting class for BH strategy."""
    
    def __init__(self):
        """Initialize backtester with trading bot."""
        self.bot = TradingBot()
        self.ist = pytz.timezone('Asia/Kolkata')
    
    def backtest_pair(self, symbol, days=30):
        """
        Backtest a single trading pair.
        
        Args:
            symbol: Trading pair symbol
            days: Number of days to backtest
            
        Returns:
            Dict with backtest results
        """
        print(f"\nBacktesting {symbol} for last {days} days...")
        
        # Fetch more data for backtesting
        limit = days * 24  # 1-hour candles
        df = self.bot.fetch_ohlcv(symbol, limit=limit)
        
        if df is None or len(df) < self.bot.BB_PERIOD + 2:
            print(f"Insufficient data for {symbol}")
            return None
        
        # Calculate indicators
        df = self.bot.calculate_bollinger_bands(df)
        df = self.bot.calculate_heikin_ashi(df)
        
        signals = []
        
        # Scan through historical data
        for i in range(self.bot.BB_PERIOD + 1, len(df)):
            # Create a slice up to current index
            df_slice = df.iloc[:i+1].copy()
            df_slice = df_slice.reset_index(drop=True)
            
            # Check for buy signal
            buy_signal, buy_details = self.bot.check_buy_signal(df_slice)
            if buy_signal:
                signals.append({
                    'type': 'BUY',
                    'timestamp': df_slice.iloc[-1]['timestamp'],
                    'price': df_slice.iloc[-1]['close'],
                    'details': buy_details
                })
            
            # Check for sell signal
            sell_signal, sell_details = self.bot.check_sell_signal(df_slice)
            if sell_signal:
                signals.append({
                    'type': 'SELL',
                    'timestamp': df_slice.iloc[-1]['timestamp'],
                    'price': df_slice.iloc[-1]['close'],
                    'details': sell_details
                })
        
        return {
            'symbol': symbol,
            'signals': signals,
            'total_signals': len(signals),
            'buy_signals': len([s for s in signals if s['type'] == 'BUY']),
            'sell_signals': len([s for s in signals if s['type'] == 'SELL'])
        }
    
    def print_backtest_results(self, results):
        """Print backtest results in a readable format."""
        if results is None:
            return
        
        print(f"\n{'='*70}")
        print(f"Backtest Results for {results['symbol']}")
        print(f"{'='*70}")
        print(f"Total Signals: {results['total_signals']}")
        print(f"Buy Signals: {results['buy_signals']}")
        print(f"Sell Signals: {results['sell_signals']}")
        print(f"\nSignal History:")
        print(f"{'-'*70}")
        
        for signal in results['signals']:
            timestamp = signal['timestamp']
            signal_type = signal['type']
            price = signal['price']
            body_percent = signal['details'].get('current_body_percent', 'N/A')
            
            print(f"{timestamp} | {signal_type:4s} | Price: ${price:,.4f} | Body: {body_percent}%")
        
        print(f"{'-'*70}\n")
    
    def run_backtest(self, pairs=None, days=30):
        """
        Run backtest on multiple pairs.
        
        Args:
            pairs: List of trading pairs (None to load from file)
            days: Number of days to backtest
        """
        if pairs is None:
            pairs = self.bot.load_pairs()
        
        if not pairs:
            print("No pairs to backtest")
            return
        
        print(f"\n{'='*70}")
        print(f"Starting Backtest - {len(pairs)} pairs for {days} days")
        print(f"{'='*70}")
        
        all_results = []
        
        for pair in pairs:
            try:
                results = self.backtest_pair(pair, days)
                if results:
                    all_results.append(results)
                    self.print_backtest_results(results)
            except Exception as e:
                print(f"Error backtesting {pair}: {e}")
        
        # Print summary
        print(f"\n{'='*70}")
        print("Backtest Summary")
        print(f"{'='*70}")
        
        total_buy = sum(r['buy_signals'] for r in all_results)
        total_sell = sum(r['sell_signals'] for r in all_results)
        total_signals = sum(r['total_signals'] for r in all_results)
        
        print(f"Total Pairs Tested: {len(all_results)}")
        print(f"Total Signals: {total_signals}")
        print(f"Total Buy Signals: {total_buy}")
        print(f"Total Sell Signals: {total_sell}")
        print(f"{'='*70}\n")


def main():
    """Main entry point for backtesting."""
    print("Binance Trading Bot - Backtesting Utility")
    
    backtester = Backtester()
    
    # Test with specific pairs mentioned in the problem statement
    test_pairs = ['DUSK/USDT', 'ARB/USDT', 'CFX/USDT', 'ETHFI/USDT']
    
    print("\nTesting specific pairs mentioned in requirements...")
    backtester.run_backtest(pairs=test_pairs, days=7)


if __name__ == "__main__":
    main()
