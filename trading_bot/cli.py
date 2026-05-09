"""
CLI entry point for trading bot.
Provides command-line interface for placing orders on Binance Futures Testnet.
"""

import argparse
import os
import sys
from typing import Any, Callable, List, Optional, Tuple
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

import colorama
from colorama import Fore, Style

from bot.client import BinanceClient, APIError, AuthenticationError, NetworkError
from bot.orders import OrderManager
from bot.validators import ValidationError, OrderValidator
from bot.logging_config import setup_logging, get_logger

colorama.init(autoreset=True)
logger = get_logger("trading_bot")


def get_credentials() -> Tuple[str, str]:
    """
    Get API credentials from environment or user input.
    
    Returns:
        Tuple of (api_key, api_secret)
    """
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    
    if not api_key:
        print(f"{Fore.YELLOW}API Key not found in environment (BINANCE_API_KEY){Style.RESET_ALL}")
        api_key = input("Enter your Binance API Key: ").strip()
        if not api_key:
            print(f"{Fore.RED}Error: API Key is required{Style.RESET_ALL}")
            sys.exit(1)
    else:
        api_key = api_key.strip()
    
    if not api_secret:
        print(f"{Fore.YELLOW}API Secret not found in environment (BINANCE_API_SECRET){Style.RESET_ALL}")
        api_secret = input("Enter your Binance API Secret: ").strip()
        if not api_secret:
            print(f"{Fore.RED}Error: API Secret is required{Style.RESET_ALL}")
            sys.exit(1)
    else:
        api_secret = api_secret.strip()
    
    return api_key, api_secret


def prompt_choice(prompt_text: str, choices: List[str], default: Optional[str] = None) -> str:
    """Prompt the user to choose from a fixed list of options."""
    options_text = "/".join(choices)
    default_text = f" [{default}]" if default else ""

    while True:
        response = input(f"{prompt_text} ({options_text}){default_text}: ").strip().upper()
        if not response and default:
            response = default
        if response in choices:
            return response
        print(f"{Fore.RED}Please choose one of: {', '.join(choices)}{Style.RESET_ALL}")


def prompt_menu(prompt_text: str, options: List[str], default_index: int = 1) -> str:
    """Prompt the user to select from a numbered menu."""
    if default_index < 1 or default_index > len(options):
        default_index = 1

    while True:
        response = input(f"{prompt_text} [1-{len(options)}] (default {default_index}): ").strip()
        if not response:
            return options[default_index - 1]
        if response.isdigit():
            selected = int(response)
            if 1 <= selected <= len(options):
                return options[selected - 1]
        print(f"{Fore.RED}Please choose a number between 1 and {len(options)}.{Style.RESET_ALL}")


def prompt_value(prompt_text: str, validator: Callable[[str], Any], required_message: str) -> str:
    """Prompt until a validator accepts the provided value."""
    while True:
        value = input(f"{prompt_text}: ").strip()
        try:
            validated = validator(value)
            return str(validated) if hasattr(validated, "normalize") else validated
        except ValidationError as e:
            print(f"{Fore.RED}{e}{Style.RESET_ALL}")
            if required_message:
                print(f"{Fore.YELLOW}{required_message}{Style.RESET_ALL}")


def prompt_credentials_if_needed(parsed_args) -> Tuple[str, str]:
    """Return CLI or environment credentials, prompting only when needed."""
    if parsed_args.api_key and parsed_args.api_secret:
        print(f"{Fore.GREEN}✓ Using provided credentials{Style.RESET_ALL}")
        return parsed_args.api_key.strip(), parsed_args.api_secret.strip()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if api_key and api_secret:
        api_key = api_key.strip()
        api_secret = api_secret.strip()
        print(f"{Fore.GREEN}✓ Using environment credentials{Style.RESET_ALL}")
        return api_key, api_secret

    print(f"{Fore.YELLOW}Credentials not found in environment. Please enter them now.{Style.RESET_ALL}")
    api_key, api_secret = get_credentials()
    print(f"{Fore.GREEN}✓ Credentials obtained{Style.RESET_ALL}")
    return api_key, api_secret


