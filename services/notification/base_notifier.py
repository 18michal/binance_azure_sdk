""" Base class for sending notifications via email. """

import smtplib
from email.message import EmailMessage

from services.market_manager import BinanceManager


class BaseNotifier:
    """
    A base class for sending email notifications using SMTP.

    Attributes:
        email_sender (str): The sender's email address.
        email_password (str): The password or app password for SMTP login.
    """

    def __init__(
        self, manager_binance: BinanceManager, email_sender: str, email_password: str
    ):
        self.manager_binance = manager_binance
        self.email_sender = email_sender
        self.email_password = email_password

        self.smtp_server = "smtp.gmail.com"
        self.port = 587

    def send_email(self, recipient_email: str, subject: str, message: str) -> None:
        """
        Sends an email to the specified recipient.

        Args:
            recipient_email (str): Email address of the recipient.
            subject (str): Subject of the email.
            message (str): Body of the email.
        """
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.email_sender
        msg["To"] = recipient_email
        msg.set_content(message)

        # Outlook SMTP server configuration
        with smtplib.SMTP(self.smtp_server, self.port) as smtp:
            smtp.starttls()
            smtp.login(self.email_sender, self.email_password)
            smtp.send_message(msg)

    def calculate_usdc_balance(self) -> float:
        """
        Calculates the total USDC balance in the wallet.

        Returns:
            float: Total USDC balance.
        """
        df_balances = self.manager_binance.get_wallet_balances()
        usdc_row = df_balances[df_balances["asset"] == "USDC"]

        if usdc_row.empty:
            return 0.0
        else:
            return usdc_row[["free", "locked"]].sum(axis=1).values[0]
