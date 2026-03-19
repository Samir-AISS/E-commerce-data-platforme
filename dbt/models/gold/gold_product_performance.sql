SELECT
    product_id,
    category_english,
    avg_price,
    total_orders,
    total_revenue,
    total_freight,
    avg_review_score,
    RANK() OVER (ORDER BY total_revenue DESC)       AS revenue_rank,
    RANK() OVER (ORDER BY total_orders DESC)        AS orders_rank,
    RANK() OVER (PARTITION BY category_english
                 ORDER BY total_revenue DESC)       AS category_rank,
    ROUND(total_revenue
          / NULLIF(SUM(total_revenue) OVER (), 0) * 100, 3) AS revenue_share_pct
FROM {{ ref('silver_products') }}
ORDER BY total_revenue DESC