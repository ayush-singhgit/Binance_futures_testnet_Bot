from __future__ import annotations
VALID_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]
VALID_SIDES = ["BUY", "SELL"]
VALID_ORDER_TYPES = ["MARKET", "LIMIT"]

def validate_symbol(symbol: str) -> str:
    s = symbol.strip().upper()
    if s not in VALID_SYMBOLS:
        raise ValueError(
            f"Invalid symbol '{s}'. Valid options: {', '.join(VALID_SYMBOLS)}"
        )
    return s

def validate_side(side: str) -> str:
    s = side.strip().upper()
    if s not in VALID_SIDES:
        raise ValueError(f"Side must be BUY or SELL, got '{side}'")
    return s

def validate_order_type(order_type: str) -> str:
    t = order_type.strip().upper()
    if t not in VALID_ORDER_TYPES:
        raise ValueError(f"Order type must be MARKET or LIMIT, got '{order_type}'")
    return t

def validate_quantity(quantity: str) -> float:
    try:
        q = float(quantity)
    except (ValueError, TypeError):
        raise ValueError(f"Quantity must be a number, got '{quantity}'")
    if q <= 0:
        raise ValueError("Quantity must be greater than 0")
    return round(q, 3)

def validate_price(price: str) -> float:
    try:
        p = float(price)
    except (ValueError, TypeError):
        raise ValueError(f"Price must be a number, got '{price}'")
    if p <= 0:
        raise ValueError("Price must be greater than 0")
    return round(p, 2)

def validate_order_inputs(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None
) -> dict:
    """Validate all inputs and return a clean dict. Raises ValueError on any problem."""
    validated = {
        "symbol": validate_symbol(symbol),
        "side": validate_side(side),
        "order_type": validate_order_type(order_type),
        "quantity": validate_quantity(quantity),
    }
    if validated["order_type"] == "LIMIT":
        if not price:
            raise ValueError("Price is required for LIMIT orders")
        validated["price"] = validate_price(price)
    elif price:
        raise ValueError("Price should not be provided for MARKET orders")
    return validated