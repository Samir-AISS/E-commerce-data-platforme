SELECT
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    INITCAP(TRIM(customer_city))                   AS customer_city,
    UPPER(TRIM(customer_state))                    AS customer_state,
    ingested_at
FROM {{ source('raw', 'customers') }}
WHERE customer_id IS NOT NULL