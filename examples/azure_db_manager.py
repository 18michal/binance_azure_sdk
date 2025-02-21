import os

from dotenv import load_dotenv

from services.azure_manager import AzureDatabaseManager, AzureKeyVaultManager
from services.market_manager import BinanceManager

load_dotenv()


azurekeyvaultconfig = AzureKeyVaultManager(
    kv_name=os.getenv("AZURE_VAULT_NAME", ""),
    kv_url=os.getenv("AZURE_VAULT_URL", ""),
)

binance_api_key = azurekeyvaultconfig.get_secret("binance-api-key")
binance_api_secret = azurekeyvaultconfig.get_secret("binance-api-secret")

if not binance_api_key or not binance_api_secret:
    raise ValueError("Missing Binance API credentials. Check your Azure Key Vault.")

manager_binance = BinanceManager(api_key=binance_api_key, api_secret=binance_api_secret)
manager_database = AzureDatabaseManager(key_vault=azurekeyvaultconfig)

wallet = manager_binance.get_wallet_balances()
top_crypto = manager_binance.fetch_biggest_crypto_data()
trades = manager_binance.get_trade_history_last_24h()

manager_database.insert_portfolio_balance(balance_data=wallet)
manager_database.insert_market_history(market_data=top_crypto)
manager_database.insert_trade(trade_data=trades)
