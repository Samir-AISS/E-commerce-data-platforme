SELECT
    review_id,
    order_id,
    review_score::INTEGER                          AS review_score,
    CASE WHEN review_score >= 4 THEN 'positive'
         WHEN review_score = 3  THEN 'neutral'
         ELSE 'negative'
    END                                            AS sentiment,
    review_creation_date::TIMESTAMP                AS review_creation_date,
    review_answer_timestamp::TIMESTAMP             AS review_answer_timestamp,
    ingested_at
FROM {{ source('raw', 'reviews') }}
WHERE review_id IS NOT NULL
  AND review_score BETWEEN 1 AND 5