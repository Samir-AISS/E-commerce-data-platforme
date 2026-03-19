WITH orders AS (
    SELECT * FROM {{ ref('bronze_orders') }}
),
payments_agg AS (
    SELECT
        order_id,
        SUM(payment_value)              AS total_payment,
        MAX(payment_installments)       AS max_installments,
        STRING_AGG(DISTINCT payment_type, ', ') AS payment_types
    FROM {{ ref('bronze_payments') }}
    GROUP BY order_id
),
items_agg AS (
    SELECT
        order_id,
        COUNT(*)                        AS n_items,
        SUM(price)                      AS items_revenue,
        SUM(freight_value)              AS freight_revenue,
        SUM(total_item_value)           AS total_revenue
    FROM {{ ref('bronze_order_items') }}
    GROUP BY order_id
),
reviews AS (
    SELECT order_id, review_score, sentiment
    FROM {{ ref('bronze_reviews') }}
)
SELECT
    o.order_id,
    o.customer_id,
    o.order_status,
    o.order_purchase_timestamp,
    DATE_TRUNC('day',   o.order_purchase_timestamp)::DATE AS order_date,
    DATE_TRUNC('week',  o.order_purchase_timestamp)::DATE AS order_week,
    DATE_TRUNC('month', o.order_purchase_timestamp)::DATE AS order_month,
    EXTRACT(YEAR  FROM o.order_purchase_timestamp)::INT   AS order_year,
    EXTRACT(MONTH FROM o.order_purchase_timestamp)::INT   AS order_month_num,
    EXTRACT(DOW   FROM o.order_purchase_timestamp)::INT   AS order_dow,
    o.is_late_delivery,
    COALESCE(i.n_items, 0)             AS n_items,
    COALESCE(i.items_revenue, 0)       AS items_revenue,
    COALESCE(i.freight_revenue, 0)     AS freight_revenue,
    COALESCE(i.total_revenue, 0)       AS total_revenue,
    COALESCE(p.total_payment, 0)       AS total_payment,
    p.payment_types,
    p.max_installments,
    r.review_score,
    r.sentiment,
    CASE WHEN o.order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
    CASE WHEN o.order_status = 'canceled'  THEN 1 ELSE 0 END AS is_canceled
FROM orders o
LEFT JOIN items_agg    i USING (order_id)
LEFT JOIN payments_agg p USING (order_id)
LEFT JOIN reviews      r USING (order_id)