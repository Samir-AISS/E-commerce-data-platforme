![Pipeline](https://github.com/Samir-AISS/E-commerce-data-platforme/actions/workflows/Pipeline.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python&logoColor=white)
![dbt](https://img.shields.io/badge/dbt-1.7-orange?logo=dbt&logoColor=white)
![Airflow](https://img.shields.io/badge/Airflow-2.8-017CEE?logo=apacheairflow&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-live-ff4b4b?logo=streamlit&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-cloud-3ECF8E?logo=supabase&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

# E-Commerce Data Platform — Olist

A **production-grade data engineering pipeline** built on the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) — 100,000 real orders from 2016 to 2018. Covers end-to-end data engineering: ingestion, transformation, quality validation, cloud deployment, and BI dashboarding.

**[Live Dashboard →](https://e-commerce-data-platforme-xprnlwq65rgewbymr6nn7h.streamlit.app/)** · [Architecture](docs/Architecture.md) · [Data Dictionary](docs/Data_dictionary.md) · [Pipeline Guide](docs/Pipeline.md) · [dbt Models](docs/Dbt_models.md)
---

## Key Results

| Metric | Value |
|--------|-------|
| Orders processed | 98,816 |
| Total Revenue | R$15.81M |
| Avg Order Value | R$159 |
| Avg Review Score | 4.10 / 5 |
| dbt Models | 12 (bronze/silver/gold) |
| Validation Checks | 12 automated tests |
| Late Delivery Rate | ~8% |
| Cancel Rate | <1% |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                          │
│         Olist CSV Files (8 tables, ~500K rows)              │
└────────────────────────┬────────────────────────────────────┘
                         │ Python + SQLAlchemy
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL / Supabase                      │
│                      schema: raw                             │
│  orders · customers · products · sellers                     │
│  payments · reviews · order_items · geolocation             │
└────────────────────────┬────────────────────────────────────┘
                         │ dbt (Apache Airflow DAG)
                         ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Bronze    │→ │    Silver    │→ │     Gold     │
│   (views)    │  │   (tables)   │  │   (tables)   │
│  Cleaning    │  │  Enrichment  │  │  KPIs & RFM  │
└──────────────┘  └──────────────┘  └──────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Streamlit Dashboard (Supabase + pkl)            │
│   Overview · Revenue · Customers · Products · Reviews        │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Ingestion | Python · SQLAlchemy · pandas | Load CSV → PostgreSQL |
| Storage | PostgreSQL 15 · Supabase | Raw + transformed data |
| Transformation | dbt 1.7 | Bronze → Silver → Gold models |
| Orchestration | Apache Airflow 2.8 | Daily pipeline scheduling |
| Quality | Custom validation (12 checks) | Data integrity tests |
| Infrastructure | Docker Compose | Local environment |
| Dashboard | Streamlit · Plotly | Interactive BI |
| CI/CD | GitHub Actions | Automated testing |

---

## Project Structure

```
ecommerce-data-platform/
├── .github/workflows/
│   └── pipeline.yml          # CI/CD — GitHub Actions
├── dags/
│   └── ecommerce_pipeline.py # Airflow DAG
├── dashboard/
│   └── App.py                # Streamlit dashboard
├── data/
│   ├── raw/                  # Olist CSV files (gitignored)
│   └── processed/
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── bronze/           # 6 cleaning models
│       ├── silver/           # 3 enrichment models
│       └── gold/             # 3 KPI models
├── docker/
│   ├── init.sql              # PostgreSQL schema init
│   └── Dockerfile.dashboard
├── docs/
│   ├── architecture.md
│   ├── data_dictionary.md
│   ├── dbt_models.md
│   └── pipeline.md
├── ingestion/
│   ├── load_to_postgres.py   # CSV → PostgreSQL
│   └── validate_data.py      # 12 quality checks
├── results/
│   └── precomputed.pkl       # Pre-computed dashboard data
├── scripts/
│   ├── export_to_pkl.py      # Export DB → pkl
│   └── migrate_to_supabase.py # Local → Supabase migration
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Samir-AISS/E-commerce-data-platforme.git
cd E-commerce-data-platforme

# 2. Environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Download Olist data from Kaggle → data/raw/

# 4. Start infrastructure
docker-compose up -d

# 5. Ingest data
python ingestion/load_to_postgres.py

# 6. Run dbt transformations
cd dbt && dbt run --profiles-dir .

# 7. Validate
cd .. && python ingestion/validate_data.py

# 8. Launch dashboard
streamlit run dashboard/App.py
# → http://localhost:8501
```

Full setup guide → [docs/pipeline.md](docs/pipeline.md)

---

## Dashboard Pages

| Page | Description |
|------|-------------|
| Overview | Total orders, revenue, AOV, review score, cancel rate |
| Revenue | Daily/monthly trends, day-of-week patterns |
| Customers | RFM segmentation, state distribution |
| Products | Category performance, review scores |
| Reviews | Sentiment analysis, score distribution |

---

## Dataset

- **Source** : [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Kaggle)
- **Period** : September 2016 – October 2018
- **Volume** : ~100,000 orders · 8 tables · ~500,000 rows total
- **Anonymized** real commercial data from a Brazilian marketplace

---

## Contact

**Samir EL AISSAOUY** — Data Engineer / Data Analyst

[![LinkedIn](https://img.shields.io/badge/LinkedIn-samir--el--aissaouy-blue?logo=linkedin)](https://www.linkedin.com/in/samir-el-aissaouy)
[![Email](https://img.shields.io/badge/Email-elaissaouy.samir12%40gmail.com-red?logo=gmail)](mailto:elaissaouy.samir12@gmail.com)

---
