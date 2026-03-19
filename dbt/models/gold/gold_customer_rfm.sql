-- Segmentation RFM sur les données Olist
WITH rfm AS (
    SELECT
        customer_id,
        CURRENT_DATE - MAX(order_date)             AS recency_days,
        COUNT(*)                                   AS frequency,
        SUM(total_revenue)                         AS monetary
    FROM {{ ref('silver_orders') }}
    WHERE order_status = 'delivered'
    GROUP BY customer_id
),
rfm_scores AS (
    SELECT *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary)          AS m_score
    FROM rfm
)
SELECT
    c.customer_id,
    c.customer_state,
    c.customer_status,
    c.total_spent,
    c.avg_review_score,
    r.recency_days,
    r.frequency,
    r.monetary,
    r.r_score,
    r.f_score,
    r.m_score,
    ROUND((r.r_score + r.f_score + r.m_score)::DECIMAL / 3, 2) AS rfm_score,
    CASE
        WHEN r.r_score >= 4 AND r.f_score >= 4 THEN 'Champions'
        WHEN r.r_score >= 3 AND r.f_score >= 3 THEN 'Loyal'
        WHEN r.r_score >= 4 AND r.f_score <= 2 THEN 'New Customers'
        WHEN r.r_score >= 3 AND r.m_score >= 4 THEN 'Potential Loyalists'
        WHEN r.r_score <= 2 AND r.f_score >= 3 THEN 'At Risk'
        WHEN r.r_score <= 2 AND r.f_score <= 2 THEN 'Lost'
        ELSE 'Needs Attention'
    END AS rfm_segment
FROM {{ ref('silver_customers') }} c
LEFT JOIN rfm_scores r USING (customer_id)