from __future__ import annotations
from bot.client import BinanceClient
from bot.logging_config import setup_logger

logger = setup_logger("trading_bot.orders")


def build_order_params(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None
) -> dict:
    params = {
        "symbol": symbol,
        "side": side,
        "type": order_type,
        "quantity": quantity,
    }
    if order_type == "LIMIT":
        params["price"] = price
        params["timeInForce"] = "GTC"  # Good Till Cancelled
    return params


def place_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None
) -> dict:
    params = build_order_params(symbol, side, order_type, quantity, price)

    logger.info(
        "Placing %s %s order | symbol=%s qty=%s price=%s",
        side, order_type, symbol, quantity, price or "MARKET"
    )

    response = client.place_order(params)

    logger.info(
        "Order placed | orderId=%s status=%s executedQty=%s avgPrice=%s",
        response.get("orderId"),
        response.get("status"),
        response.get("executedQty"),
        response.get("avgPrice"),
    )

    return response