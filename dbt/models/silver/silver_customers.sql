WITH customers AS (
    SELECT * FROM {{ ref('bronze_customers') }}
),
order_stats AS (
    SELECT
        customer_id,
        COUNT(*)                                    AS total_orders,
        SUM(total_revenue)                          AS total_spent,
        AVG(total_revenue)                          AS avg_order_value,
        MIN(order_purchase_timestamp)               AS first_order_date,
        MAX(order_purchase_timestamp)               AS last_order_date,
        AVG(review_score)                           AS avg_review_score,
        SUM(is_delivered)                           AS delivered_orders,
        SUM(is_canceled)                            AS canceled_orders
    FROM {{ ref('silver_orders') }}
    GROUP BY customer_id
)
SELECT
    c.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    COALESCE(o.total_orders, 0)                    AS total_orders,
    COALESCE(o.total_spent, 0)                     AS total_spent,
    COALESCE(o.avg_order_value, 0)                 AS avg_order_value,
    o.first_order_date,
    o.last_order_date,
    COALESCE(o.avg_review_score, 0)                AS avg_review_score,
    COALESCE(o.delivered_orders, 0)                AS delivered_orders,
    COALESCE(o.canceled_orders, 0)                 AS canceled_orders,
    CASE
        WHEN o.total_orders IS NULL                THEN 'never_purchased'
        WHEN o.last_order_date >= NOW() - INTERVAL '180 days' THEN 'active'
        WHEN o.last_order_date >= NOW() - INTERVAL '365 days' THEN 'at_risk'
        ELSE 'churned'
    END AS customer_status
FROM customers c
LEFT JOIN order_stats o USING (customer_id)