import os, pickle, pandas as pd
from sqlalchemy import create_engine
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_URL   = os.getenv("DATABASE_URL", "postgresql://postgres.sffuarkudbvekidgwutb:Olist-samir@aws-1-eu-central-1.pooler.supabase.com:6543/postgres")
OUT_PATH = Path("results/precomputed.pkl")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(DB_URL)

# Détecter les schémas
from sqlalchemy import inspect, text
schemas = inspect(engine).get_schema_names()
silver = "public_silver"
gold   = "public_gold"
bronze = "public_bronze"

print(f"Schémas détectés: silver={silver}, gold={gold}, bronze={bronze}")

data = {}
queries = {
    "kpi_overview": f"SELECT COUNT(DISTINCT order_id) AS n_orders, COUNT(DISTINCT customer_id) AS n_customers, SUM(total_revenue) AS total_revenue, AVG(total_revenue) AS avg_order_value, AVG(review_score) AS avg_review, ROUND(SUM(is_canceled)::DECIMAL / COUNT(*) * 100, 2) AS cancel_rate FROM {silver}.silver_orders WHERE order_status != 'canceled'",
    "revenue_monthly": f"SELECT order_month AS month, SUM(total_revenue) AS revenue, COUNT(*) AS orders FROM {silver}.silver_orders WHERE order_status = 'delivered' GROUP BY 1 ORDER BY 1",
    "orders_by_status": f"SELECT order_status, COUNT(*) AS n FROM {silver}.silver_orders GROUP BY 1 ORDER BY 2 DESC",
    "revenue_daily": f"SELECT * FROM {gold}.gold_revenue_daily ORDER BY order_date",
    "rfm_segments": f"SELECT rfm_segment, COUNT(*) AS n, AVG(monetary) AS avg_spent, AVG(frequency) AS avg_orders, AVG(recency_days) AS avg_recency FROM {gold}.gold_customer_rfm WHERE rfm_segment IS NOT NULL GROUP BY 1 ORDER BY 2 DESC",
    "customers_by_state": f"SELECT customer_state, COUNT(*) AS n_customers, SUM(total_spent) AS total_revenue FROM {silver}.silver_customers GROUP BY 1 ORDER BY 3 DESC LIMIT 10",
    "product_performance": f"SELECT category_english, COUNT(*) AS n_products, SUM(total_orders) AS total_orders, SUM(total_revenue) AS total_revenue, AVG(avg_review_score) AS avg_review FROM {gold}.gold_product_performance WHERE category_english IS NOT NULL GROUP BY 1 ORDER BY 4 DESC LIMIT 15",
    "reviews_dist": f"SELECT review_score, sentiment, COUNT(*) AS n FROM {bronze}.bronze_reviews GROUP BY 1,2 ORDER BY 1",
    "reviews_by_category": f"SELECT p.category_english, AVG(r.review_score) AS avg_score, COUNT(*) AS n FROM {bronze}.bronze_reviews r JOIN {silver}.silver_orders o USING(order_id) JOIN {bronze}.bronze_order_items oi USING(order_id) JOIN {bronze}.bronze_products p USING(product_id) WHERE p.category_english IS NOT NULL GROUP BY 1 HAVING COUNT(*) > 100 ORDER BY 2 DESC LIMIT 12",
}

for key, sql in queries.items():
    df = pd.read_sql(sql, engine)
    data[key] = df
    print(f"  ok {key} — {len(df)} rows")

with open(OUT_PATH, "wb") as f:
    pickle.dump(data, f)

print(f"\n Sauvegardé → {OUT_PATH} ({OUT_PATH.stat().st_size/1e6:.1f} MB)")
