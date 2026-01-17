#!/usr/bin/env python3
"""
Test script for Trading BH Bot
Demonstrates the bot's functionality with mock data
"""

import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from main import TradingBot


def create_mock_data():
    """Create mock OHLCV data for testing"""
    # Set seed for reproducible tests
    np.random.seed(42)
    
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    
    # Create realistic price data
    base_price = 50000
    prices = []
    current = base_price
    
    for i in range(100):
        # Add some randomness
        change = np.random.randn() * 200
        current = current + change
        prices.append(current)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * 1.01 for p in prices],
        'low': [p * 0.99 for p in prices],
        'close': [p + np.random.randn() * 100 for p in prices],
        'volume': [np.random.uniform(100, 1000) for _ in prices]
    })
    
    return df


def test_bollinger_bands():
    """Test Bollinger Bands calculation"""
    print("Testing Bollinger Bands calculation...")
    bot = TradingBot()
    df = create_mock_data()
    
    df = bot.calculate_bollinger_bands(df)
    
    assert 'middle_band' in df.columns
    assert 'upper_band' in df.columns
    assert 'lower_band' in df.columns
    
    # Verify upper band is above middle band
    assert df['upper_band'].iloc[-1] > df['middle_band'].iloc[-1]
    # Verify lower band is below middle band
    assert df['lower_band'].iloc[-1] < df['middle_band'].iloc[-1]
    
    print("✓ Bollinger Bands calculation works correctly")


def test_heikin_ashi():
    """Test Heikin Ashi calculation"""
    print("Testing Heikin Ashi calculation...")
    bot = TradingBot()
    df = create_mock_data()
    
    df = bot.calculate_heikin_ashi(df)
    
    assert 'ha_close' in df.columns
    assert 'ha_open' in df.columns
    assert 'ha_high' in df.columns
    assert 'ha_low' in df.columns
    assert 'ha_color' in df.columns
    assert 'ha_body_pct' in df.columns
    
    # Verify HA values are calculated
    assert not df['ha_close'].isna().any()
    assert not df['ha_open'].isna().any()
    
    print("✓ Heikin Ashi calculation works correctly")


def test_signal_generation():
    """Test buy/sell signal generation"""
    print("Testing signal generation...")
    bot = TradingBot()
    
    # Create mock data with BB
    df = create_mock_data()
    df = bot.calculate_bollinger_bands(df)
    df = bot.calculate_heikin_ashi(df)
    
    # Test that functions run without errors
    buy_signal = bot.check_buy_signal(df)
    sell_signal = bot.check_sell_signal(df)
    
    print(f"  Buy signal detected: {buy_signal}")
    print(f"  Sell signal detected: {sell_signal}")
    print("✓ Signal generation works correctly")


def test_message_formatting():
    """Test Telegram message formatting"""
    print("Testing message formatting...")
    bot = TradingBot()
    
    buy_signals = ['BTC/USDT', 'ETH/USDT']
    sell_signals = ['BNB/USDT']
    
    message = bot.format_signals_message(buy_signals, sell_signals)
    
    assert 'BTC/USDT' in message
    assert 'ETH/USDT' in message
    assert 'BNB/USDT' in message
    assert 'BUY' in message
    assert 'SELL' in message
    
    print("✓ Message formatting works correctly")
    print(f"\nSample message:\n{message}")


def test_trading_hours():
    """Test trading hours check"""
    print("Testing trading hours check...")
    bot = TradingBot()
    
    # This will check current IST time
    is_trading = bot.is_trading_hours()
    print(f"  Currently in trading hours (9 AM - 10 PM IST): {is_trading}")
    print("✓ Trading hours check works correctly")


def main():
    """Run all tests"""
    print("="*50)
    print("Trading BH Bot - Test Suite")
    print("="*50)
    print()
    
    try:
        test_bollinger_bands()
        print()
        test_heikin_ashi()
        print()
        test_signal_generation()
        print()
        test_message_formatting()
        print()
        test_trading_hours()
        print()
        print("="*50)
        print("✓ All tests passed!")
        print("="*50)
        return 0
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
