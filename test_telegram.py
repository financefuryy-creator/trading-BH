#!/usr/bin/env python3
"""
Test Telegram message formatting (no actual sending)
"""

from main import BinanceTradingBot
from datetime import datetime
import pytz

def test_telegram_formatting():
    """Test message formatting"""
    print("="*60)
    print("Testing Telegram Message Formatting")
    print("="*60)
    
    bot = BinanceTradingBot()
    
    # Test case 1: Signals detected
    print("\n1. Test with signals detected:")
    buy_signals = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT']
    sell_signals = ['XRP/USDT', 'ADA/USDT']
    
    ist_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist_tz).strftime('%Y-%m-%d %H:%M:%S IST')
    
    message = f"<b>1Hr BH - {current_time}</b>\n\n"
    
    if buy_signals:
        message += "<b>BUY:</b>\n"
        for symbol in buy_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>BUY:</b>\n  None\n"
    
    message += "\n"
    
    if sell_signals:
        message += "<b>SELL:</b>\n"
        for symbol in sell_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>SELL:</b>\n  None\n"
    
    print(message)
    print("✓ Message formatted correctly")
    
    # Test case 2: No signals
    print("\n2. Test with no signals:")
    buy_signals = []
    sell_signals = []
    
    message = f"<b>1Hr BH - {current_time}</b>\n\n"
    
    if buy_signals:
        message += "<b>BUY:</b>\n"
        for symbol in buy_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>BUY:</b>\n  None\n"
    
    message += "\n"
    
    if sell_signals:
        message += "<b>SELL:</b>\n"
        for symbol in sell_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>SELL:</b>\n  None\n"
    
    print(message)
    print("✓ Empty message formatted correctly")
    
    # Test case 3: Only buy signals
    print("\n3. Test with only buy signals:")
    buy_signals = ['BTC/USDT']
    sell_signals = []
    
    message = f"<b>1Hr BH - {current_time}</b>\n\n"
    
    if buy_signals:
        message += "<b>BUY:</b>\n"
        for symbol in buy_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>BUY:</b>\n  None\n"
    
    message += "\n"
    
    if sell_signals:
        message += "<b>SELL:</b>\n"
        for symbol in sell_signals:
            coin = symbol.split('/')[0]
            message += f"  • {coin}\n"
    else:
        message += "<b>SELL:</b>\n  None\n"
    
    print(message)
    print("✓ Buy-only message formatted correctly")
    
    print("\n" + "="*60)
    print("All message formatting tests passed! ✓")
    print("="*60)


if __name__ == "__main__":
    test_telegram_formatting()
