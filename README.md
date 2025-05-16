# Automated Cryptocurrency Trading SDK
A modular SDK for automating cryptocurrency trading using **Binance API**, **CoinGecko** and **Azure services** (Key Vault & SQL Database).

👉 It does not have a main.py file but instead provides usage examples in the examples/ folder.

## Overview
This SDK provides:<br>
✅ Secure retrieval of secrets (API keys) from Azure Key Vault.<br>
✅ Real-time cryptocurrency price tracking using Binance API and CoinGecko API.<br>
✅ Trading operations (buy/sell orders, wallet balance checks) using Binance API.<br>
✅ Database storage for historical price data, trade history, and portfolio balances in Azure SQL.<br>
✅ Flexible DCA (Dollar-Cost Averaging) strategy per user, based on configurable drop thresholds.<br>
✅ Automatic retries & logging for robust execution.<br>
✅ Unit tests for validating API & database interactions.<br>

## Strategy Layer – Rule-Based DCA Automation
The SDK project contains **rule-based DCA (Dollar-Cost Averaging)** crypto strategy with user-level configuration. The goal is to give each user control over their trading parameters and allow for low-cost, scheduled automation via **Raspberry Pi**.

⚠️ **Note:** The actual logic in dca_strategy.py is intentionally left minimal to give users flexibility in defining their own strategy logic. This keeps the SDK reusable and not opinionated.

### 📁 Folder Structure – Strategy
```bash
strategy/
├── dca_config_loader.py     # Loads and validates user strategy config
├── dca_strategy.py          # Core logic for running user-defined DCA strategy
└── src/
    ├── azure_sql.py         # Interacts with Azure SQL (e.g., price history, trade logs)
    ├── binance_trading.py   # Simplified Binance order execution helpers
    ├── dates.py             # Date range helpers (e.g., month start, today)
    └── setup.py             # Initializes Azure and Binance manager objects
```

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

3. **Configuration File (`config.yaml`)**
    Before running the script, update the config.yaml file with your database and Binance trading settings:
    ```yaml
    azure_database:
    driver: "{ODBC Driver 18 for SQL Server}"
    sql_database: "CryptoDB"

    binance:
    min_trade_amount: 15.0 # Fixed minimum trade amount in USDC
    ```

4. **Environment Variables (.env file)**
    Before running the code localy, create a `.env` file in the project root and add:
    ```bash
    AZURE_CLIENT_ID="your-client-id"
    AZURE_TENANT_ID="your-tenant-id"
    AZURE_CLIENT_SECRET="your-client-secret"
    AZURE_VAULT_URL="https://your-keyvault-name.vault.azure.net"
    AZURE_VAULT_NAME="your-keyvault-name"

    # Binance Credentials (Stored in Azure Key Vault)
    BINANCE_API_KEY="BINANCE_API_KEY"
    BINANCE_API_SECRET="BINANCE_API_SECRET"

    # Azure SQL Database Credentials (Stored in Azure Key Vault)
    AZURE_SQL_SERVER="your-sql-server.database.windows.net"
    AZURE_SQL_USERNAME="your-username"
    AZURE_SQL_PASSWORD="your-password"
    ```
    👉 **Important:** Never share `.env` files or commit them to Git!

## SDK Modules & Classes
1. Modules
    | Module    | Description |
    | -------- | ------- |
    | services/azure_manager.py | Handles secure retrieval of API keys from Azure Key Vault. |
    | services/market_manager.py | Handles Binance API interactions (trades, balances, orders). |
    | services/crypto_market_fetcher.py | Fetches data about top 100 Cryptocurrencies from CoinGecko API. |
    | services/src/helpers.py | Configures logging system for debugging & tracking. |
    | services/src/market_manager_helper.py | Helper functions for Binance trading logic. |

2. Class Azure Services - azure_manager.py
    - `AzureKeyVaultManager` Manages retrieval of secrets (API keys, database credentials) from Azure Key Vault:
        - Securely fetches API keys
        - Handles errors & logging
    - `AzureDatabaseManager` Manages connection to Azure SQL, storing & retrieving trade history, portfolio balances, and market data:
        - Inserts data
        - Fetches portfolio balances
        - Deletes old records


3. Class Binance Trading - market_manager.py<br>
    `BinanceManager` Handles all interactions with Binance API, including fetching wallet balances, market data, and placing trades:
    - Fetches real-time prices
    - Retrieves account type
    - Checks open orders
    - Places buy/sell orders
    - Cancels orders
    - Gets the yesterdays price for requested asset

4. Class Market Data (CoinGecko API) - crypto_market_fetcher.py<br>
    `CoinGeckoMarketData` Fetches real-time cryptocurrency market data from CoinGecko API:
    - Retrieves top 100 cryptocurrencies
    - Cleans and structures data
    - Handles API rate limits

## Database Schema (Azure SQL)
Before using the SDK, create the following tables in Azure SQL Database:
- Portfolio Balance Table (Portfolio_Balance)
- Trade History Table (Trade_History)
- Market Capitalization History Table (Market_Capitalization_History)
- DCA Table Helper For Storing The Daily High Price For Each Asset (Daily_High_Price)

This schema is available to copy and use here: `examples/databse_table_creation.sql`<br>
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

## Recommended Setup: Raspberry Pi for Cost Efficiency
Instead of using Azure Functions, Virtual Network and assign a static ip (which can be expensive), I recommend using a Raspberry Pi for scheduling tasks.

## Support This Project – Sign Up for Binance Using My Referral
If you find this project useful and don’t have a Binance account yet, please support my work by using my referral link!<br>
🔗 [Binance Referral Link](https://www.binance.com/activity/referral-entry/CPA?ref=CPA_00FXDN66MY)<br>
🆔 [Referral ID](CPA_00FXDN66MY)