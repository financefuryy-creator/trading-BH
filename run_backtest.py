"""
Utility script for backtesting the trading strategy.
"""
import logging
import pandas as pd
import argparse
from data_fetcher import BinanceDataFetcher
from backtesting import Backtester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_trading_pairs(filepath='trading_pairs.csv'):
    """Load trading pairs from CSV file."""
    try:
        df = pd.read_csv(filepath)
        # Convert to CCXT format
        symbols = []
        for symbol in df['symbol'].tolist():
            if 'USDT' in symbol:
                base = symbol.replace('USDT', '')
                symbols.append(f"{base}/USDT")
            else:
                symbols.append(symbol)
        return symbols
    except Exception as e:
        logger.error(f"Error loading trading pairs: {e}")
        return []


def run_backtest(symbols=None, limit=500, initial_capital=10000):
    """
    Run backtest on specified trading pairs.
    
    Args:
        symbols: List of trading pairs (None = load from CSV)
        limit: Number of historical candles to fetch
        initial_capital: Initial capital for backtesting
    """
    if symbols is None:
        symbols = load_trading_pairs()
    
    if not symbols:
        logger.error("No trading pairs to backtest")
        return
    
    logger.info(f"Starting backtest for {len(symbols)} pairs")
    logger.info(f"Initial capital: ${initial_capital}")
    
    # Fetch historical data
    fetcher = BinanceDataFetcher()
    data_dict = fetcher.fetch_multiple_pairs(symbols, timeframe='1h', limit=limit)
    
    if not data_dict:
        logger.error("Failed to fetch historical data")
        return
    
    # Run backtest
    backtester = Backtester(initial_capital=initial_capital)
    results = backtester.backtest_multiple_pairs(data_dict)
    
    # Generate and display reports
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    
    total_capital = 0
    total_trades = 0
    winning_pairs = 0
    
    for symbol, result in results.items():
        print(backtester.generate_report(result))
        total_capital += result['final_capital']
        total_trades += result['total_trades']
        if result['returns_percentage'] > 0:
            winning_pairs += 1
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total pairs backtested: {len(results)}")
    print(f"Profitable pairs: {winning_pairs}")
    print(f"Total trades executed: {total_trades}")
    print(f"Average capital per pair: ${total_capital / len(results):.2f}")
    print("=" * 80)


def main():
    """Main entry point for backtest script."""
    parser = argparse.ArgumentParser(description='Backtest trading strategy')
    parser.add_argument('--pairs', nargs='+', help='Trading pairs to backtest (e.g., BTC/USDT ETH/USDT)')
    parser.add_argument('--limit', type=int, default=500, help='Number of historical candles (default: 500)')
    parser.add_argument('--capital', type=float, default=10000, help='Initial capital (default: 10000)')
    
    args = parser.parse_args()
    
    run_backtest(symbols=args.pairs, limit=args.limit, initial_capital=args.capital)


if __name__ == "__main__":
    main()
