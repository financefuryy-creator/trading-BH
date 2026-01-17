"""
Module for generating buy/sell signals based on Bollinger Bands and Heikin-Ashi strategy.
"""
import logging
from indicators import (
    calculate_bollinger_bands,
    calculate_heikin_ashi,
    get_ha_candle_color,
    calculate_ha_body_size_percentage
)

logger = logging.getLogger(__name__)


def check_bb_touch(row, band_type='lower'):
    """
    Check if a Heikin-Ashi candle touches or breaks a Bollinger Band.
    
    Args:
        row: DataFrame row with HA candles and BB data
        band_type: 'lower' or 'upper' band to check
    
    Returns:
        True if candle touches/breaks the band, False otherwise
    """
    if band_type == 'lower':
        # Check if HA candle body or wick touches/breaks lower BB
        return row['HA_LOW'] <= row['BB_LOWER']
    else:  # upper
        # Check if HA candle body or wick touches/breaks upper BB
        return row['HA_HIGH'] >= row['BB_UPPER']


def generate_signals(df, min_body_size=30):
    """
    Generate buy/sell signals based on the strategy.
    
    Strategy:
    - Buy Signal: Red HA candle touches/breaks lower BB, next candle is green with >=30% body
    - Sell Signal: Green HA candle touches/breaks upper BB, next candle is red with >=30% body
    
    Args:
        df: DataFrame with OHLC data
        min_body_size: Minimum body size percentage for confirmation (default: 30)
    
    Returns:
        Tuple of (signal_type, signal_details) where signal_type is 'BUY', 'SELL', or None
    """
    # Calculate indicators
    df = calculate_bollinger_bands(df)
    df = calculate_heikin_ashi(df)
    
    # Add color and body size columns
    df['HA_COLOR'] = df.apply(get_ha_candle_color, axis=1)
    df['HA_BODY_SIZE'] = df.apply(calculate_ha_body_size_percentage, axis=1)
    
    # Need at least 2 candles to generate signals
    if len(df) < 2:
        return None, None
    
    # Look at the last 2 candles
    prev_candle = df.iloc[-2]
    current_candle = df.iloc[-1]
    
    # Check for BUY signal
    # Previous candle: red HA touching/breaking lower BB
    # Current candle: green HA with at least 30% body size
    if (prev_candle['HA_COLOR'] == 'red' and 
        check_bb_touch(prev_candle, 'lower') and
        current_candle['HA_COLOR'] == 'green' and
        current_candle['HA_BODY_SIZE'] >= min_body_size):
        
        signal_details = {
            'signal': 'BUY',
            'prev_candle_low': prev_candle['HA_LOW'],
            'bb_lower': prev_candle['BB_LOWER'],
            'current_body_size': current_candle['HA_BODY_SIZE'],
            'timestamp': df.index[-1]
        }
        logger.info(f"BUY signal generated: {signal_details}")
        return 'BUY', signal_details
    
    # Check for SELL signal
    # Previous candle: green HA touching/breaking upper BB
    # Current candle: red HA with at least 30% body size
    if (prev_candle['HA_COLOR'] == 'green' and 
        check_bb_touch(prev_candle, 'upper') and
        current_candle['HA_COLOR'] == 'red' and
        current_candle['HA_BODY_SIZE'] >= min_body_size):
        
        signal_details = {
            'signal': 'SELL',
            'prev_candle_high': prev_candle['HA_HIGH'],
            'bb_upper': prev_candle['BB_UPPER'],
            'current_body_size': current_candle['HA_BODY_SIZE'],
            'timestamp': df.index[-1]
        }
        logger.info(f"SELL signal generated: {signal_details}")
        return 'SELL', signal_details
    
    return None, None


def scan_multiple_pairs(data_dict, min_body_size=30):
    """
    Scan multiple trading pairs for buy/sell signals.
    
    Args:
        data_dict: Dictionary with symbol as key and DataFrame as value
        min_body_size: Minimum body size percentage for confirmation
    
    Returns:
        Dictionary with 'BUY' and 'SELL' lists containing symbols
    """
    signals = {
        'BUY': [],
        'SELL': []
    }
    
    for symbol, df in data_dict.items():
        try:
            signal_type, signal_details = generate_signals(df, min_body_size)
            if signal_type == 'BUY':
                signals['BUY'].append(symbol)
            elif signal_type == 'SELL':
                signals['SELL'].append(symbol)
        except Exception as e:
            logger.error(f"Error generating signals for {symbol}: {e}")
    
    return signals
