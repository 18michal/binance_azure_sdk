import os

from dotenv import load_dotenv
from pandas import DataFrame
from tenacity import retry, stop_after_attempt, wait_exponential

from services.azure_manager import AzureDatabaseManager, AzureKeyVaultManager
from services.market_manager import BinanceManager

RETRY_POLICY = retry(
    stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=10)
)


@RETRY_POLICY
def insert_portfolio_balance(
    database_manager: AzureDatabaseManager, balance_data: DataFrame
) -> None:
    database_manager.insert_portfolio_balance(balance_data=balance_data)


@RETRY_POLICY
def insert_market_history(
    database_manager: AzureDatabaseManager, market_data_list: list
) -> None:
    database_manager.insert_market_history(market_data_list=market_data_list)


@RETRY_POLICY
def insert_trade(database_manager: AzureDatabaseManager, trade_data: DataFrame) -> None:
    database_manager.insert_trade(trade_data=trade_data)


def load_credentials():
    """Load API credentials from .env file."""
    load_dotenv()
    kv_name = os.getenv("AZURE_VAULT_NAME")
    kv_url = os.getenv("AZURE_VAULT_URL")

    if not kv_name or not kv_url:
        raise ValueError("Missing Binance API credentials. Check your .env file.")

    return kv_name, kv_url


def init_managers(
    kv_name: str, kv_url: str
) -> tuple[BinanceManager, AzureDatabaseManager]:
    """Initialize Binance and Azure Database Managers."""
    azurekeyvaultconfig = AzureKeyVaultManager(
        kv_name=kv_name,
        kv_url=kv_url,
    )

    binance_api_key = azurekeyvaultconfig.get_secret("binance-api-key")
    binance_api_secret = azurekeyvaultconfig.get_secret("binance-api-secret")

    if not binance_api_key or not binance_api_secret:
        raise ValueError("Missing Binance API credentials. Check your Azure Key Vault.")

    manager_binance = BinanceManager(
        api_key=binance_api_key, api_secret=binance_api_secret
    )
    manager_database = AzureDatabaseManager(key_vault=azurekeyvaultconfig)

    return manager_binance, manager_database


def main():
    """Main function to interact with Binance API and Azure Database."""
    try:
        kv_name, kv_url = load_credentials()
        manager_binance, manager_database = init_managers(
            kv_name=kv_name, kv_url=kv_url
        )

        wallet = manager_binance.get_wallet_balances()
        top_crypto = manager_binance.fetch_biggest_crypto_data()
        trades = manager_binance.get_trade_history_last_24h()

        insert_portfolio_balance(database_manager=manager_database, balance_data=wallet)
        insert_market_history(
            database_manager=manager_database, market_data_list=top_crypto
        )
        insert_trade(database_manager=manager_database, trade_data=trades)

    except Exception as e:  # pylint: disable=W0718
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
