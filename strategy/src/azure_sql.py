"""Azure SQL Database interaction module to get data from Daily_High_Price table."""

from services.azure_manager import AzureDatabaseManager


def get_saved_high_price_from_azure_sql(
    manager_database: AzureDatabaseManager,
    asset_name: str,
) -> dict[str, str | float] | None:
    """
    Retrieves the last saved high price and date for a given asset from the Azure SQL database.

    Args:
        manager_database (AzureDatabaseManager): An instance to query the database.
        asset_name (str): The name of the asset (e.g., "BTC") to look up.

    Returns:
        dict[str, str | float] | None: A dictionary with:
            - 'asset_high_price' (float): The stored high price of the asset.
            - 'asset_high_price_date' (str): The date the high price was recorded.
        Returns None if the asset is not found in the table.
    """
    assets_high_prices = manager_database.get_values_from_table(
        table_name="Daily_High_Price"
    )

    for asset in assets_high_prices:
        if asset[1] == asset_name:
            return {
                "asset_high_price": float(asset[2]),
                "asset_high_price_date": asset[3],
            }
    return None
