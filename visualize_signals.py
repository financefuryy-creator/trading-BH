#!/usr/bin/env python3
"""
Visualization utility for validating signal accuracy
Plots Heikin-Ashi candles with Bollinger Bands
"""

import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import sys
import os
import tempfile


class SignalVisualizer:
    """Visualize trading signals with HA candles and BB"""
    
    # Configuration constant (should match main.py)
    MIN_BODY_PERCENTAGE = 30  # Minimum body size as percentage of candle range for signal confirmation
    
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.timeframe = '2h'
        self.bb_period = 20
        self.bb_std = 2
    
    def fetch_ohlcv(self, symbol, limit=100):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return None
    
    def calculate_heikin_ashi(self, df):
        """Calculate Heikin-Ashi candles"""
        ha_df = df.copy()
        
        ha_df['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_df['ha_open'] = (df['open'] + df['close']) / 2
        ha_df['ha_high'] = df['high']
        ha_df['ha_low'] = df['low']
        
        for i in range(1, len(df)):
            ha_df.loc[i, 'ha_open'] = (ha_df.loc[i-1, 'ha_open'] + ha_df.loc[i-1, 'ha_close']) / 2
            ha_df.loc[i, 'ha_close'] = (df.loc[i, 'open'] + df.loc[i, 'high'] + 
                                        df.loc[i, 'low'] + df.loc[i, 'close']) / 4
            ha_df.loc[i, 'ha_high'] = max(df.loc[i, 'high'], ha_df.loc[i, 'ha_open'], ha_df.loc[i, 'ha_close'])
            ha_df.loc[i, 'ha_low'] = min(df.loc[i, 'low'], ha_df.loc[i, 'ha_open'], ha_df.loc[i, 'ha_close'])
        
        ha_df['ha_color'] = ha_df['ha_close'] >= ha_df['ha_open']
        
        ha_range = ha_df['ha_high'] - ha_df['ha_low']
        ha_body = abs(ha_df['ha_close'] - ha_df['ha_open'])
        # Avoid division by zero
        ha_df['ha_body_pct'] = np.where(ha_range > 0, ha_body / ha_range * 100, 0)
        
        return ha_df
    
    def calculate_bollinger_bands(self, df):
        """Calculate Bollinger Bands"""
        df['sma'] = df['close'].rolling(window=self.bb_period).mean()
        df['std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['sma'] + (df['std'] * self.bb_std)
        df['bb_lower'] = df['sma'] - (df['std'] * self.bb_std)
        return df
    
    def plot_chart(self, symbol, candles_to_show=50):
        """Plot HA candles with Bollinger Bands"""
        print(f"Fetching data for {symbol}...")
        df = self.fetch_ohlcv(symbol, limit=100)
        
        if df is None or len(df) < self.bb_period + 10:
            print("Insufficient data")
            return
        
        # Calculate indicators
        df = self.calculate_bollinger_bands(df)
        ha_df = self.calculate_heikin_ashi(df)
        
        # Get last N candles
        ha_df = ha_df.tail(candles_to_show).reset_index(drop=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 9))
        
        # Plot Bollinger Bands
        ax.plot(ha_df.index, ha_df['bb_upper'], 'b--', label='Upper BB', linewidth=1, alpha=0.7)
        ax.plot(ha_df.index, ha_df['sma'], 'gray', label='SMA', linewidth=1, alpha=0.7)
        ax.plot(ha_df.index, ha_df['bb_lower'], 'b--', label='Lower BB', linewidth=1, alpha=0.7)
        
        # Fill between bands
        ax.fill_between(ha_df.index, ha_df['bb_upper'], ha_df['bb_lower'], alpha=0.1, color='blue')
        
        # Plot Heikin-Ashi candles
        for idx in ha_df.index:
            row = ha_df.loc[idx]
            
            # Determine color
            color = 'green' if row['ha_color'] else 'red'
            
            # Draw body
            body_height = abs(row['ha_close'] - row['ha_open'])
            body_bottom = min(row['ha_open'], row['ha_close'])
            
            # Candle body
            rect = mpatches.Rectangle((idx - 0.3, body_bottom), 0.6, body_height,
                                     facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
            ax.add_patch(rect)
            
            # Upper wick
            ax.plot([idx, idx], [max(row['ha_open'], row['ha_close']), row['ha_high']],
                   color='black', linewidth=1)
            
            # Lower wick
            ax.plot([idx, idx], [row['ha_low'], min(row['ha_open'], row['ha_close'])],
                   color='black', linewidth=1)
        
        # Detect and mark signals
        buy_signals = []
        sell_signals = []
        
        for i in range(2, len(ha_df)):
            prev_candle = ha_df.loc[i-1]
            curr_candle = ha_df.loc[i]
            
            # Buy signal
            prev_is_red = not prev_candle['ha_color']
            prev_touches_lower = (prev_candle['ha_low'] <= prev_candle['bb_lower'] or
                                 min(prev_candle['ha_open'], prev_candle['ha_close']) <= prev_candle['bb_lower'])
            curr_is_green = curr_candle['ha_color']
            curr_body_ok_buy = curr_candle['ha_body_pct'] >= self.MIN_BODY_PERCENTAGE
            
            if prev_is_red and prev_touches_lower and curr_is_green and curr_body_ok_buy:
                buy_signals.append(i)
            
            # Sell signal
            prev_is_green = prev_candle['ha_color']
            prev_touches_upper = (prev_candle['ha_high'] >= prev_candle['bb_upper'] or
                                 max(prev_candle['ha_open'], prev_candle['ha_close']) >= prev_candle['bb_upper'])
            curr_is_red = not curr_candle['ha_color']
            curr_body_ok_sell = curr_candle['ha_body_pct'] >= self.MIN_BODY_PERCENTAGE
            
            if prev_is_green and prev_touches_upper and curr_is_red and curr_body_ok_sell:
                sell_signals.append(i)
        
        # Mark buy signals
        for idx in buy_signals:
            row = ha_df.loc[idx]
            ax.scatter(idx, row['ha_low'] - (ha_df['ha_high'].max() - ha_df['ha_low'].min()) * 0.02,
                      marker='^', s=200, color='green', edgecolors='darkgreen', linewidth=2, zorder=5)
        
        # Mark sell signals
        for idx in sell_signals:
            row = ha_df.loc[idx]
            ax.scatter(idx, row['ha_high'] + (ha_df['ha_high'].max() - ha_df['ha_low'].min()) * 0.02,
                      marker='v', s=200, color='red', edgecolors='darkred', linewidth=2, zorder=5)
        
        # Formatting
        ax.set_xlabel('Candle Index', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.set_title(f'{symbol} - Heikin-Ashi with Bollinger Bands (2h)\nBuy: {len(buy_signals)}, Sell: {len(sell_signals)}',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Save figure
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Use cross-platform temp directory
        temp_dir = tempfile.gettempdir()
        filename = os.path.join(temp_dir, f'chart_{symbol.replace("/", "_")}_{timestamp}.png')
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        print(f"Chart saved to: {filename}")
        
        plt.show()
        
        # Print signal details
        print(f"\n{symbol} Analysis:")
        print(f"Buy Signals: {len(buy_signals)} at indices {buy_signals}")
        print(f"Sell Signals: {len(sell_signals)} at indices {sell_signals}")
        
        # Print last few candles info
        print("\nLast 5 candles:")
        for idx in ha_df.tail(5).index:
            row = ha_df.loc[idx]
            color_str = "GREEN" if row['ha_color'] else "RED"
            print(f"  [{idx}] {color_str} | Body: {row['ha_body_pct']:.1f}% | "
                  f"Close: {row['ha_close']:.2f} | BB: [{row['bb_lower']:.2f}, {row['bb_upper']:.2f}]")


def main():
    """Main function"""
    if len(sys.argv) > 1:
        symbol = sys.argv[1]
    else:
        symbol = 'BTC/USDT'
    
    visualizer = SignalVisualizer()
    visualizer.plot_chart(symbol)


if __name__ == "__main__":
    main()
