from typing import Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from services.helpers import configure_logger


class AzureKeyVaultConfig:
    """
    A helper class for securely retrieving secrets from Azure Key Vault.

    This class initializes a connection to an Azure Key Vault instance using the `DefaultAzureCredential`
    and provides a method to retrieve stored secrets.

    Attributes:
        kv_name (str): The name of the Azure Key Vault.
        kv_url (str): The full URL of the Azure Key Vault.
        credential (DefaultAzureCredential): The authentication credential used to access the vault.

    Methods:
        get_secret(secret_object_name: str) -> Optional[str]:
            Retrieves a secret value from the Azure Key Vault.
    """

    def __init__(
        self,
        kv_name: str,
        kv_url: str,
    ):
        self.kv_name = kv_name
        self.kv_url = kv_url

        self.credential = DefaultAzureCredential()
        self.logger = configure_logger(__name__)

    def get_secret(self, secret_object_name: str) -> Optional[str]:
        """
        Retrieves a secret from Azure Key Vault.

        Args:
            secret_object_name (str): The name of the secret to retrieve.

        Returns:
            Optional[str]: The secret value if found, otherwise None.

        Raises:
            ResourceNotFoundError: If the specified secret does not exist in the Key Vault.
        """
        try:
            client = SecretClient(vault_url=self.kv_url, credential=self.credential)
            secret = client.get_secret(secret_object_name)
            return secret.value
        except ResourceNotFoundError as e:
            self.logger.error("Error retrieving secret %s.\n %s", secret_object_name, e)
            return None
        except Exception as e:  # Pylint: disable=W0718
            self.logger.error("An unexpected error occurred.\n %s", e)
            return None
