"""
Module for backtesting the trading strategy.
"""
import pandas as pd
import logging
from datetime import datetime
from signals import generate_signals

# Constants
MIN_INDICATOR_PERIODS = 30  # Minimum data points needed for BB calculation

logger = logging.getLogger(__name__)


class Backtester:
    """Backtesting engine for the Bollinger Band + Heikin-Ashi strategy."""
    
    def __init__(self, initial_capital=10000):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Initial capital for backtesting (default: 10000)
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.position = None  # 'long', 'short', or None
        self.position_size = 0
        self.entry_price = 0
        self.trades = []
        logger.info(f"Backtester initialized with capital: {initial_capital}")
    
    def backtest_single_pair(self, df, symbol, min_body_size=30):
        """
        Backtest strategy on a single trading pair.
        
        Args:
            df: DataFrame with OHLC data
            symbol: Trading pair symbol
            min_body_size: Minimum body size percentage
        
        Returns:
            Dictionary with backtest results
        """
        self.capital = self.initial_capital
        self.position = None
        self.position_size = 0
        self.entry_price = 0
        self.trades = []
        
        # Need enough data for indicators
        if len(df) < MIN_INDICATOR_PERIODS:
            logger.warning(f"Insufficient data for backtesting {symbol}")
            return None
        
        # Iterate through data points starting from MIN_INDICATOR_PERIODS
        for i in range(MIN_INDICATOR_PERIODS, len(df)):
            current_df = df.iloc[:i+1].copy()
            signal_type, signal_details = generate_signals(current_df, min_body_size)
            current_price = df.iloc[i]['close']
            current_time = df.index[i]
            
            # Handle BUY signal
            if signal_type == 'BUY' and self.position is None:
                # Enter long position
                self.position = 'long'
                self.entry_price = current_price
                self.position_size = self.capital / current_price
                self.trades.append({
                    'type': 'ENTRY_LONG',
                    'timestamp': current_time,
                    'price': current_price,
                    'size': self.position_size
                })
                logger.debug(f"Entered long at {current_price} on {current_time}")
            
            # Handle SELL signal
            elif signal_type == 'SELL':
                # If in long position, exit
                if self.position == 'long':
                    exit_value = self.position_size * current_price
                    profit = exit_value - self.capital
                    self.capital = exit_value
                    self.trades.append({
                        'type': 'EXIT_LONG',
                        'timestamp': current_time,
                        'price': current_price,
                        'size': self.position_size,
                        'profit': profit
                    })
                    logger.debug(f"Exited long at {current_price} on {current_time}, profit: {profit}")
                    self.position = None
                    self.position_size = 0
                    self.entry_price = 0
                # If no position, enter short (not implemented for spot trading)
                # For spot trading, we only trade long positions
        
        # Calculate results
        results = self._calculate_results(symbol)
        return results
    
    def _calculate_results(self, symbol):
        """Calculate performance metrics."""
        total_trades = len([t for t in self.trades if t['type'] in ['EXIT_LONG', 'EXIT_SHORT']])
        winning_trades = len([t for t in self.trades if t.get('profit', 0) > 0])
        losing_trades = len([t for t in self.trades if t.get('profit', 0) < 0])
        
        total_profit = sum([t.get('profit', 0) for t in self.trades])
        final_capital = self.capital
        returns = ((final_capital - self.initial_capital) / self.initial_capital) * 100
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        results = {
            'symbol': symbol,
            'initial_capital': self.initial_capital,
            'final_capital': final_capital,
            'total_profit': total_profit,
            'returns_percentage': returns,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'trades': self.trades
        }
        
        return results
    
    def generate_report(self, results):
        """
        Generate a formatted backtest report.
        
        Args:
            results: Dictionary with backtest results
        
        Returns:
            Formatted report string
        """
        if results is None:
            return "Insufficient data for backtesting"
        
        report = f"""
=== Backtest Report for {results['symbol']} ===
Initial Capital: ${results['initial_capital']:.2f}
Final Capital: ${results['final_capital']:.2f}
Total Profit/Loss: ${results['total_profit']:.2f}
Returns: {results['returns_percentage']:.2f}%

Total Trades: {results['total_trades']}
Winning Trades: {results['winning_trades']}
Losing Trades: {results['losing_trades']}
Win Rate: {results['win_rate']:.2f}%
"""
        return report
    
    def backtest_multiple_pairs(self, data_dict, min_body_size=30):
        """
        Backtest strategy on multiple trading pairs.
        
        Args:
            data_dict: Dictionary with symbol as key and DataFrame as value
            min_body_size: Minimum body size percentage
        
        Returns:
            Dictionary with results for each symbol
        """
        all_results = {}
        for symbol, df in data_dict.items():
            try:
                results = self.backtest_single_pair(df, symbol, min_body_size)
                if results:
                    all_results[symbol] = results
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
        
        return all_results
