""" This module contains classes for managing Azure Key Vault and Azure SQL Database. """

from datetime import datetime, timedelta
from re import IGNORECASE, search
from typing import Optional, Union

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pandas import DataFrame
from pyodbc import Connection, Error, connect  # pylint: disable=E0611

from services.src.helpers import configure_logger, load_config


class AzureKeyVaultManager:
    """
    A helper class for securely retrieving secrets from Azure Key Vault.

    This class initializes a connection to an Azure Key Vault instance using
    the `DefaultAzureCredential` and provides a method to retrieve stored secrets.

    Attributes:
        kv_name (str): The name of the Azure Key Vault.
        kv_url (str): The full URL of the Azure Key Vault.
        credential (DefaultAzureCredential): The authentication credential used to access the vault.
        logger (Logger): Logger for logging Binance API interactions.

    Methods:
        get_secret(secret_object_name: str) -> Optional[str]:
            Retrieves a secret value from the Azure Key Vault.
    """

    def __init__(
        self,
        kv_name: str,
        kv_url: str,
    ):
        self.kv_name = kv_name
        self.kv_url = kv_url

        self.credential = DefaultAzureCredential()
        self.logger = configure_logger(__name__)

        self.client = SecretClient(vault_url=self.kv_url, credential=self.credential)

    def get_secret(self, secret_object_name: str) -> Optional[str]:
        """
        Retrieves a secret from Azure Key Vault.

        Args:
            secret_object_name (str): The name of the secret to retrieve.

        Returns:
            Optional[str]: The secret value if found, otherwise None.

        Raises:
            ResourceNotFoundError: If the specified secret does not exist in the Key Vault.
        """
        try:
            secret = self.client.get_secret(secret_object_name)
            return secret.value
        except ResourceNotFoundError as e:
            self.logger.error("Error retrieving secret %s.\n %s", secret_object_name, e)
            return None
        except Exception as e:  # pylint: disable=W0718
            self.logger.error("An unexpected error occurred.\n %s", e)
            return None


