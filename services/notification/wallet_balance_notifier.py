""" Class to notify users about low wallet balances """

from services.market_manager import BinanceManager
from services.notification.base_notifier import BaseNotifier
from services.src.helpers import configure_logger


class WalletBalanceNotifier(BaseNotifier):
    """
    Class to notify users about low wallet balances interacting with Binance.
    This class send email notifications when the USDC balance is below a specified threshold.

    Attributes:
        manager_binance (BinanceManager): Instance of BinanceManager to fetch wallet balances.
        email_sender (str): The sender's email address.
        email_password (str): The password or app password for SMTP login.
    """

    def __init__(
        self, manager_binance: BinanceManager, email_sender: str, email_password: str
    ):
        super().__init__(manager_binance, email_sender, email_password)

        self.logger = configure_logger(name=self.__class__.__name__)

    def check_and_notify(self, recipient_email: str, usd_required: float) -> None:
        """
        Checks if the USDC balance is sufficient. If not, sends an email alert.

        Args:
            recipient_email (str): Email to notify if balance is too low.
            usd_required (float): Minimum required amount of USDC.

        Returns:
            None
        """
        usdc_total = self.calculate_usdc_balance()

        if float(usdc_total) < usd_required:
            message = self._render_message(actual=usdc_total, required=usd_required)
            self.send_email(
                recipient_email, subject="Low USDC Balance Alert", message=message
            )

            self.logger.info("Sent low balance alert to %s", recipient_email)

    def _render_message(self, actual: float, required: float) -> str:
        return f"""
        Dear User,

        We noticed that your USDC wallet balance is currently below the required threshold for automated DCA trading.

        📉 Required Balance: ${required:.2f}  
        💼 Current Balance:  ${actual:.2f}

        To ensure uninterrupted trading, please top up your wallet at your earliest convenience.

        Thank you,  
        The Trading Bot Team
        """
