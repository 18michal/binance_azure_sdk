-- Portfolio Balance Table
CREATE TABLE Portfolio_Balance (
   id INT IDENTITY(1,1) PRIMARY KEY,
   asset VARCHAR(20) NOT NULL,
   free DECIMAL(18,8) NOT NULL,
   locked DECIMAL(18,8) NOT NULL,
   timestamp DATETIME NOT NULL,
   CONSTRAINT UQ_Portfolio_Asset_Time UNIQUE (asset, timestamp)
);

-- Trade History Table
CREATE TABLE Trade_History (
   id INT IDENTITY(1,1) PRIMARY KEY,
   order_id VARCHAR(50) NOT NULL,
   symbol VARCHAR(20) NOT NULL,
   side VARCHAR(4) NOT NULL CHECK (side IN ('BUY', 'SELL')),
   order_type VARCHAR(10) NOT NULL,
   price DECIMAL(18,8) NOT NULL,
   quantity DECIMAL(18,8) NOT NULL,
   status VARCHAR(20) NOT NULL,
   executed_qty DECIMAL(18,8) NOT NULL,
   stop_price DECIMAL(18,8) NOT NULL,
   timestamp DATETIME NOT NULL,
   CONSTRAINT UQ_Trade_Order UNIQUE (order_id)
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
   CONSTRAINT UQ_MarketCap_Symbol_Time UNIQUE (symbol, timestamp)
);
