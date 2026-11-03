-- ==========================================
-- SILVER LAYER: Staging Customers
-- PURPOSE: Clean and standardize customer data
-- ==========================================

WITH bronze_customers AS (
    SELECT * FROM {{ source('bronze', 'raw_customers') }}
),

cleaned_customers AS (
    SELECT
        CAST(customer_id AS VARCHAR(50)) AS customer_id,
        CAST(signup_date AS DATE) AS signup_date,
        UPPER(location) AS location_city
    FROM bronze_customers
    WHERE customer_id IS NOT NULL
)

SELECT * FROM cleaned_customers