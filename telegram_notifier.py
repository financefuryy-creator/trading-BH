"""
Module for sending Telegram notifications.
"""
import logging
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handler for sending Telegram notifications."""
    
    def __init__(self, bot_token, chat_id):
        """
        Initialize Telegram bot.
        
        Args:
            bot_token: Telegram bot token
            chat_id: Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token)
        logger.info(f"Telegram bot initialized for chat ID: {chat_id}")
    
    async def send_message_async(self, message):
        """
        Send a message asynchronously via Telegram.
        
        Args:
            message: Message text to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
            logger.info(f"Message sent successfully to chat {self.chat_id}")
            return True
        except TelegramError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def send_message(self, message):
        """
        Send a message via Telegram (synchronous wrapper).
        
        Args:
            message: Message text to send
        
        Returns:
            True if successful, False otherwise
        """
        try:
            return asyncio.run(self.send_message_async(message))
        except Exception as e:
            logger.error(f"Error in send_message: {e}")
            return False
    
    def format_signals(self, signals):
        """
        Format signals for Telegram message.
        
        Args:
            signals: Dictionary with 'BUY' and 'SELL' lists
        
        Returns:
            Formatted message string
        """
        # Get current IST timestamp
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %I:%M %p IST')
        
        message = "*GHTB - 2Hr BH*\n"
        message += f"_{current_time}_\n\n"
        
        # Format BUY signals
        message += "*BUY*:\n"
        if signals['BUY']:
            for symbol in signals['BUY']:
                # Extract coin name (remove /USDT, USDT suffix)
                coin_name = symbol.replace('/USDT', '').replace('USDT', '')
                message += f"  • {coin_name}\n"
        else:
            message += "  • None\n"
        
        message += "\n"
        
        # Format SELL signals
        message += "*SELL*:\n"
        if signals['SELL']:
            for symbol in signals['SELL']:
                # Extract coin name (remove /USDT, USDT suffix)
                coin_name = symbol.replace('/USDT', '').replace('USDT', '')
                message += f"  • {coin_name}\n"
        else:
            message += "  • None\n"
        
        return message
    
    def send_signals(self, signals):
        """
        Send formatted signals via Telegram.
        
        Args:
            signals: Dictionary with 'BUY' and 'SELL' lists
        
        Returns:
            True if successful, False otherwise
        """
        message = self.format_signals(signals)
        return self.send_message(message)


def send_to_multiple_bots(signals, bot_configs):
    """
    Send signals to multiple Telegram bots.
    
    Args:
        signals: Dictionary with 'BUY' and 'SELL' lists
        bot_configs: List of tuples (bot_token, chat_id)
    
    Returns:
        List of success/failure results
    """
    results = []
    for bot_token, chat_id in bot_configs:
        try:
            notifier = TelegramNotifier(bot_token, chat_id)
            success = notifier.send_signals(signals)
            results.append(success)
        except Exception as e:
            logger.error(f"Error sending to bot {chat_id}: {e}")
            results.append(False)
    return results
