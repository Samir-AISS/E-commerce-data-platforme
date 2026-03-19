![Pipeline](https://github.com/Samir-AISS/ecommerce-data-platform/actions/workflows/pipeline.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![dbt](https://img.shields.io/badge/dbt-1.7-orange)
![Airflow](https://img.shields.io/badge/Airflow-2.8-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

# E-Commerce Data Platform — Olist

Production-grade data engineering pipeline built on the **Olist Brazilian E-Commerce dataset** (100K real orders, 2016–2018). Covers ingestion, transformation, quality validation, and BI dashboarding.

**[Live Dashboard](http://localhost:8501)** · [Methodology](#architecture) · [Dataset](#dataset)

---

## Results

| Metric | Value |
|--------|-------|
| Orders processed | 98,816 |
| Total Revenue | R$15.81M |
| Avg Order Value | R$159 |
| Avg Review Score | 4.10 / 5 |
| dbt Models | 12 (bronze/silver/gold) |
| Validation Checks | 12 automated tests |

---

## Architecture

```
Olist CSV (8 files)
        ↓
Ingestion (Python + SQLAlchemy)
        ↓
PostgreSQL — schema raw
        ↓  Airflow DAG (daily 6h)
dbt Bronze → Silver → Gold
        ↓
Validation (12 checks)
        ↓
Streamlit Dashboard
```

---

## Stack

| Layer | Tool |
|-------|------|
| Orchestration | Apache Airflow 2.8 |
| Transformation | dbt 1.7 (bronze/silver/gold) |
| Storage | PostgreSQL 15 |
| Quality | Custom validation (12 checks) |
| Infrastructure | Docker Compose |
| Dashboard | Streamlit |
| CI/CD | GitHub Actions |

---

## dbt Models

| Layer | Models | Description |
|-------|--------|-------------|
| Bronze | orders, customers, products, order_items, payments, reviews | Cleaning, casting, deduplication |
| Silver | orders, customers, products | Enrichment, joins, business logic |
| Gold | revenue_daily, customer_rfm, product_performance | KPIs, RFM segmentation, rankings |

---

## Quick Start

```bash
git clone https://github.com/Samir-AISS/ecommerce-data-platform.git
cd ecommerce-data-platform

# Start infrastructure
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Load Olist data (download from Kaggle first)
python ingestion/load_to_postgres.py

# Run dbt transformations
cd dbt && dbt run --profiles-dir .

# Validate data
cd .. && python ingestion/validate_data.py

# Dashboard → http://localhost:8501
```

---

## Dataset

- **Source** : [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- **100,000** real orders · 2016–2018
- **8 tables** : orders, customers, products, sellers, payments, reviews, order_items, geolocation
- **Anonymized** real commercial data

---

## KPIs Tracked

- Daily/monthly revenue & AOV
- Customer RFM segmentation (Champions, Loyal, At Risk, Lost)
- Product performance & category rankings
- Review score distribution & sentiment
- Late delivery rate & cancel rate

---

## Contact

**Samir EL AISSAOUY** — Data Engineer / Analyst

[LinkedIn](https://www.linkedin.com/in/samir-el-aissaouy) · Elaissaouy.samir12@gmail.com · Île-de-France