"""
validate_data.py
----------------
Validation des données Olist dans PostgreSQL.

Usage:
    python ingestion/validate_data.py
"""

import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://ecommerce:ecommerce123@localhost:5432/ecommerce_db")

CHECKS = [
    # Orders
    ("orders — no null order_id",
     "SELECT COUNT(*) FROM raw.orders WHERE order_id IS NULL", "==", 0),
    ("orders — no null customer_id",
     "SELECT COUNT(*) FROM raw.orders WHERE customer_id IS NULL", "==", 0),
    ("orders — valid status",
     "SELECT COUNT(*) FROM raw.orders WHERE order_status NOT IN ('delivered','shipped','canceled','invoiced','processing','created','approved','unavailable')", "==", 0),
    ("orders — minimum rows",
     "SELECT COUNT(*) FROM raw.orders", ">=", 90000),

    # Customers
    ("customers — no null customer_id",
     "SELECT COUNT(*) FROM raw.customers WHERE customer_id IS NULL", "==", 0),
    ("customers — no null state",
     "SELECT COUNT(*) FROM raw.customers WHERE customer_state IS NULL", "==", 0),

    # Products
    ("products — no null product_id",
     "SELECT COUNT(*) FROM raw.products WHERE product_id IS NULL", "==", 0),

    # Payments
    ("payments — positive values",
     "SELECT COUNT(*) FROM raw.payments WHERE payment_value < 0", "==", 0),
    ("payments — valid types",
     "SELECT COUNT(*) FROM raw.payments WHERE payment_type NOT IN ('credit_card','boleto','voucher','debit_card','not_defined')", "==", 0),

    # Reviews
    ("reviews — score between 1 and 5",
     "SELECT COUNT(*) FROM raw.reviews WHERE review_score NOT BETWEEN 1 AND 5", "==", 0),

    # Referential integrity
    ("order_items — valid order_id",
     "SELECT COUNT(*) FROM raw.order_items oi LEFT JOIN raw.orders o USING(order_id) WHERE o.order_id IS NULL", "==", 0),
    ("payments — valid order_id",
     "SELECT COUNT(*) FROM raw.payments p LEFT JOIN raw.orders o USING(order_id) WHERE o.order_id IS NULL", "==", 0),
]

def validate():
    engine = sqlalchemy.create_engine(DB_URL)

    print("=" * 55)
    print("  Data Validation — Olist Dataset")
    print("=" * 55)

    passed = 0
    failed = []

    for name, query, op, expected in CHECKS:
        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query)).scalar()
        ok = (result == expected if op == "==" else result >= expected)
        status = "Ok" if ok else "❌"
        print(f"  {status} {name:<45} → {result}")
        if ok:
            passed += 1
        else:
            failed.append(name)

    print(f"\n  {passed}/{len(CHECKS)} checks passed")
    if failed:
        print("  Failed checks:")
        for f in failed:
            print(f"    ❌ {f}")
        raise ValueError(f"Validation failed: {len(failed)} check(s)")
    print(" top: All validations passed")

if __name__ == "__main__":
    validate()