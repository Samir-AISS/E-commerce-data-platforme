"""
migrate_to_supabase.py
----------------------
Migre les données depuis PostgreSQL local vers Supabase.

Usage:
    python scripts/migrate_to_supabase.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time

load_dotenv()

LOCAL_URL = os.getenv("DATABASE_URL",
    "postgresql://ecommerce:ecommerce123@localhost:5432/ecommerce_db")

SUPABASE_URL = os.getenv("SUPABASE_URL",
    "postgresql://postgres.sffuarkudbvekidgwutb:Olist-samir@aws-1-eu-central-1.pooler.supabase.com:6543/postgres")

TABLES = [
    "orders",
    "order_items",
    "customers",
    "products",
    "sellers",
    "payments",
    "reviews",
    "category_translation",
]

def init_supabase(remote):
    """Crée les schémas et tables sur Supabase."""
    print("Initialisation des schémas Supabase...")
    with open("docker/init.sql") as f:
        sql = f.read()
    with remote.connect() as conn:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception:
                    pass
        conn.commit()
    print("  Schémas créés\n")

def migrate():
    local  = create_engine(LOCAL_URL)
    remote = create_engine(SUPABASE_URL)

    print("=" * 55)
    print("  Migration PostgreSQL local → Supabase")
    print("=" * 55)

    # Init schémas
    init_supabase(remote)

    total_rows = 0
    t_total = time.time()

    for table in TABLES:
        t0 = time.time()
        print(f"  Migrating raw.{table}...")

        # Lecture locale
        try:
            df = pd.read_sql(f"SELECT * FROM raw.{table}", local)
        except Exception as e:
            print(f"  ⚠️  {table} not found locally — skipping ({e})")
            continue

        # Truncate remote
        with remote.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE raw.{table}"))
            conn.commit()

        # Insertion par chunks
        df.to_sql(table, remote, schema="raw",
                  if_exists="append", index=False, chunksize=2000)

        duration = time.time() - t0
        total_rows += len(df)
        print(f"  ✅ raw.{table:<25} {len(df):>7,} rows  ({duration:.1f}s)")

    print(f"\n{'=' * 55}")
    print(f"   Migration terminée")
    print(f"  Total : {total_rows:,} rows en {time.time()-t_total:.0f}s")
    print(f"{'=' * 55}")
    print("\nProchaine étape :")
    print("  Ajoute SUPABASE_URL dans les secrets Streamlit Cloud")

if __name__ == "__main__":
    migrate()