WITH bronze_orders AS (
    SELECT * FROM {{ source('bronze', 'raw_orders') }}
),

cleaned_orders AS (
    SELECT
        CAST(order_id AS VARCHAR(50)) AS order_id,
        CAST(customer_id AS VARCHAR(50)) AS customer_id,
        CAST(order_date AS DATE) AS order_date,
        UPPER(order_status) AS order_status
    FROM bronze_orders
    WHERE order_id IS NOT NULL
)

SELECT * FROM cleaned_orders