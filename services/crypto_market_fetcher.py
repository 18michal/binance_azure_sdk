""" Contains a helper class to fetch market data for cryptocurrencies from CoinGecko API. """

from typing import Any

from requests import RequestException, get

from services.src.helpers import configure_logger


class CoinGeckoMarketData:
    """
    A helper class to interact with the CoinGecko API to fetch market data for cryptocurrencies.

    This class allows users to retrieve top cryptocurrencies based on market data,
    clean the data, and handle API request errors effectively.
    """

    def __init__(
        self,
        api_url: str = "https://api.coingecko.com/api/v3/coins/markets",
        currency: str = "usd",
        per_page: int = 50,
        total_pages: int = 2,
    ):
        """
        Args:
            api_url (str): The base URL for the CoinGecko API.
            currency (str): The currency to use for market data.
            per_page (int): The number of cryptocurrencies per page.
            total_pages (int): The total number of pages to fetch.
        """
        self.api_url = api_url
        self.currency = currency
        self.per_page = per_page
        self.total_pages = total_pages

        self.logger = configure_logger(__name__)

    def get_top_cryptocurrencies(self) -> list[dict[str, Any]]:
        """
        This method fetches market data for the specified number of pages, cleans the data,
        and returns the relevant information for each cryptocurrency.

        Returns:
            list[dict[str, Any]]: Cleaned market data for top cryptocurrencies.
        """
        data_coins = []
        for page in range(1, self.total_pages + 1):
            data_coins.extend(self._fetch_market_data(page))

        self.logger.info(
            "Successfully fetched data of cryptocurrencies from CoinGecko API."
        )
        return self._clean_market_data(data=data_coins)

    def _fetch_market_data(self, page: int) -> list[dict[str, Any]]:
        """
        Retrieves raw market data for a specific page from the CoinGecko API.

        Args:
            page (int): The page number to fetch from the API.
        Returns:
            list[dict[str, Any]]: Raw market data for the cryptocurrencies.
        Raises:
            RuntimeError: If the API request fails or returns an error.
        """
        params = {
            "vs_currency": self.currency,
            "order": "market_cap_desc",
            "per_page": self.per_page,
            "page": page,
            "sparkline": "false",
        }
        try:
            response = get(url=self.api_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            self.logger.error("Error fetching page %s", page)
            raise RuntimeError(f"API request failed for page {page}: {e}") from e

    def _clean_market_data(self, data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Cleans the market data by filtering relevant columns.

        Args:
            data (list[dict[str, Any]]): The raw market data to clean.
        Returns:
            list[dict[str, Any]]: Market data containing only the relevant columns.
        Raises:
            ValueError: If the data is missing any required columns.
        """
        columns = [
            "id",
            "last_updated",
            "market_cap",
            "name",
            "symbol",
            "market_cap_rank",
            "current_price",
            "high_24h",
            "low_24h",
        ]
        missing_columns = [col for col in columns if col not in data[0]]
        if missing_columns:
            self.logger.error(
                "Missing columns in data from CoinGecko API:\n%s", missing_columns
            )
            raise ValueError()

        cleaned_data = [{col: crypto[col] for col in columns} for crypto in data]
        self.logger.info(
            "Data cleaning complete. Returning %d records.", len(cleaned_data)
        )
        return cleaned_data
