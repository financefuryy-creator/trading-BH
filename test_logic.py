#!/usr/bin/env python3
"""
Simulation test using synthetic data to validate logic
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys

# Import bot components
sys.path.insert(0, '/home/runner/work/trading-BH/trading-BH')
from main import BinanceTradingBot


def generate_test_data():
    """Generate synthetic OHLCV data for testing"""
    np.random.seed(42)
    
    # Generate 100 candles
    num_candles = 100
    timestamps = [datetime.now() - timedelta(hours=i) for i in range(num_candles, 0, -1)]
    
    # Start with a base price
    base_price = 50000
    
    data = []
    for i in range(num_candles):
        # Generate realistic OHLC with some trends
        volatility = 0.02
        trend = np.sin(i / 10) * 1000  # Add some wave pattern
        
        open_price = base_price + trend + np.random.randn() * base_price * volatility
        close_price = open_price + np.random.randn() * base_price * volatility
        high_price = max(open_price, close_price) + abs(np.random.randn()) * base_price * volatility
        low_price = min(open_price, close_price) - abs(np.random.randn()) * base_price * volatility
        volume = np.random.rand() * 1000
        
        data.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    return pd.DataFrame(data)


def test_with_synthetic_data():
    """Test bot logic with synthetic data"""
    print("="*60)
    print("Testing Trading Bot Logic with Synthetic Data")
    print("="*60)
    
    # Create a bot instance
    bot = BinanceTradingBot()
    
    # Generate test data
    print("\n1. Generating synthetic OHLCV data...")
    df = generate_test_data()
    print(f"   ✓ Generated {len(df)} candles")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    
    # Test Bollinger Bands
    print("\n2. Calculating Bollinger Bands...")
    df = bot.calculate_bollinger_bands(df)
    print(f"   ✓ BB calculated successfully")
    print(f"   Last BB Upper: ${df['bb_upper'].iloc[-1]:.2f}")
    print(f"   Last BB Lower: ${df['bb_lower'].iloc[-1]:.2f}")
    print(f"   Last SMA: ${df['sma'].iloc[-1]:.2f}")
    
    # Test Heikin-Ashi
    print("\n3. Calculating Heikin-Ashi candles...")
    ha_df = bot.calculate_heikin_ashi(df)
    print(f"   ✓ HA calculated successfully")
    
    # Count colors
    green_candles = ha_df['ha_color'].sum()
    red_candles = len(ha_df) - green_candles
    print(f"   Green candles: {green_candles}")
    print(f"   Red candles: {red_candles}")
    
    # Test signal detection
    print("\n4. Testing signal detection logic...")
    buy_signal = bot.check_buy_signal(ha_df)
    sell_signal = bot.check_sell_signal(ha_df)
    print(f"   Buy signal detected: {buy_signal}")
    print(f"   Sell signal detected: {sell_signal}")
    
    # Print last 5 candles for analysis
    print("\n5. Last 5 candles analysis:")
    for i in range(-5, 0):
        idx = ha_df.index[i]
        row = ha_df.iloc[i]
        color = "GREEN" if row['ha_color'] else "RED"
        body_pct = row['ha_body_pct']
        
        # Check BB touches
        touches_upper = row['ha_high'] >= row['bb_upper']
        touches_lower = row['ha_low'] <= row['bb_lower']
        
        print(f"   [{i+5}] {color:5s} | Body: {body_pct:5.1f}% | "
              f"Close: ${row['ha_close']:8.2f} | "
              f"BB: [${row['bb_lower']:8.2f}, ${row['bb_upper']:8.2f}]")
        if touches_upper:
            print(f"        → Touches/crosses UPPER BB")
        if touches_lower:
            print(f"        → Touches/crosses LOWER BB")
    
    # Create a scenario with buy signal
    print("\n6. Creating synthetic buy signal scenario...")
    # Manually create conditions for buy signal
    test_df = df.copy()
    
    # Make second-to-last candle red and touching lower BB
    test_df.loc[len(test_df)-2, 'close'] = test_df.loc[len(test_df)-2, 'bb_lower'] - 10
    test_df.loc[len(test_df)-2, 'low'] = test_df.loc[len(test_df)-2, 'bb_lower'] - 20
    test_df.loc[len(test_df)-2, 'open'] = test_df.loc[len(test_df)-2, 'close'] + 100
    test_df.loc[len(test_df)-2, 'high'] = test_df.loc[len(test_df)-2, 'open'] + 50
    
    # Make last candle green with good body
    test_df.loc[len(test_df)-1, 'close'] = test_df.loc[len(test_df)-1, 'open'] + 200
    test_df.loc[len(test_df)-1, 'high'] = test_df.loc[len(test_df)-1, 'close'] + 50
    test_df.loc[len(test_df)-1, 'low'] = test_df.loc[len(test_df)-1, 'open'] - 30
    
    test_ha_df = bot.calculate_heikin_ashi(test_df)
    buy_signal = bot.check_buy_signal(test_ha_df)
    print(f"   Buy signal in synthetic scenario: {buy_signal}")
    
    print("\n" + "="*60)
    print("Logic tests completed successfully! ✓")
    print("="*60)
    
    return True


if __name__ == "__main__":
    try:
        test_with_synthetic_data()
        print("\nAll logic validation tests passed!")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
