-- ==========================================
-- GOLD LAYER: Customer 360, RFM Analysis & Product Preferences
-- PURPOSE: Aggregate customer transactions to calculate RFM metrics, 
--          extract top product category using Window Functions, 
--          and define the Churn target variable for Machine Learning.
-- ==========================================

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

-- ==========================================
-- STEP 1: Calculate Total Value per Order
-- ==========================================
orders_totals AS (
    SELECT
        order_id,
        SUM(quantity * unit_price) AS total_order_value
    FROM order_items
    GROUP BY order_id
),

-- ==========================================
-- STEP 2: Combine Orders with their Financial Value
-- ==========================================
customer_orders AS (
    SELECT
        o.customer_id,
        o.order_id,
        o.order_date,
        o.order_status,
        ot.total_order_value
    FROM orders o
    LEFT JOIN orders_totals ot
        ON o.order_id = ot.order_id
    WHERE o.order_status = 'COMPLETED'
),

-- ==========================================
-- STEP 3: Aggregate Metrics per Customer (RFM)
-- ==========================================
rfm_metrics AS (
    SELECT
        customer_id,
        MAX(order_date) AS last_order_date,
        COUNT(DISTINCT order_id) AS frequency_total_orders,
        SUM(total_order_value) AS monetary_total_spend
    FROM customer_orders
    GROUP BY customer_id
),

-- ==========================================
-- STEP 4: Feature Engineering - Favorite Category
-- ==========================================
product_preferences AS (
    SELECT
        o.customer_id,
        p.category_name,
        COUNT(oi.product_id) AS purchase_count,
        -- Using Window Function to rank categories by purchase frequency per customer
        ROW_NUMBER() OVER(PARTITION BY o.customer_id ORDER BY COUNT(oi.product_id) DESC) AS rank_num
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    JOIN products p
        ON oi.product_id = p.product_id
    WHERE o.order_status = 'COMPLETED'
    GROUP BY o.customer_id, p.category_name
),

top_category AS (
    SELECT
        customer_id,
        category_name AS favorite_category
    FROM product_preferences
    WHERE rank_num = 1
),

-- ==========================================
-- STEP 5: Build the Final Data Mart & Churn Logic
-- ==========================================
final_customer_mart AS (
    SELECT
        c.customer_id,
        c.location_city,
        c.signup_date,

        COALESCE(r.frequency_total_orders, 0) AS total_orders,
        COALESCE(r.monetary_total_spend, 0) AS total_spend,
        r.last_order_date,

        -- Join the new favorite category feature
        COALESCE(tc.favorite_category, 'UNKNOWN') AS favorite_category,

        CASE
            WHEN r.last_order_date IS NULL THEN 999
            ELSE CURRENT_DATE - r.last_order_date
        END AS days_since_last_order,

        CASE
            WHEN r.last_order_date IS NULL OR (CURRENT_DATE - r.last_order_date) > 90 THEN 1
            ELSE 0
            END AS is_churned
    
    FROM customers c
    LEFT JOIN rfm_metrics r
        ON c.customer_id = r.customer_id
    LEFT JOIN top_category tc
        ON c.customer_id = tc.customer_id
)

SELECT * FROM final_customer_mart