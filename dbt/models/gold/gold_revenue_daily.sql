SELECT
    order_date,
    order_year,
    order_month_num,
    order_dow,
    COUNT(order_id)                                AS n_orders,
    COUNT(DISTINCT customer_id)                    AS n_customers,
    SUM(total_revenue)                             AS gross_revenue,
    SUM(freight_revenue)                           AS freight_revenue,
    AVG(total_revenue)                             AS avg_order_value,
    SUM(n_items)                                   AS total_items,
    AVG(review_score)                              AS avg_review_score,
    SUM(is_delivered)                              AS delivered_orders,
    SUM(is_canceled)                               AS canceled_orders,
    ROUND(SUM(is_canceled)::DECIMAL
          / NULLIF(COUNT(*), 0) * 100, 2)          AS cancel_rate_pct,
    ROUND(SUM(CASE WHEN is_late_delivery THEN 1 ELSE 0 END)::DECIMAL
          / NULLIF(SUM(is_delivered), 0) * 100, 2) AS late_delivery_pct
FROM {{ ref('silver_orders') }}
WHERE order_date IS NOT NULL
GROUP BY 1,2,3,4
ORDER BY 1