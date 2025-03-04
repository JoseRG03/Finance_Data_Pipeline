{{ config(
    materialized='table'
) }}

WITH monthly_summary AS (
    SELECT 
        symbol,
        toYYYYMM(date) AS month,
        (avg(open) + avg(close)) / 2 AS avg_open_close_price,
        avg(volume) AS avg_volume
    FROM default.stock_price
    GROUP BY symbol, month
)
SELECT * FROM monthly_summary;
