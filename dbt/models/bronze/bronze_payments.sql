SELECT
    order_id,
    payment_sequential,
    LOWER(TRIM(payment_type))                      AS payment_type,
    payment_installments,
    payment_value::DECIMAL(10,2)                   AS payment_value,
    ingested_at
FROM {{ source('raw', 'payments') }}
WHERE order_id IS NOT NULL
  AND payment_value >= 0