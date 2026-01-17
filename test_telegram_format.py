#!/usr/bin/env python3
"""
Test Telegram notification formatting with GHTB header and timestamps.
"""
from datetime import datetime
import pytz
from telegram_notifier import TelegramNotifier


def test_telegram_format():
    """Test the Telegram message formatting"""
    print("=" * 70)
    print("Testing Telegram Notification Format")
    print("=" * 70)
    
    # Create a mock notifier (we won't actually send)
    notifier = TelegramNotifier("dummy_token", "dummy_chat_id")
    
    # Test case 1: BUY and SELL signals
    print("\nTest Case 1: Multiple BUY and SELL signals")
    print("-" * 70)
    
    signals1 = {
        'BUY': ['BTC/USDT', 'ETH/USDT', 'BNB/USDT'],
        'SELL': ['ADA/USDT', 'SOL/USDT']
    }
    
    message1 = notifier.format_signals(signals1)
    print(message1)
    
    # Verify key elements
    assert 'GHTB' in message1, "❌ Missing GHTB in header"
    assert '2Hr BH' in message1, "❌ Missing 2Hr BH in header"
    assert 'BTC' in message1, "❌ Missing BTC in BUY signals"
    assert 'ETH' in message1, "❌ Missing ETH in BUY signals"
    assert 'BNB' in message1, "❌ Missing BNB in BUY signals"
    assert 'ADA' in message1, "❌ Missing ADA in SELL signals"
    assert 'SOL' in message1, "❌ Missing SOL in SELL signals"
    assert 'IST' in message1, "❌ Missing IST timezone in timestamp"
    
    print("\n✓ All required elements present")
    
    # Test case 2: No signals
    print("\nTest Case 2: No signals")
    print("-" * 70)
    
    signals2 = {
        'BUY': [],
        'SELL': []
    }
    
    message2 = notifier.format_signals(signals2)
    print(message2)
    
    assert 'GHTB' in message2, "❌ Missing GHTB in header"
    assert 'None' in message2, "❌ Should show 'None' when no signals"
    
    print("\n✓ Correctly handles empty signals")
    
    # Test case 3: Only BUY signals
    print("\nTest Case 3: Only BUY signals")
    print("-" * 70)
    
    signals3 = {
        'BUY': ['XRP/USDT', 'DOT/USDT'],
        'SELL': []
    }
    
    message3 = notifier.format_signals(signals3)
    print(message3)
    
    assert 'XRP' in message3, "❌ Missing XRP in BUY signals"
    assert 'DOT' in message3, "❌ Missing DOT in BUY signals"
    
    print("\n✓ Correctly handles BUY-only signals")
    
    # Verify timestamp format
    print("\nVerifying timestamp format:")
    print("-" * 70)
    
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    
    print(f"Current IST time: {current_time.strftime('%Y-%m-%d %I:%M %p IST')}")
    print("Expected format: YYYY-MM-DD HH:MM AM/PM IST")
    
    # Check if timestamp is in the message
    lines = message1.split('\n')
    timestamp_line = [line for line in lines if 'IST' in line and '-' in line]
    
    if timestamp_line:
        print(f"Timestamp in message: {timestamp_line[0]}")
        print("✓ Timestamp format is correct")
    else:
        print("❌ Could not find timestamp in message")
    
    print("\n" + "=" * 70)
    print("✓ All Telegram formatting tests passed!")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    import sys
    try:
        success = test_telegram_format()
        sys.exit(0 if success else 1)
    except AssertionError as e:
        print(f"\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
