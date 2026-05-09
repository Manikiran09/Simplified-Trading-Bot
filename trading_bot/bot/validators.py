"""
Input validation module for trading operations.
Validates user input before sending to Binance API.
"""

import logging
from decimal import Decimal, InvalidOperation
from typing import Tuple

logger = logging.getLogger("trading_bot")


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class OrderValidator:
    """Validates order parameters."""
    
    # Valid order types
    VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_LIMIT"}
    
    # Valid sides
    VALID_SIDES = {"BUY", "SELL"}
    
    # Common trading pairs
    COMMON_PAIRS = {
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT",
        "XRPUSDT", "LTCUSDT", "SOLUSDT", "MATICUSDT", "UNIUSDT"
    }
    
    # Minimum and maximum order values
    MIN_NOTIONAL = 5  # Minimum order notional value in USDT
    MAX_NOTIONAL = 10000000  # Maximum order notional value
    
    # Min/max quantities (common values, actual depends on symbol)
    MIN_QUANTITY = Decimal("0.001")
    MAX_QUANTITY = Decimal("10000")
    
    # Min/max prices
    MIN_PRICE = Decimal("0.01")
    MAX_PRICE = Decimal("999999")
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """
        Validate trading symbol format.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            
        Returns:
            Normalized symbol
            
        Raises:
            ValidationError: If symbol is invalid
        """
        if not isinstance(symbol, str) or not symbol:
            raise ValidationError("Symbol must be a non-empty string")
        
        symbol = symbol.upper()
        
        if not symbol.endswith("USDT"):
            raise ValidationError("Symbol must be USDT-quoted pair (e.g., BTCUSDT)")
        
        if len(symbol) < 7 or len(symbol) > 10:
            raise ValidationError(f"Invalid symbol length: {symbol}")
        
        logger.debug(f"Symbol validated: {symbol}")
        return symbol
    
    @staticmethod
    def validate_side(side: str) -> str:
        """
        Validate order side (BUY/SELL).
        
        Args:
            side: Order side
            
        Returns:
            Normalized side (uppercase)
            
        Raises:
            ValidationError: If side is invalid
        """
        if not isinstance(side, str) or not side:
            raise ValidationError("Side must be a non-empty string")
        
        side = side.upper()
        
        if side not in OrderValidator.VALID_SIDES:
            raise ValidationError(f"Side must be BUY or SELL, got: {side}")
        
        logger.debug(f"Side validated: {side}")
        return side
    
    @staticmethod
    def validate_order_type(order_type: str) -> str:
        """
        Validate order type.
        
        Args:
            order_type: Order type (MARKET, LIMIT)
            
        Returns:
            Normalized order type (uppercase)
            
        Raises:
            ValidationError: If order type is invalid
        """
        if not isinstance(order_type, str) or not order_type:
            raise ValidationError("Order type must be a non-empty string")
        
        order_type = order_type.upper()
        
        if order_type not in OrderValidator.VALID_ORDER_TYPES:
            raise ValidationError(
                f"Order type must be MARKET, LIMIT, or STOP_LIMIT, got: {order_type}"
            )
        
        logger.debug(f"Order type validated: {order_type}")
        return order_type
    
    @staticmethod
    def validate_quantity(quantity: str) -> Decimal:
        """
        Validate order quantity.
        
        Args:
            quantity: Order quantity as string
            
        Returns:
            Quantity as Decimal
            
        Raises:
            ValidationError: If quantity is invalid
        """
        try:
            qty = Decimal(str(quantity).strip())
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError(f"Quantity must be a valid number, got: {quantity}")
        
        if qty <= 0:
            raise ValidationError(f"Quantity must be positive, got: {qty}")
        
        if qty < OrderValidator.MIN_QUANTITY:
            raise ValidationError(
                f"Quantity too small: {qty} (minimum: {OrderValidator.MIN_QUANTITY})"
            )
        
        if qty > OrderValidator.MAX_QUANTITY:
            raise ValidationError(
                f"Quantity too large: {qty} (maximum: {OrderValidator.MAX_QUANTITY})"
            )
        
        # Limit to 8 decimal places (Binance standard)
        qty = qty.quantize(Decimal("0.00000001"))
        
        logger.debug(f"Quantity validated: {qty}")
        return qty
    
    @staticmethod
    def validate_price(price: str) -> Decimal:
        """
        Validate order price.
        
        Args:
            price: Order price as string
            
        Returns:
            Price as Decimal
            
        Raises:
            ValidationError: If price is invalid
        """
        try:
            p = Decimal(str(price).strip())
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError(f"Price must be a valid number, got: {price}")
        
        if p <= 0:
            raise ValidationError(f"Price must be positive, got: {p}")
        
        if p < OrderValidator.MIN_PRICE:
            raise ValidationError(
                f"Price too small: {p} (minimum: {OrderValidator.MIN_PRICE})"
            )
        
        if p > OrderValidator.MAX_PRICE:
            raise ValidationError(
                f"Price too large: {p} (maximum: {OrderValidator.MAX_PRICE})"
            )
        
        # Limit to 8 decimal places
        p = p.quantize(Decimal("0.00000001"))
        
        logger.debug(f"Price validated: {p}")
        return p
    
    @staticmethod
    def validate_order_params(
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str = None,
        stop_price: str = None
    ) -> Tuple[str, str, str, Decimal, Decimal, Decimal]:
        """
        Validate all order parameters together.
        
        Args:
            symbol: Trading pair symbol
            side: Order side (BUY/SELL)
            order_type: Order type (MARKET/LIMIT/STOP_LIMIT)
            quantity: Order quantity
            price: Order price (required for LIMIT and STOP_LIMIT orders)
            stop_price: Stop price (required for STOP_LIMIT orders)
            
        Returns:
            Tuple of validated parameters
            
        Raises:
            ValidationError: If any parameter is invalid
        """
        # Validate individual parameters
        symbol = OrderValidator.validate_symbol(symbol)
        side = OrderValidator.validate_side(side)
        order_type = OrderValidator.validate_order_type(order_type)
        quantity = OrderValidator.validate_quantity(quantity)
        
        # Validate price and stop price requirements
        if order_type in {"LIMIT", "STOP_LIMIT"}:
            if price is None or price == "":
                raise ValidationError(f"Price is required for {order_type} orders")
            price = OrderValidator.validate_price(price)
        else:
            price = None

        if order_type == "STOP_LIMIT":
            if stop_price is None or stop_price == "":
                raise ValidationError("Stop price is required for STOP_LIMIT orders")
            stop_price = OrderValidator.validate_price(stop_price)
        else:
            stop_price = None
        
        logger.info(
            f"Order parameters validated: {symbol} {side} {order_type} {quantity} "
            f"{'@' + str(price) if price else ''}"
            f"{' stop@' + str(stop_price) if stop_price else ''}"
        )
        
        return symbol, side, order_type, quantity, price, stop_price
