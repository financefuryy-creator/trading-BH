"""
Module for visual verification of trading signals.
Generates charts with Heikin-Ashi candles and Bollinger Bands for signal validation.
"""
import logging
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime
import os
import tempfile
import numpy as np

from indicators import (
    calculate_bollinger_bands,
    calculate_heikin_ashi,
    get_ha_candle_color,
    calculate_ha_body_size_percentage
)

logger = logging.getLogger(__name__)


def generate_chart(df, symbol, signal_type=None, save_dir=None):
    """
    Generate a chart with Heikin-Ashi candles and Bollinger Bands.
    
    Args:
        df: DataFrame with OHLC data
        symbol: Trading pair symbol
        signal_type: Type of signal ('BUY', 'SELL', or None)
        save_dir: Directory to save charts (default: temp directory)
    
    Returns:
        Path to saved chart file or None if error occurs
    """
    try:
        # Calculate indicators
        df_with_bb = calculate_bollinger_bands(df.copy())
        df_with_ha = calculate_heikin_ashi(df_with_bb.copy())
        
        # Add color and body size
        df_with_ha['HA_COLOR'] = df_with_ha.apply(get_ha_candle_color, axis=1)
        df_with_ha['HA_BODY_SIZE'] = df_with_ha.apply(calculate_ha_body_size_percentage, axis=1)
        
        # Use last 50 candles for visualization
        plot_df = df_with_ha.tail(50).reset_index(drop=True)
        
        # Create figure
        fig, ax = plt.subplots(figsize=(16, 9))
        
        # Plot Bollinger Bands
        ax.plot(plot_df.index, plot_df['BB_UPPER'], 'b--', label='Upper BB', linewidth=1, alpha=0.7)
        ax.plot(plot_df.index, plot_df['BB_MIDDLE'], 'gray', label='SMA', linewidth=1, alpha=0.7)
        ax.plot(plot_df.index, plot_df['BB_LOWER'], 'b--', label='Lower BB', linewidth=1, alpha=0.7)
        
        # Fill between bands
        ax.fill_between(plot_df.index, plot_df['BB_UPPER'], plot_df['BB_LOWER'], alpha=0.1, color='blue')
        
        # Plot Heikin-Ashi candles
        for idx in plot_df.index:
            row = plot_df.loc[idx]
            
            # Determine color
            color = 'green' if row['HA_COLOR'] == 'green' else 'red'
            
            # Draw body
            body_height = abs(row['HA_CLOSE'] - row['HA_OPEN'])
            body_bottom = min(row['HA_OPEN'], row['HA_CLOSE'])
            
            # Candle body
            rect = mpatches.Rectangle((idx - 0.3, body_bottom), 0.6, body_height,
                                     facecolor=color, edgecolor='black', linewidth=0.5, alpha=0.8)
            ax.add_patch(rect)
            
            # Upper wick
            ax.plot([idx, idx], [max(row['HA_OPEN'], row['HA_CLOSE']), row['HA_HIGH']],
                   color='black', linewidth=1)
            
            # Lower wick
            ax.plot([idx, idx], [row['HA_LOW'], min(row['HA_OPEN'], row['HA_CLOSE'])],
                   color='black', linewidth=1)
        
        # Mark the last candle if there's a signal
        if signal_type and len(plot_df) >= 2:
            last_idx = plot_df.index[-1]
            last_candle = plot_df.iloc[-1]
            
            if signal_type == 'BUY':
                ax.scatter(last_idx, last_candle['HA_LOW'] - (plot_df['HA_HIGH'].max() - plot_df['HA_LOW'].min()) * 0.02,
                          marker='^', s=300, color='green', edgecolors='darkgreen', linewidth=2, zorder=5, label='BUY Signal')
            elif signal_type == 'SELL':
                ax.scatter(last_idx, last_candle['HA_HIGH'] + (plot_df['HA_HIGH'].max() - plot_df['HA_LOW'].min()) * 0.02,
                          marker='v', s=300, color='red', edgecolors='darkred', linewidth=2, zorder=5, label='SELL Signal')
        
        # Formatting
        ax.set_xlabel('Candle Index', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        
        signal_text = f" - {signal_type} SIGNAL" if signal_type else ""
        ax.set_title(f'{symbol} - Heikin-Ashi with Bollinger Bands (2h){signal_text}',
                    fontsize=14, fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Save figure
        if save_dir is None:
            save_dir = tempfile.gettempdir()
        
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(save_dir, f'chart_{symbol.replace("/", "_")}_{timestamp}.png')
        
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        logger.info(f"Chart saved: {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error generating chart for {symbol}: {e}", exc_info=True)
        return None


def verify_signals_visually(data_dict, signals, save_dir=None):
    """
    Generate verification charts for all signals.
    
    Args:
        data_dict: Dictionary with symbol as key and DataFrame as value
        signals: Dictionary with 'BUY' and 'SELL' lists
        save_dir: Directory to save charts (default: temp directory)
    
    Returns:
        Dictionary with symbol as key and chart path as value
    """
    chart_paths = {}
    
    # Generate charts for BUY signals
    for symbol in signals.get('BUY', []):
        if symbol in data_dict:
            chart_path = generate_chart(data_dict[symbol], symbol, 'BUY', save_dir)
            if chart_path:
                chart_paths[symbol] = chart_path
    
    # Generate charts for SELL signals
    for symbol in signals.get('SELL', []):
        if symbol in data_dict:
            chart_path = generate_chart(data_dict[symbol], symbol, 'SELL', save_dir)
            if chart_path:
                chart_paths[symbol] = chart_path
    
    logger.info(f"Generated {len(chart_paths)} verification charts")
    return chart_paths
