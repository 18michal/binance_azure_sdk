import os

from dotenv import load_dotenv

from src.market_manager import BinanceManager

load_dotenv()

API_KEY = os.environ.get("BINANCE_API_KEY", "")
API_SECRET = os.environ.get("BINANCE_API_SECRET", "")

binance_manager = BinanceManager(api_key=API_KEY, api_secret=API_SECRET)

print(binance_manager.get_account_type())

wallet = binance_manager.get_wallet_balances()
print(wallet)

coins = binance_manager.fetch_biggest_crypto_data()
print(coins[0])
