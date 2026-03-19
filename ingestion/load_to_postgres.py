"""
load_to_postgres.py
-------------------
Charge les CSV Olist dans PostgreSQL (schéma raw).

Usage:
    python ingestion/load_to_postgres.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_URL  = os.getenv("DATABASE_URL", "postgresql://ecommerce:ecommerce123@localhost:5432/ecommerce_db")
RAW_DIR = Path(__file__).parents[1] / "data" / "raw"

# Mapping fichiers Olist → tables PostgreSQL
TABLES = {
    "olist_orders_dataset":                ("raw", "orders"),
    "olist_order_items_dataset":           ("raw", "order_items"),
    "olist_customers_dataset":             ("raw", "customers"),
    "olist_products_dataset":              ("raw", "products"),
    "olist_sellers_dataset":               ("raw", "sellers"),
    "olist_order_payments_dataset":        ("raw", "payments"),
    "olist_order_reviews_dataset":         ("raw", "reviews"),
    "product_category_name_translation":   ("raw", "category_translation"),
}

def load():
    engine = create_engine(DB_URL)
    print("=" * 50)
    print("  Olist → PostgreSQL Ingestion")
    print("=" * 50)

    for filename, (schema, table) in TABLES.items():
        path = RAW_DIR / f"{filename}.csv"
        if not path.exists():
            print(f"  ⚠️  {filename}.csv not found — skipping")
            continue

        df = pd.read_csv(path, low_memory=False)

        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {schema}.{table}"))
            conn.commit()

        df.to_sql(table, engine, schema=schema,
                  if_exists="append", index=False, chunksize=5000)
        print(f"  ok : {schema}.{table:<25} {len(df):>7,} rows")

    print("\n Ingestion terminée")

if __name__ == "__main__":
    load()