def collect_order_inputs(parsed_args) -> dict:
    """Collect order inputs from args or interactive prompts."""
    interactive_mode = parsed_args.interactive or not all(
        [parsed_args.symbol, parsed_args.side, parsed_args.order_type, parsed_args.quantity]
    )

    print(f"{Fore.BLUE}Interactive mode: {'enabled' if interactive_mode else 'disabled'}{Style.RESET_ALL}")

    if not interactive_mode and parsed_args.symbol:
        symbol = parsed_args.symbol.strip().upper()
    else:
        symbol = prompt_value(
            "Enter symbol (e.g., BTCUSDT)",
            OrderValidator.validate_symbol,
            "Symbol must be a USDT pair like BTCUSDT.",
        )

    if not interactive_mode and parsed_args.side:
        side = parsed_args.side.strip().upper()
    else:
        print("\nChoose side:")
        print("  1) BUY")
        print("  2) SELL")
        side = prompt_menu("Select an option", ["BUY", "SELL"], default_index=1)

    if not interactive_mode and parsed_args.order_type:
        order_type = parsed_args.order_type.strip().upper()
    else:
        print("\nChoose order type:")
        print("  1) MARKET")
        print("  2) LIMIT")
        print("  3) STOP_LIMIT")
        order_type = prompt_menu("Select an option", ["MARKET", "LIMIT", "STOP_LIMIT"], default_index=1)

    if not interactive_mode and parsed_args.quantity:
        quantity = parsed_args.quantity.strip()
    else:
        quantity = prompt_value(
            "Enter quantity",
            OrderValidator.validate_quantity,
            "Quantity must be a valid positive number.",
        )

    price = parsed_args.price
    stop_price = parsed_args.stop_price

    if (interactive_mode or not price) and order_type in {"LIMIT", "STOP_LIMIT"}:
        price = prompt_value(
            "Enter limit price",
            OrderValidator.validate_price,
            "Price must be a valid positive number.",
        )

    if (interactive_mode or not stop_price) and order_type == "STOP_LIMIT":
        stop_price = prompt_value(
            "Enter stop price",
            OrderValidator.validate_price,
            "Stop price must be a valid positive number.",
        )

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
        "interactive_mode": interactive_mode,
    }


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Simplified Trading Bot - Place orders on Binance Futures Testnet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Place a market BUY order:
    python trading_bot/cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  
  Place a limit SELL order:
    python trading_bot/cli.py --symbol ETHUSDT --side SELL --type LIMIT --quantity 1 --price 2500

    Place a stop-limit SELL order:
        python trading_bot/cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 47000 --stop-price 46500

    Use interactive mode:
        python trading_bot/cli.py --interactive
        """
    )
    
    parser.add_argument(
        "--symbol",
        help="Trading pair (e.g., BTCUSDT, ETHUSDT)"
    )
    
    parser.add_argument(
        "--side",
        choices=["BUY", "SELL"],
        help="Order side"
    )
    
    parser.add_argument(
        "--type",
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP_LIMIT"],
        help="Order type"
    )
    
    parser.add_argument(
        "--quantity",
        help="Order quantity"
    )
    
    parser.add_argument(
        "--price",
        help="Order price (required for LIMIT and STOP_LIMIT orders)"
    )

    parser.add_argument(
        "--stop-price",
        dest="stop_price",
        help="Stop price required for STOP_LIMIT orders"
    )

    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive prompts to build the order"
    )
    
    parser.add_argument(
        "--api-key",
        help="Binance API key (or set BINANCE_API_KEY env var)"
    )
    
    parser.add_argument(
        "--api-secret",
        help="Binance API secret (or set BINANCE_API_SECRET env var)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Log file directory (default: logs)"
    )
    
    return parser


def display_header() -> None:
    """Display application header."""
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"SIMPLIFIED TRADING BOT - Binance Futures Testnet")
    print(f"{'='*70}{Style.RESET_ALL}\n")


def display_section(title: str) -> None:
    """Display a section header."""
    print(f"\n{Fore.BLUE}{title}{Style.RESET_ALL}")
    print("-" * len(title))


def main(args: Optional[list] = None) -> int:
    """
    Main CLI entry point.
    
    Args:
        args: Command-line arguments (for testing)
        
    Returns:
        Exit code
    """
    # Parse arguments
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Setup logging
    setup_logging(log_dir=parsed_args.log_dir, log_level=parsed_args.log_level)
    
    display_header()
    display_section("CONFIGURATION")

    # Collect and validate order parameters before any client setup or credential prompts.
    display_section("ORDER REQUEST SUMMARY")
    order_inputs = collect_order_inputs(parsed_args)

    try:
        symbol = order_inputs["symbol"]
        side = order_inputs["side"]
        order_type = order_inputs["order_type"]
        symbol, side, order_type, quantity_value, price_value, stop_price_value = OrderValidator.validate_order_params(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=order_inputs["quantity"],
            price=order_inputs["price"],
            stop_price=order_inputs["stop_price"],
        )
    except ValidationError as e:
        print(f"\n✗ Order placement failed: {e}\n")
        print(f"{Fore.RED}Validation Error: {e}{Style.RESET_ALL}")
        logger.error(f"Validation error: {e}")
        return 1

    print("\n" + "=" * 70)
    print("ORDER REQUEST SUMMARY")
    print("=" * 70)
    print(f"{'Symbol':<20}: {symbol}")
    print(f"{'Side':<20}: {side}")
    print(f"{'Type':<20}: {order_type}")
    print(f"{'Quantity':<20}: {quantity_value}")
    if price_value is not None:
        print(f"{'Price':<20}: {price_value}")
        print(f"{'Notional Value':<20}: {quantity_value * price_value} USDT")
    if stop_price_value is not None:
        print(f"{'Stop Price':<20}: {stop_price_value}")
    print("=" * 70)

    # Get credentials only after the request has been validated.
    api_key, api_secret = prompt_credentials_if_needed(parsed_args)

    try:
        # Initialize client
        display_section("INITIALIZING CLIENT")
        client = BinanceClient(api_key=api_key, api_secret=api_secret)
        print(f"{Fore.GREEN}✓ Connected to Binance Futures Testnet{Style.RESET_ALL}")
        logger.info(f"Connected to Binance Futures Testnet")

        # Create order manager
        order_manager = OrderManager(client)
        
        # Ask for confirmation
        display_section("CONFIRMATION")
        confirm = input("Proceed with placing order? (yes/no): ").strip().lower()
        if confirm not in ["yes", "y"]:
            print(f"{Fore.YELLOW}Order cancelled by user{Style.RESET_ALL}")
            logger.info("Order cancelled by user")
            return 0
        
        # Place order
        display_section("PLACING ORDER")
        
        try:
            if order_type == "MARKET":
                response = order_manager.place_market_order(
                    symbol=symbol,
                    side=side,
                    quantity=order_inputs["quantity"]
                )
            elif order_type == "LIMIT":
                response = order_manager.place_limit_order(
                    symbol=symbol,
                    side=side,
                    quantity=order_inputs["quantity"],
                    price=order_inputs["price"]
                )
            else:
                response = order_manager.place_stop_limit_order(
                    symbol=symbol,
                    side=side,
                    quantity=order_inputs["quantity"],
                    price=order_inputs["price"],
                    stop_price=order_inputs["stop_price"]
                )
            
            # Display response
            print(order_manager.format_order_response(response))
            order_id = response.get("orderId")
            status = response.get("status")
            executed_qty = response.get("executedQty")
            avg_price = response.get("avgPrice")
            
            # Display success message
            print(order_manager.format_success_message(order_id, order_type, side))
            print(f"{Fore.GREEN}Status: {status} | Executed: {executed_qty} | Avg Price: {avg_price}{Style.RESET_ALL}")
            
            logger.info(
                f"Order placed successfully - ID: {order_id}, Status: {status}, "
                f"Executed: {executed_qty}, AvgPrice: {avg_price}"
            )
            
            return 0
            
        except ValidationError as e:
            print(order_manager.format_error_message(str(e)))
            print(f"{Fore.RED}Validation Error: {e}{Style.RESET_ALL}")
            logger.error(f"Validation error: {e}")
            return 1

        except AuthenticationError as e:
            print(order_manager.format_error_message(str(e)))
            print(f"{Fore.RED}Authentication Error: {e}{Style.RESET_ALL}")
            logger.error(f"Authentication error: {e}")
            return 1
            
        except APIError as e:
            print(order_manager.format_error_message(str(e)))
            print(f"{Fore.RED}API Error: {e}{Style.RESET_ALL}")
            logger.error(f"API error: {e}")
            return 1
            
        except NetworkError as e:
            print(order_manager.format_error_message(str(e)))
            print(f"{Fore.RED}Network Error: {e}{Style.RESET_ALL}")
            logger.error(f"Network error: {e}")
            return 1
    
    except Exception as e:
        print(f"\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
