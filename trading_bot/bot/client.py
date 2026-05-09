"""
Binance Futures API client wrapper.
Handles API communication with Binance Futures Testnet.
"""

import logging
import time
from decimal import Decimal
from typing import Dict, Any, Optional
from urllib.parse import urlencode

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("trading_bot")


class NetworkError(Exception):
    """Exception for network-related errors."""
    pass


class APIError(Exception):
    """Exception for API-related errors."""
    pass


class AuthenticationError(APIError):
    """Exception for authentication and API key/secret format issues."""
    pass


class BinanceClient:
    """
    Binance Futures Testnet client.
    Provides methods to interact with Binance Futures Testnet API.
    """
    
    BASE_URL = "https://testnet.binancefuture.com"
    ORDER_ENDPOINT = "/fapi/v1/order"
    
    def __init__(self, api_key: str, api_secret: str, timeout: int = 10):
        """
        Initialize Binance client.
        
        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self.session = self._create_session()
        
        logger.info("BinanceClient initialized with Testnet")
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry strategy.
        
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        
        # Retry strategy for network resilience
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Accept": "application/json",
            "User-Agent": "trading-bot/1.0"
        })
        
        return session
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC SHA256 signature for request.
        
        Args:
            params: Request parameters
            
        Returns:
            Signature string
        """
        import hmac
        import hashlib
        
        query_string = urlencode(params, doseq=True)
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict[str, Any] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make API request to Binance.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs signature
            
        Returns:
            API response as dictionary
            
        Raises:
            NetworkError: If network error occurs
            APIError: If API returns error
        """
        url = f"{self.BASE_URL}{endpoint}"
        params = params or {}
        
        # Add timestamp and signature for signed requests
        if signed:
            signing_params = dict(params)
            signing_params["timestamp"] = int(time.time() * 1000)
            params["timestamp"] = signing_params["timestamp"]
            params["signature"] = self._generate_signature(signing_params)
        
        headers = {"X-MBX-APIKEY": self.api_key}
        
        try:
            logger.debug(f"API Request: {method} {endpoint} | Params: {params}")
            
            if method == "GET":
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method == "POST":
                response = self.session.post(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            elif method == "DELETE":
                response = self.session.delete(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                raise NetworkError(f"Unsupported HTTP method: {method}")
            
            # Log response status
            logger.debug(f"API Response Status: {response.status_code}")
            
            # Handle non-2xx responses
            if response.status_code >= 400:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                error_msg = error_data.get("msg", response.text)
                error_code = error_data.get("code", response.status_code)
                
                logger.error(
                    f"API Error ({error_code}): {error_msg} | "
                    f"Request: {method} {endpoint}"
                )
                
                if error_code in (-2014, -2015):
                    raise AuthenticationError(
                        "Binance rejected the API credentials. "
                        "Re-check BINANCE_API_KEY / BINANCE_API_SECRET from the Futures Testnet API page, "
                        "and make sure there are no spaces or line breaks."
                    )

                raise APIError(f"API Error {error_code}: {error_msg}")
            
            # Parse and return JSON response
            response_data = response.json()
            logger.debug(f"API Response: {response_data}")
            
            return response_data
            
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
            raise NetworkError(f"Request timeout after {self.timeout}s")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise NetworkError(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise NetworkError(f"Request error: {e}")
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise APIError(f"Invalid JSON response: {e}")
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Place an order on Binance Futures Testnet.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY/SELL)
            order_type: Order type (MARKET/LIMIT/STOP_LIMIT)
            quantity: Order quantity
            price: Order price (required for LIMIT and STOP_LIMIT orders)
            stop_price: Stop price (required for STOP_LIMIT orders)
            
        Returns:
            Order response
            
        Raises:
            APIError: If API call fails
            NetworkError: If network error occurs
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity)
        }
        
        api_order_type = order_type

        # Add price for limit and stop-limit orders
        if order_type == "LIMIT":
            if price is None:
                raise APIError("Price is required for LIMIT orders")
            params["price"] = str(price)
            params["timeInForce"] = "GTC"  # Good Till Cancel
        elif order_type == "STOP_LIMIT":
            if price is None:
                raise APIError("Price is required for STOP_LIMIT orders")
            if stop_price is None:
                raise APIError("Stop price is required for STOP_LIMIT orders")
            params["price"] = str(price)
            params["stopPrice"] = str(stop_price)
            params["timeInForce"] = "GTC"
            api_order_type = "STOP"

        params["type"] = api_order_type
        
        try:
            logger.info(f"Placing {side} {order_type} order: {symbol} x {quantity}")
            
            response = self._make_request(
                method="POST",
                endpoint=self.ORDER_ENDPOINT,
                params=params,
                signed=True
            )
            
            logger.info(f"Order placed successfully: {response.get('orderId')}")
            return response
            
        except (APIError, NetworkError) as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def get_order(
        self,
        symbol: str,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Get order details from Binance.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID
            
        Returns:
            Order details
            
        Raises:
            APIError: If API call fails
        """
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        
        try:
            logger.debug(f"Fetching order {order_id} for {symbol}")
            
            response = self._make_request(
                method="GET",
                endpoint=self.ORDER_ENDPOINT,
                params=params,
                signed=True
            )
            
            return response
            
        except (APIError, NetworkError) as e:
            logger.error(f"Failed to get order: {e}")
            raise
    
    def cancel_order(
        self,
        symbol: str,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Cancel an order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID to cancel
            
        Returns:
            Cancelled order details
            
        Raises:
            APIError: If API call fails
        """
        params = {
            "symbol": symbol,
            "orderId": order_id
        }
        
        try:
            logger.info(f"Cancelling order {order_id} for {symbol}")
            
            response = self._make_request(
                method="DELETE",
                endpoint=self.ORDER_ENDPOINT,
                params=params,
                signed=True
            )
            
            logger.info(f"Order cancelled: {order_id}")
            return response
            
        except (APIError, NetworkError) as e:
            logger.error(f"Failed to cancel order: {e}")
            raise
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information.
        
        Returns:
            Account details
            
        Raises:
            APIError: If API call fails
        """
        try:
            response = self._make_request(
                method="GET",
                endpoint="/fapi/v2/account",
                signed=True
            )
            return response
        except (APIError, NetworkError) as e:
            logger.error(f"Failed to get account info: {e}")
            raise
