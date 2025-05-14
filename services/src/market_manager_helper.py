""" Helper class for managing Binance exchange information and trading operations. """

from logging import Logger
from typing import Optional

import pandas as pd


class BinanceManagerHelper:
    """
    A helper class to manage Binance exchange information and trading operations.

    Attributes:
        exchange_info (dict): Exchange information obtained from the Binance API.
        logger (Logger): Logger instance for logging messages.
        min_trade_amount (float): Minimum trade amount (USDC) required for Binance trades.
    """

    def __init__(self, exchange_info: dict, logger: Logger, min_trade_amount: float):
        """
        Initializes the BinanceManagerHelper instance.

        Args:
            exchange_info (dict): Exchange information from the Binance API.
            logger (Logger): Logger instance for logging events.
            min_trade_amount (float): Minimum trade amount required for Binance trades.
        """
        self.exchange_info = exchange_info
        self.logger = logger
        self.min_trade_amount = min_trade_amount

    def get_binance_coin_symbols(self) -> set[str]:
        """
        Retrieves a set of all available Binance coin symbols that support USDC spot trading.

        Returns:
            set[str]: A set of coin symbols available for USDC spot trading.

        Raises:
            ValueError: If the 'symbols' key is missing in the exchange_info dictionary.
        """
        if "symbols" not in self.exchange_info:
            raise ValueError("Unexpected Binance API response: Missing 'symbols'.")

        symbols = {
            symbol["baseAsset"].lower()
            for symbol in self.exchange_info["symbols"]
            if self.is_usdc_spot_trading_allowed(symbol)
        }

        self.logger.info("Successfully fetched exchange symbols from Binance API.")
        return symbols

    def is_usdc_spot_trading_allowed(self, symbol_data: dict) -> bool:
        """
        Checks if a given trading pair supports USDC spot trading.

        Args:
            symbol_data (dict): A dictionary containing trading pair information.

        Returns:
            bool: True if the pair allows USDC spot trading, False otherwise.
        """
        return symbol_data.get("quoteAsset") == "USDC" and symbol_data.get(
            "isSpotTradingAllowed", False
        )

    def has_sufficient_funds(
        self, amount: float, balances: pd.DataFrame, asset: str = "USDC"
    ) -> bool:
        """
        Checks if there are enough free funds in the wallet to execute a trade.

        Args:
            amount (float): The required amount for the trade.
            balances (pd.DataFrame): DataFrame containing columns like 'asset' and 'free'.
            asset (str, optional): The asset symbol to check funds for. Defaults to "USDC".

        Returns:
            bool: True if sufficient funds are available, False otherwise.
        """
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

    def validate_trade_limits(self, usdc_amount: float) -> bool:
        """
        Validates whether a trade amount meets the Binance minimum trade requirement.

        Args:
            usdc_amount (float): The trade amount in USDC.

        Returns:
            bool: True if the trade amount meets the minimum requirement, False otherwise.
        """
        if usdc_amount < self.min_trade_amount:
            self.logger.warning(
                "Order amount %.2f USDC is below minimum required: %.2f USDC",
                usdc_amount,
                self.min_trade_amount,
            )
            return True

        self.logger.info(
            "Order amount %.2f USDC meets the minimum required: %.2f USDC",
            usdc_amount,
            self.min_trade_amount,
        )
        return True

    def open_orders_ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensures that all required columns exist in an open orders DataFrame.
        Missing columns are added with None values.

        Args:
            df (pd.DataFrame): A DataFrame containing open order data.

        Returns:
            pd.DataFrame: The DataFrame with all required columns ensured.
        """
        required_columns = [
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

        for col in required_columns:
            if col not in df.columns:
                df[col] = None
                self.logger.warning("Column '%s' not found in open orders.", col)

        return df[required_columns]

    def open_orders_convert_column_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Converts relevant columns in an open orders DataFrame to appropriate data types.

        - Converts numerical columns to float.
        - Converts time-related columns to datetime with Berlin timezone.

        Args:
            df (pd.DataFrame): A DataFrame containing open orders.

        Returns:
            pd.DataFrame: The updated DataFrame with converted data types.
        """
        float_columns = ["price", "origQty", "executedQty", "cummulativeQuoteQty"]

        for col in float_columns:
            if col in df.columns:
                df[col] = df[col].astype(float)

        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df["workingTime"] = pd.to_datetime(df["workingTime"], unit="ms", utc=True)
        df["time"] = df["time"].dt.tz_convert("Europe/Berlin")
        df["workingTime"] = df["workingTime"].dt.tz_convert("Europe/Berlin")

        return df

    def validate_order_params(
        self, side: str, order_type: str, price: Optional[float]
    ) -> None:
        """
        Validates order parameters before placing an order.

        Args:
            side (str): Order side, either "BUY" or "SELL".
            order_type (str): Type of order, e.g., "LIMIT".
            price (Optional[float]): The price for LIMIT orders (required).

        Raises:
            ValueError: If the side is invalid or if price is missing for LIMIT orders.
        """
        if side not in {"BUY", "SELL"}:
            self.logger.error("Invalid order side: %s", side)
            raise ValueError("Side must be 'BUY' or 'SELL'.")

        if order_type == "LIMIT" and price is None:
            self.logger.error("Price must be specified for LIMIT orders.")
            raise ValueError("Price is required for LIMIT orders.")
