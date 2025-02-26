""" Example script to interact with Binance API. """

import os

from dotenv import load_dotenv

from services.market_manager import BinanceManager


def load_credentials():
    """Load API credentials from .env file."""
    load_dotenv()

    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise ValueError("Missing Binance API credentials. Check your .env file.")

    return api_key, api_secret


def main():
    """Main function to interact with Binance API."""
    api_key, api_secret = load_credentials()
    binance_manager = BinanceManager(api_key=api_key, api_secret=api_secret)

    try:
        print("Account Type:", end="\n")
        print(binance_manager.get_account_type())

        print("Wallet with Non-Zero Balances:", end="\n")
        print(binance_manager.get_wallet_balances())

        print("First of the Top 100 Cryptocurrencies:", end="\n")
        biggest_crypto = binance_manager.fetch_biggest_crypto_data()
        print(biggest_crypto[0] if biggest_crypto else "No data available.")

        symbol_to_check = "BTC"
        symbol_checked_bool = binance_manager.check_market_status(symbol_to_check)
        print(f"Is {symbol_to_check}/USDT tradeable?: {symbol_checked_bool}", end="\n")

        print("\nOpen Orders:")
        print(binance_manager.get_open_orders())

    except Exception as e:  # pylint: disable=W0718
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
