""" Setup module for initializing the Azure and Binance. """

from dotenv import load_dotenv

from services.azure_manager import AzureDatabaseManager, AzureKeyVaultManager
from services.market_manager import BinanceManager


def load_credentials(user_config: dict) -> tuple[str, str]:
    """
    Loads Azure Key Vault credentials from the user configuration and environment variables.

    Args:
        user_config (dict): Configuration dictionary containing Azure Key Vault details.

    Raises:
        ValueError: If either the Key Vault name or URL is missing.

    Returns:
        tuple[str, str]: A tuple containing the Key Vault name and Key Vault URL.
    """
    load_dotenv()
    kv_name = user_config["azure_vault"]["name"]
    kv_url = user_config["azure_vault"]["url"]

    if not kv_name or not kv_url:
        raise ValueError(
            "Missing Azure Key Vault credentials in configuration or .env file."
        )

    return kv_name, kv_url


def init_managers(
    kv_name: str, kv_url: str
) -> tuple[BinanceManager, AzureDatabaseManager]:
    """
    Initializes the BinanceManager and AzureDatabaseManager.

    Args:
        kv_name (str): The name of the Azure Key Vault.
        kv_url (str): The URL endpoint of the Azure Key Vault.

    Raises:
        ValueError: If Binance API key or secret is missing in the Key Vault.

    Returns:
        tuple[BinanceManager, AzureDatabaseManager]: Instances initialized with credentials.
    """
    azure_key_vault_config = AzureKeyVaultManager(
        kv_name=kv_name,
        kv_url=kv_url,
    )

    binance_api_key = azure_key_vault_config.get_secret("binance-api-key")
    binance_api_secret = azure_key_vault_config.get_secret("binance-api-secret")

    if not binance_api_key or not binance_api_secret:
        raise ValueError("Missing Binance API credentials. Check your Azure Key Vault.")

    manager_binance = BinanceManager(
        api_key=binance_api_key, api_secret=binance_api_secret
    )
    manager_database = AzureDatabaseManager(key_vault=azure_key_vault_config)

    return manager_binance, manager_database