class AzureDatabaseManager:
    """
    A class for interacting with an Azure SQL database.

    This class supports inserting, retrieving, updating, and deleting records
    in various tables of the database.

    Attributes:
        driver (str): The ODBC driver used for database connections.
        sql_database (str): The name of the SQL database.
        logger (Logger): Logger for logging Binance API interactions.
    """

    def __init__(self, key_vault: AzureKeyVaultManager):
        """
        Initializes the AzureDatabaseManager with credentials from Azure Key Vault.

        Args:
            key_vault (AzureKeyVaultManager): Instance of AzureKeyVaultManager to retrieve secrets.

        Raises:
            ValueError: If any of the required database credentials are missing.
        """
        config = load_config().get("azure_database", {})
        self.driver = config.get("driver")
        self.sql_database = config.get("sql_database")

        if self.driver is None or self.sql_database is None:
            raise ValueError(
                "Configuration error: azure_database values missing in config.yaml"
            )

        self.kv_config = key_vault
        self.logger = configure_logger(__name__)

        self.server = self.kv_config.get_secret("azure-sql-server")
        self.sql_username = self.kv_config.get_secret("azure-sql-username")
        self.sql_password = self.kv_config.get_secret("azure-sql-password")

        if not all([self.server, self.sql_username, self.sql_password]):
            raise ValueError("Missing database credentials from Azure Key Vault.")

    def insert_trade(self, trade_data: DataFrame):
        """
        Inserts a new trade record into the Trade_History table.

        Args:
            trade_data (pd.DataFrame): A DataFrame containing trade details with columns:
                - orderId (str)
                - symbol (str)
                - price (float)
                - qty (float)               # quantity
                - quoteQty (float)          # quote_quantity
                - commission (float)
                - commissionAsset (str)     # commission_asset
                - isBuyer (str)             # is_buyer
                - time (datetime)
        """

        query = """
        INSERT INTO Trade_History (order_id, symbol, price, quantity, quote_quantity, commission, commission_asset, is_buyer, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values_list = [
            (
                row["orderId"],  # order_id
                row["symbol"],
                row["price"],
                row["qty"],  # quantity
                row["quoteQty"],  # quote_quantity
                row["commission"],
                row["commissionAsset"],  # commission_asset
                row["isBuyer"],  # is_buyer
                row["time"],
            )
            for _, row in trade_data.iterrows()
        ]

        self._execute_query(query=query, values=values_list, many=True)

    def insert_market_history(
        self, market_data_list: list[dict[str, str | int | float | bool | datetime]]
    ):
        """
        Inserts  market capitalization data into the Market_Capitalization_History table.

        Args:
            market_data (list[dict]): A dictionary containing market data, including:
                - market_cap_rank (int)
                - name (str)
                - symbol (str)
                - price (float)
                - price_high (float)
                - price_low (float)
                - market_cap (float)
                - is_available_on_binance (bool)
                - timestamp (datetime)
        """
        query = """
        INSERT INTO Market_Capitalization_History 
        (market_cap_rank, name, symbol, price, price_high, price_low, market_cap, is_available_on_binance, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        values_list = [
            (
                market_data["market_cap_rank"],
                market_data["name"],
                market_data["symbol"],
                market_data["current_price"],  # price
                market_data["high_24h"],  # price_high
                market_data["low_24h"],  # price_low
                market_data["market_cap"],
                market_data["is_available_on_binance"],
                market_data["last_updated"],  # timestamp
            )
            for market_data in market_data_list
        ]

        self._execute_query(query=query, values=values_list, many=True)

    def insert_portfolio_balance(self, balance_data: DataFrame):
        """
        Inserts portfolio balance records from a DataFrame into the Portfolio_Balance table.

        Args:
            balance_data (pd.DataFrame): A DataFrame containing balance details with columns:
                - asset (str)
                - free (float)
                - locked (float)
        """

        query = """
        INSERT INTO Portfolio_Balance (asset, free, locked, timestamp)
        VALUES (?, ?, ?, ?)
        """
        timestamp = datetime.now()
        values_list = [
            (row["asset"], row["free"], row["locked"], timestamp)
            for _, row in balance_data.iterrows()
        ]

        self._execute_query(query=query, values=values_list, many=True)

    def insert_daily_high_price(self, high_price_data: list[dict[str, str | float]]):
        """
        Inserts daily high price data into the Daily_High_Price table.

        Args:
            high_price_data (list[dict]): A list of dictionaries with keys:
                - asset (str): The name of the asset.
                - high_price (float): The high price of the asset.
        """

        query = """
        INSERT INTO Daily_High_Price (asset, high_price, timestamp)
        VALUES (?, ?, ?)
        """
        timestamp = datetime.now()

        values_list = [
            (row["asset"], row["high_price"], timestamp) for row in high_price_data
        ]

        self._execute_query(query=query, values=values_list, many=True)

    def delete_old_trades(self):
        """
        Deletes trade records older than one year from the Trade_History table.

        This helps optimize database storage by removing outdated data.
        """
        one_year_ago = datetime.now() - timedelta(days=365)
        query = "DELETE FROM Trade_History WHERE timestamp < ?"
        values = (one_year_ago,)

        self._execute_query(query=query, values=values)
        self.logger.info("Deleted trades older than one year.")

    def get_values_from_table(self, table_name: str):
        """
        Retrieves all records from the specified table.

        Args:
            table_name (str): The name of the table to retrieve data from.

        Returns:
            List[tuple]: A list of tuples representing the table's rows.
        """
        query = f"SELECT * FROM {table_name}"
        return self._fetch_query(query=query)

    def _connect(self) -> Connection:
        """
        Establishes a connection to the Azure SQL database.

        Returns:
            Connection: A connection object to the Azure SQL database.

        Raises:
            ConnectionError: If the connection to the database fails.
        """
        try:
            conn_str = f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.sql_database};UID={self.sql_username};PWD={self.sql_password}"  # pylint: disable=C0301
            conn = connect(conn_str)
            return conn
        except Error as e:
            self.logger.error("Database connection failed")
            raise ConnectionError(
                f"Failed to connect to the Azure SQL database. Error: {e}"
            ) from e

    def _execute_query(
        self, query: str, values: Union[tuple, list[tuple]], many: bool = False
    ):
        """
        Executes an SQL query that modifies the database (e.g., INSERT, UPDATE, DELETE).

        Args:
            query (str): The SQL query to execute.
            values (tuple | list[tuple]): The values to use in the query.
            many (bool, optional): Executes a batch insert using executemany(). Defaults to False.

        Raises:
            RuntimeError: If the query execution fails.
        """
        table_name = None
        match = search(r"INTO\s+([^\s(]+)", query, IGNORECASE)
        if match:
            table_name = match.group(1)
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                if many:
                    cursor.executemany(query, values)
                else:
                    cursor.execute(query, values)
                conn.commit()
        except Error as e:
            self.logger.error("Error executing query. %s", e)
            raise RuntimeError("Error executing database query.") from e
        finally:
            self.logger.info("Query executed successfully on table: %s", table_name)

    def _fetch_query(self, query: str):
        """
        Executes a SELECT query and retrieves the results.

        Args:
            query (str): The SQL SELECT query to execute.

        Returns:
            List[tuple]: A list of tuples containing the query results.

        Raises:
            RuntimeError: If the query execution fails.
        """
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return cursor.fetchall()
        except Error as e:
            self.logger.error("Error fetching query results.")
            raise RuntimeError("Error fetching database query results.") from e
