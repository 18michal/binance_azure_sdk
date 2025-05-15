""" BinanceManager class for interacting with the Binance Spot API. """

from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Optional

import pandas as pd
from binance.error import ClientError
from binance.spot import Spot

from services.crypto_market_fetcher import CoinGeckoMarketData
from services.src.helpers import configure_logger, load_config
from services.src.market_manager_helper import BinanceManagerHelper


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
        min_trade_amount (float): Minimum trade amount in USDC.
        client (Spot): Binance API client.
        logger (Logger): Logger for logging Binance API interactions.
        manager_helper (BinanceManagerHelper): Helper class for Binance operations.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initializes the BinanceManager.

        Args:
            api_key (str): Binance API key.
            api_secret (str): Binance API secret.
        """
        config = load_config().get("binance", {})
        self.min_trade_amount = config.get("min_trade_amount")

        if self.min_trade_amount is None:
            raise ValueError(
                "Configuration error: 'min_trade_amount' is missing in config.yaml"
            )

        self.client = Spot(api_key=api_key, api_secret=api_secret)
        self.logger = configure_logger(__name__)

        self.manager_helper = BinanceManagerHelper(
            exchange_info=self.exchange_info,
            logger=self.logger,
            min_trade_amount=self.min_trade_amount,
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

    @handle_binance_manager_errors
    def get_current_symbol_price(self, symbol: str) -> float:
        """
        Fetch the current price of the symbol from Binance API.

        Args:
            symbol (str): Trading pair (e.g., BTCUSDC).

        Returns:
            float: The current price of the asset.
        """
        return float(self.client.ticker_price(symbol=symbol)["price"])

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
        Checks if a cryptocurrency supports USDC spot trading.

        Args:
            symbol_name (str): The base asset symbol (e.g., "BTC").

        Returns:
            bool: True if trading is allowed, False otherwise.
        """
        for symbol in self.exchange_info.get("symbols", []):
            if symbol["baseAsset"].lower() == symbol_name.lower():
                return self.manager_helper.is_usdc_spot_trading_allowed(
                    symbol_data=symbol
                )
        return False

    @handle_binance_manager_errors
    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """
        Cancels an existing order on Binance.

        Args:
            symbol (str): Trading pair (e.g., "BTCUSDC").
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
        - symbol: Trading pair (e.g., BTCUSDC)
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
            symbol (str): Trading pair (e.g., BTCUSDC).
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

        usdc_amount = quantity * (
            price if price else self.get_current_symbol_price(symbol=symbol)
        )  # Estimated cost

        asset, required_funds = (
            ("USDC", usdc_amount)
            if side == "BUY"
            else (
                symbol.replace(
                    "USDC", ""
                ),  # Extract base asset (e.g., BTC from BTCUSDC)
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

        if not self.manager_helper.validate_trade_limits(usdc_amount=usdc_amount):
            return {
                "status": "failed",
                "reason": "trade amount too low",
                "amount": usdc_amount,
            }

        # Construct order parameters
        order_params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": ("%.4f" % quantity),  # pylint: disable=C0209
        }

        if order_type == "LIMIT":

            if price is None:
                self.logger.error("Price must be specified for LIMIT orders.")
                raise ValueError()

            order_params["price"] = f"{price:f}"
            order_params["timeInForce"] = "GTC"  # Good-Til-Canceled

        # Place the order
        response = self.client.new_order(**order_params)
        self.logger.info("Order placed successfully:\n%s", response)
        return response

    @handle_binance_manager_errors
    def fetch_symbol_trade_history(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> pd.DataFrame | None:
        """
        Fetches trade history for a given symbol within a specified time range.
        If no time range is provided, it fetches trades without any time constraints.

        Args:
            symbol (str): The trading pair symbol (e.g., "BTCUSDC").
            start_time (Optional[int]): The start time in milliseconds if provided.
            end_time (Optional[int]): The end time in milliseconds if provided.

        Returns:
            pd.DataFrame: A DataFrame containing trade history details with the following columns:
                - symbol (str): The trading pair.
                - orderId (int): The order ID associated with the trade.
                - price (float): The executed price of the trade.
                - qty (float): The traded quantity.
                - quoteQty (float): The traded quote quantity.
                - commission (float): The commission paid for the trade.
                - commissionAsset (str): The asset in which the commission was paid.
                - time (datetime): The timestamp of the trade (UTC).
                - isBuyer (bool): Whether the trade was a buy order (True) or sell order (False).
        """
        trades_list = []

        if start_time is None and end_time is None:
            trades = self.client.my_trades(symbol=symbol)
        else:
            trades = self.client.my_trades(
                symbol=symbol, startTime=start_time, endTime=end_time
            )

        if trades:
            for trade in trades:
                trades_list.append(
                    {
                        "symbol": trade["symbol"],
                        "orderId": trade["orderId"],
                        "price": float(trade["price"]),
                        "qty": float(trade["qty"]),
                        "quoteQty": float(trade["quoteQty"]),
                        "commission": float(trade["commission"]),
                        "commissionAsset": trade["commissionAsset"],
                        "time": datetime.fromtimestamp(
                            int(trade["time"]) / 1000, tz=timezone.utc
                        ),
                        "isBuyer": trade["isBuyer"],
                    }
                )
        else:
            return None

        return pd.DataFrame(trades_list)

    @handle_binance_manager_errors
    def get_trade_history_last_24h(self) -> pd.DataFrame:
        """
        Fetches trade history for all symbols in the last 24 hours.

        Returns:
            pd.DataFrame: A DataFrame containing trade history details.
        """
        now = datetime.now(timezone.utc)
        start_time = int((now - timedelta(days=1)).timestamp() * 1000)
        end_time = int(now.timestamp() * 1000)

        balances = self.get_wallet_balances()
        symbols = [
            f"{row.asset}USDC" for _, row in balances.iterrows() if row.asset != "USDC"
        ]

        trade_list = [
            self.fetch_symbol_trade_history(
                symbol=symbol, start_time=start_time, end_time=end_time
            )
            for symbol in symbols
        ]

        if not trade_list[0]:
            self.logger.info("No trades within 24 hours found.")
            return pd.DataFrame()

        return pd.concat(trade_list, ignore_index=True)

    def get_symbol_info(self, symbol: str):
        """Fetch symbol trading rules from Binance."""
        exchange_info = self.client.exchange_info()
        for s in exchange_info["symbols"]:
            if s["symbol"] == symbol:
                return s
        return None

    @handle_binance_manager_errors
    def was_asset_bought_this_month(self, symbol: str) -> bool:
        """
        Check if the asset was bought during the current month.

        Args:
            symbol (str): The trading pair symbol (e.g., 'BTCUSDC').

        Returns:
            bool: True if a BUY trade occurred this month, False otherwise.
        """
        now = datetime.now(timezone.utc)
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        start_time_ms = int(start_of_month.timestamp() * 1000)

        trades = self.fetch_symbol_trade_history(
            symbol=symbol, start_time=start_time_ms
        )

        if trades is None:
            return False

        for _, trade in trades.iterrows():
            if trade["isBuyer"]:  # True indicates it's a BUY trade
                return True

        return False

    @handle_binance_manager_errors
    def get_yesterdays_high_price(self, symbol: str) -> float:
        """
        Fetches the high price of the previous day for a given symbol from the Binance API.

        Args:
            symbol (str): The trading pair symbol (e.g., "BTCUSDC") to retrieve the high price for.

        Returns:
            float: The high price of the previous day for the specified trading pair.
        """
        now = datetime.now(timezone.utc)
        yesterday = now - timedelta(days=1)

        start_time = datetime(
            yesterday.year, yesterday.month, yesterday.day, tzinfo=timezone.utc
        )
        end_time = start_time + timedelta(days=1)

        klines = self._get_yesterdays_price(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time,
        )

        return float(klines[1])

    @handle_binance_manager_errors
    def _get_yesterdays_price(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> list:
        """
        Fetches the historical price data for a given symbol from the Binance API
        for a specific date range, returning the Open, High, Low, and Close (OHLC)
        prices for that day.

        Args:
            symbol (str): The trading pair symbol (e.g., "BTCUSDC") to retrieve data for.
            start_time (datetime): The starting datetime object for the time period.
            end_time (datetime): The ending datetime object for the time period.

        Returns:
            list: A list containing the OHLC prices for the specified date.
                    The list order is [Open, High, Low, Close].
        """
        klines = self.client.klines(
            symbol=symbol,
            interval="1d",
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000),
            limit=1,
        )

        return klines[0][1:5]  # Open, High, Low, Close prices
