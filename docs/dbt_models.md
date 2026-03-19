# dbt Models Documentation

## Overview

The transformation layer uses **dbt 1.7** with a 3-layer Medallion Architecture. All models are written in SQL and reference each other using `{{ ref() }}` and `{{ source() }}` macros.

```
raw (PostgreSQL) → bronze (views) → silver (tables) → gold (tables)
```

---

## Project Configuration

**`dbt_project.yml`**
```yaml
name: ecommerce
profile: ecommerce

models:
  ecommerce:
    bronze:
      +schema: bronze
      +materialized: view
    silver:
      +schema: silver
      +materialized: table
    gold:
      +schema: gold
      +materialized: table
```

**Materialization strategy:**
- **Bronze → views**: No storage cost, always reflects latest raw data
- **Silver → tables**: Materialized for query performance (joins are expensive)
- **Gold → tables**: Materialized for instant dashboard queries

---

## Source Declarations

All raw tables are declared in `models/bronze/sources.yml`:

```yaml
sources:
  - name: raw
    schema: raw
    tables:
      - name: orders
      - name: order_items
      - name: customers
      - name: products
      - name: sellers
      - name: payments
      - name: reviews
      - name: category_translation
```

---

## Bronze Layer

### `bronze_orders`
**Materialization**: view  
**Source**: `{{ source('raw', 'orders') }}`

Transformations applied:
- `order_status` → lowercased and trimmed
- All timestamp columns → cast to `TIMESTAMP`
- `is_late_delivery` → derived boolean (`delivered_date > estimated_date`)
- Filters: `order_id IS NOT NULL AND customer_id IS NOT NULL`

---

### `bronze_order_items`
**Materialization**: view  
**Source**: `{{ source('raw', 'order_items') }}`

Transformations applied:
- `price`, `freight_value` → cast to `DECIMAL(10,2)`
- `total_item_value` → derived as `price + freight_value`
- Filters: `order_id IS NOT NULL AND price >= 0`

---

### `bronze_customers`
**Materialization**: view  
**Source**: `{{ source('raw', 'customers') }}`

Transformations applied:
- `customer_city` → `INITCAP(TRIM(...))`
- `customer_state` → `UPPER(TRIM(...))`
- Filters: `customer_id IS NOT NULL`

---

### `bronze_products`
**Materialization**: view  
**Sources**: `{{ source('raw', 'products') }}` + `{{ source('raw', 'category_translation') }}`

Transformations applied:
- LEFT JOIN with `category_translation` to get English category names
- `category_english` → `COALESCE(english_name, portuguese_name, 'unknown')`
- Filters: `product_id IS NOT NULL`

---

### `bronze_payments`
**Materialization**: view  
**Source**: `{{ source('raw', 'payments') }}`

Transformations applied:
- `payment_type` → lowercased and trimmed
- `payment_value` → cast to `DECIMAL(10,2)`
- Filters: `order_id IS NOT NULL AND payment_value >= 0`

---

### `bronze_reviews`
**Materialization**: view  
**Source**: `{{ source('raw', 'reviews') }}`

Transformations applied:
- `review_score` → cast to `INTEGER`
- `sentiment` → derived: `positive` (≥4), `neutral` (3), `negative` (≤2)
- Filters: `review_id IS NOT NULL AND review_score BETWEEN 1 AND 5`

---

## Silver Layer

### `silver_orders`
**Materialization**: table  
**Dependencies**: `bronze_orders`, `bronze_order_items`, `bronze_payments`, `bronze_reviews`

Key transformations:
```sql
-- Date dimensions
DATE_TRUNC('day',   order_purchase_timestamp) AS order_date,
DATE_TRUNC('week',  order_purchase_timestamp) AS order_week,
DATE_TRUNC('month', order_purchase_timestamp) AS order_month,
EXTRACT(YEAR  FROM order_purchase_timestamp)  AS order_year,
EXTRACT(MONTH FROM order_purchase_timestamp)  AS order_month_num,
EXTRACT(DOW   FROM order_purchase_timestamp)  AS order_dow

-- Revenue aggregation (from order_items)
SUM(price)           AS items_revenue,
SUM(freight_value)   AS freight_revenue,
SUM(total_item_value) AS total_revenue,

-- Payment aggregation
SUM(payment_value)   AS total_payment,
STRING_AGG(payment_type, ', ') AS payment_types,

-- Review join
review_score, sentiment,

-- Status flags
CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END AS is_delivered,
CASE WHEN order_status = 'canceled'  THEN 1 ELSE 0 END AS is_canceled
```

