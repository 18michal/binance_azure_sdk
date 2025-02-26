""" Example to get a secret from Azure Key Vault. """

import os

from dotenv import load_dotenv

from services.azure_manager import AzureKeyVaultManager


def load_credentials():
    """Load API credentials from .env file."""
    load_dotenv()

    kv_name = os.getenv("AZURE_VAULT_NAME")
    kv_url = os.getenv("AZURE_VAULT_URL")

    secret_object_name = os.getenv("SECRET_OBJECT_NAME")

    if not kv_name or not kv_url or not secret_object_name:
        raise ValueError("Missing Binance API credentials. Check your .env file.")

    return kv_name, kv_url, secret_object_name


def main():
    """Main function to interact with Azure Key Vault."""
    kv_name, kv_url, secret_object_name = load_credentials()

    azurekeyvaultconfig = AzureKeyVaultManager(
        kv_name=kv_name,
        kv_url=kv_url,
    )

    print(
        f"Your secret is '{azurekeyvaultconfig.get_secret(secret_object_name=secret_object_name)}'."
    )


if __name__ == "__main__":
    main()
