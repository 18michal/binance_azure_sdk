""" Helper module to load binance API """

from services.azure_manager import AzureKeyVaultManager
from services.market_manager import BinanceManager


def init_binance(kv_name: str, kv_url: str) -> BinanceManager:
    """
    Initializes the BinanceManager.

    Args:
        kv_name (str): The name of the Azure Key Vault.
        kv_url (str): The URL endpoint of the Azure Key Vault.

    Raises:
        ValueError: If Binance API key or secret is missing in the Key Vault.

    Returns:
        BinanceManager: Instances initialized with credentials.
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

    return manager_binance
