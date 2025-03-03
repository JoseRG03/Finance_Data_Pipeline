CREATE SCHEMA company_registry;

CREATE TABLE finance_data.company_registry.bank_info (
    symbol VARCHAR(5) PRIMARY KEY,
    industry VARCHAR(100),
    sector VARCHAR(100),
    employee_count INT,
    city VARCHAR(100),
    phone VARCHAR(20),
    state VARCHAR(100),
    country VARCHAR(100),
    website VARCHAR(255),
    address VARCHAR(255)
);

CREATE TABLE finance_data.company_registry.stock_price (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(5) REFERENCES finance_data.company_registry.bank_info (symbol),
    date TIMESTAMP,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER
);

CREATE TABLE finance_data.company_registry.fundamentals (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(5) REFERENCES finance_data.company_registry.bank_info (symbol),
    period VARCHAR(100),
    assets BIGINT,
    debt BIGINT,
    invested_capital BIGINT,
    shares_issued BIGINT,
    UNIQUE (symbol, period)
);

CREATE TABLE finance_data.company_registry.holders (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    symbol VARCHAR(5) REFERENCES finance_data.company_registry.bank_info (symbol),
    date TIMESTAMP,
    holder VARCHAR(255),
    shares BIGINT,
    value BIGINT
);