WITH bronze_products AS (
    SELECT * FROM {{ source('bronze', 'raw_products') }}
),

cleaned_products AS (
    SELECT
        CAST(product_id AS VARCHAR(50)) AS product_id,
        UPPER(category) AS category_name,
        product_name
    FROM bronze_products
    WHERE product_id IS NOT NULL
)

SELECT * FROM cleaned_products