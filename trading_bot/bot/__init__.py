"""
Simplified Trading Bot - Binance Futures Testnet Order Placement Application
"""

__version__ = "1.0.0"
__author__ = "Trading Bot"

from .client import BinanceClient
from .orders import OrderManager

__all__ = ["BinanceClient", "OrderManager"]
