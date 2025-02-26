from unittest.mock import patch

import pandas as pd
import pytest

from services.market_manager import BinanceManager


@pytest.fixture
def binance_manager():
    """Fixture to create a BinanceManager instance with a mocked Binance Spot client."""
    with patch("services.market_manager.Spot") as mock_spot:
        mock_client = mock_spot.return_value
        mock_client.account.return_value = {
            "accountType": "SPOT",
            "balances": [
                {"asset": "BTC", "free": "0.5", "locked": "0.1"},
                {"asset": "ETH", "free": "0", "locked": "0"},
            ],
        }

        return BinanceManager(api_key="test", api_secret="test")


def test_get_account_type(binance_manager):
    """Test get_account_type extracts the correct account type."""
    assert binance_manager.get_account_type() == "SPOT"


def test_get_wallet_balances(binance_manager):
    """Test get_wallet_balances filters zero balances and converts values."""
    df = binance_manager.get_wallet_balances()

    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert len(df) == 1  # Only BTC should be included
    assert df.iloc[0]["asset"] == "BTC"
    assert df.iloc[0]["free"] == 0.5
    assert df.iloc[0]["locked"] == 0.1
