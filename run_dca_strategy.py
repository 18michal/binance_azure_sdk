""" Main entry point for running the DCA strategy """

from strategy.dca_config_loader import DCAConfigLoader
from strategy.dca_strategy import run_dca_strategy
from strategy.src.setup import init_managers, load_credentials


def main():
    """Main function to execute the DCA strategy for a user."""
    dca_config_loader = DCAConfigLoader()
    user_config = dca_config_loader.get_user_config(user_id="user_1")

    kv_name, kv_url = load_credentials(user_config=user_config)
    manager_binance, manager_database = init_managers(kv_name=kv_name, kv_url=kv_url)

    drop_percent = user_config["drop_percent"]

    for asset_name in user_config["assets"]:
        amount_usd = user_config["amount_usd"][asset_name]

        run_dca_strategy(
            manager_binance=manager_binance,
            manager_database=manager_database,
            asset=asset_name,
            amount_usd=amount_usd,
            drop_percent=drop_percent,
            usd_coin="USDC",
        )


if __name__ == "__main__":
    main()
