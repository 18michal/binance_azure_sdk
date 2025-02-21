from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from pyodbc import Error

from services.azure_manager import AzureDatabaseManager, AzureKeyVaultManager


@pytest.fixture
def mock_key_vault():
    """Mock Azure Key Vault Manager"""
    mock_kv = MagicMock(spec=AzureKeyVaultManager)
    mock_kv.get_secret.side_effect = lambda key: {
        "azure-sql-server": "test-server.database.windows.net",
        "azure-sql-username": "test_user",
        "azure-sql-password": "test_password",
    }.get(key, None)
    return mock_kv


@pytest.fixture
def db_manager(mock_key_vault):
    """Fixture for AzureDatabaseManager"""
    return AzureDatabaseManager(key_vault=mock_key_vault)


@patch("services.azure_manager.connect")
def test_init(mock_connect, mock_key_vault):
    """Test database manager initialization"""
    db_manager = AzureDatabaseManager(mock_key_vault)

    assert db_manager.server == "test-server.database.windows.net"
    assert db_manager.sql_username == "test_user"
    assert db_manager.sql_password == "test_password"


@patch("services.azure_manager.AzureDatabaseManager")
def test_database_connection_error(mock_connect, db_manager):
    """Test database connection failure handling"""
    mock_connect.side_effect = Exception("Connection failed")

    with pytest.raises(
        ConnectionError, match="Failed to connect to the Azure SQL database"
    ):
        db_manager._connect()


@patch("services.azure_manager.AzureDatabaseManager._connect")
def test_execute_query_success(mock_connect, db_manager):
    """Test successful execution of a database-modifying query"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    db_manager._execute_query("INSERT INTO test_table VALUES (?)", ("value",))

    mock_cursor.execute.assert_called_once_with(
        "INSERT INTO test_table VALUES (?)", ("value",)
    )
    mock_conn.commit.assert_called_once()


@patch("services.azure_manager.AzureDatabaseManager._connect")
def test_execute_query_failure(mock_connect, db_manager):
    """Test that a RuntimeError is raised when query execution fails"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.side_effect = Error("Query failed")

    with pytest.raises(RuntimeError, match="Error executing database query"):
        db_manager._execute_query("INSERT INTO test_table VALUES (?)", ("value",))


@patch("services.azure_manager.AzureDatabaseManager._connect")
def test_fetch_query_success(mock_connect, db_manager):
    """Test successful execution of a SELECT query"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

    result = db_manager._fetch_query("SELECT * FROM test_table")

    mock_cursor.execute.assert_called_once_with("SELECT * FROM test_table")
    assert result == [("row1",), ("row2",)]  # Verify expected output


@patch("services.azure_manager.AzureDatabaseManager._connect")
def test_fetch_query_failure(mock_connect, db_manager):
    """Test that a RuntimeError is raised when a SELECT query fails"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_connect.return_value.__enter__.return_value = mock_conn
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.side_effect = Error("Query failed")  # Simulate DB failure

    with pytest.raises(RuntimeError, match="Error fetching database query results"):
        db_manager._fetch_query("SELECT * FROM test_table")


@patch("services.azure_manager.AzureDatabaseManager._execute_query")
def test_insert_trade(mock_execute_query, db_manager):
    """Test inserting a trade record"""
    trade_data = {
        "order_id": "12345",
        "symbol": "BTCUSDT",
        "side": "BUY",
        "order_type": "LIMIT",
        "price": 50000.0,
        "quantity": 0.1,
        "status": "FILLED",
        "executed_qty": 0.1,
        "stop_price": 49000.0,
        "timestamp": datetime.now(),
    }

    db_manager.insert_trade(trade_data)
    mock_execute_query.assert_called_once()


@patch("services.azure_manager.AzureDatabaseManager._execute_query")
def test_insert_market_history(mock_execute_query, db_manager):
    """Test inserting market history data"""
    market_data = {
        "market_cap_rank": 1,
        "name": "Bitcoin",
        "symbol": "BTC",
        "price": 50000.0,
        "price_high": 51000.0,
        "price_low": 49000.0,
        "market_cap": 900000000000.0,
        "is_available_on_binance": True,
        "timestamp": datetime.now(),
    }

    db_manager.insert_market_history(market_data)
    mock_execute_query.assert_called_once()


@patch("services.azure_manager.AzureDatabaseManager._execute_query")
def test_insert_portfolio_balance(mock_execute_query, db_manager):
    """Test inserting portfolio balance data"""
    balance_data = {
        "asset": "BTC",
        "free": 0.5,
        "locked": 0.1,
    }

    db_manager.insert_portfolio_balance(balance_data)
    mock_execute_query.assert_called_once()


@patch("services.azure_manager.AzureDatabaseManager._execute_query")
def test_delete_old_trades(mock_execute_query, db_manager):
    """Test deleting old trades"""
    db_manager.delete_old_trades()
    mock_execute_query.assert_called_once()


@patch("services.azure_manager.AzureDatabaseManager._fetch_query")
def test_get_values_from_table(mock_fetch_query, db_manager):
    """Test retrieving values from a table"""
    mock_fetch_query.return_value = [("BTCUSDT", "BUY", 50000.0)]

    result = db_manager.get_values_from_table("Trade_History")
    assert result == [("BTCUSDT", "BUY", 50000.0)]
    mock_fetch_query.assert_called_once_with(query="SELECT * FROM Trade_History")
