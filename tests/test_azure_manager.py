from unittest.mock import patch

import pytest
from azure.core.exceptions import ResourceNotFoundError

from services.azure_manager import AzureKeyVaultConfig


@pytest.fixture
def keyvault_config(mocker):
    """Fixture to create an instance of AzureKeyVaultConfig with mocked logger."""
    mock_logger = mocker.patch("src.azure_config.configure_logger")
    return AzureKeyVaultConfig(
        kv_name="test-kv", kv_url="https://test-kv.vault.azure.net/"
    )


@patch("src.azure_config.SecretClient")
def test_get_secret_success(mock_secret_client, keyvault_config):
    """Test retrieving a secret successfully."""
    # Mock the SecretClient behavior
    mock_client_instance = mock_secret_client.return_value
    mock_client_instance.get_secret.return_value.value = "mocked_secret_value"

    secret = keyvault_config.get_secret("test-secret")

    assert secret == "mocked_secret_value"
    mock_client_instance.get_secret.assert_called_once_with("test-secret")


@patch("src.azure_config.SecretClient")
def test_get_secret_not_found(mock_secret_client, keyvault_config, mocker):
    """Test when the secret is not found in Key Vault."""
    mock_client_instance = mock_secret_client.return_value
    mock_client_instance.get_secret.side_effect = ResourceNotFoundError(
        "Secret not found."
    )

    mock_logger = mocker.patch.object(keyvault_config, "logger")

    secret = keyvault_config.get_secret("non-existent-secret")

    assert secret is None
    mock_logger.error.assert_called_once()


@patch("src.azure_config.SecretClient")
def test_get_secret_unexpected_exception(mock_secret_client, keyvault_config, mocker):
    """Test handling an unexpected exception."""
    mock_client_instance = mock_secret_client.return_value
    mock_client_instance.get_secret.side_effect = Exception("Unexpected error")

    mock_logger = mocker.patch.object(keyvault_config, "logger")

    secret = keyvault_config.get_secret("test-secret")

    assert secret is None
    mock_logger.error.assert_called_once()
