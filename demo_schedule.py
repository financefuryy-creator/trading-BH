#!/usr/bin/env python3
"""
Schedule Demonstration Script
Shows the trading bot's execution schedule without running the full bot
"""

import schedule
import pytz
from datetime import datetime, timedelta
import time

# IST Timezone
IST = pytz.timezone('Asia/Kolkata')


def demo_execution(scheduled_time):
    """Simulated bot execution"""
    current = datetime.now(IST)
    print(f"✓ Executed at {current.strftime('%H:%M:%S')} IST (scheduled: {scheduled_time})")


def demonstrate_schedule():
    """Demonstrate the schedule configuration"""
    print("=" * 70)
    print("Trading Bot Schedule Demonstration")
    print("=" * 70)
    
    # Clear schedule
    schedule.clear()
    
    # Configure schedule (same as in main.py)
    schedule_times = [
        "09:30", "10:30", "11:30", "12:30", "13:30", "14:30", "15:30",
        "16:30", "17:30", "18:30", "19:30", "20:30", "21:30", "22:30"
    ]
    
    print(f"\n📅 Current Time: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"\n📋 Scheduled Execution Times:")
    print(f"   Pattern: Every hour at :30 minutes")
    print(f"   Timezone: IST (UTC+5:30)")
    print(f"   Total executions per day: {len(schedule_times)}\n")
    
    # Schedule all jobs
    for i, time_str in enumerate(schedule_times, 1):
        schedule.every().day.at(time_str).do(demo_execution, time_str)
        print(f"   {i:2d}. {time_str} IST")
    
    # Show next execution
    next_run = schedule.next_run()
    if next_run:
        print(f"\n⏰ Next scheduled execution:")
        print(f"   {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Calculate time until next run
        now = datetime.now()
        time_until = next_run - now
        hours = time_until.seconds // 3600
        minutes = (time_until.seconds % 3600) // 60
        print(f"   Time until next run: {hours}h {minutes}m")
    
    print(f"\n{'=' * 70}")
    print(f"✅ Schedule configured successfully!")
    print(f"{'=' * 70}\n")
    
    # Show all upcoming executions for today
    print("📊 All scheduled times for reference:")
    print("   " + ", ".join(schedule_times))
    print()


if __name__ == "__main__":
    demonstrate_schedule()
    
    # Optional: Run for a few iterations to show it working
    print("To see the schedule in action, the bot would run continuously.")
    print("Each execution analyzes trading pairs and sends Telegram notifications.")
    print("\nPress Ctrl+C to exit demonstration.\n")
    
    try:
        iteration = 0
        while iteration < 3:  # Just show a few iterations
            schedule.run_pending()
            time.sleep(1)
            iteration += 1
    except KeyboardInterrupt:
        print("\nDemonstration stopped.")
