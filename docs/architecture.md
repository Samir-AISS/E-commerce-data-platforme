# Architecture & Technical Decisions

## Overview

This project implements a modern data engineering stack to process the Olist Brazilian E-Commerce dataset. The architecture follows the **Medallion Architecture** pattern (Bronze → Silver → Gold) and is designed to be reproducible, testable, and deployable to the cloud.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  SOURCE LAYER                                                │
│  8 CSV files from Olist (Kaggle)                            │
│  orders · customers · products · sellers                     │
│  payments · reviews · order_items · category_translation    │
└────────────────────────┬────────────────────────────────────┘
                         │
              Python + SQLAlchemy + pandas
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STORAGE LAYER                                               │
│  PostgreSQL 15 (local Docker) + Supabase (cloud)            │
│  Schema: raw                                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
              Apache Airflow 2.8 (daily at 6h UTC)
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│  TRANSFORMATION LAYER — dbt 1.7                              │
│                                                              │
│  Bronze (views)     Silver (tables)     Gold (tables)        │
│  ─────────────      ──────────────      ──────────────       │
│  Cleaning           Enrichment          KPIs                 │
│  Type casting       Business logic      RFM segments         │
│  Deduplication      Cross-table joins   Rankings             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  SERVING LAYER                                               │
│  Streamlit Cloud + Supabase                                  │
│  Fallback: precomputed.pkl                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Technical Decisions

### 1. Medallion Architecture (Bronze/Silver/Gold)

**Decision**: Use a 3-layer data model instead of a single flat table.

**Rationale**:
- **Bronze** — raw data preserved as-is, only cleaning and casting. Easy to re-process if logic changes.
- **Silver** — business logic applied (joins, derived columns, status flags). Reusable across multiple gold models.
- **Gold** — aggregated KPIs optimized for dashboard queries. Minimal query time at read.

**Trade-off**: More complexity than a single table, but much easier to debug and maintain.

---

### 2. dbt for Transformations

**Decision**: Use dbt instead of raw SQL scripts or pandas.

**Rationale**:
- SQL-based transformations are version-controlled and testable
- `{{ ref() }}` and `{{ source() }}` create a DAG of dependencies
- dbt auto-generates documentation and lineage graphs
- Supports incremental models for large datasets

**Trade-off**: Learning curve for dbt syntax, but industry standard for data transformation.

---

### 3. PostgreSQL over other databases

**Decision**: Use PostgreSQL (local + Supabase) instead of DuckDB or BigQuery.

**Rationale**:
- Olist dataset (~500K rows) fits comfortably in PostgreSQL
- Supabase provides free hosted PostgreSQL with a REST API
- Well-supported by dbt, Airflow, and SQLAlchemy
- Production-realistic choice for mid-size data

**Trade-off**: Would use BigQuery/Snowflake for 100M+ rows, but overkill here.

---

### 4. Docker Compose for Local Environment

**Decision**: Containerize PostgreSQL and Airflow with Docker Compose.

**Rationale**:
- Reproducible environment across machines
- Single command to start the full stack: `docker-compose up -d`
- Mirrors production infrastructure patterns

**Trade-off**: Requires Docker installation, higher resource usage than running services natively.

---

### 5. Precomputed PKL for Dashboard

**Decision**: Pre-compute all dashboard queries and save to a `.pkl` file.

**Rationale**:
- Streamlit Cloud has no persistent database connection by default
- Avoids cold-start latency from querying Supabase on every page load
- Dashboard loads instantly from local file
- Supabase used as fallback when pkl is not available

**Trade-off**: Data is not real-time — requires re-running `export_to_pkl.py` and pushing to refresh.

---

### 6. Airflow for Orchestration

**Decision**: Use Apache Airflow instead of Prefect or Cron.

**Rationale**:
- Industry standard for data pipeline orchestration
- Visual DAG editor shows pipeline dependencies clearly
- Built-in retry logic, alerting, and monitoring
- Runs inside Docker — no external service needed

**Trade-off**: Heavy resource usage (~1GB RAM). For a lighter alternative, Prefect Cloud was used in the MMM project.

---

## Data Flow

```
1. Download Olist CSVs from Kaggle
        ↓
2. load_to_postgres.py
   → TRUNCATE + reload raw tables
        ↓
3. dbt run
   → bronze views (cleaning)
   → silver tables (enrichment)
   → gold tables (KPIs)
        ↓
4. validate_data.py
   → 12 checks: nulls, ranges, referential integrity
        ↓
5. export_to_pkl.py
   → Query gold/silver tables
   → Save to results/precomputed.pkl
        ↓
6. git push
   → Streamlit Cloud auto-deploys
   → Dashboard reads pkl
```

---

## Infrastructure

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| Database | PostgreSQL 15 | 5432 | Local data storage |
| Orchestration | Airflow Webserver | 8080 | Pipeline UI |
| Orchestration | Airflow Scheduler | — | DAG execution |
| Dashboard | Streamlit | 8501 | Local development |
| Cloud DB | Supabase | 6543 | Production database |
| Cloud Dashboard | Streamlit Cloud | 443 | Public dashboard |
