from unittest.mock import MagicMock, patch

import pytest

from services.crypto_market_fetcher import CoinGeckoMarketData


@pytest.fixture
def market_data():
    """Fixture to create an instance of CoinGeckoMarketData."""
    return CoinGeckoMarketData()


@patch("services.crypto_market_fetcher.get")
def test_fetch_market_data_success(mock_get, market_data):
    """Test successful API response."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "id": "bitcoin",
            "last_updated": "2023-12-31T12:00:00Z",
            "market_cap": 1000000,
            "name": "Bitcoin",
            "symbol": "BTC",
            "market_cap_rank": 1,
            "current_price": 45000,
            "high_24h": 46000,
            "low_24h": 44000,
        }
    ]
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    data = market_data._fetch_market_data(page=1)

    assert len(data) == 1
    assert data[0]["id"] == "bitcoin"
    mock_get.assert_called_once()
