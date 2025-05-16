from services.azure_manager import AzureKeyVaultManager
from services.notification.helpers import init_binance
from services.notification.wallet_balance_notifier import WalletBalanceNotifier
from strategy.dca_config_loader import DCAConfigLoader
from strategy.src.setup import load_credentials


def main(usd_for_x_months: int = 2):
    """Main function to notify the user about low USDC balance."""
    dca_config_loader = DCAConfigLoader()
    user_config = dca_config_loader.get_user_config(user_id="user_1")

    kv_name, kv_url = load_credentials(user_config=user_config)

    azure_key_vault_config = AzureKeyVaultManager(
        kv_name=kv_name,
        kv_url=kv_url,
    )

    manager_binance = init_binance(kv_name=kv_name, kv_url=kv_url)

    email_password = azure_key_vault_config.get_secret("google-password")

    if not email_password:
        raise ValueError("Missing email password. Check your Azure Key Vault.")

    email_sender = user_config["email_from"]
    recipient_email = user_config["email_to"]
    usd_required = sum(user_config["amount_usd"].values()) * usd_for_x_months

    wallet_balance_notifier = WalletBalanceNotifier(
        manager_binance=manager_binance,
        email_sender=email_sender,
        email_password=email_password,
    )
    wallet_balance_notifier.check_and_notify(
        recipient_email=recipient_email,
        usd_required=usd_required,
    )


if __name__ == "__main__":
    main()
