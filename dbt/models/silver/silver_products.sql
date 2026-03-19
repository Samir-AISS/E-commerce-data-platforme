WITH products AS (
    SELECT * FROM {{ ref('bronze_products') }}
),
sales AS (
    SELECT
        oi.product_id,
        COUNT(DISTINCT oi.order_id)                AS total_orders,
        SUM(oi.price)                              AS total_revenue,
        AVG(oi.price)                              AS avg_price,
        SUM(oi.freight_value)                      AS total_freight,
        AVG(r.review_score)                        AS avg_review_score
    FROM {{ ref('bronze_order_items') }} oi
    LEFT JOIN {{ ref('silver_orders') }} o  USING (order_id)
    LEFT JOIN {{ ref('bronze_reviews') }} r USING (order_id)
    WHERE o.order_status = 'delivered'
    GROUP BY oi.product_id
)
SELECT
    p.product_id,
    p.category_english,
    p.category_portuguese,
    p.product_photos_qty,
    p.product_weight_g,
    COALESCE(s.total_orders, 0)                    AS total_orders,
    COALESCE(s.total_revenue, 0)                   AS total_revenue,
    COALESCE(s.avg_price, 0)                       AS avg_price,
    COALESCE(s.total_freight, 0)                   AS total_freight,
    COALESCE(s.avg_review_score, 0)                AS avg_review_score
FROM products p
LEFT JOIN sales s USING (product_id)