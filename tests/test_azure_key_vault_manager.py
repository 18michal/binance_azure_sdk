from unittest.mock import patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from services.azure_manager import AzureKeyVaultManager


@pytest.fixture
@patch("services.azure_manager.SecretClient")
def keyvault_config(mock_secret_client, mocker):
    """Fixture to create an instance of AzureKeyVaultConfig with mocked SecretClient, logger."""
    mock_secret_client.return_value.get_secret.return_value.value = (
        "mocked_secret_value"
    )
    mock_logger = mocker.patch("services.azure_manager.configure_logger")
    return AzureKeyVaultManager(
        kv_name="test-kv", kv_url="https://test-kv.vault.azure.net/"
    )


def test_get_secret_success(keyvault_config):
    """Test retrieving a secret successfully."""
    secret = keyvault_config.get_secret("test-secret")

    assert secret == "mocked_secret_value"
    keyvault_config.client.get_secret.assert_called_once_with("test-secret")


def test_get_secret_not_found(keyvault_config):
    """Test when the secret is not found in Key Vault."""
    keyvault_config.client.get_secret.side_effect = ResourceNotFoundError(
        "Secret not found."
    )

    secret = keyvault_config.get_secret("non-existent-secret")

    assert secret is None
    keyvault_config.logger.error.assert_called_once()


def test_get_secret_unexpected_exception(keyvault_config):
    """Test handling an unexpected exception."""
    keyvault_config.client.get_secret.side_effect = Exception("Unexpected error")

    secret = keyvault_config.get_secret("test-secret")

    assert secret is None
    keyvault_config.logger.error.assert_called_once()