---

### `silver_customers`
**Materialization**: table  
**Dependencies**: `bronze_customers`, `silver_orders`

Key transformations:
```sql
-- Order statistics per customer
COUNT(*) AS total_orders,
SUM(total_revenue) AS total_spent,
AVG(total_revenue) AS avg_order_value,
MIN(order_purchase_timestamp) AS first_order_date,
MAX(order_purchase_timestamp) AS last_order_date,

-- Customer lifecycle status
CASE
    WHEN last_order_date >= NOW() - INTERVAL '180 days' THEN 'active'
    WHEN last_order_date >= NOW() - INTERVAL '365 days' THEN 'at_risk'
    ELSE 'churned'
END AS customer_status
```

---

### `silver_products`
**Materialization**: table  
**Dependencies**: `bronze_products`, `bronze_order_items`, `silver_orders`, `bronze_reviews`

Key transformations:
```sql
-- Sales statistics (delivered orders only)
COUNT(DISTINCT order_id) AS total_orders,
SUM(price)               AS total_revenue,
AVG(price)               AS avg_price,
AVG(review_score)        AS avg_review_score
```

---

## Gold Layer

### `gold_revenue_daily`
**Materialization**: table  
**Dependencies**: `silver_orders`

Aggregates daily business KPIs:
```sql
COUNT(order_id)     AS n_orders,
SUM(total_revenue)  AS gross_revenue,
AVG(total_revenue)  AS avg_order_value,
ROUND(SUM(is_canceled) / COUNT(*) * 100, 2) AS cancel_rate_pct,
ROUND(SUM(is_late) / SUM(is_delivered) * 100, 2) AS late_delivery_pct
```

---

### `gold_customer_rfm`
**Materialization**: table  
**Dependencies**: `silver_orders`, `silver_customers`

RFM segmentation using NTILE(5) scoring:
```sql
-- RFM scores (1-5, 5 = best)
NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
NTILE(5) OVER (ORDER BY frequency)         AS f_score,
NTILE(5) OVER (ORDER BY monetary)          AS m_score,

-- Segments
CASE
    WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
    WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
    WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
    WHEN r_score >= 3 AND m_score >= 4 THEN 'Potential Loyalists'
    WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
    WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
    ELSE 'Needs Attention'
END AS rfm_segment
```

---

### `gold_product_performance`
**Materialization**: table  
**Dependencies**: `silver_products`

Product rankings:
```sql
RANK() OVER (ORDER BY total_revenue DESC)   AS revenue_rank,
RANK() OVER (ORDER BY total_orders DESC)    AS orders_rank,
RANK() OVER (PARTITION BY category_english
             ORDER BY total_revenue DESC)   AS category_rank,
total_revenue / SUM(total_revenue) OVER ()  AS revenue_share_pct
```

---

## DAG Lineage

```
raw.orders ──────────────────────────────────────────┐
raw.order_items ──── bronze_order_items ──────────────┤
raw.customers ────── bronze_customers ─────────────────┤
raw.products ─────── bronze_products ──────────────────┤──→ silver_orders ──→ gold_revenue_daily
raw.payments ─────── bronze_payments ──────────────────┤──→ silver_customers ──→ gold_customer_rfm
raw.reviews ──────── bronze_reviews ───────────────────┤──→ silver_products ──→ gold_product_performance
raw.category_translation ──────────────────────────────┘
```

---

## Running dbt

```bash
# All models
cd dbt && dbt run --profiles-dir .

# Specific layer
dbt run --select bronze --profiles-dir .
dbt run --select silver --profiles-dir .
dbt run --select gold   --profiles-dir .

# Tests
dbt test --profiles-dir .

# Documentation
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .
```
