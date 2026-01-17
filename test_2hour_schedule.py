#!/usr/bin/env python3
"""
Test the new 2-hour schedule logic.
"""
from datetime import datetime
import pytz


def test_2hour_schedule():
    """Test the 2-hour schedule logic for IST"""
    
    # Expected schedule times
    TRADING_SCHEDULE_TIMES = [
        (9, 30),   # 9:30 AM IST
        (11, 30),  # 11:30 AM IST
        (13, 30),  # 1:30 PM IST
        (15, 30),  # 3:30 PM IST
        (17, 30),  # 5:30 PM IST
        (19, 30),  # 7:30 PM IST
        (21, 30),  # 9:30 PM IST
    ]
    
    print("Testing 2-Hour Schedule Logic")
    print("=" * 60)
    print("Expected execution times (IST):")
    for hour, minute in TRADING_SCHEDULE_TIMES:
        print(f"  • {hour:02d}:{minute:02d} ({hour % 12 or 12}:{minute:02d} {'PM' if hour >= 12 else 'AM'})")
    print("=" * 60)
    
    # Test cases: (hour, minute, should_run)
    test_cases = [
        (9, 30, True),   # 9:30 AM - Should run
        (9, 31, True),   # 9:31 AM - Within tolerance
        (9, 29, True),   # 9:29 AM - Within tolerance
        (10, 30, False), # 10:30 AM - Not scheduled
        (11, 30, True),  # 11:30 AM - Should run
        (12, 30, False), # 12:30 PM - Not scheduled
        (13, 30, True),  # 1:30 PM - Should run
        (14, 30, False), # 2:30 PM - Not scheduled
        (15, 30, True),  # 3:30 PM - Should run
        (16, 30, False), # 4:30 PM - Not scheduled
        (17, 30, True),  # 5:30 PM - Should run
        (18, 30, False), # 6:30 PM - Not scheduled
        (19, 30, True),  # 7:30 PM - Should run
        (20, 30, False), # 8:30 PM - Not scheduled
        (21, 30, True),  # 9:30 PM - Should run
        (22, 30, False), # 10:30 PM - Not scheduled
        (8, 30, False),  # 8:30 AM - Before first run
        (23, 30, False), # 11:30 PM - After last run
    ]
    
    print("\nTest Cases:")
    print("-" * 60)
    
    passed = 0
    failed = 0
    
    for hour, minute, expected in test_cases:
        # Simulate the schedule check logic
        is_scheduled = False
        for sched_hour, sched_minute in TRADING_SCHEDULE_TIMES:
            if hour == sched_hour and abs(minute - sched_minute) <= 1:
                is_scheduled = True
                break
        
        # Check result
        test_passed = (is_scheduled == expected)
        status = "✓ PASS" if test_passed else "✗ FAIL"
        
        if test_passed:
            passed += 1
        else:
            failed += 1
        
        time_str = f"{hour:02d}:{minute:02d}"
        am_pm = "PM" if hour >= 12 else "AM"
        hour_12 = hour % 12 or 12
        readable = f"{hour_12}:{minute:02d} {am_pm}"
        
        expected_str = "RUN" if expected else "SKIP"
        actual_str = "RUN" if is_scheduled else "SKIP"
        
        print(f"{status} | {time_str} ({readable:>11}) | Expected: {expected_str:4} | Actual: {actual_str:4}")
    
    print("-" * 60)
    print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    
    # Show current IST time
    ist = pytz.timezone('Asia/Kolkata')
    current_ist = datetime.now(ist)
    print(f"\nCurrent IST time: {current_ist.strftime('%Y-%m-%d %I:%M:%S %p')}")
    
    # Check if bot would run now
    is_now_scheduled = False
    for hour, minute in TRADING_SCHEDULE_TIMES:
        if current_ist.hour == hour and abs(current_ist.minute - minute) <= 1:
            is_now_scheduled = True
            break
    
    if is_now_scheduled:
        print("✓ Bot would RUN NOW")
    else:
        print("✗ Bot would NOT run at this time")
        
        # Calculate next run time
        next_run = None
        for hour, minute in TRADING_SCHEDULE_TIMES:
            if (hour > current_ist.hour) or (hour == current_ist.hour and minute > current_ist.minute):
                next_run = (hour, minute)
                break
        
        if next_run is None:
            next_run = TRADING_SCHEDULE_TIMES[0]  # Next day
            print(f"Next scheduled run: Tomorrow at {next_run[0]:02d}:{next_run[1]:02d}")
        else:
            print(f"Next scheduled run: Today at {next_run[0]:02d}:{next_run[1]:02d}")
    
    print("=" * 60)
    
    # Verify 2-hour intervals
    print("\nVerifying 2-hour intervals:")
    for i in range(len(TRADING_SCHEDULE_TIMES) - 1):
        curr = TRADING_SCHEDULE_TIMES[i]
        next_time = TRADING_SCHEDULE_TIMES[i + 1]
        
        curr_minutes = curr[0] * 60 + curr[1]
        next_minutes = next_time[0] * 60 + next_time[1]
        diff_hours = (next_minutes - curr_minutes) / 60
        
        print(f"  {curr[0]:02d}:{curr[1]:02d} -> {next_time[0]:02d}:{next_time[1]:02d}: {diff_hours} hours")
    
    return failed == 0


if __name__ == "__main__":
    success = test_2hour_schedule()
    exit(0 if success else 1)
