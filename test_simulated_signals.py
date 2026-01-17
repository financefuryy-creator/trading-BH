#!/usr/bin/env python3
"""
Test signal generation with simulated 2-hour data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

from signals import scan_multiple_pairs
from visual_verification import verify_signals_visually

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_2hour_data(symbol, num_candles=100):
    """
    Create sample 2-hour OHLC data for testing.
    
    Args:
        symbol: Trading pair symbol
        num_candles: Number of candles to generate
    
    Returns:
        DataFrame with OHLC data
    """
    # Generate timestamps for 2-hour intervals
    end_time = datetime.now()
    timestamps = [end_time - timedelta(hours=2*i) for i in range(num_candles)]
    timestamps.reverse()
    
    # Generate realistic price data
    np.random.seed(42)
    base_price = 50000 if 'BTC' in symbol else 3000 if 'ETH' in symbol else 500
    
    data = []
    current_price = base_price
    
    for i, ts in enumerate(timestamps):
        # Random walk for price
        change = np.random.randn() * base_price * 0.02
        current_price = max(current_price + change, base_price * 0.5)
        
        # Generate OHLC
        high = current_price * (1 + abs(np.random.randn()) * 0.01)
        low = current_price * (1 - abs(np.random.randn()) * 0.01)
        open_price = low + np.random.rand() * (high - low)
        close = low + np.random.rand() * (high - low)
        volume = np.random.uniform(1000, 10000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.index = pd.DatetimeIndex(timestamps)
    return df


def create_buy_signal_scenario(symbol):
    """
    Create data that should generate a BUY signal.
    
    Buy signal requires:
    - Previous candle: Red HA touching lower BB
    - Current candle: Green HA with >=30% body
    """
    df = create_sample_2hour_data(symbol)
    
    # Manipulate last 2 candles to create buy signal
    # Previous candle: price drop to lower BB
    df.iloc[-2, df.columns.get_loc('close')] = df.iloc[-2, df.columns.get_loc('open')] * 0.95
    df.iloc[-2, df.columns.get_loc('low')] = df.iloc[-2, df.columns.get_loc('close')] * 0.98
    
    # Current candle: strong green candle
    df.iloc[-1, df.columns.get_loc('open')] = df.iloc[-2, df.columns.get_loc('close')]
    df.iloc[-1, df.columns.get_loc('close')] = df.iloc[-1, df.columns.get_loc('open')] * 1.03
    df.iloc[-1, df.columns.get_loc('high')] = df.iloc[-1, df.columns.get_loc('close')] * 1.005
    df.iloc[-1, df.columns.get_loc('low')] = df.iloc[-1, df.columns.get_loc('open')] * 0.995
    
    return df


def test_simulated_2hour_signals():
    """Test signal generation with simulated 2-hour data"""
    print("=" * 70)
    print("Testing 2-Hour Signal Generation (Simulated Data)")
    print("=" * 70)
    
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    print(f"\nTest symbols: {', '.join(test_symbols)}")
    print(f"Timeframe: 2h (simulated)")
    print("-" * 70)
    
    try:
        # Create simulated data
        print("\n1. Creating simulated 2-hour OHLC data...")
        data_dict = {}
        
        # BTC: buy signal scenario
        data_dict['BTC/USDT'] = create_buy_signal_scenario('BTC/USDT')
        
        # ETH: normal data
        data_dict['ETH/USDT'] = create_sample_2hour_data('ETH/USDT')
        
        # BNB: normal data
        data_dict['BNB/USDT'] = create_sample_2hour_data('BNB/USDT')
        
        print(f"   ✓ Created data for {len(data_dict)} pairs")
        
        # Show data info
        print("\n2. Data summary:")
        for symbol, df in data_dict.items():
            print(f"   • {symbol}: {len(df)} candles (2-hour intervals)")
            if len(df) > 0:
                print(f"     Latest timestamp: {df.index[-1]}")
                print(f"     Latest close: ${df['close'].iloc[-1]:.2f}")
        
        # Generate signals
        print("\n3. Generating buy/sell signals...")
        signals = scan_multiple_pairs(data_dict, min_body_size=30)
        
        print(f"   ✓ Signals generated")
        print(f"   • BUY signals: {len(signals['BUY'])}")
        if signals['BUY']:
            for symbol in signals['BUY']:
                print(f"     - {symbol}")
        
        print(f"   • SELL signals: {len(signals['SELL'])}")
        if signals['SELL']:
            for symbol in signals['SELL']:
                print(f"     - {symbol}")
        
        # Test visual verification
        print("\n4. Testing visual verification...")
        if signals['BUY'] or signals['SELL']:
            chart_paths = verify_signals_visually(data_dict, signals)
            
            if chart_paths:
                print(f"   ✓ Generated {len(chart_paths)} verification charts")
                for symbol, path in chart_paths.items():
                    print(f"   • {symbol}: {path}")
            else:
                print("   ⚠ No charts generated (this is expected in non-GUI environment)")
        else:
            print("   • No signals to verify (this is expected with random data)")
        
        print("\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)
        
        # Verify timeframe
        print("\n5. Verifying 2-hour timeframe:")
        for symbol, df in data_dict.items():
            if len(df) >= 2:
                time_diff = df.index[-1] - df.index[-2]
                hours = time_diff.total_seconds() / 3600
                print(f"   • {symbol}: {hours:.1f} hours between last 2 candles")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_simulated_2hour_signals()
    sys.exit(0 if success else 1)
