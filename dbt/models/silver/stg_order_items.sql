WITH bronze_items AS (
    SELECT * FROM {{ source('bronze', 'raw_order_items') }}
),

cleaned_items AS (
    SELECT
        CAST(order_id AS VARCHAR(50)) AS order_id,
        CAST(product_id AS VARCHAR(50)) AS product_id,
        CAST(quantity AS INT) AS quantity,
        CAST(price AS DECIMAL(10, 2)) AS unit_price
    FROM bronze_items
    WHERE order_id IS NOT NULL AND product_id IS NOT NULL
)

SELECT * FROM cleaned_items