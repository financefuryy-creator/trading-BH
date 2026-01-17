#!/usr/bin/env python3
"""
Demo script showing bot capabilities without long-running schedule
Performs one scan and exits
"""

import sys
from main import BinanceTradingBot
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def demo_scan():
    """Perform a single demo scan"""
    print("\n" + "="*60)
    print("Binance Trading Bot - Demo Scan")
    print("="*60)
    print("\nThis will perform a single scan of all configured pairs")
    print("and display any buy/sell signals detected.\n")
    
    try:
        # Create bot instance
        print("Initializing bot...")
        bot = BinanceTradingBot()
        print(f"✓ Bot initialized with {len(bot.pairs)} pairs\n")
        
        # Run scan
        print("Starting scan (this may take 1-2 minutes)...")
        print("-" * 60)
        bot.run_scan()
        print("-" * 60)
        
        print("\n✓ Demo scan completed successfully!")
        print("\nTo run the bot on schedule (XX:22 from 9:22 AM to 10:22 PM IST):")
        print("  python main.py")
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(demo_scan())
