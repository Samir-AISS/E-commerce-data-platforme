SELECT
    p.product_id,
    COALESCE(t.product_category_name_english,
             p.product_category_name,
             'unknown')                            AS category_english,
    p.product_category_name                        AS category_portuguese,
    p.product_photos_qty,
    p.product_weight_g,
    p.ingested_at
FROM {{ source('raw', 'products') }} p
LEFT JOIN {{ source('raw', 'category_translation') }} t
    ON p.product_category_name = t.product_category_name
WHERE p.product_id IS NOT NULL