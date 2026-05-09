"""
Order management module.
Handles order placement logic and order state management.
"""

import logging
from decimal import Decimal
from typing import Dict, Any, Optional

from .client import BinanceClient, APIError, NetworkError
from .validators import OrderValidator, ValidationError

logger = logging.getLogger("trading_bot")


class OrderManager:
    """Manages order placement and tracking."""
    
    def __init__(self, client: BinanceClient):
        """
        Initialize OrderManager.
        
        Args:
            client: BinanceClient instance
        """
        self.client = client
        self.orders = {}  # Track placed orders
        
        logger.info("OrderManager initialized")
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: str
    ) -> Dict[str, Any]:
        """
        Place a market order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            
        Returns:
            Order response details
            
        Raises:
            ValidationError: If input validation fails
            APIError: If API call fails
            NetworkError: If network error occurs
        """
        try:
            # Validate input
            symbol, side, _, quantity, _, _ = OrderValidator.validate_order_params(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                price=None,
                stop_price=None
            )
            
            # Place order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type="MARKET",
                quantity=quantity,
                price=None,
                stop_price=None
            )
            
            # Store order
            order_id = response.get("orderId")
            self.orders[order_id] = response
            
            return response
            
        except (ValidationError, APIError, NetworkError) as e:
            logger.error(f"Market order failed: {e}")
            raise
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str
    ) -> Dict[str, Any]:
        """
        Place a limit order.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Limit price
            
        Returns:
            Order response details
            
        Raises:
            ValidationError: If input validation fails
            APIError: If API call fails
            NetworkError: If network error occurs
        """
        try:
            # Validate input
            symbol, side, _, quantity, price, _ = OrderValidator.validate_order_params(
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                stop_price=None
            )
            
            # Place order
            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type="LIMIT",
                quantity=quantity,
                price=price,
                stop_price=None
            )
            
            # Store order
            order_id = response.get("orderId")
            self.orders[order_id] = response
            
            return response
            
        except (ValidationError, APIError, NetworkError) as e:
            logger.error(f"Limit order failed: {e}")
            raise

    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        stop_price: str
    ) -> Dict[str, Any]:
        """
        Place a stop-limit order.

        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            quantity: Order quantity
            price: Limit price
            stop_price: Trigger price

        Returns:
            Order response details

        Raises:
            ValidationError: If input validation fails
            APIError: If API call fails
            NetworkError: If network error occurs
        """
        try:
            symbol, side, _, quantity, price, stop_price = OrderValidator.validate_order_params(
                symbol=symbol,
                side=side,
                order_type="STOP_LIMIT",
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )

            response = self.client.place_order(
                symbol=symbol,
                side=side,
                order_type="STOP_LIMIT",
                quantity=quantity,
                price=price,
                stop_price=stop_price,
            )

            order_id = response.get("orderId")
            self.orders[order_id] = response

            return response

        except (ValidationError, APIError, NetworkError) as e:
            logger.error(f"Stop-limit order failed: {e}")
            raise
    
    def format_order_response(self, response: Dict[str, Any]) -> str:
        """
        Format order response for display.
        
        Args:
            response: Order response from API
            
        Returns:
            Formatted string for display
        """
        output = "\n" + "=" * 70 + "\n"
        output += "ORDER RESPONSE\n"
        output += "=" * 70 + "\n"
        
        # Key fields
        key_fields = [
            ("Order ID", "orderId"),
            ("Symbol", "symbol"),
            ("Side", "side"),
            ("Type", "type"),
            ("Orig Type", "origType"),
            ("Status", "status"),
            ("Quantity", "origQty"),
            ("Executed Qty", "executedQty"),
            ("Price", "price"),
            ("Stop Price", "stopPrice"),
            ("Avg Price", "avgPrice"),
            ("Commission", "commission"),
            ("Commission Asset", "commissionAsset"),
            ("Time In Force", "timeInForce"),
        ]
        
        for label, key in key_fields:
            value = response.get(key)
            if value is not None:
                output += f"{label:20s}: {value}\n"
        
        output += "=" * 70 + "\n"
        
        return output
    
    def format_order_summary(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None
    ) -> str:
        """
        Format order request summary for display.
        
        Args:
            symbol: Trading pair symbol
            side: Order side
            order_type: Order type (MARKET/LIMIT/STOP_LIMIT)
            quantity: Order quantity
            price: Order price (for LIMIT and STOP_LIMIT orders)
            stop_price: Stop price (for STOP_LIMIT orders)
            
        Returns:
            Formatted string for display
        """
        output = "\n" + "=" * 70 + "\n"
        output += "ORDER REQUEST SUMMARY\n"
        output += "=" * 70 + "\n"
        output += f"{'Symbol':<20}: {symbol}\n"
        output += f"{'Side':<20}: {side}\n"
        output += f"{'Type':<20}: {order_type}\n"
        output += f"{'Quantity':<20}: {quantity}\n"
        
        if price:
            output += f"{'Price':<20}: {price}\n"
            notional = quantity * price
            output += f"{'Notional Value':<20}: {notional} USDT\n"

        if stop_price:
            output += f"{'Stop Price':<20}: {stop_price}\n"
        
        output += "=" * 70 + "\n"
        
        return output
    
    @staticmethod
    def format_success_message(order_id: int, order_type: str, side: str) -> str:
        """Format success message."""
        return f"\n✓ {side} {order_type} order placed successfully (ID: {order_id})\n"
    
    @staticmethod
    def format_error_message(error_message: str) -> str:
        """Format error message."""
        return f"\n✗ Order placement failed: {error_message}\n"
