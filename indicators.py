"""
Module for calculating technical indicators: Bollinger Bands and Heikin-Ashi candles.
"""
import pandas as pd
import numpy as np


def calculate_bollinger_bands(df, period=20, std_dev=2):
    """
    Calculate Bollinger Bands for a given dataframe.
    
    Args:
        df: DataFrame with OHLC data containing 'close' column
        period: Period for moving average (default: 20)
        std_dev: Standard deviation multiplier (default: 2)
    
    Returns:
        DataFrame with BB_MIDDLE, BB_UPPER, BB_LOWER columns added
    """
    df = df.copy()
    df['BB_MIDDLE'] = df['close'].rolling(window=period).mean()
    df['BB_STD'] = df['close'].rolling(window=period).std()
    df['BB_UPPER'] = df['BB_MIDDLE'] + (std_dev * df['BB_STD'])
    df['BB_LOWER'] = df['BB_MIDDLE'] - (std_dev * df['BB_STD'])
    df.drop('BB_STD', axis=1, inplace=True)
    return df


def calculate_heikin_ashi(df):
    """
    Calculate Heikin-Ashi candles from OHLC data.
    
    Args:
        df: DataFrame with OHLC data (open, high, low, close columns)
    
    Returns:
        DataFrame with HA_OPEN, HA_HIGH, HA_LOW, HA_CLOSE columns added
    """
    df = df.copy()
    
    # Calculate HA Close
    df['HA_CLOSE'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
    
    # Calculate HA Open
    df['HA_OPEN'] = 0.0
    for i in range(len(df)):
        if i == 0:
            df.loc[df.index[i], 'HA_OPEN'] = (df.loc[df.index[i], 'open'] + df.loc[df.index[i], 'close']) / 2
        else:
            df.loc[df.index[i], 'HA_OPEN'] = (df.loc[df.index[i-1], 'HA_OPEN'] + df.loc[df.index[i-1], 'HA_CLOSE']) / 2
    
    # Calculate HA High and HA Low
    df['HA_HIGH'] = df[['high', 'HA_OPEN', 'HA_CLOSE']].max(axis=1)
    df['HA_LOW'] = df[['low', 'HA_OPEN', 'HA_CLOSE']].min(axis=1)
    
    return df


def get_ha_candle_color(row):
    """
    Determine if a Heikin-Ashi candle is green (bullish) or red (bearish).
    
    Args:
        row: DataFrame row with HA_OPEN and HA_CLOSE
    
    Returns:
        'green' if bullish, 'red' if bearish
    """
    return 'green' if row['HA_CLOSE'] > row['HA_OPEN'] else 'red'


def calculate_ha_body_size_percentage(row):
    """
    Calculate the body size percentage of a Heikin-Ashi candle.
    
    Args:
        row: DataFrame row with HA_OPEN, HA_HIGH, HA_LOW, HA_CLOSE
    
    Returns:
        Body size as a percentage of the total candle range
    """
    total_range = row['HA_HIGH'] - row['HA_LOW']
    if total_range == 0:
        return 0
    body_size = abs(row['HA_CLOSE'] - row['HA_OPEN'])
    return (body_size / total_range) * 100
