-- ==========================================
-- GOLD LAYER: Daily Revenue & Sales Performance
-- PURPOSE: Provide time-series aggregations for financial dashboarding.
-- ==========================================

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

daily_metrics AS (
    SELECT
        o.order_date,
        COUNT(DISTINCT o.order_id) AS total_successful_orders,
        SUM(oi.quantity) AS total_items_sold,
        SUM(oi.quantity * oi.unit_price) AS total_daily_revenue
    FROM orders o
    JOIN order_items oi
        ON o.order_id = oi.order_id
    WHERE o.order_status = 'COMPLETED'
    GROUP BY o.order_date
)

SELECT
    order_date,
    total_successful_orders,
    total_items_sold,
    total_daily_revenue,
    -- Calculate Average Order Value (AOV) safely to prevent division by zero
    CASE
        WHEN total_successful_orders = 0 THEN 0
        ELSE ROUND(total_daily_revenue / total_successful_orders, 2)
    END AS average_order_value
FROM daily_metrics
ORDER BY order_date DESC