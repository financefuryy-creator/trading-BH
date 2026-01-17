#!/usr/bin/env python3
"""
Test script for validating the trading bot functionality
"""

import sys
import logging
from main import BinanceTradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_bot():
    """Test the bot functionality"""
    print("="*60)
    print("Testing Binance Trading Bot")
    print("="*60)
    
    try:
        # Initialize bot
        print("\n1. Initializing bot...")
        bot = BinanceTradingBot()
        print(f"   ✓ Bot initialized with {len(bot.pairs)} pairs")
        
        # Test data fetching
        print("\n2. Testing data fetch for BTC/USDT...")
        df = bot.fetch_ohlcv('BTC/USDT', limit=50)
        if df is not None and len(df) > 0:
            print(f"   ✓ Fetched {len(df)} candles")
            print(f"   Latest close: ${df['close'].iloc[-1]:.2f}")
        else:
            print("   ✗ Failed to fetch data")
            return False
        
        # Test Bollinger Bands calculation
        print("\n3. Testing Bollinger Bands calculation...")
        df = bot.calculate_bollinger_bands(df)
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns:
            print(f"   ✓ BB calculated successfully")
            print(f"   Upper: ${df['bb_upper'].iloc[-1]:.2f}")
            print(f"   Lower: ${df['bb_lower'].iloc[-1]:.2f}")
        else:
            print("   ✗ BB calculation failed")
            return False
        
        # Test Heikin-Ashi calculation
        print("\n4. Testing Heikin-Ashi calculation...")
        ha_df = bot.calculate_heikin_ashi(df)
        if 'ha_close' in ha_df.columns and 'ha_color' in ha_df.columns:
            print(f"   ✓ HA calculated successfully")
            last_color = "GREEN" if ha_df['ha_color'].iloc[-1] else "RED"
            print(f"   Last candle: {last_color}")
            print(f"   HA Close: ${ha_df['ha_close'].iloc[-1]:.2f}")
        else:
            print("   ✗ HA calculation failed")
            return False
        
        # Test signal detection
        print("\n5. Testing signal detection...")
        buy_signal = bot.check_buy_signal(ha_df)
        sell_signal = bot.check_sell_signal(ha_df)
        print(f"   Buy signal: {buy_signal}")
        print(f"   Sell signal: {sell_signal}")
        
        # Test full scan on limited pairs
        print("\n6. Running limited scan (first 5 pairs)...")
        original_pairs = bot.pairs
        bot.pairs = bot.pairs[:5]
        buy_signals, sell_signals = bot.scan_all_pairs()
        bot.pairs = original_pairs
        print(f"   ✓ Scan completed")
        print(f"   Buy signals: {buy_signals}")
        print(f"   Sell signals: {sell_signals}")
        
        print("\n" + "="*60)
        print("All tests passed! ✓")
        print("="*60)
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_bot()
    sys.exit(0 if success else 1)
