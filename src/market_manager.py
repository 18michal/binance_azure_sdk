from typing import Any

import pandas as pd
from binance.spot import Spot

from src.crypto_market_fetcher import CoinGeckoMarketData
from src.helpers import configure_logger


class BinanceManager:

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
            raise RuntimeError() from e

    def get_account_type(self) -> str:
        """Returns the account type from Binance wallet info."""
        return self.wallet.get("accountType", "Unknown")

    def get_wallet_balances(self) -> pd.DataFrame:
        wallet_info = self.wallet

        if "balances" not in wallet_info:
            self.logger.error("No balances found in wallet info.")
            raise ValueError()

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

        binance_symobls = self._get_binance_coin_symbols()

        for coin in data_top_coins:
            coin["is_available_on_binance"] = coin["symbol"].lower() in binance_symobls

        return data_top_coins

    def _get_binance_coin_symbols(self) -> set[str]:
        data_exchange = self.exchange_info
        if "symbols" not in data_exchange:
            raise ValueError("Unexpected Binance API response: Missing 'symbols'.")

        symbols = {
            symbol["baseAsset"].lower()
            for symbol in data_exchange["symbols"]
            if symbol["quoteAsset"] == "USDT" and symbol["isSpotTradingAllowed"]
        }

        self.logger.info("Successfully fetched exchange symbols from Binance API.")
        return symbols
