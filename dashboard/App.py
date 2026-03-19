"""
app.py — Olist E-Commerce Analytics Dashboard
Streamlit Cloud ready — charge depuis Supabase ou precomputed.pkl
"""

import os
import pickle
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Olist Analytics", layout="wide",
                   initial_sidebar_state="expanded")

COLORS = {
    "bg": "#0D0F14", "surface": "#13161E", "surface2": "#1A1E2A",
    "border": "#252A38", "accent": "#4F7EFF", "accent2": "#00D4AA",
    "accent3": "#FF6B6B", "text": "#E8EAF0", "text_muted": "#6B7280",
    "cat": ["#4F7EFF","#00D4AA","#FFB547","#FF6B6B","#A78BFA",
            "#F472B6","#34D399","#FB923C","#60A5FA","#FBBF24"],
}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
html,body,[class*="css"]{{font-family:'DM Sans',sans-serif;background:{COLORS['bg']};color:{COLORS['text']};}}
.stApp{{background:{COLORS['bg']};}}
[data-testid="stSidebar"]{{background:{COLORS['surface']};border-right:1px solid {COLORS['border']};}}
[data-testid="stSidebar"] *{{color:{COLORS['text']} !important;}}
.block-container{{padding-top:1.5rem;max-width:1400px;}}
.kpi{{background:{COLORS['surface']};border:1px solid {COLORS['border']};border-radius:10px;padding:18px 22px;}}
.kpi-label{{font-size:10px;font-weight:600;letter-spacing:.09em;text-transform:uppercase;color:{COLORS['text_muted']};margin-bottom:7px;}}
.kpi-value{{font-size:26px;font-weight:600;font-family:'DM Mono',monospace;color:{COLORS['text']};}}
.kpi-sub{{font-size:11px;margin-top:5px;font-family:'DM Mono',monospace;}}
.pos{{color:{COLORS['accent2']};}} .neg{{color:{COLORS['accent3']};}} .neu{{color:{COLORS['text_muted']};}}
.sec{{font-size:11px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:{COLORS['text_muted']};border-bottom:1px solid {COLORS['border']};padding-bottom:9px;margin-bottom:18px;}}
.page-title{{font-size:22px;font-weight:600;margin-bottom:4px;}}
.page-sub{{font-size:13px;color:{COLORS['text_muted']};margin-bottom:26px;}}
.badge{{display:inline-block;padding:3px 10px;border-radius:20px;font-size:10px;font-weight:600;letter-spacing:.06em;}}
#MainMenu,footer,header{{visibility:hidden;}}
[data-testid="collapsedControl"]{{display:none !important;}}
[data-testid="stSidebarCollapseButton"]{{display:none !important;}}
</style>""", unsafe_allow_html=True)

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=COLORS["text"], size=12),
    margin=dict(l=16,r=16,t=36,b=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=COLORS["border"], borderwidth=1),
    hoverlabel=dict(bgcolor=COLORS["surface2"], bordercolor=COLORS["border"], font_color=COLORS["text"]),
)

def apply_layout(fig, title="", height=300):
    fig.update_layout(**PLOTLY_BASE, height=height,
        title=dict(text=title, font_size=12, font_color=COLORS["text_muted"], x=0))
    fig.update_xaxes(gridcolor=COLORS["border"], linecolor=COLORS["border"])
    fig.update_yaxes(gridcolor=COLORS["border"], linecolor=COLORS["border"])
    return fig

def kpi(label, value, sub=None, cls="neu"):
    sub_html = f'<div class="kpi-sub {cls}">{sub}</div>' if sub else ""
    return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div>{sub_html}</div>'

def sec(t): st.markdown(f'<div class="sec">{t}</div>', unsafe_allow_html=True)

def fmt(v):
    if v >= 1e6: return f"R${v/1e6:.2f}M"
    if v >= 1e3: return f"R${v/1e3:.0f}K"
    return f"R${v:.0f}"

# ── DATA LOADING ──────────────────────────────────────────────────────────────
@st.cache_data
def load_precomputed():
    """Charge depuis precomputed.pkl — cherche dans plusieurs emplacements"""
    candidates = [
        Path(__file__).parent / "precomputed.pkl",
        Path(__file__).parents[1] / "results" / "precomputed.pkl",
        Path("results/precomputed.pkl"),
        Path("precomputed.pkl"),
    ]
    for pkl_path in candidates:
        if pkl_path.exists():
            with open(pkl_path, "rb") as f:
                return pickle.load(f), "precomputed"
    return None, None

@st.cache_resource
def get_engine():
    """Connexion Supabase ou PostgreSQL local"""
    try:
        from sqlalchemy import create_engine
        db_url = os.getenv("DATABASE_URL", "postgresql://ecommerce:ecommerce123@localhost:5432/ecommerce_db")
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(__import__('sqlalchemy').text("SELECT 1"))
        return engine
    except:
        return None

def get_data(key):
    """Retourne les données depuis pkl ou DB"""
    data, source = load_precomputed()
    if data and key in data:
        return data[key]

    engine = get_engine()
    if not engine:
        return pd.DataFrame()

    # Détecter le bon schéma
    from sqlalchemy import text, inspect
    insp = inspect(engine)
    schemas = insp.get_schema_names()
    silver = "public_silver" if "public_silver" in schemas else ("bronze_silver" if "bronze_silver" in schemas else "silver")
    gold   = "public_gold"   if "public_gold"   in schemas else ("bronze_gold" if "bronze_gold" in schemas else "gold")
    bronze = "public_bronze" if "public_bronze" in schemas else ("bronze_bronze" if "bronze_bronze" in schemas else "bronze")

    queries = {
        "kpi_overview": f"""
            SELECT COUNT(DISTINCT order_id) AS n_orders,
                   COUNT(DISTINCT customer_id) AS n_customers,
                   SUM(total_revenue) AS total_revenue,
                   AVG(total_revenue) AS avg_order_value,
                   AVG(review_score) AS avg_review,
                   ROUND(SUM(is_canceled)::DECIMAL / COUNT(*) * 100, 2) AS cancel_rate
            FROM {silver}.silver_orders WHERE order_status != 'canceled'
        """,
        "revenue_monthly": f"""
            SELECT order_month AS month, SUM(total_revenue) AS revenue, COUNT(*) AS orders
            FROM {silver}.silver_orders WHERE order_status = 'delivered'
            GROUP BY 1 ORDER BY 1
        """,
        "orders_by_status": f"""
            SELECT order_status, COUNT(*) AS n
            FROM {silver}.silver_orders GROUP BY 1 ORDER BY 2 DESC
        """,
        "revenue_daily": f"SELECT * FROM {gold}.gold_revenue_daily ORDER BY order_date",
        "rfm_segments": f"""
            SELECT rfm_segment, COUNT(*) AS n,
                   AVG(monetary) AS avg_spent, AVG(frequency) AS avg_orders,
                   AVG(recency_days) AS avg_recency
            FROM {gold}.gold_customer_rfm WHERE rfm_segment IS NOT NULL
            GROUP BY 1 ORDER BY 2 DESC
        """,
        "customers_by_state": f"""
            SELECT customer_state, COUNT(*) AS n_customers, SUM(total_spent) AS total_revenue
            FROM {silver}.silver_customers GROUP BY 1 ORDER BY 3 DESC LIMIT 10
        """,
        "product_performance": f"""
            SELECT category_english, COUNT(*) AS n_products,
                   SUM(total_orders) AS total_orders, SUM(total_revenue) AS total_revenue,
                   AVG(avg_review_score) AS avg_review
            FROM {gold}.gold_product_performance WHERE category_english IS NOT NULL
            GROUP BY 1 ORDER BY 4 DESC LIMIT 15
        """,
        "reviews_dist": f"""
            SELECT review_score, sentiment, COUNT(*) AS n
            FROM {bronze}.bronze_reviews GROUP BY 1,2 ORDER BY 1
        """,
        "reviews_by_category": f"""
            SELECT p.category_english, AVG(r.review_score) AS avg_score, COUNT(*) AS n
            FROM {bronze}.bronze_reviews r
            JOIN {silver}.silver_orders o USING(order_id)
            JOIN {bronze}.bronze_order_items oi USING(order_id)
            JOIN {bronze}.bronze_products p USING(product_id)
            WHERE p.category_english IS NOT NULL
            GROUP BY 1 HAVING COUNT(*) > 100
            ORDER BY 2 DESC LIMIT 12
        """,
    }

    try:
        return pd.read_sql(queries[key], engine)
    except:
        return pd.DataFrame()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
data, source = load_precomputed()
engine = get_engine()
mode = "precomputed" if data else ("live" if engine else "offline")

with st.sidebar:
    st.markdown(f"""
    <div style="padding:6px 0 22px">
      <div style="font-size:17px;font-weight:700;color:{COLORS['text']}">Olist Analytics</div>
      <div style="font-size:11px;color:{COLORS['text_muted']};margin-top:3px">E-Commerce · Brazil · 2016–2018</div>
    </div>""", unsafe_allow_html=True)

    page = st.selectbox("", ["Overview","Revenue","Customers","Products","Reviews"],
                        label_visibility="collapsed")

    st.markdown(f"<hr style='border-color:{COLORS['border']};margin:14px 0'>", unsafe_allow_html=True)

    mode_color = COLORS["accent2"] if mode == "precomputed" else (COLORS["accent"] if mode == "live" else COLORS["accent3"])
    st.markdown(f"""
    <div style="font-size:11px;color:{COLORS['text_muted']};line-height:1.9">
      <span style="color:{mode_color}">● {mode.capitalize()}</span><br>
      ~100K orders · 2016–2018<br>
      Bronze → Silver → Gold<br>
      dbt · Airflow · Docker
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════
# PAGE 1 — OVERVIEW
# ════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.markdown('<div class="page-title">Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Olist E-Commerce — Key Metrics</div>', unsafe_allow_html=True)

    df_kpi = get_data("kpi_overview")
    if not df_kpi.empty:
        r = df_kpi.iloc[0]
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: st.markdown(kpi("Total Orders",    f"{int(r.n_orders):,}",        "all time"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Total Revenue",   fmt(r.total_revenue),           "gross", "pos"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Avg Order Value", fmt(r.avg_order_value),         "per order"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Avg Review",      f"{r.avg_review:.2f} / 5",     "customer score"), unsafe_allow_html=True)
        with c5: st.markdown(kpi("Cancel Rate",     f"{r.cancel_rate:.1f}%",       "of orders", "neg"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    cl, cr = st.columns([2,1])

    with cl:
        sec("Monthly Revenue")
        df_rev = get_data("revenue_monthly")
        if not df_rev.empty:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_rev["month"], y=df_rev["revenue"],
                fill="tozeroy", fillcolor="rgba(79,126,255,0.07)",
                line=dict(color=COLORS["accent"], width=2),
                hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
            ))
            apply_layout(fig, height=260)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    with cr:
        sec("Orders by Status")
        df_status = get_data("orders_by_status")
        if not df_status.empty:
            fig = go.Figure(go.Bar(
                x=df_status["n"], y=df_status["order_status"], orientation="h",
                marker_color=COLORS["accent"],
                hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>",
            ))
            apply_layout(fig, height=260)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ════════════════════════════════════════════════════════════════════════
# PAGE 2 — REVENUE
# ════════════════════════════════════════════════════════════════════════
elif page == "Revenue":
    st.markdown('<div class="page-title">Revenue Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Daily & Monthly Revenue Breakdown</div>', unsafe_allow_html=True)

    df = get_data("revenue_daily")
    if not df.empty:
        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(kpi("Total Revenue",   fmt(df.gross_revenue.sum()),    "all time", "pos"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Total Orders",    f"{df.n_orders.sum():,.0f}",    "delivered"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Avg Order Value", fmt(df.avg_order_value.mean()), "per order"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Late Delivery",   f"{df.late_delivery_pct.mean():.1f}%", "of deliveries","neg"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        sec("Revenue Over Time")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["order_date"], y=df["gross_revenue"],
            fill="tozeroy", fillcolor="rgba(79,126,255,0.07)",
            line=dict(color=COLORS["accent"], width=1.5),
            hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
        ))
        apply_layout(fig, height=250)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        cl, cr = st.columns(2)
        dow_labels = {0:"Sun",1:"Mon",2:"Tue",3:"Wed",4:"Thu",5:"Fri",6:"Sat"}
        month_labels = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"May",6:"Jun",
                       7:"Jul",8:"Aug",9:"Sep",10:"Oct",11:"Nov",12:"Dec"}
        with cl:
            sec("Revenue by Day of Week")
            df_dow = df.groupby("order_dow")["gross_revenue"].sum().reset_index()
            df_dow["day"] = df_dow["order_dow"].map(dow_labels)
            fig = go.Figure(go.Bar(
                x=df_dow["day"], y=df_dow["gross_revenue"],
                marker_color=COLORS["accent"],
                hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
            ))
            apply_layout(fig, height=250)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        with cr:
            sec("Revenue by Month")
            df_mon = df.groupby("order_month_num")["gross_revenue"].sum().reset_index()
            df_mon["month"] = df_mon["order_month_num"].map(month_labels)
            fig = go.Figure(go.Bar(
                x=df_mon["month"], y=df_mon["gross_revenue"],
                marker_color=COLORS["accent2"],
                hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
            ))
            apply_layout(fig, height=250)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ════════════════════════════════════════════════════════════════════════
# PAGE 3 — CUSTOMERS
# ════════════════════════════════════════════════════════════════════════
elif page == "Customers":
    st.markdown('<div class="page-title">Customer Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">RFM Segmentation · State Distribution</div>', unsafe_allow_html=True)

    df_rfm = get_data("rfm_segments")
    if not df_rfm.empty:
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(kpi("Total Customers", f"{df_rfm.n.sum():,}", "unique"), unsafe_allow_html=True)
        champ = df_rfm[df_rfm.rfm_segment=="Champions"]["n"].sum() if "Champions" in df_rfm.rfm_segment.values else 0
        risk  = df_rfm[df_rfm.rfm_segment=="At Risk"]["n"].sum()   if "At Risk"   in df_rfm.rfm_segment.values else 0
        with c2: st.markdown(kpi("Champions", f"{champ:,}", "top segment", "pos"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("At Risk",   f"{risk:,}",  "need attention", "neg"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns(2)
        with cl:
            sec("RFM Segments")
            fig = go.Figure(go.Bar(
                x=df_rfm["n"], y=df_rfm["rfm_segment"], orientation="h",
                marker_color=COLORS["cat"][:len(df_rfm)],
                text=df_rfm["n"].apply(lambda x: f"{x:,}"),
                textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x:,} customers<extra></extra>",
            ))
            apply_layout(fig, height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        with cr:
            sec("Avg Spend by Segment")
            fig = go.Figure(go.Bar(
                x=df_rfm["rfm_segment"], y=df_rfm["avg_spent"],
                marker_color=COLORS["cat"][:len(df_rfm)],
                hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
            ))
            apply_layout(fig, height=300)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    sec("Top 10 States by Revenue")
    df_state = get_data("customers_by_state")
    if not df_state.empty:
        fig = go.Figure(go.Bar(
            x=df_state["customer_state"], y=df_state["total_revenue"],
            marker_color=COLORS["accent"],
            hovertemplate="<b>%{x}</b><br>R$%{y:,.0f}<extra></extra>",
        ))
        apply_layout(fig, height=250)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ════════════════════════════════════════════════════════════════════════
# PAGE 4 — PRODUCTS
# ════════════════════════════════════════════════════════════════════════
elif page == "Products":
    st.markdown('<div class="page-title">Product Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Top Categories · Revenue Rankings</div>', unsafe_allow_html=True)

    df_cat = get_data("product_performance")
    if not df_cat.empty:
        c1,c2,c3 = st.columns(3)
        with c1: st.markdown(kpi("Categories", f"{len(df_cat)}", "top 15"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Top Category", df_cat.iloc[0]["category_english"], "by revenue", "pos"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Best Rated",
            df_cat.loc[df_cat.avg_review.idxmax(),"category_english"],
            f"{df_cat.avg_review.max():.2f}/5", "pos"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns([3,2])
        with cl:
            sec("Revenue by Category")
            fig = go.Figure(go.Bar(
                x=df_cat["total_revenue"], y=df_cat["category_english"],
                orientation="h", marker_color=COLORS["accent"],
                hovertemplate="<b>%{y}</b><br>R$%{x:,.0f}<extra></extra>",
            ))
            apply_layout(fig, height=420)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        with cr:
            sec("Orders vs Review Score")
            fig = go.Figure(go.Scatter(
                x=df_cat["total_orders"], y=df_cat["avg_review"],
                mode="markers+text",
                text=df_cat["category_english"].str[:12],
                textposition="top center",
                textfont=dict(size=9, color=COLORS["text_muted"]),
                marker=dict(
                    size=df_cat["total_revenue"]/df_cat["total_revenue"].max()*30+8,
                    color=COLORS["accent"], opacity=0.7),
                hovertemplate="<b>%{text}</b><br>Orders: %{x:,}<br>Review: %{y:.2f}<extra></extra>",
            ))
            apply_layout(fig, height=420)
            fig.update_xaxes(title="Total Orders")
            fig.update_yaxes(title="Avg Review Score")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

# ════════════════════════════════════════════════════════════════════════
# PAGE 5 — REVIEWS
# ════════════════════════════════════════════════════════════════════════
elif page == "Reviews":
    st.markdown('<div class="page-title">Reviews & Satisfaction</div>', unsafe_allow_html=True)
    st.markdown('<div class="page-sub">Customer Sentiment · Score Distribution</div>', unsafe_allow_html=True)

    df_rev = get_data("reviews_dist")
    if not df_rev.empty:
        total = df_rev["n"].sum()
        pos = df_rev[df_rev["sentiment"]=="positive"]["n"].sum()
        neg = df_rev[df_rev["sentiment"]=="negative"]["n"].sum()
        neu = df_rev[df_rev["sentiment"]=="neutral"]["n"].sum()

        c1,c2,c3,c4 = st.columns(4)
        with c1: st.markdown(kpi("Total Reviews", f"{total:,}", "all orders"), unsafe_allow_html=True)
        with c2: st.markdown(kpi("Positive", f"{pos/total*100:.1f}%", "score 4-5", "pos"), unsafe_allow_html=True)
        with c3: st.markdown(kpi("Neutral",  f"{neu/total*100:.1f}%", "score 3",   "neu"), unsafe_allow_html=True)
        with c4: st.markdown(kpi("Negative", f"{neg/total*100:.1f}%", "score 1-2", "neg"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cl, cr = st.columns(2)
        with cl:
            sec("Score Distribution")
            colors_map = {1:COLORS["accent3"],2:"#FF8C6B",3:COLORS["text_muted"],
                         4:COLORS["accent2"],5:"#00FFB3"}
            fig = go.Figure(go.Bar(
                x=df_rev["review_score"].astype(str), y=df_rev["n"],
                marker_color=[colors_map[s] for s in df_rev["review_score"]],
                hovertemplate="<b>Score %{x}</b><br>%{y:,} reviews<extra></extra>",
            ))
            apply_layout(fig, height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

        with cr:
            sec("Sentiment Breakdown")
            fig = go.Figure(go.Pie(
                labels=["Positive","Neutral","Negative"], values=[pos, neu, neg],
                hole=0.6,
                marker_colors=[COLORS["accent2"], COLORS["text_muted"], COLORS["accent3"]],
                textinfo="percent+label", textfont_size=11,
            ))
            apply_layout(fig, height=280)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})

    sec("Review Score by Category")
    df_cat_rev = get_data("reviews_by_category")
    if not df_cat_rev.empty:
        fig = go.Figure(go.Bar(
            x=df_cat_rev["avg_score"], y=df_cat_rev["category_english"],
            orientation="h",
            marker_color=[COLORS["accent2"] if s >= 4 else COLORS["accent3"]
                          for s in df_cat_rev["avg_score"]],
            hovertemplate="<b>%{y}</b><br>Avg score: %{x:.2f}<extra></extra>",
        ))
        fig.add_vline(x=4, line_color=COLORS["text_muted"], line_dash="dash")
        apply_layout(fig, height=350)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})