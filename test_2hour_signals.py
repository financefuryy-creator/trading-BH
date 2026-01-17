#!/usr/bin/env python3
"""
Test 2-hour signal generation and visual verification.
"""
import sys
import logging
from data_fetcher import BinanceDataFetcher
from signals import scan_multiple_pairs
from visual_verification import verify_signals_visually

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_2hour_signals():
    """Test signal generation with 2-hour timeframe"""
    print("=" * 70)
    print("Testing 2-Hour Signal Generation")
    print("=" * 70)
    
    # Test with a few pairs
    test_symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
    
    print(f"\nTest symbols: {', '.join(test_symbols)}")
    print(f"Timeframe: 2h")
    print("-" * 70)
    
    try:
        # Initialize data fetcher
        print("\n1. Initializing Binance data fetcher...")
        fetcher = BinanceDataFetcher()
        print("   ✓ Data fetcher initialized")
        
        # Fetch 2-hour data
        print("\n2. Fetching 2-hour OHLC data from Binance...")
        data_dict = fetcher.fetch_multiple_pairs(test_symbols, timeframe='2h', limit=100)
        
        if not data_dict:
            print("   ✗ Failed to fetch any data")
            return False
        
        print(f"   ✓ Successfully fetched data for {len(data_dict)} pairs")
        
        # Show data info
        print("\n3. Data summary:")
        for symbol, df in data_dict.items():
            print(f"   • {symbol}: {len(df)} candles")
            if len(df) > 0:
                print(f"     Latest timestamp: {df.index[-1]}")
                print(f"     Latest close: {df['close'].iloc[-1]:.2f}")
        
        # Generate signals
        print("\n4. Generating buy/sell signals...")
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
        
        # Test visual verification if there are signals
        if signals['BUY'] or signals['SELL']:
            print("\n5. Testing visual verification...")
            chart_paths = verify_signals_visually(data_dict, signals)
            
            if chart_paths:
                print(f"   ✓ Generated {len(chart_paths)} verification charts")
                for symbol, path in chart_paths.items():
                    print(f"   • {symbol}: {path}")
            else:
                print("   ⚠ No charts generated")
        else:
            print("\n5. No signals to verify visually")
        
        print("\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_2hour_signals()
    sys.exit(0 if success else 1)
