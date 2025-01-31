# Automated BTC & ETH Buy Strategy
A modular SDK for automating cryptocurrency trading using **Binance API** and **Azure services**.

## Overview
This SDK provides:<br>
✅ Secure retrieval of secrets (API keys) from Azure Key Vault.<br>
✅ A logging system for debugging & tracking.<br>
✅ Unit tests for validating Key Vault interactions.

## Prerequisites
1. **Azure Setup<br>**
    To use this SDK, you need:
    - An **Azure Key Vault** instance.
    - An **Azure Active Directory (AAD) application** with the following:
        - Client ID (`AZURE_CLIENT_ID`)
        - Tenant ID (`AZURE_TENANT_ID`)
        - Client Secret (`AZURE_CLIENT_SECRET`)

    Follow [this tutorial](https://www.youtube.com/watch?v=Vs3wyFk9upo&ab_channel=TechyTacos) to set up Azure Key Vault and retrieve these credentials.

2. **Environment Variables (.env file)**<br>
    Before running the code localy, create a `.env` file in the project root and add:
    ```bash
    AZURE_CLIENT_ID="your-client-id"
    AZURE_TENANT_ID="your-tenant-id"
    AZURE_CLIENT_SECRET="your-client-secret"
    AZURE_VAULT_URL="https://your-keyvault-name.vault.azure.net"
    AZURE_VAULT_NAME="your-keyvault-name"
    SECRET_OBJECT_NAME="your-secret-name"
    ```
    👉 **Important:** Never share `.env` files or commit them to Git!


## Running Code & Tests tip<br>
1. To execute a code, use this example:
    ```bash
    python -m examples.azure_get_secret_key
    ```
2. To execute unit tests, use this example:
    ```bash
    python -m pytest tests/test_azure_config.py

    ```
