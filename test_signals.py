#!/usr/bin/env python3
"""
Unit tests for signal generation logic.
Tests the BH strategy with mock data to ensure accuracy.
"""

import pandas as pd
import numpy as np
from main import TradingBot


class SignalTester:
    """Test class for validating signal generation logic."""
    
    def __init__(self):
        """Initialize tester with trading bot."""
        self.bot = TradingBot()
    
    def create_mock_data(self, num_candles=30):
        """
        Create mock OHLCV data for testing.
        
        Args:
            num_candles: Number of candles to generate
            
        Returns:
            DataFrame with mock OHLCV data
        """
        # Set seed for reproducible test data
        np.random.seed(42)
        
        # Generate mock data with realistic price movements
        base_price = 100.0
        timestamps = pd.date_range(start='2024-01-01', periods=num_candles, freq='1h')
        
        data = []
        current_price = base_price
        
        for i, ts in enumerate(timestamps):
            # Random price movements
            volatility = 0.02
            change = np.random.randn() * volatility * current_price
            
            open_price = current_price
            close_price = current_price + change
            high_price = max(open_price, close_price) * (1 + abs(np.random.randn() * 0.01))
            low_price = min(open_price, close_price) * (1 - abs(np.random.randn() * 0.01))
            volume = np.random.uniform(1000, 10000)
            
            data.append({
                'timestamp': ts,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        return pd.DataFrame(data)
    
    def create_buy_signal_scenario(self):
        """
        Create a scenario that should generate a buy signal.
        
        Scenario:
        - Previous candle: Red HA candle touching lower BB
        - Current candle: Green HA candle with >30% body
        """
        df = self.create_mock_data(30)
        
        # Calculate indicators
        df = self.bot.calculate_bollinger_bands(df)
        df = self.bot.calculate_heikin_ashi(df)
        
        # Manually set up buy signal scenario in last 2 candles
        # Previous candle: Red and touching lower BB
        df.loc[len(df)-2, 'ha_open'] = 100.0
        df.loc[len(df)-2, 'ha_close'] = 95.0  # Red candle (close < open)
        df.loc[len(df)-2, 'ha_low'] = 94.0
        df.loc[len(df)-2, 'ha_high'] = 101.0
        df.loc[len(df)-2, 'bb_lower'] = 95.5  # Lower BB above ha_low (candle touches it)
        
        # Current candle: Green with good body size
        df.loc[len(df)-1, 'ha_open'] = 95.0
        df.loc[len(df)-1, 'ha_close'] = 99.0  # Green candle (close > open)
        df.loc[len(df)-1, 'ha_low'] = 94.5
        df.loc[len(df)-1, 'ha_high'] = 99.5
        # Body = 4.0, Range = 5.0, Body% = 80% (well above 30%)
        
        return df
    
    def create_sell_signal_scenario(self):
        """
        Create a scenario that should generate a sell signal.
        
        Scenario:
        - Previous candle: Green HA candle touching upper BB
        - Current candle: Red HA candle with >30% body
        """
        df = self.create_mock_data(30)
        
        # Calculate indicators
        df = self.bot.calculate_bollinger_bands(df)
        df = self.bot.calculate_heikin_ashi(df)
        
        # Manually set up sell signal scenario in last 2 candles
        # Previous candle: Green and touching upper BB
        df.loc[len(df)-2, 'ha_open'] = 100.0
        df.loc[len(df)-2, 'ha_close'] = 105.0  # Green candle (close > open)
        df.loc[len(df)-2, 'ha_low'] = 99.0
        df.loc[len(df)-2, 'ha_high'] = 106.0
        df.loc[len(df)-2, 'bb_upper'] = 105.5  # Upper BB below ha_high (candle touches it)
        
        # Current candle: Red with good body size
        df.loc[len(df)-1, 'ha_open'] = 105.0
        df.loc[len(df)-1, 'ha_close'] = 101.0  # Red candle (close < open)
        df.loc[len(df)-1, 'ha_low'] = 100.5
        df.loc[len(df)-1, 'ha_high'] = 105.5
        # Body = 4.0, Range = 5.0, Body% = 80% (well above 30%)
        
        return df
    
    def create_no_signal_scenario(self):
        """
        Create a scenario that should NOT generate any signal.
        
        Scenario:
        - Candles don't touch BB or don't meet body size requirements
        """
        df = self.create_mock_data(30)
        
        # Calculate indicators
        df = self.bot.calculate_bollinger_bands(df)
        df = self.bot.calculate_heikin_ashi(df)
        
        # Set up scenario with no valid signal
        # Previous candle: Red but not touching lower BB
        df.loc[len(df)-2, 'ha_open'] = 100.0
        df.loc[len(df)-2, 'ha_close'] = 98.0
        df.loc[len(df)-2, 'ha_low'] = 97.0
        df.loc[len(df)-2, 'ha_high'] = 101.0
        df.loc[len(df)-2, 'bb_lower'] = 95.0  # Well below candle
        
        # Current candle: Green but small body
        df.loc[len(df)-1, 'ha_open'] = 98.0
        df.loc[len(df)-1, 'ha_close'] = 98.2  # Small body
        df.loc[len(df)-1, 'ha_low'] = 97.5
        df.loc[len(df)-1, 'ha_high'] = 99.0
        # Body = 0.2, Range = 1.5, Body% = 13.3% (below 30%)
        
        return df
    
    def test_buy_signal_detection(self):
        """Test buy signal detection."""
        print("\n" + "="*70)
        print("TEST: Buy Signal Detection")
        print("="*70)
        
        df = self.create_buy_signal_scenario()
        buy_signal, buy_details = self.bot.check_buy_signal(df)
        
        print(f"\nScenario Setup:")
        print(f"  Previous Candle: Red HA touching lower BB")
        print(f"  Current Candle: Green HA with large body")
        print(f"\nExpected Result: BUY signal = True")
        print(f"Actual Result: BUY signal = {buy_signal}")
        print(f"\nDetails:")
        for key, value in buy_details.items():
            if key not in ['timestamp']:
                print(f"  {key}: {value}")
        
        if buy_signal:
            print(f"\n✓ TEST PASSED: Buy signal correctly detected")
        else:
            print(f"\n✗ TEST FAILED: Buy signal not detected when it should be")
        
        return buy_signal
    
    def test_sell_signal_detection(self):
        """Test sell signal detection."""
        print("\n" + "="*70)
        print("TEST: Sell Signal Detection")
        print("="*70)
        
        df = self.create_sell_signal_scenario()
        sell_signal, sell_details = self.bot.check_sell_signal(df)
        
        print(f"\nScenario Setup:")
        print(f"  Previous Candle: Green HA touching upper BB")
        print(f"  Current Candle: Red HA with large body")
        print(f"\nExpected Result: SELL signal = True")
        print(f"Actual Result: SELL signal = {sell_signal}")
        print(f"\nDetails:")
        for key, value in sell_details.items():
            if key not in ['timestamp']:
                print(f"  {key}: {value}")
        
        if sell_signal:
            print(f"\n✓ TEST PASSED: Sell signal correctly detected")
        else:
            print(f"\n✗ TEST FAILED: Sell signal not detected when it should be")
        
        return sell_signal
    
    def test_no_signal_detection(self):
        """Test that no signal is generated when conditions aren't met."""
        print("\n" + "="*70)
        print("TEST: No Signal Detection")
        print("="*70)
        
        df = self.create_no_signal_scenario()
        buy_signal, buy_details = self.bot.check_buy_signal(df)
        sell_signal, sell_details = self.bot.check_sell_signal(df)
        
        print(f"\nScenario Setup:")
        print(f"  Previous Candle: Red but not touching BB")
        print(f"  Current Candle: Green with small body (<30%)")
        print(f"\nExpected Result: No signals")
        print(f"Actual Result: BUY={buy_signal}, SELL={sell_signal}")
        print(f"\nBuy Details:")
        for key, value in buy_details.items():
            if key not in ['timestamp']:
                print(f"  {key}: {value}")
        
        if not buy_signal and not sell_signal:
            print(f"\n✓ TEST PASSED: No false signals generated")
        else:
            print(f"\n✗ TEST FAILED: False signal detected")
        
        return not buy_signal and not sell_signal
    
    def test_body_size_calculation(self):
        """Test body size percentage calculation."""
        print("\n" + "="*70)
        print("TEST: Body Size Calculation")
        print("="*70)
        
        # Test case 1: 50% body
        ha_open, ha_close, ha_high, ha_low = 100, 102, 103, 99
        body_percent = self.bot.calculate_body_size_percent(ha_open, ha_close, ha_high, ha_low)
        expected = 50.0  # Body=2, Range=4, 2/4=50%
        print(f"\nTest 1: Body=2, Range=4")
        print(f"  Expected: 50.0%")
        print(f"  Actual: {body_percent}%")
        print(f"  {'✓ PASSED' if abs(body_percent - expected) < 0.1 else '✗ FAILED'}")
        
        # Test case 2: 80% body
        ha_open, ha_close, ha_high, ha_low = 100, 104, 104.5, 99.5
        body_percent = self.bot.calculate_body_size_percent(ha_open, ha_close, ha_high, ha_low)
        expected = 80.0  # Body=4, Range=5, 4/5=80%
        print(f"\nTest 2: Body=4, Range=5")
        print(f"  Expected: 80.0%")
        print(f"  Actual: {body_percent}%")
        print(f"  {'✓ PASSED' if abs(body_percent - expected) < 0.1 else '✗ FAILED'}")
        
        # Test case 3: 25% body (below threshold)
        ha_open, ha_close, ha_high, ha_low = 100, 101, 102, 98
        body_percent = self.bot.calculate_body_size_percent(ha_open, ha_close, ha_high, ha_low)
        expected = 25.0  # Body=1, Range=4, 1/4=25%
        print(f"\nTest 3: Body=1, Range=4")
        print(f"  Expected: 25.0%")
        print(f"  Actual: {body_percent}%")
        print(f"  {'✓ PASSED' if abs(body_percent - expected) < 0.1 else '✗ FAILED'}")
    
    def test_candle_color_detection(self):
        """Test candle color detection."""
        print("\n" + "="*70)
        print("TEST: Candle Color Detection")
        print("="*70)
        
        # Test red candle
        is_red = self.bot.is_red_candle(100, 95)
        print(f"\nTest 1: Open=100, Close=95 (Red candle)")
        print(f"  Expected: True")
        print(f"  Actual: {is_red}")
        print(f"  {'✓ PASSED' if is_red else '✗ FAILED'}")
        
        # Test green candle
        is_green = self.bot.is_green_candle(95, 100)
        print(f"\nTest 2: Open=95, Close=100 (Green candle)")
        print(f"  Expected: True")
        print(f"  Actual: {is_green}")
        print(f"  {'✓ PASSED' if is_green else '✗ FAILED'}")
    
    def test_bb_touch_detection(self):
        """Test Bollinger Band touch detection."""
        print("\n" + "="*70)
        print("TEST: Bollinger Band Touch Detection")
        print("="*70)
        
        # Test lower BB touch with low
        touches = self.bot.touches_or_breaks_lower_bb(ha_low=95, ha_close=98, bb_lower=96)
        print(f"\nTest 1: Candle low (95) touches lower BB (96)")
        print(f"  Expected: True")
        print(f"  Actual: {touches}")
        print(f"  {'✓ PASSED' if touches else '✗ FAILED'}")
        
        # Test lower BB touch with close
        touches = self.bot.touches_or_breaks_lower_bb(ha_low=97, ha_close=95, bb_lower=96)
        print(f"\nTest 2: Candle close (95) touches lower BB (96)")
        print(f"  Expected: True")
        print(f"  Actual: {touches}")
        print(f"  {'✓ PASSED' if touches else '✗ FAILED'}")
        
        # Test upper BB touch with high
        touches = self.bot.touches_or_breaks_upper_bb(ha_high=105, ha_close=102, bb_upper=104)
        print(f"\nTest 3: Candle high (105) touches upper BB (104)")
        print(f"  Expected: True")
        print(f"  Actual: {touches}")
        print(f"  {'✓ PASSED' if touches else '✗ FAILED'}")
        
        # Test upper BB touch with close
        touches = self.bot.touches_or_breaks_upper_bb(ha_high=103, ha_close=105, bb_upper=104)
        print(f"\nTest 4: Candle close (105) touches upper BB (104)")
        print(f"  Expected: True")
        print(f"  Actual: {touches}")
        print(f"  {'✓ PASSED' if touches else '✗ FAILED'}")
    
    def run_all_tests(self):
        """Run all tests and report results."""
        print("\n" + "="*70)
        print("RUNNING ALL SIGNAL GENERATION TESTS")
        print("="*70)
        
        results = []
        
        # Run individual component tests
        self.test_body_size_calculation()
        self.test_candle_color_detection()
        self.test_bb_touch_detection()
        
        # Run signal detection tests
        results.append(("Buy Signal Detection", self.test_buy_signal_detection()))
        results.append(("Sell Signal Detection", self.test_sell_signal_detection()))
        results.append(("No Signal Detection", self.test_no_signal_detection()))
        
        # Print summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASSED" if result else "✗ FAILED"
            print(f"{test_name}: {status}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        print("="*70 + "\n")
        
        return passed == total


def main():
    """Main entry point for testing."""
    print("Binance Trading Bot - Signal Generation Tests")
    
    tester = SignalTester()
    all_passed = tester.run_all_tests()
    
    if all_passed:
        print("✓ All tests passed! Signal generation logic is working correctly.")
    else:
        print("✗ Some tests failed. Please review the signal generation logic.")


if __name__ == "__main__":
    main()
