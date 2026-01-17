"""
Module for fetching OHLC data from Binance API.
"""
import ccxt
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BinanceDataFetcher:
    """Fetcher for Binance OHLC data using CCXT."""
    
    def __init__(self):
        """Initialize Binance exchange connection."""
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',  # Use spot market
                }
            })
            logger.info("Binance exchange initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Binance exchange: {e}")
            raise
    
    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100):
        """
        Fetch OHLCV data for a given symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')
            timeframe: Timeframe for candles (default: '1h')
            limit: Number of candles to fetch (default: 100)
        
        Returns:
            DataFrame with OHLCV data or None if error occurs
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            if not ohlcv:
                logger.warning(f"No data returned for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} candles for {symbol}")
            return df
            
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching data for {symbol}: {e}")
            return None
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching data for {symbol}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data for {symbol}: {e}")
            return None
    
    def fetch_multiple_pairs(self, symbols, timeframe='1h', limit=100):
        """
        Fetch OHLCV data for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            timeframe: Timeframe for candles (default: '1h')
            limit: Number of candles to fetch (default: 100)
        
        Returns:
            Dictionary with symbol as key and DataFrame as value
        """
        results = {}
        for symbol in symbols:
            df = self.fetch_ohlcv(symbol, timeframe, limit)
            if df is not None:
                results[symbol] = df
        return results
