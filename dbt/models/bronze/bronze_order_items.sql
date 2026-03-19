SELECT
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date::TIMESTAMP                 AS shipping_limit_date,
    price::DECIMAL(10,2)                           AS price,
    freight_value::DECIMAL(10,2)                   AS freight_value,
    (price + freight_value)::DECIMAL(10,2)         AS total_item_value,
    ingested_at
FROM {{ source('raw', 'order_items') }}
WHERE order_id IS NOT NULL
  AND price >= 0