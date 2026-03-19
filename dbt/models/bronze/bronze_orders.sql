SELECT
    order_id,
    customer_id,
    LOWER(TRIM(order_status))                      AS order_status,
    order_purchase_timestamp::TIMESTAMP            AS order_purchase_timestamp,
    order_approved_at::TIMESTAMP                   AS order_approved_at,
    order_delivered_carrier_date::TIMESTAMP        AS order_delivered_carrier_date,
    order_delivered_customer_date::TIMESTAMP       AS order_delivered_customer_date,
    order_estimated_delivery_date::TIMESTAMP       AS order_estimated_delivery_date,
    CASE WHEN order_delivered_customer_date IS NOT NULL
         AND order_estimated_delivery_date IS NOT NULL
         THEN order_delivered_customer_date::TIMESTAMP
              > order_estimated_delivery_date::TIMESTAMP
         ELSE NULL
    END                                            AS is_late_delivery,
    ingested_at
FROM {{ source('raw', 'orders') }}
WHERE order_id IS NOT NULL
  AND customer_id IS NOT NULL