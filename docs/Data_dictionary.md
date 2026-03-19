# data Dictionary

## Source Layer — `raw` schema

All tables are loaded as-is from Olist CSV files. No transformations applied.

---

### `raw.orders`

Core table — one row per order.

| Column | Type | Description |
|--------|------|-------------|
| order_id | VARCHAR(50) | Unique order identifier (PK) |
| customer_id | VARCHAR(50) | Customer identifier → `raw.customers` |
| order_status | VARCHAR(20) | Status: `delivered`, `shipped`, `canceled`, `invoiced`, `processing`, `created`, `approved`, `unavailable` |
| order_purchase_timestamp | TIMESTAMP | When the order was placed |
| order_approved_at | TIMESTAMP | When payment was approved |
| order_delivered_carrier_date | TIMESTAMP | When handed to carrier |
| order_delivered_customer_date | TIMESTAMP | When delivered to customer |
| order_estimated_delivery_date | TIMESTAMP | Estimated delivery date |

---

### `raw.order_items`

One row per item per order.

| Column | Type | Description |
|--------|------|-------------|
| order_id | VARCHAR(50) | → `raw.orders` |
| order_item_id | INTEGER | Item sequence within order (1, 2, 3...) |
| product_id | VARCHAR(50) | → `raw.products` |
| seller_id | VARCHAR(50) | → `raw.sellers` |
| shipping_limit_date | TIMESTAMP | Deadline for seller to ship |
| price | DECIMAL(10,2) | Item price in BRL |
| freight_value | DECIMAL(10,2) | Shipping cost in BRL |

---

### `raw.customers`

One row per customer-order pair (not unique customers).

| Column | Type | Description |
|--------|------|-------------|
| customer_id | VARCHAR(50) | Order-level customer ID (PK) |
| customer_unique_id | VARCHAR(50) | True customer ID (can have multiple orders) |
| customer_zip_code_prefix | VARCHAR(10) | ZIP code |
| customer_city | VARCHAR(100) | City name |
| customer_state | VARCHAR(5) | Brazilian state code (SP, RJ, MG...) |

---

### `raw.products`

One row per product.

| Column | Type | Description |
|--------|------|-------------|
| product_id | VARCHAR(50) | Unique product identifier (PK) |
| product_category_name | VARCHAR(100) | Category in Portuguese |
| product_name_lenght | INTEGER | Character count of product name (typo in source) |
| product_description_lenght | INTEGER | Character count of description (typo in source) |
| product_photos_qty | INTEGER | Number of product photos |
| product_weight_g | DECIMAL | Weight in grams |
| product_length_cm | DECIMAL | Length in cm |
| product_height_cm | DECIMAL | Height in cm |
| product_width_cm | DECIMAL | Width in cm |

> **Note**: `product_name_lenght` and `product_description_lenght` are intentional typos from the original Olist dataset — preserved as-is in raw schema.

---

### `raw.sellers`

| Column | Type | Description |
|--------|------|-------------|
| seller_id | VARCHAR(50) | Unique seller identifier (PK) |
| seller_zip_code_prefix | VARCHAR(10) | ZIP code |
| seller_city | VARCHAR(100) | City |
| seller_state | VARCHAR(5) | State code |

---

### `raw.payments`

One row per payment installment per order.

| Column | Type | Description |
|--------|------|-------------|
| order_id | VARCHAR(50) | → `raw.orders` |
| payment_sequential | INTEGER | Payment sequence (1 = first payment) |
| payment_type | VARCHAR(30) | Method: `credit_card`, `boleto`, `voucher`, `debit_card` |
| payment_installments | INTEGER | Number of installments (credit card) |
| payment_value | DECIMAL(10,2) | Amount paid in BRL |

---

### `raw.reviews`

Customer satisfaction surveys sent after delivery.

| Column | Type | Description |
|--------|------|-------------|
| review_id | VARCHAR(50) | Unique review ID (PK) |
| order_id | VARCHAR(50) | → `raw.orders` |
| review_score | INTEGER | Score 1–5 (5 = best) |
| review_comment_title | TEXT | Optional title |
| review_comment_message | TEXT | Optional message |
| review_creation_date | TIMESTAMP | When review was created |
| review_answer_timestamp | TIMESTAMP | When seller answered |

---

### `raw.category_translation`

Maps Portuguese category names to English.

| Column | Type | Description |
|--------|------|-------------|
| product_category_name | VARCHAR(100) | Portuguese name |
| product_category_name_english | VARCHAR(100) | English translation |

---

## Bronze Layer — `public_bronze` schema

Views on top of raw tables. Applies cleaning, type casting, and basic derived columns.

### Key derived columns

| Table | Column | Logic |
|-------|--------|-------|
| bronze_orders | `is_late_delivery` | `delivered_date > estimated_date` |
| bronze_order_items | `total_item_value` | `price + freight_value` |
| bronze_customers | `customer_city` | `INITCAP(TRIM(...))` |
| bronze_products | `category_english` | Join with category_translation |
| bronze_reviews | `sentiment` | `positive` (≥4), `neutral` (3), `negative` (≤2) |

---

## Silver Layer — `public_silver` schema

Enriched tables with business logic and cross-table joins.

### `silver.silver_orders`

| Column | Description |
|--------|-------------|
| order_date | Truncated to day |
| order_week / order_month | Truncated to week/month |
| order_year / order_month_num / order_dow | Extracted date parts |
| total_revenue | Sum of all item values |
| freight_revenue | Sum of freight costs |
| n_items | Number of items in order |
| review_score / sentiment | From bronze_reviews |
| is_delivered / is_canceled | Binary flags |

### `silver.silver_customers`

| Column | Description |
|--------|-------------|
| total_orders | Count of all orders |
| total_spent | Sum of total_revenue |
| avg_order_value | Average per order |
| first/last_order_date | Min/max order dates |
| customer_status | `active`, `at_risk`, `churned`, `never_purchased` |

### `silver.silver_products`

| Column | Description |
|--------|-------------|
| total_orders | Count of delivered orders |
| total_revenue | Sum of item revenue |
| avg_price | Average selling price |
| avg_review_score | Average review from customers |

---

## Gold Layer — `public_gold` schema

Aggregated KPI tables optimized for dashboard queries.

### `gold.gold_revenue_daily`

Daily revenue aggregations.

| Column | Description |
|--------|-------------|
| order_date | Date |
| n_orders / n_customers | Counts |
| gross_revenue / freight_revenue | Revenue splits |
| avg_order_value | AOV |
| cancel_rate_pct | % canceled orders |
| late_delivery_pct | % late deliveries |

### `gold.gold_customer_rfm`

RFM segmentation for all customers.

| Column | Description |
|--------|-------------|
| recency_days | Days since last order |
| frequency | Number of orders |
| monetary | Total spend |
| r_score / f_score / m_score | RFM quintile scores (1–5) |
| rfm_segment | Champions, Loyal, New Customers, Potential Loyalists, At Risk, Lost, Needs Attention |

### `gold.gold_product_performance`

Product rankings and metrics.

| Column | Description |
|--------|-------------|
| revenue_rank | Overall revenue ranking |
| orders_rank | Overall orders ranking |
| category_rank | Ranking within category |
| revenue_share_pct | % of total revenue |
