from logging import Logger
from unittest.mock import MagicMock

import pandas as pd
import pytest

from services.src.market_manager_helper import BinanceManagerHelper


@pytest.fixture
def exchange_info():
    """Fixture to provide mock Binance exchange information."""
    return {
        "symbols": [
            {"baseAsset": "BTC", "quoteAsset": "USDT", "isSpotTradingAllowed": True},
            {"baseAsset": "ETH", "quoteAsset": "USDT", "isSpotTradingAllowed": True},
            {"baseAsset": "XRP", "quoteAsset": "USDT", "isSpotTradingAllowed": False},
        ]
    }


@pytest.fixture
def logger():
    """Fixture to provide a mock logger."""
    return MagicMock(spec=Logger)


@pytest.fixture
def binance_helper(exchange_info, logger):
    """Fixture to create a BinanceManagerHelper instance."""
    return BinanceManagerHelper(exchange_info, logger, min_trade_amount=15.0)


def test_is_usdt_spot_trading_allowed(binance_helper):
    """Test checking if a trading pair supports USDT spot trading."""
    assert binance_helper.is_usdt_spot_trading_allowed(
        {"baseAsset": "BTC", "quoteAsset": "USDT", "isSpotTradingAllowed": True}
    )
    assert not binance_helper.is_usdt_spot_trading_allowed(
        {"baseAsset": "XRP", "quoteAsset": "USDT", "isSpotTradingAllowed": False}
    )


def test_get_binance_coin_symbols(binance_helper):
    """Test fetching available Binance coin symbols for USDT spot trading."""
    result = binance_helper.get_binance_coin_symbols()
    assert result == {"btc", "eth"}


def test_has_sufficient_funds(binance_helper):
    """Test checking if there are sufficient funds for a trade."""
    balances = pd.DataFrame({"asset": ["USDT", "BTC"], "free": [50.0, 0.1]})

    assert binance_helper.has_sufficient_funds(20.0, balances)
    assert not binance_helper.has_sufficient_funds(100.0, balances)
    assert not binance_helper.has_sufficient_funds(1.0, balances, asset="ETH")


def test_validate_trade_limits(binance_helper):
    """Test validating if the trade amount meets Binance's minimum requirement."""
    assert binance_helper.validate_trade_limits(25.0)
    assert not binance_helper.validate_trade_limits(5.0)


def test_open_orders_ensure_columns(binance_helper):
    """Test ensuring that all required columns exist in an open orders DataFrame."""
    df = pd.DataFrame(
        {"symbol": ["BTCUSDT"], "orderId": [123]}
    )  # Missing other required columns

    updated_df = binance_helper.open_orders_ensure_columns(df)

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

    assert all(col in updated_df.columns for col in required_columns)


def test_open_orders_convert_column_types(binance_helper):
    """Test converting open orders column types (float and datetime conversions)."""
    df = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "price": ["45000"],
            "origQty": ["0.5"],
            "executedQty": ["0.2"],
            "cummulativeQuoteQty": ["9000"],
            "time": [1704067200000],
            "workingTime": [1704067200000],
        }
    )

    converted_df = binance_helper.open_orders_convert_column_types(df)

    assert converted_df["price"].dtype == "float64"
    assert converted_df["origQty"].dtype == "float64"
    assert converted_df["executedQty"].dtype == "float64"
    assert converted_df["cummulativeQuoteQty"].dtype == "float64"
    assert pd.api.types.is_datetime64_any_dtype(converted_df["time"])
    assert pd.api.types.is_datetime64_any_dtype(converted_df["workingTime"])


def test_validate_order_params(binance_helper):
    """Test order parameter validation."""
    binance_helper.validate_order_params("BUY", "LIMIT", 45000)  # No error
    binance_helper.validate_order_params("SELL", "LIMIT", 500)  # No error
    binance_helper.validate_order_params("BUY", "MARKET", None)  # No error
    binance_helper.validate_order_params("SELL", "MARKET", None)  # No error

    with pytest.raises(ValueError, match="Side must be 'BUY' or 'SELL'."):
        binance_helper.validate_order_params("HOLD", "LIMIT", 45000)

    with pytest.raises(ValueError, match="Price is required for LIMIT orders."):
        binance_helper.validate_order_params("BUY", "LIMIT", None)
