from typing import Any, Optional

import pandas as pd
from binance.error import ClientError
from binance.spot import Spot

from src.crypto_market_fetcher import CoinGeckoMarketData
from src.helpers import configure_logger


class BinanceManager:

    MIN_TRADE_AMOUNT = 15.0  # Fixed minimum trade amount in USDT

    def __init__(self, api_key: str, api_secret: str):
        self.client = Spot(api_key=api_key, api_secret=api_secret)
        self.logger = configure_logger(__name__)

    @property
    def wallet(self) -> dict:
        """Fetches fresh wallet info from Binance API."""
        try:
            return self.client.account()
        except Exception as e:
            self.logger.error("Failed to fetch wallet info")
            raise RuntimeError() from e

    @property
    def exchange_info(self) -> dict:
        """Fetches fresh exchange info from Binance API."""
        try:
            return self.client.exchange_info()
        except Exception as e:
            self.logger.error("Failed to fetch exchange info")
            raise RuntimeError(f"Binance API error: {e}") from e

    def get_account_type(self) -> str:
        """Returns the account type from Binance wallet info."""
        return self.wallet.get("accountType", "Unknown")

    def get_wallet_balances(self) -> pd.DataFrame:
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
        ].map(lambda x: f"{x:.8f}")

        return filtered_balances

    def fetch_biggest_crypto_data(self) -> list[dict[str, Any]]:
        coin_gecko = CoinGeckoMarketData()
        data_top_coins = coin_gecko.get_top_cryptocurrencies()

        binance_symbols = self._get_binance_coin_symbols()

        for coin in data_top_coins:
            coin["is_available_on_binance"] = coin["symbol"].lower() in binance_symbols

        return data_top_coins

    def _get_binance_coin_symbols(self) -> set[str]:
        data_exchange = self.exchange_info
        if "symbols" not in data_exchange:
            raise ValueError("Unexpected Binance API response: Missing 'symbols'.")

        symbols = {
            symbol["baseAsset"].lower()
            for symbol in data_exchange["symbols"]
            if self._is_usdt_spot_trading_allowed(symbol)
        }

        self.logger.info("Successfully fetched exchange symbols from Binance API.")
        return symbols

    def _is_usdt_spot_trading_allowed(self, symbol_data: dict) -> bool:
        """Checks if a given symbol supports USDT spot trading."""
        return (
            symbol_data["quoteAsset"] == "USDT" and symbol_data["isSpotTradingAllowed"]
        )

    def _check_market_status(self, symbol_name: str) -> bool:
        """Checks if a specific symbol supports USDT spot trading."""
        for symbol in self.exchange_info.get("symbols", []):
            if symbol["baseAsset"].lower() == symbol_name.lower():
                return self._is_usdt_spot_trading_allowed(symbol)
        return False

    def _validate_trade_limits(self, usdt_amount: float) -> bool:
        """Ensure the USDT amount meets Binance's minimum trade requirement."""
        if usdt_amount < self.MIN_TRADE_AMOUNT:
            self.logger.warning(
                "Order amount %.2f USDT is below minimum required: %.2f USDT",
                usdt_amount,
                self.MIN_TRADE_AMOUNT,
            )
            return False

        self.logger.info(
            "Order amount %.2f USDT meets the minimum required: %.2f USDT",
            usdt_amount,
            self.MIN_TRADE_AMOUNT,
        )
        return True

    def _has_sufficient_funds(self, amount: float, asset: str = "USDT") -> bool:
        """Check if there is enough free balance for the trade.

        Args:
            amount (float): The required amount for the trade.
            asset (str): The asset to check balance for (e.g., 'USDT' for buying, 'BTC' for selling).

        Returns:
            bool: True if sufficient funds are available, False otherwise.
        """
        balances = self.get_wallet_balances()
        asset_balance = balances.loc[balances["asset"] == asset, "free"]

        if asset_balance.empty:
            self.logger.warning("No %s balance found in wallet.", asset)
            return False

        free_balance = float(asset_balance.iloc[0])

        if free_balance < amount:
            self.logger.warning(
                "Insufficient funds: Available %.6f %s, required %.6f %s",
                free_balance,
                asset,
                amount,
                asset,
            )
            return False

        self.logger.info("Sufficient funds: %.6f %s available", free_balance, asset)
        return True

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
            dict: Order response.
        """

        # Validate side parameter
        if side not in {"BUY", "SELL"}:
            self.logger.error("Invalid order side: %s", side)
            raise ValueError("Side must be 'BUY' or 'SELL'.")

        # Estimate required funds
        usdt_amount = quantity * (price if price else 1)  # Estimated cost
        # Check available balance depending on order side
        if side == "BUY":
            asset = "USDT"
            required_funds = usdt_amount
        else:  # side == "SELL"
            asset = symbol.replace(
                "USDT", ""
            )  # Extract base asset (e.g., BTC from BTCUSDT)
            required_funds = quantity  # Need enough BTC to sell

        if not self._has_sufficient_funds(required_funds, asset):
            return {"status": "failed", "reason": "insufficient funds", "asset": asset}

        if not self._validate_trade_limits(usdt_amount):
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
                raise ValueError("Price is required for LIMIT orders.")
            order_params["price"] = price
            order_params["timeInForce"] = "GTC"  # Good-Til-Canceled

        # Place the order
        try:
            response = self.client.new_order(**order_params)
            self.logger.info("Order placed successfully:\n%s", response)
            return response
        except ClientError as e:
            self.logger.error("Failed to place order: %s", e.error_message)
            raise RuntimeError(f"Binance API error: {e.error_message}") from e

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        """
        Cancels an existing order on Binance.

        Args:
            symbol (str): Trading pair (e.g., "BTCUSDT").
            order_id (int): ID of the order to cancel.

        Returns:
            dict: API response.
        """
        try:
            response = self.client.cancel_order(symbol=symbol, orderId=order_id)
            self.logger.info("Order %s canceled:\n%s", order_id, response)
            return response
        except ClientError as e:
            self.logger.error(
                "Failed to cancel order %s: %s", order_id, e.error_message
            )
            raise RuntimeError(f"Binance API error: {e.error_message}") from e

    def get_open_orders(self, symbol: Optional[str] = None) -> pd.DataFrame:
        """
        Fetch all open orders from Binance and return them as a DataFrame.

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
        """
        try:
            open_orders = self.client.get_open_orders(symbol=symbol)

            if not open_orders:
                self.logger.info("No open orders found.")
                return pd.DataFrame()  # Return an empty DataFrame if no orders exist

            orders_df = pd.DataFrame(open_orders)

            columns_needed = [
                "symbol",
                "orderId",
                "clientOrderId",
                "price",
                "origQty",
                "executedQty",
                "cummulativeQuoteQty",
                "status",
                "type",
                "side",
                "stopPrice",
                "time",
                "workingTime",
            ]

            for col in columns_needed:
                if col not in orders_df:
                    orders_df[col] = None
                    self.logger.warning("Column '%s' not found in open orders.", col)

            orders_df = orders_df[columns_needed]

            float_columns = ["price", "origQty", "executedQty", "cummulativeQuoteQty"]
            for col in float_columns:
                if col in orders_df:
                    orders_df[col] = orders_df[col].astype(float)

            orders_df["time"] = pd.to_datetime(orders_df["time"], unit="ms", utc=True)
            orders_df["workingTime"] = pd.to_datetime(
                orders_df["workingTime"], unit="ms", utc=True
            )

            orders_df["time"] = orders_df["time"].dt.tz_convert("Europe/Berlin")
            orders_df["workingTime"] = orders_df["workingTime"].dt.tz_convert(
                "Europe/Berlin"
            )

            return orders_df

        except ClientError as e:
            self.logger.error("Failed to fetch open orders:")
            raise RuntimeError(f"Binance API error: {e.error_message}") from e

        except Exception as e:
            self.logger.error("Failed to fetch open orders: %s", str(e))
            raise Exception(e) from e
