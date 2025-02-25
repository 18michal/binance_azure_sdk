# Automated Cryptocurrency Trading SDK
A modular SDK for automating cryptocurrency trading using **Binance API**, **CoinGecko** and **Azure services** (Key Vault & SQL Database).

## Overview
This SDK provides:<br>
✅ Secure retrieval of secrets (API keys) from Azure Key Vault.<br>
✅ Real-time cryptocurrency price tracking using Binance API and CoinGecko API.
✅ Trading operations (buy/sell orders, wallet balance checks) using Binance API.
✅ Database storage for historical price data, trade history, and portfolio balances in Azure SQL.
✅ A logging system for debugging & tracking.<br>
✅ Unit tests for validating Key Vault and Binance API interactions.

## Prerequisites
1. **Azure Setup**
    To use this SDK, you need:
    - **Azure Key Vault** (for storing credentials).
    - **Azure SQL Database** (for storing trade & portfolio data).
    - **Azure Active Directory (AAD) application** with the following:
        - Client ID (`AZURE_CLIENT_ID`)
        - Tenant ID (`AZURE_TENANT_ID`)
        - Client Secret (`AZURE_CLIENT_SECRET`)

    Follow [this tutorial](https://www.youtube.com/watch?v=Vs3wyFk9upo&ab_channel=TechyTacos) to set up Azure Key Vault and retrieve these credentials.

2. Binance API Setup
    - Create Binance API Keys: [Guide](https://www.binance.com/en/support/faq/how-to-create-api-keys-on-binance-360002502072)
    - Create a Binance Subaccount: [Guide](https://www.binance.com/en/support/faq/binance-sub-account-functions-and-frequently-asked-questions-360020632811)
    - Binance Connector API Documentation: [Read the Docs](https://binance-connector.readthedocs.io/en/latest/index.html)

3. **Environment Variables (.env file)**
    Before running the code localy, create a `.env` file in the project root and add:
    ```bash
    AZURE_CLIENT_ID="your-client-id"
    AZURE_TENANT_ID="your-tenant-id"
    AZURE_CLIENT_SECRET="your-client-secret"
    AZURE_VAULT_URL="https://your-keyvault-name.vault.azure.net"
    AZURE_VAULT_NAME="your-keyvault-name"
    SECRET_OBJECT_NAME="your-secret-name"

    # Binance Credentials (Stored in Azure Key Vault)
    BINANCE_API_KEY="BINANCE_API_KEY"
    BINANCE_API_SECRET="BINANCE_API_SECRET"

    # Azure SQL Database Credentials (Stored in Azure Key Vault)
    AZURE_SQL_SERVER="your-sql-server.database.windows.net"
    AZURE_SQL_DATABASE="CryptoDB"
    AZURE_SQL_USERNAME="your-username"
    AZURE_SQL_PASSWORD="your-password"
    ```
    👉 **Important:** Never share `.env` files or commit them to Git!

## SDK Modules
| Module    | Description |
| -------- | ------- |
| services/azure_manager.py | Handles secure retrieval of API keys from Azure Key Vault. |
| services/src/helpers.py | Configures logging system for debugging & tracking. |
| services/market_manager.py | Handles Binance API interactions (trades, balances, orders). |
| services/src/market_manager_helper.py | Helper functions for Binance trading logic. |
| services/crypto_market_fetcher.py | Fetches data about top 100 Cryptocurrencies from CoinGecko API. |

## Database Schema (Azure SQL)
Before using the SDK, create the following tables in Azure SQL Database:
- Portfolio Balance Table (Portfolio_Balance)
- Trade History Table (Trade_History)
- (Market Capitalization History Table) Market_Capitalization_History

This schema is available to copy and use here: `examples/databse_table_creation.sql`
Conection to the database is based on the sql user and password.

## Running Code & Tests tip
1. To execute a code, use this example:
    ```bash
    python -m examples.azure_get_secret_key
    ```
2. To execute unit tests, use this example:
    ```bash
    python -m pytest tests/test_azure_database_manager.py
    ```
