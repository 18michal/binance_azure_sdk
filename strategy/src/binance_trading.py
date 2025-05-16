""" Binance integration module to simplify trading functions. """

from services.market_manager import BinanceManager
from services.src.helpers import configure_logger

logger = configure_logger(name="binance_trading")


def place_market_buy_order(
    binance_manager: BinanceManager, symbol: str, amount_usd: float
) -> dict:
    """
    Places a market buy order using USDC to buy a given asset.

    Args:
        binance_manager (BinanceManager): Instance of BinanceManager.
        symbol (str): Symbol of the asset to buy (e.g., "BTCUSDC").
        amount_usd (float): Amount in USDC to spend.

    Returns:
        dict: Result of the order attempt.
    """

    # Get current price of the asset
    current_price = binance_manager.get_current_symbol_price(symbol=symbol)

    quantity = round(amount_usd / current_price, 5)

    return binance_manager.create_order(
        symbol=symbol,
        side="BUY",
        order_type="MARKET",
        quantity=quantity,
    )


def place_limit_buy_order(
    binance_manager: BinanceManager, symbol: str, amount_usd: float, price: float
) -> dict:
    """
    Places a limit buy order using USDC to buy a given asset.

    Args:
        binance_manager (BinanceManager): Instance of BinanceManager.
        symbol (str): Symbol of the asset to buy (e.g., "BTCUSDC").
        amount_usd (float): Amount in USDC to spend.
        price (float): The price at which to buy the asset.

    Returns:
        dict: Result of the order attempt.
    """
    # Calculate quantity based on target price
    quantity = round(amount_usd / price, 5)

    return binance_manager.create_order(
        symbol=symbol, side="BUY", order_type="LIMIT", quantity=quantity, price=price
    )


def cancel_all_open_orders_for_asset(
    binance_manager: BinanceManager, symbol: str
) -> None:
    """
    Cancels all open orders for a given asset paired with USDC.

    Parameters:
    - symbol (str): The base asset symbol, e.g., "BTCUSDC" or "ETHUSDC".
    """
    open_orders = binance_manager.get_open_orders(symbol=symbol)

    if open_orders.empty:
        logger.info("No open orders found for %s.", symbol)
        return

    for _, order in open_orders.iterrows():
        order_id = order["orderId"]

        binance_manager.cancel_order(symbol=symbol, order_id=order_id)

    logger.info("Cancelled %d open orders for %s.", len(open_orders), symbol)
