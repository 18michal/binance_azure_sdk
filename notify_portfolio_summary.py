from services.azure_manager import AzureKeyVaultManager
from services.notification.portfolio_reporter import PortfolioReporter
from strategy.dca_config_loader import DCAConfigLoader
from strategy.src.dates import get_previous_month_start
from strategy.src.setup import init_managers, load_credentials


def main():
    """Main function to execute the DCA strategy for a user."""
    dca_config_loader = DCAConfigLoader()
    user_config = dca_config_loader.get_user_config(user_id="user_1")

    kv_name, kv_url = load_credentials(user_config=user_config)

    azure_key_vault_config = AzureKeyVaultManager(
        kv_name=kv_name,
        kv_url=kv_url,
    )

    email_password = azure_key_vault_config.get_secret("google-password")
    if not email_password:
        raise ValueError("Missing email password. Check your Azure Key Vault.")
    manager_binance, manager_database = init_managers(kv_name=kv_name, kv_url=kv_url)

    start_prev_month = get_previous_month_start()

    for asset_name in user_config["assets"]:
        df_trades = manager_binance.fetch_symbol_trade_history(
            symbol=asset_name + "USDC", start_time=start_prev_month
        )
        if df_trades is not None and not df_trades.empty:
            manager_database.insert_trade(trade_data=df_trades)

    email_sender = user_config["email_from"]
    recipient_email = user_config["email_to"]

    portfolio_reporter = PortfolioReporter(
        manager_binance=manager_binance,
        manager_database=manager_database,
        email_sender=email_sender,
        email_password=email_password,
    )
    portfolio_reporter.generate_and_send_report(recipient_email=recipient_email)


if __name__ == "__main__":
    main()
