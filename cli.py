#!/usr/bin/env python3
"""Trading bot CLI — places Market and Limit orders on Binance Futures Testnet."""
from __future__ import annotations
import argparse
import os
import sys

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

from bot import BinanceClient, place_order, validate_order_inputs
from bot.logging_config import setup_logger

load_dotenv()
logger = setup_logger("trading_bot.cli")


def print_separator():
    print("─" * 52)


def print_order_summary(params: dict):
    print_separator()
    print("  ORDER SUMMARY")
    print_separator()
    print(f"  Symbol     : {params['symbol']}")
    print(f"  Side       : {params['side']}")
    print(f"  Type       : {params['order_type']}")
    print(f"  Quantity   : {params['quantity']}")
    if "price" in params:
        print(f"  Price      : {params['price']}")
    print_separator()


def print_order_response(response: dict):
    print("  ORDER RESPONSE")
    print_separator()
    print(f"  Order ID   : {response.get('orderId', 'N/A')}")
    print(f"  Status     : {response.get('status', 'N/A')}")
    print(f"  Exec. Qty  : {response.get('executedQty', '0')}")
    avg = response.get("avgPrice") or response.get("price", "N/A")
    print(f"  Avg Price  : {avg}")
    print(f"  Symbol     : {response.get('symbol', 'N/A')}")
    print(f"  Client OID : {response.get('clientOrderId', 'N/A')}")
    print_separator()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --quantity 0.01
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --quantity 0.1 --price 3000
        """
    )
    parser.add_argument("--symbol",   required=True, help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",     required=True, help="BUY or SELL")
    parser.add_argument("--type",     required=True, dest="order_type", help="MARKET or LIMIT")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price",    required=False, default=None, help="Limit price (LIMIT orders only)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    # --- Validate inputs ---
    try:
        validated = validate_order_inputs(
            symbol=args.symbol,
            side=args.side,
            order_type=args.order_type,
            quantity=args.quantity,
            price=args.price,
        )
    except ValueError as e:
        logger.error("Validation failed: %s", e)
        print(f"\n  ✗ Validation error: {e}\n")
        sys.exit(1)

    print_order_summary(validated)

    # --- Load credentials ---
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        logger.error("Missing API credentials in environment")
        print("  ✗ Error: BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env\n")
        sys.exit(1)

    # --- Place order ---
    client = BinanceClient(api_key, api_secret)

    try:
        response = place_order(
            client=client,
            symbol=validated["symbol"],
            side=validated["side"],
            order_type=validated["order_type"],
            quantity=validated["quantity"],
            price=validated.get("price"),
        )
        print_order_response(response)
        print("  ✓ Order placed successfully!\n")
        logger.info("CLI run complete — success")

    except (ConnectionError, TimeoutError) as e:
        logger.error("Network error: %s", e)
        print(f"\n  ✗ Network error: {e}\n")
        sys.exit(1)
    except RuntimeError as e:
        logger.error("Order failed: %s", e)
        print(f"\n  ✗ Order failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        print(f"\n  ✗ Unexpected error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()