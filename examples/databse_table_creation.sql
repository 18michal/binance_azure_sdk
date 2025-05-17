-- Portfolio Balance Table
CREATE TABLE Portfolio_Balance (
   id INT IDENTITY(1,1) PRIMARY KEY,
   asset VARCHAR(20) NOT NULL,
   free DECIMAL(18,8) NOT NULL,
   locked DECIMAL(18,8) NOT NULL,
   timestamp DATETIME NOT NULL
);

-- Trade History Table
CREATE TABLE Trade_History (
   id INT IDENTITY(1,1) PRIMARY KEY,
   order_id VARCHAR(50) NOT NULL,
   symbol VARCHAR(20) NOT NULL,
   price DECIMAL(18,8) NOT NULL,
   quantity DECIMAL(18,8) NOT NULL,
   quote_quantity DECIMAL(18,8) NOT NULL,
   commission DECIMAL(18,8) NOT NULL,
   commission_asset VARCHAR(20) NOT NULL,
   is_buyer BIT NOT NULL,
   timestamp DATETIME NOT NULL
);

-- Market Capitalization History Table
CREATE TABLE Market_Capitalization_History (
   id INT IDENTITY(1,1) PRIMARY KEY,
   market_cap_rank INT NOT NULL,
   name VARCHAR(255) NOT NULL,
   symbol VARCHAR(20) NOT NULL,
   price DECIMAL(18,8) NOT NULL,
   price_high DECIMAL(18,8) NOT NULL,
   price_low DECIMAL(18,8) NOT NULL,
   market_cap DECIMAL(18,2) NOT NULL,
   is_available_on_binance BIT NOT NULL,
   timestamp DATETIME NOT NULL,
);

-- DCA Table Helper For Storing The Daily High Price For Each Asset
CREATE TABLE Daily_High_Price ( 
    id INT IDENTITY(1,1) PRIMARY KEY,
    asset VARCHAR(20) NOT NULL UNIQUE,
    high_price FLOAT NOT NULL,
    timestamp DATETIME NOT NULL
);

