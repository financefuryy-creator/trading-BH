#!/usr/bin/env python3
"""
Test to verify the index fix in signal detection
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from main import BinanceTradingBot

def test_index_logic():
    """Test that the index logic correctly checks adjacent candles"""
    print("Testing Index Logic for Signal Detection")
    print("="*60)
    
    bot = BinanceTradingBot()
    
    # Create a specific test case with known buy signal
    # We'll have: Red candle touching lower BB at index -2, Green candle at index -1
    
    data = []
    base_price = 50000
    num_candles = 30
    
    for i in range(num_candles):
        data.append({
            'timestamp': datetime.now() - timedelta(hours=num_candles-i),
            'open': base_price + i * 10,
            'high': base_price + i * 10 + 100,
            'low': base_price + i * 10 - 100,
            'close': base_price + i * 10 + 50,
            'volume': 1000
        })
    
    df = pd.DataFrame(data)
    df = bot.calculate_bollinger_bands(df)
    
    # Manually set up a buy signal pattern at the end
    # Make index -2 (second to last) a red candle touching lower BB
    df.loc[len(df)-2, 'open'] = df.loc[len(df)-2, 'bb_lower'] + 50
    df.loc[len(df)-2, 'close'] = df.loc[len(df)-2, 'bb_lower'] - 50  # Red candle
    df.loc[len(df)-2, 'low'] = df.loc[len(df)-2, 'bb_lower'] - 100   # Touching lower BB
    df.loc[len(df)-2, 'high'] = df.loc[len(df)-2, 'open'] + 50
    
    # Make index -1 (last) a green candle with good body
    df.loc[len(df)-1, 'open'] = df.loc[len(df)-2, 'close'] + 10
    df.loc[len(df)-1, 'close'] = df.loc[len(df)-1, 'open'] + 1200  # Green with very big body
    df.loc[len(df)-1, 'low'] = df.loc[len(df)-1, 'open'] - 100
    df.loc[len(df)-1, 'high'] = df.loc[len(df)-1, 'close'] + 200
    
    ha_df = bot.calculate_heikin_ashi(df)
    
    print("\nLast 3 candles:")
    for i in range(-3, 0):
        idx = ha_df.index[i]
        row = ha_df.iloc[i]
        color = "GREEN" if row['ha_color'] else "RED"
        body_pct = row['ha_body_pct']
        touches_upper = row['ha_high'] >= row['bb_upper']
        touches_lower = row['ha_low'] <= row['bb_lower']
        
        print(f"  Index {i} (actual {idx}): {color:5s} | Body: {body_pct:5.1f}%", end="")
        if touches_upper:
            print(" | Touches UPPER BB", end="")
        if touches_lower:
            print(" | Touches LOWER BB", end="")
        print()
    
    # Test buy signal detection
    print("\nTesting buy signal detection...")
    buy_signal = bot.check_buy_signal(ha_df)
    print(f"Buy signal detected: {buy_signal}")
    
    if buy_signal:
        print("✓ PASS - Buy signal correctly detected")
    else:
        print("✗ FAIL - Buy signal should have been detected")
        print("\nDebugging info:")
        print(f"  Index -2 (prev): RED={not ha_df.iloc[-2]['ha_color']}, "
              f"Touches lower BB={ha_df.iloc[-2]['ha_low'] <= ha_df.iloc[-2]['bb_lower']}")
        print(f"  Index -1 (curr): GREEN={ha_df.iloc[-1]['ha_color']}, "
              f"Body={ha_df.iloc[-1]['ha_body_pct']:.1f}% (need >=30%)")
        return False
    
    # Now test that we're checking ADJACENT candles, not always the last one
    # Create a scenario where signal is at -3 -> -2, but NOT at -2 -> -1
    df2 = df.copy()
    
    # Make index -3 red touching lower BB
    df2.loc[len(df2)-3, 'open'] = df2.loc[len(df2)-3, 'bb_lower'] + 50
    df2.loc[len(df2)-3, 'close'] = df2.loc[len(df2)-3, 'bb_lower'] - 50
    df2.loc[len(df2)-3, 'low'] = df2.loc[len(df2)-3, 'bb_lower'] - 100
    df2.loc[len(df2)-3, 'high'] = df2.loc[len(df2)-3, 'open'] + 50
    
    # Make index -2 green with good body (this creates a buy signal at -3 -> -2)
    df2.loc[len(df2)-2, 'open'] = df2.loc[len(df2)-3, 'close'] + 10
    df2.loc[len(df2)-2, 'close'] = df2.loc[len(df2)-2, 'open'] + 1200
    df2.loc[len(df2)-2, 'low'] = df2.loc[len(df2)-2, 'open'] - 100
    df2.loc[len(df2)-2, 'high'] = df2.loc[len(df2)-2, 'close'] + 200
    
    # Make index -1 also red (no buy signal at -2 -> -1, since -2 is green, -1 is red - that's a sell pattern)
    df2.loc[len(df2)-1, 'open'] = df2.loc[len(df2)-2, 'close']
    df2.loc[len(df2)-1, 'close'] = df2.loc[len(df2)-1, 'open'] - 100  # Red candle
    df2.loc[len(df2)-1, 'low'] = df2.loc[len(df2)-1, 'close'] - 50
    df2.loc[len(df2)-1, 'high'] = df2.loc[len(df2)-1, 'open'] + 50
    
    ha_df2 = bot.calculate_heikin_ashi(df2)
    
    print("\nTesting buy signal at index -3 -> -2 (not -2 -> -1)...")
    buy_signal2 = bot.check_buy_signal(ha_df2)
    print(f"Buy signal detected: {buy_signal2}")
    
    if buy_signal2:
        print("✓ PASS - Buy signal correctly detected at earlier position")
    else:
        print("✗ FAIL - Should detect signal at -3 -> -2")
        return False
    
    print("\n" + "="*60)
    print("All index logic tests passed! ✓")
    print("="*60)
    return True


if __name__ == "__main__":
    success = test_index_logic()
    sys.exit(0 if success else 1)
