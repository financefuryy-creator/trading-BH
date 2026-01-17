#!/usr/bin/env python3
"""
Test scheduler logic and IST time checking
"""

from datetime import datetime
import pytz

def test_time_in_range():
    """Test the IST time range checking logic"""
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    print("Testing IST time range logic")
    print("="*60)
    
    # Test different times
    test_cases = [
        (9, 22),   # 9:22 AM - Should be True
        (10, 22),  # 10:22 AM - Should be True
        (14, 22),  # 2:22 PM - Should be True
        (22, 22),  # 10:22 PM - Should be True
        (23, 22),  # 11:22 PM - Should be False (outside range)
        (8, 22),   # 8:22 AM - Should be False (before 9 AM)
        (12, 30),  # 12:30 PM - Should be False (not at :22)
        (15, 22),  # 3:22 PM - Should be True
    ]
    
    for hour, minute in test_cases:
        # Create a test datetime
        test_time = datetime.now(ist_tz).replace(hour=hour, minute=minute)
        
        # Check logic
        is_valid = False
        if minute == 22:
            if 9 <= hour <= 22:
                is_valid = True
        
        status = "✓ PASS" if is_valid else "✗ SKIP"
        print(f"{status} | {test_time.strftime('%I:%M %p')} (Hour: {hour:02d})")
    
    print("="*60)
    
    # Show current IST time
    current_ist = datetime.now(ist_tz)
    print(f"\nCurrent IST time: {current_ist.strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"Current hour: {current_ist.hour}, minute: {current_ist.minute}")
    
    if current_ist.minute == 22 and 9 <= current_ist.hour <= 22:
        print("✓ Bot would run NOW")
    else:
        print("✗ Bot would NOT run at this time")
    
    # Calculate next run time
    next_hour = current_ist.hour
    if current_ist.minute >= 22:
        next_hour += 1
    
    if next_hour < 9:
        next_hour = 9
    elif next_hour > 22:
        next_hour = 9  # Next day
    
    print(f"\nNext scheduled run would be at: {next_hour:02d}:22")


if __name__ == "__main__":
    test_time_in_range()
