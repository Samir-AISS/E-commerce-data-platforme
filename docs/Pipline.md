# Pipeline Guide

Step-by-step guide to run the full pipeline from scratch.

---

## Prerequisites

- Python 3.11+
- Docker Desktop
- Git
- Kaggle account (to download dataset)

---

## 1. Clone & Setup

```bash
git clone https://github.com/Samir-AISS/E-commerce-data-platforme.git
cd E-commerce-data-platforme

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Download Olist Dataset

1. Go to [kaggle.com/datasets/olistbr/brazilian-ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
2. Click **Download** → extract the zip
3. Place all CSV files in `data/raw/`:

```
data/raw/
├── olist_customers_dataset.csv
├── olist_order_items_dataset.csv
├── olist_order_payments_dataset.csv
├── olist_order_reviews_dataset.csv
├── olist_orders_dataset.csv
├── olist_products_dataset.csv
├── olist_sellers_dataset.csv
└── product_category_name_translation.csv
```

---

## 3. Start Infrastructure

```bash
docker-compose up -d
```

Wait ~60 seconds for all services to start, then verify:

```bash
docker-compose ps
```

Expected output:
```
ecommerce_postgres      Up
airflow_webserver       Up
airflow_scheduler       Up
ecommerce_dashboard     Up
```

Services:
- **PostgreSQL** → `localhost:5432`
- **Airflow UI** → `http://localhost:8080` (admin/admin)
- **Dashboard** → `http://localhost:8501`

---

## 4. Ingest Data

```bash
python ingestion/load_to_postgres.py
```

Expected output:
```
✅ raw.orders                     99,441 rows
✅ raw.order_items               112,650 rows
✅ raw.customers                  99,441 rows
✅ raw.products                   32,951 rows
✅ raw.sellers                     3,095 rows
✅ raw.payments                  103,886 rows
✅ raw.reviews                    99,224 rows
✅ raw.category_translation           71 rows
```

---

## 5. Run dbt Transformations

```bash
cd dbt
dbt run --profiles-dir .
```

Expected output:
```
12 of 12 OK — PASS=12 WARN=0 ERROR=0
Finished in 2.32 seconds
```

Run dbt tests:
```bash
dbt test --profiles-dir .
cd ..
```

---

## 6. Validate Data

```bash
python ingestion/validate_data.py
```

Expected output:
```
12/12 checks passed
✅ All validations passed
```

---

## 7. Launch Dashboard Locally

```bash
streamlit run dashboard/App.py
```

Open → `http://localhost:8501`

---

## 8. Migrate to Supabase (Cloud)

Create a free project on [supabase.com](https://supabase.com), then:

```bash
# Set your Supabase URL in .env
echo 'SUPABASE_URL=postgresql://postgres.[PROJECT]:[PASSWORD]@aws-x-eu-x.pooler.supabase.com:6543/postgres' >> .env

# Run migration
python scripts/migrate_to_supabase.py

# Run dbt against Supabase
# Update dbt/profiles.yml with Supabase credentials
cd dbt && dbt run --profiles-dir .
```

---

## 9. Export Precomputed Results

```bash
python scripts/export_to_pkl.py
```

This queries gold/silver tables and saves `results/precomputed.pkl` for fast dashboard loading.

---

## 10. Deploy to Streamlit Cloud

1. Push everything to GitHub:
```bash
git add .
git commit -m "deploy: update precomputed results"
git push
```

2. Go to [share.streamlit.io](https://share.streamlit.io)
3. New app → select repo → `dashboard/App.py`
4. Add secret in Advanced settings:
```toml
DATABASE_URL = "your-supabase-url"
```
5. Deploy

---

## Airflow DAG

The pipeline runs automatically every day at 6h UTC via Airflow.

Access the UI at `http://localhost:8080` (admin/admin):

```
ingest → dbt_bronze → dbt_silver → dbt_gold → dbt_test → validate
```

To trigger manually:
- Go to DAGs → `olist_ecommerce_pipeline` → ▶ Trigger

---

## Troubleshooting

**Docker containers not starting:**
```bash
docker-compose down -v
docker-compose up -d
```

**dbt schema prefix issue (bronze_ prefix):**
```bash
# Run from inside dbt/ directory
cd dbt && dbt run --profiles-dir .
```

**Streamlit shows DB errors:**
- Verify `results/precomputed.pkl` exists and is committed to GitHub
- Check Supabase credentials in Streamlit Cloud secrets

**products table column error:**
```bash
# Recreate with correct column names (Olist typo)
docker exec -i ecommerce_postgres psql -U ecommerce -d ecommerce_db -c "
DROP TABLE IF EXISTS raw.products;
CREATE TABLE raw.products (
    product_id VARCHAR(50),
    product_category_name VARCHAR(100),
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    ...
);"
```