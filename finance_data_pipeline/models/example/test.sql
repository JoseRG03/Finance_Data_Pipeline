{{ config(
    materialized='view'
) }}

WITH source_data AS (
    SELECT 
        id,
        name,
        created_at,
        updated_at
    FROM {{ source('my_source', 'my_table') }}
)

SELECT 
    id,
    name,
    created_at,
    updated_at,
    CURRENT_TIMESTAMP AS processed_at
FROM source_data
