-- ==========================================
-- GOLD LAYER: Product Category Performance & Churn Correlation
-- PURPOSE: Analyze which products generate the most revenue and observe 
--          the churn rate of customers buying these products.
-- ==========================================

WITH products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers_rfm AS (
    SELECT * FROM {{ ref('mart_customer_rfm') }}
),

product_sales AS (
    SELECT
        p.product_id,
        p.product_name,
        p.category_name,
        COUNT(DISTINCT o.order_id) AS times_purchased,
        SUM(oi.quantity) AS total_quantity_sold,
        SUM(oi.quantity * oi.unit_price) AS total_revenue_generated,

        -- Count how many distinct customers bought this product
        COUNT(DISTINCT o.customer_id) AS unique_buyers,

        -- Sum the churned customers who bought this product
        SUM(c.is_churned) AS churned_buyers
    FROM products p
    JOIN order_items oi
        ON p.product_id = oi.product_id
    JOIN orders o
        ON oi.order_id = o.order_id
    JOIN customers_rfm c
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'COMPLETED'
    GROUP BY p.product_id, p.product_name, p.category_name
)

SELECT
    product_id,
    product_name,
    category_name,
    times_purchased,
    total_quantity_sold,
    total_revenue_generated,
    unique_buyers,
    churned_buyers,

    -- Calculate the churn rate for this specific product
    CASE
        WHEN unique_buyers = 0 THEN 0
        ELSE ROUND((churned_buyers::DECIMAL / unique_buyers) * 100, 2)
    END AS product_churn_rate_percentage
FROM product_sales
ORDER BY total_revenue_generated DESC