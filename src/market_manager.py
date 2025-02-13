""" BinanceManager class for interacting with the Binance Spot API. """

from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from binance.error import ClientError
from binance.spot import Spot

from src.crypto_market_fetcher import CoinGeckoMarketData
from src.helpers import configure_logger
from src.market_manager_helper import BinanceManagerHelper


def handle_binance_manager_errors(func: Callable):
    """Decorator for handling Binance API errors and logging them."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        try:
            return func(*args, **kwargs)
        except ClientError as e:
            self.logger.error("Binance API error in %s.\n", func.__name__)
            raise RuntimeError(f"Binance API error: {e.error_message}") from e
        except Exception as e:
            self.logger.error("Unexpected error in %s.\n", func.__name__)
            raise RuntimeError(f"Unexpected error: {e}") from e

    return wrapper


class BinanceManager:
    """
    A manager class for interacting with the Binance Spot API.

    Attributes:
        MIN_TRADE_AMOUNT (float): Minimum trade amount in USDT.
        client (Spot): Binance API client.
        logger (Logger): Logger for logging Binance API interactions.
        manager_helper (BinanceManagerHelper): Helper class for Binance operations.
    """

    MIN_TRADE_AMOUNT = 15.0  # Fixed minimum trade amount in USDT

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the BinanceManager.

        Args:
            api_key (str): Binance API key.
            api_secret (str): Binance API secret.
        """
        self.client = Spot(api_key=api_key, api_secret=api_secret)
        self.logger = configure_logger(__name__)

        self.manager_helper = BinanceManagerHelper(
            exchange_info=self.exchange_info,
            logger=self.logger,
            min_trade_amount=self.MIN_TRADE_AMOUNT,
        )

    @property
    @handle_binance_manager_errors
    def wallet(self) -> dict:
        """Fetches fresh wallet info from Binance API."""
        return self.client.account()

    @property
    @handle_binance_manager_errors
    def exchange_info(self) -> dict:
        """Fetches fresh exchange info from Binance API."""
        return self.client.exchange_info()

    @handle_binance_manager_errors
    def get_account_type(self) -> str:
        """
        Fetches the account type from Binance wallet info.

        Returns:
            str: Account type (e.g., "SPOT", "MARGIN").
        """
        return self.wallet.get("accountType", "Unknown")

    def get_wallet_balances(self) -> pd.DataFrame:
        """
        Retrieves non-zero balances from the Binance wallet.

        Returns:
            pd.DataFrame: A DataFrame with 'asset', 'free', and 'locked' balances.
        """
        wallet_info = self.wallet

        if "balances" not in wallet_info:
            self.logger.error("No balances found in wallet info.")
            raise ValueError("Invalid wallet response")

        balances = pd.DataFrame(wallet_info["balances"])
        balances[["free", "locked"]] = balances[["free", "locked"]].astype(float)

        # Filter the DataFrame where 'free' is not 0 or 'locked' is not 0
        filtered_balances = balances.loc[
            (balances["free"] != 0) | (balances["locked"] != 0)
        ].copy()

        if filtered_balances.empty:
            self.logger.info("No non-zero balances found.")
            return filtered_balances

        filtered_balances[["free", "locked"]] = filtered_balances[
            ["free", "locked"]
        ].map(lambda x: round(x, 8))

        return filtered_balances

    @handle_binance_manager_errors
    def fetch_biggest_crypto_data(self) -> list[dict[str, Any]]:
        """
        Fetches the top cryptocurrencies from CoinGecko and checks their availability on Binance.

        Returns:
            list[dict[str, Any]]: List of top cryptocurrencies with availability on Binance.
        """
        coin_gecko = CoinGeckoMarketData()
        data_top_coins = coin_gecko.get_top_cryptocurrencies()

        binance_symbols = self.manager_helper.get_binance_coin_symbols()

        binance_symbols_set = set(binance_symbols)
        for coin in data_top_coins:
            coin["is_available_on_binance"] = (
                coin["symbol"].lower() in binance_symbols_set
            )

        return data_top_coins

    @handle_binance_manager_errors
    def check_market_status(self, symbol_name: str) -> bool:
        """
        Checks if a cryptocurrency supports USDT spot trading.

        Args:
            symbol_name (str): The base asset symbol (e.g., "BTC").

        Returns:
            bool: True if trading is allowed, False otherwise.
        """
        for symbol in self.exchange_info.get("symbols", []):
            if symbol["baseAsset"].lower() == symbol_name.lower():
                return self.manager_helper.is_usdt_spot_trading_allowed(
                    symbol_data=symbol
                )
        return False

    @handle_binance_manager_errors
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """
        Cancels an existing order on Binance.

        Args:
            symbol (str): Trading pair (e.g., "BTCUSDT").
            order_id (int): ID of the order to cancel.

        Returns:
            dict: API response.
        """
        response = self.client.cancel_order(symbol=symbol, orderId=order_id)
        self.logger.info("Order %s canceled:\n%s", order_id, response)
        return response

    @handle_binance_manager_errors
    def get_open_orders(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch all open orders from Binance.

        Columns:
        - symbol: Trading pair (e.g., BTCUSDT)
        - orderId: Unique order ID
        - clientOrderId: A field, which can be set by the user,
            in the JSON response for POST /api/v3/order to identify the newly placed order.
        - price: Order price
        - origQty: The original quantity that was sent during order placement.
        - executedQty: The field that shows how much of the quantity was filled in an order.
        - cummulativeQuoteQty: The accumulation of the price * qty for each fill of an order.
        - status: PENDING_NEW, PARTIALLY_FILLED, NEW, EXPIRED, EXPIRED_IN_MATCH, CANCELED, HALT,
            BREAK (represents the symbol is not available for trading, due to expected downtime.)
        - type: Order Type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, etc.
        - side: BUY or SELL
        - stopPrice: Trigger price (if applicable)
        - time: Time when trades/allocations were executed.
        - workingTime: When the order appeared on the book (type: UTCTIMESTAMP)

        More details: https://developers.binance.com/docs/binance-spot-api-docs/faqs#i

        Args:
            symbol (Optional[str]): Specific trading pair to filter orders.

        Returns:
            pd.DataFrame: DataFrame containing open order details.
        """
        open_orders = self.client.get_open_orders(symbol=symbol)

        if not open_orders:
            self.logger.info("No open orders found.")
            return pd.DataFrame()  # Return an empty DataFrame if no orders exist

        df_orders = pd.DataFrame(open_orders)

        self.manager_helper.open_orders_ensure_columns(df=df_orders)
        self.manager_helper.open_orders_convert_column_types(df=df_orders)

        return df_orders

    @handle_binance_manager_errors
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> dict:
        """
        Place an order on Binance.

        Args:
            symbol (str): Trading pair (e.g., BTCUSDT).
            side (str): Order direction ('BUY' or 'SELL').
            order_type (str): Type of order ('LIMIT', 'MARKET', 'STOP_LOSS_LIMIT', etc.).
            quantity (float): Amount of asset to buy/sell.
            price (Optional[float]): Price for limit orders.

        Returns:
            dict: API response with order details or failure reason.
        """

        if side not in {"BUY", "SELL"}:
            self.logger.error("Invalid order side: %s", side)
            raise ValueError("Side must be 'BUY' or 'SELL'.")

        usdt_amount = quantity * (price if price else 1)  # Estimated cost

        asset, required_funds = (
            ("USDT", usdt_amount)
            if side == "BUY"
            else (
                symbol.replace(
                    "USDT", ""
                ),  # Extract base asset (e.g., BTC from BTCUSDT)
                quantity,  # e.g. Need enough BTC to sell
            )
        )

        if not self.manager_helper.has_sufficient_funds(
            amount=required_funds, balances=self.get_wallet_balances(), asset=asset
        ):
            return {
                "status": "failed",
                "reason": "insufficient funds",
                "asset": asset,
            }

        if not self.manager_helper.validate_trade_limits(usdt_amount=usdt_amount):
            return {
                "status": "failed",
                "reason": "trade amount too low",
                "amount": usdt_amount,
            }

        # Construct order parameters
        order_params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if order_type == "LIMIT":

            if price is None:
                self.logger.error("Price must be specified for LIMIT orders.")
                raise ValueError()

            order_params["price"] = price
            order_params["timeInForce"] = "GTC"  # Good-Til-Canceled

        # Place the order
        response = self.client.new_order_test(**order_params)
        self.logger.info("Order placed successfully:\n%s", response)
        return response
