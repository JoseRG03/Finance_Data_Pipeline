WITH invalid_prices AS (
    SELECT * FROM finance_data.company_registry_stock_price
    WHERE open < 0 OR close < 0 OR volume < 0
)
SELECT COUNT(*) AS invalid_count FROM invalid_prices;