""" Class to notify users about portfolio performance. """

import pandas as pd

from services.azure_manager import AzureDatabaseManager
from services.market_manager import BinanceManager
from services.notification.base_notifier import BaseNotifier
from services.src.helpers import configure_logger


class PortfolioReporter(BaseNotifier):
    """
    Class to notify users about portfolio performane.

    Attributes:
        manager_binance (BinanceManager): Instance of BinanceManager to fetch wallet balances.
        manager_database (AzureDatabaseManager): Instance to retrieve trade history.
        email_sender (str): The sender's email address.
        email_password (str): The password or app password for SMTP login.
    """

    def __init__(
        self,
        manager_binance: BinanceManager,
        manager_database: AzureDatabaseManager,
        email_sender: str,
        email_password: str,
    ):
        super().__init__(manager_binance, email_sender, email_password)
        self.manager_database = manager_database

        self.logger = configure_logger(name=self.__class__.__name__)

    def generate_and_send_report(self, recipient_email: str):
        """
        Generates the portfolio performance report and sends it via email.

        The report includes the USDC balance, portfolio performance summary, and asset breakdown.

        Args:
            recipient_email (str): The recipient email address to send the portfolio report.
        """
        usdc_balance = self.calculate_usdc_balance()
        assets_data = self._calculate_assets_balances()
        assets_value = self._calculate_current_values(assets_data=assets_data)
        portfolio_value = self._calculate_total_and_value_change(
            assets_value=assets_value
        )

        message = self._render_portfolio_report_message(
            usdc_balance=usdc_balance,
            assets_value=assets_value,
            portfolio_value=portfolio_value,
        )

        self.send_email(
            recipient_email, subject="Your DCA Portfolio Report", message=message
        )
        self.logger.info("Portfolio report sent to %s", recipient_email)

    def _render_portfolio_report_message(
        self, usdc_balance: float, assets_value: dict, portfolio_value: dict
    ) -> str:
        """
        Renders the portfolio performance report as a nicely formatted message.

        This message includes the user's USDC wallet balance, a portfolio overview (total spend,
        current value, value change, and percentage change), and a breakdown of each asset.

        Args:
            usdc_balance (float): The current USDC balance in the user's account.
            assets_value (dict): A dictionary containing data for each asset.
            portfolio_value (dict): A dictionary containing the overall portfolio values.

        Returns:
            str: A string representing the portfolio report in a human-readable format.
        """
        message = f"""
        Dear User,

        📊 Here is the summary of your portfolio:

        💰 **USDC Wallet Balance**: ${usdc_balance:.2f}

        🏦 **Portfolio Overview**:
        - Total Spend: ${portfolio_value['total_spend_sum']:.2f}
        - Current Value: ${portfolio_value['current_value_sum']:.2f}
        - Value Change: ${portfolio_value['total_value_change']:.2f}
        - Percentage Change: {portfolio_value['value_change_percentage']:.2f}%

        🧐 **Asset Breakdown**:
        Asset         | Value     | Spend     | Change     | % Change
        --------------------------------------------------------------
        """
        for symbol, data in assets_value.items():
            message += (
                f"{symbol:<13} | ${data['current_value']:.2f} | "
                f"${data['total_spend']:.2f} | ${data['value_change']:.2f} | "
                f"{data['value_change_percentage']:.2f}%\n"
            )

        message += """
        Thank you,  
        The Trading Bot Team
        """

        return message

    def _calculate_total_and_value_change(self, assets_value: dict) -> dict:
        """
        Calculates the total spend, current value, value change, and % change of the portfolio.

        Args:
            assets_value (dict): Containing the current values and total spends for each asset.

        Returns:
            dict: Containing the summed values and value change percentages for the portfolio.
        """
        total_spend_sum = sum(data["total_spend"] for data in assets_value.values())
        current_value_sum = sum(data["current_value"] for data in assets_value.values())

        total_value_change = current_value_sum - total_spend_sum

        if total_spend_sum > 0:  # Avoid division by zero
            value_change_percentage = (total_value_change / total_spend_sum) * 100
        else:
            value_change_percentage = 0.0

        return {
            "total_spend_sum": total_spend_sum,
            "current_value_sum": current_value_sum,
            "total_value_change": total_value_change,
            "value_change_percentage": value_change_percentage,
        }

    def _calculate_assets_balances(self) -> dict:
        """
        Fetches trade data from the database, calculates data for each asset,
        and returns a dictionary containing each asset's balances and averages.

        Returns:
            dict: Calculated total spend, average price, and current quantity for each asset.
        """
        trades = self.manager_database.get_values_from_table(table_name="Trade_History")
        if not trades:
            raise ValueError("No trades found in the database.")

        trades_tuples = [tuple(trade) for trade in trades]
        columns = [
            "id",
            "order_id",
            "symbol",
            "price",
            "quantity",
            "quote_quantity",
            "commission",
            "commission_asset",
            "is_buyer",
            "timestamp",
        ]

        df = pd.DataFrame(trades_tuples, columns=columns)

        df["price"] = df["price"].astype(float)
        df["quantity"] = df["quantity"].astype(float)
        df["quote_quantity"] = df["quote_quantity"].astype(float)
        df["is_buyer"] = df["is_buyer"].astype(bool)

        buys = df[df["is_buyer"]]
        grouped_buys = buys.groupby("symbol").agg(
            total_spend=pd.NamedAgg(column="quote_quantity", aggfunc="sum"),
            total_quantity_bought=pd.NamedAgg(column="quantity", aggfunc="sum"),
        )

        sells = df[~df["is_buyer"]]
        grouped_sells = sells.groupby("symbol").agg(
            total_quantity_sold=pd.NamedAgg(column="quantity", aggfunc="sum"),
        )

        result = grouped_buys.merge(grouped_sells, how="left", on="symbol").fillna(0)
        result["average_price"] = (
            result["total_spend"] / result["total_quantity_bought"]
        )
        result["current_quantity"] = (
            result["total_quantity_bought"] - result["total_quantity_sold"]
        )

        return result[["total_spend", "average_price", "current_quantity"]].to_dict(
            orient="index"
        )

    def _calculate_current_values(self, assets_data: dict) -> dict:
        """
        Fetches current prices from Binance, calculates the current value and change for each asset.

        Args:
            assets_data (dict): A dictionary containing asset data (quantity, total spend, etc.).

        Returns:
            dict: Updated asset data with current price, current value, value change, and % change.
        """
        for symbol, data in assets_data.items():
            current_price = self.manager_binance.get_current_symbol_price(symbol=symbol)

            current_value = data["current_quantity"] * current_price

            value_change = current_value - data["total_spend"]

            if data["total_spend"] > 0:
                value_change_percentage = (value_change / data["total_spend"]) * 100
            else:
                value_change_percentage = 0.0

            data["current_price"] = current_price
            data["current_value"] = current_value
            data["value_change"] = value_change
            data["value_change_percentage"] = value_change_percentage

        return assets_data
