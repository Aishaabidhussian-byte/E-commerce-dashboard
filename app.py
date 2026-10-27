from __future__ import annotations

from pathlib import Path
import io

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit as st

st.markdown(
    """
    <style>
    /* Main dashboard background color */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Dark Sidebar Design (jaise reference image mein hai) */
    [data-testid="stSidebar"] {
        background-color: #121824 !important;
        padding-top: 20px;
    }
    
    /* Sidebar text and labels color */
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
        color: #94a3b8 !important;
    }
    
    /* Sidebar headings */
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        font-size: 14px;
        letter-spacing: 1px;
    }
    
    /* Clean white metric cards and containers */
    div[data-testid="stMetric"], div.element-container {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        border: 1px solid #f1f5f9;
    }
    
    /* Input fields styling */
    .stTextInput > div > div, .stSelectbox > div > div, .stDateInput > div > div {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        color: #1e293b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


st.set_page_config(
    page_title="Pakistan E-commerce Insights",
    layout="wide",
     initial_sidebar_state="expanded",
)

INK = "#17212b"
MUTED = "#687581"
TEAL = "#18a999"
PALETTE = ["#18a999", "#476c9b", "#f4a259", "#8c6bb1", "#e76f51", "#4d908e"]
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, sans-serif", color=INK, size=12),
    margin=dict(l=12, r=12, t=48, b=12),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #f5f7f8; color: #17212b; }
    [data-testid="stSidebar"] { background: #102a35; }
    [data-testid="stSidebar"] * { color: #edf5f5; }
    [data-testid="stSidebar"] [data-testid="stFileUploader"] { background: #173b46; border-radius: 12px; }
    .hero { background: linear-gradient(115deg,#102a35 0%,#174b50 72%,#18a999 140%); padding: 28px 32px; border-radius: 18px; color: white; margin-bottom: 20px; }
    .hero h1 { font-family: Manrope,sans-serif; font-size: 30px; letter-spacing: -.7px; margin: 0 0 5px; }
    .hero p { margin: 0; color: #c9dcdf; font-size: 14px; }
    .eyebrow { text-transform: uppercase; letter-spacing: 1.7px; font-size: 10px; font-weight: 700; }
    .section-title { font: 700 19px Manrope,sans-serif; color: #17212b; margin: 4px 0 2px; }
    .section-note { color: #687581; font-size: 12px; margin: 0 0 12px; }
    div[data-testid="stMetric"] { background: white; border: 1px solid #e8edef; border-radius: 14px; padding: 16px; }
    div[data-testid="stMetricLabel"] { color: #687581; }
    div[data-testid="stMetricValue"] { font: 700 24px Manrope,sans-serif; color: #17212b; }
    .insight { background: white; border: 1px solid #e8edef; border-left: 4px solid #18a999; border-radius: 12px; padding: 14px 17px; }
    .warning { background: #fff8e9; border: 1px solid #f4e1b5; border-radius: 12px; padding: 14px 17px; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] { height: 44px; padding: 0 14px; }
    hr { border-color: #e6ecee; }
    </style>
    """,
    unsafe_allow_html=True,
)
    


@st.cache_data(show_spinner="Reading and preparing the transaction file…")
def load_data(file_bytes: bytes, file_name: str) -> pd.DataFrame:
    """Read only useful fields; blank spreadsheet padding is discarded."""
    header = pd.read_csv(io.BytesIO(file_bytes), nrows=0).columns
    normalized = {c: str(c).strip() for c in header}
    keep = {"item_id", "status", "created_at", "sku", "price", "qty_ordered", "grand_total", "increment_id", "category_name_1", "discount_amount", "payment_method", "Working Date", "Customer ID", "Customer Since"}
    usecols = [c for c in header if normalized[c] in keep]
    raw = pd.read_csv(io.BytesIO(file_bytes), usecols=usecols, low_memory=False)
    raw.columns = [str(c).strip() for c in raw.columns]
    raw = raw.loc[:, ~raw.columns.str.match(r"^Unnamed(:|$)", case=False)]
    # This file contains trailing spreadsheet rows with no transaction values.
    if "item_id" in raw.columns:
        raw = raw[raw["item_id"].notna()].copy()
    elif "increment_id" in raw.columns:
        raw = raw[raw["increment_id"].notna()].copy()

    aliases = {" MV ": "MV", "Customer ID": "customer_id", "created_at": "created_at"}
    raw = raw.rename(columns=aliases)
    if "created_at" in raw:
        raw["created_at"] = pd.to_datetime(raw["created_at"], errors="coerce")
    elif "Working Date" in raw:
        raw["created_at"] = pd.to_datetime(raw["Working Date"], errors="coerce")
    else:
        raw["created_at"] = pd.NaT

    for col in ["price", "qty_ordered", "grand_total", "discount_amount", "Year", "Month", "customer_id"]:
        if col in raw:
            raw[col] = pd.to_numeric(raw[col], errors="coerce")
    for col in ["status", "category_name_1", "payment_method", "sku", "increment_id", "FY"]:
        if col not in raw:
            raw[col] = "Unknown"
        raw[col] = raw[col].fillna("Unknown").astype(str).str.strip()
        raw.loc[raw[col].isin(["", r"\N", "nan", "None"]), col] = "Unknown"
    if "discount_amount" not in raw:
        raw["discount_amount"] = 0.0
    if "grand_total" not in raw:
        raw["grand_total"] = np.nan
    if "qty_ordered" not in raw:
        raw["qty_ordered"] = 1.0
    if "price" not in raw:
        raw["price"] = np.nan
    raw["month_name"] = raw["created_at"].dt.strftime("%b")
    raw["month_period"] = raw["created_at"].dt.to_period("M").astype(str)
    return raw


def money(value: float) -> str:
    if pd.isna(value):
        return "—"
    a = abs(value)
    if a >= 1_000_000_000:
        return f"PKR {value / 1_000_000_000:,.2f}B"
    if a >= 1_000_000:
        return f"PKR {value / 1_000_000:,.1f}M"
    if a >= 100_000:
        return f"PKR {value / 1_000:,.0f}K"
    return f"PKR {value:,.0f}"


def style(fig, height=360):
    fig.update_layout(**CHART_LAYOUT, height=height)
    fig.update_xaxes(showgrid=True, gridcolor="#edf1f2", zeroline=False, title=None)
    fig.update_yaxes(showgrid=False, zeroline=False, title=None)
    return fig


def heading(title: str, note: str):
    st.markdown(f'<div class="section-title">{title}</div><div class="section-note">{note}</div>', unsafe_allow_html=True)


def no_data(message="No rows match these filters."):
    st.info(message)


st.sidebar.markdown("## 🛍️ Store Insights")
st.sidebar.caption("PAKISTAN · E-COMMERCE PERFORMANCE")
uploaded = st.sidebar.file_uploader("Load transaction CSV", type=["csv"], help="Upload the Pakistan Largest Ecommerce Dataset CSV used by the notebook.")

default_path = Path(__file__).parent / "Pakistan Largest Ecommerce Dataset.csv"
if uploaded is not None:
    source_bytes, source_name = uploaded.getvalue(), uploaded.name
elif default_path.exists():
    source_bytes, source_name = default_path.read_bytes(), default_path.name
else:
    source_bytes = source_name = None

st.markdown(
    '<div class="hero"><div class="eyebrow">Commerce intelligence · Pakistan</div>'
    '<h1>Store performance, at a glance.</h1>'
    '<p>Explore sales, customers, products, order health, and seasonality across your transaction history.</p></div>',
    unsafe_allow_html=True,
)

if source_bytes is None:
    st.markdown("### Add the dataset to get started")
    st.write("The notebook is present, but its CSV data file is not in this project folder. Upload **Pakistan Largest Ecommerce Dataset.csv** in the sidebar to populate the dashboard.")
    st.caption("This dashboard follows the notebook’s analysis, while excluding empty spreadsheet rows and avoiding average-filling missing values that would inflate sales.")
    st.stop()

try:
    df = load_data(source_bytes, source_name)
except Exception as exc:
    st.error(f"Could not read this CSV: {exc}")
    st.stop()

if df.empty:
    st.error("The file has no identifiable transaction rows. Check that it includes an item_id or increment_id column.")
    st.stop()

# Filters are deliberately composable and apply to every chart and KPI.
st.sidebar.markdown("---")
st.sidebar.markdown("### Refine the view")
available_dates = df["created_at"].dropna()
if not available_dates.empty:
    min_date, max_date = available_dates.min().date(), available_dates.max().date()
    date_range = st.sidebar.date_input("Order date", value=(min_date, max_date), min_value=min_date, max_value=max_date)
else:
    date_range = ()
categories = sorted(c for c in df["category_name_1"].unique() if c != "Unknown")
chosen_categories = st.sidebar.multiselect("Category", categories, placeholder="All categories")
statuses = sorted(c for c in df["status"].unique() if c != "Unknown")
chosen_statuses = st.sidebar.multiselect("Order status", statuses, placeholder="All statuses")
payments = sorted(c for c in df["payment_method"].unique() if c != "Unknown")
chosen_payments = st.sidebar.multiselect("Payment method", payments, placeholder="All methods")
include_unknown = st.sidebar.toggle("Include unknown categories", value=False, help="The notebook found category missingness on about 44% of source rows.")

view = df.copy()
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    view = view[view["created_at"].between(start, end)]
if chosen_categories:
    view = view[view["category_name_1"].isin(chosen_categories)]
elif not include_unknown:
    view = view[view["category_name_1"] != "Unknown"]
if chosen_statuses:
    view = view[view["status"].isin(chosen_statuses)]
if chosen_payments:
    view = view[view["payment_method"].isin(chosen_payments)]

dated = view[view["created_at"].notna()]
revenue = view["grand_total"].sum(min_count=1)
orders = view.loc[view["increment_id"] != "Unknown", "increment_id"].nunique()
customers = view.loc[view["customer_id"].notna(), "customer_id"].nunique() if "customer_id" in view else 0
avg_order = view[view["increment_id"] != "Unknown"].groupby("increment_id")["grand_total"].sum().mean() if orders else np.nan
cancel_rate = view["status"].str.lower().eq("canceled").mean() * 100 if len(view) else np.nan

st.caption(f"Source: **{source_name}** · {len(view):,} line items in view · {dated['created_at'].min().date() if len(dated) else 'No dates'} to {dated['created_at'].max().date() if len(dated) else 'No dates'}")
k = st.columns(5)
k[0].metric("Recorded sales", money(revenue), help="Sum of grand_total on populated transaction rows; all visible statuses are included.")
k[1].metric("Orders", f"{orders:,}")
k[2].metric("Customers", f"{customers:,}")
k[3].metric("Avg. order value", money(avg_order), help="Sum of visible line-item grand_total grouped by increment_id, then averaged.")
k[4].metric("Canceled items", f"{cancel_rate:.1f}%" if pd.notna(cancel_rate) else "—")

st.markdown('<div class="insight"><b>Reading the totals:</b> The source sheet has 1,048,575 rows, but only 584,524 populated item rows. The notebook filled missing numeric fields with averages, which incorrectly turns blank rows into sales. This dashboard excludes blank rows and never imputes sales values. Unknown categories are hidden by default; turn them on to inspect data coverage.</div>', unsafe_allow_html=True)

tab_overview, tab_products, tab_orders, tab_customers, tab_data = st.tabs(["✦ Overview", "▦ Products & categories", "↗ Orders & payments", "◎ Customers", "⌕ Data quality"])

with tab_overview:
    a, b = st.columns([1.65, 1])
    with a:
        heading("Sales over time", "Monthly recorded sales · hover for detail")
        if not dated.empty:
            trend = dated.groupby("month_period", as_index=False).agg(sales=("grand_total", "sum"), orders=("increment_id", "nunique"))
            trend = trend[trend["month_period"] != "NaT"].sort_values("month_period")
            if not trend.empty:
                fig = px.area(trend, x="month_period", y="sales", markers=True, custom_data=["orders"], color_discrete_sequence=[TEAL])
                fig.update_traces(line=dict(width=2.5), fillcolor="rgba(24,169,153,.12)", hovertemplate="%{x}<br>Sales: PKR %{y:,.0f}<br>Orders: %{customdata[0]:,.0f}<extra></extra>")
                fig.update_layout(yaxis_tickprefix="PKR ", yaxis_tickformat="~s")
                st.plotly_chart(style(fig, 350), use_container_width=True)
            else:
                no_data()
        else:
            no_data("The selected rows have no usable order dates.")
    with b:
        heading("Order status", "Transaction line items in the selected view")
        status = view[view["status"] != "Unknown"]["status"].value_counts().rename_axis("status").reset_index(name="items")
        if not status.empty:
            fig = px.pie(status, names="status", values="items", hole=.68, color_discrete_sequence=PALETTE)
            fig.update_traces(textposition="inside", textinfo="percent", hovertemplate="%{label}<br>%{value:,} items · %{percent}<extra></extra>")
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-.15, x=0), margin=dict(l=5, r=5, t=25, b=5))
            st.plotly_chart(style(fig, 350), use_container_width=True)
        else:
            no_data()
    a, b = st.columns(2)
    with a:
        heading("Sales by month of year", "Seasonality across all available years")
        season = dated.assign(month_num=dated["created_at"].dt.month).groupby("month_num", as_index=False).agg(sales=("grand_total", "sum"), orders=("increment_id", "nunique"))
        if not season.empty:
            season["month"] = pd.to_datetime(season["month_num"], format="%m").dt.strftime("%b")
            fig = px.bar(season, x="month", y="sales", color="sales", color_continuous_scale=["#cceee9", TEAL], custom_data=["orders"])
            fig.update_traces(hovertemplate="%{x}<br>Sales: PKR %{y:,.0f}<br>Orders: %{customdata[0]:,.0f}<extra></extra>")
            fig.update_layout(coloraxis_showscale=False, yaxis_tickprefix="PKR ", yaxis_tickformat="~s")
            st.plotly_chart(style(fig, 310), use_container_width=True)
        else:
            no_data()
    with b:
        heading("Payment mix", "Sales value by payment method")
        pay = view[view["payment_method"] != "Unknown"].groupby("payment_method", as_index=False)["grand_total"].sum().sort_values("grand_total", ascending=True).tail(9)
        if not pay.empty:
            fig = px.bar(pay, x="grand_total", y="payment_method", orientation="h", color_discrete_sequence=["#476c9b"])
            fig.update_layout(xaxis_tickprefix="PKR ", xaxis_tickformat="~s")
            st.plotly_chart(style(fig, 310), use_container_width=True)
        else:
            no_data()
    # Notebook-level signal, re-evaluated against the actual usable data.
    nov = season.loc[season["month_num"] == 11, "sales"].sum() if not season.empty else 0
    other_avg = season.loc[season["month_num"] != 11, "sales"].mean() if len(season) > 1 else 0
    if other_avg and nov:
        st.markdown(f'<div class="insight"><b>Seasonality signal:</b> November recorded {nov / other_avg:.1f}× the average monthly sales of the other calendar months in the current view. The notebook also identifies November as its strongest sales month; use the date and category filters to check where the peak comes from.</div>', unsafe_allow_html=True)

with tab_products:
    c1, c2 = st.columns([1.3, 1])
    with c1:
        heading("Category performance", "Switch between sales and item volume")
        measure = st.radio("Rank categories by", ["Sales", "Items", "Quantity"], horizontal=True, label_visibility="collapsed", key="category_measure")
        metric_col = {"Sales": "grand_total", "Items": "item_id", "Quantity": "qty_ordered"}[measure]
        cats = view[view["category_name_1"] != "Unknown"].groupby("category_name_1", as_index=False).agg(value=(metric_col, "sum"), orders=("increment_id", "nunique")).sort_values("value", ascending=True).tail(12)
        if not cats.empty:
            fig = px.bar(cats, x="value", y="category_name_1", orientation="h", color="value", color_continuous_scale=["#cceee9", TEAL], custom_data=["orders"])
            fig.update_traces(hovertemplate="%{y}<br>%{x:,.0f}<br>Orders: %{customdata[0]:,.0f}<extra></extra>")
            fig.update_layout(coloraxis_showscale=False, xaxis_tickprefix="PKR " if measure == "Sales" else "")
            st.plotly_chart(style(fig, 440), use_container_width=True)
        else:
            no_data()
    with c2:
        heading("Top products", "Ranked by recorded sales")
        products = view[view["sku"] != "Unknown"].groupby("sku", as_index=False).agg(sales=("grand_total", "sum"), items=("item_id", "count"), quantity=("qty_ordered", "sum")).sort_values("sales", ascending=False).head(12).sort_values("sales")
        if not products.empty:
            fig = px.bar(products, x="sales", y="sku", orientation="h", color_discrete_sequence=["#f4a259"], custom_data=["items", "quantity"])
            fig.update_traces(hovertemplate="%{y}<br>Sales: PKR %{x:,.0f}<br>Line items: %{customdata[0]:,.0f}<br>Qty: %{customdata[1]:,.0f}<extra></extra>")
            fig.update_layout(xaxis_tickprefix="PKR ", xaxis_tickformat="~s")
            st.plotly_chart(style(fig, 440), use_container_width=True)
        else:
            no_data()
    heading("Price and quantity", "Each point is a transaction line; log scale keeps extreme values in view")
    scatter = view.dropna(subset=["price", "qty_ordered"]).copy()
    scatter = scatter[(scatter["price"] > 0) & (scatter["qty_ordered"] > 0)]
    if len(scatter) > 18000:
        scatter = scatter.sample(18000, random_state=42)
    if not scatter.empty:
        fig = px.scatter(scatter, x="price", y="qty_ordered", color="category_name_1", hover_data=["sku", "status"], opacity=.62, color_discrete_sequence=PALETTE, log_x=True)
        fig.update_layout(xaxis_title="Unit price (PKR, log scale)", yaxis_title="Quantity ordered")
        st.plotly_chart(style(fig, 390), use_container_width=True)
    else:
        no_data()

with tab_orders:
    a, b = st.columns(2)
    with a:
        heading("Status × category", "Line-item count; useful for spotting returns and cancellations")
        cross = view[(view["category_name_1"] != "Unknown") & (view["status"] != "Unknown")]
        if not cross.empty:
            top_names = cross["category_name_1"].value_counts().head(10).index
            cross = cross[cross["category_name_1"].isin(top_names)]
            fig = px.density_heatmap(cross, x="status", y="category_name_1", histfunc="count", color_continuous_scale="Tealgrn", text_auto=".2s")
            fig.update_layout(xaxis_tickangle=-30, coloraxis_colorbar_title="Items")
            st.plotly_chart(style(fig, 420), use_container_width=True)
        else:
            no_data()
    with b:
        heading("Discount and sales", "Discount amount against recorded line sales")
        discount = view.dropna(subset=["discount_amount", "grand_total"])
        discount = discount[discount["discount_amount"] >= 0]
        if len(discount) > 12000:
            discount = discount.sample(12000, random_state=7)
        if not discount.empty:
            fig = px.scatter(discount, x="discount_amount", y="grand_total", color="category_name_1", opacity=.55, hover_data=["status", "payment_method"], color_discrete_sequence=PALETTE)
            fig.update_layout(xaxis_title="Discount (PKR)", yaxis_title="Recorded sales (PKR)", yaxis_tickformat="~s")
            st.plotly_chart(style(fig, 420), use_container_width=True)
        else:
            no_data()
    heading("Order status detail", "Counts and sales by status")
    status_table = view.groupby("status", as_index=False).agg(items=("item_id", "count"), orders=("increment_id", "nunique"), sales=("grand_total", "sum"), discount=("discount_amount", "sum")).sort_values("items", ascending=False)
    st.dataframe(status_table, use_container_width=True, hide_index=True, column_config={"sales": st.column_config.NumberColumn("Sales (PKR)", format="PKR %,.0f"), "discount": st.column_config.NumberColumn("Discount (PKR)", format="PKR %,.0f")})

with tab_customers:
    customers_df = view[view["customer_id"].notna()].copy() if "customer_id" in view else pd.DataFrame()
    if customers_df.empty:
        no_data("Customer IDs are not available for this selection.")
    else:
        orders_by_customer = customers_df[customers_df["increment_id"] != "Unknown"].groupby("customer_id", as_index=False).agg(orders=("increment_id", "nunique"), sales=("grand_total", "sum"), quantity=("qty_ordered", "sum"))
        repeat = orders_by_customer["orders"] > 1
        a, b, c, d = st.columns(4)
        a.metric("Identified customers", f"{len(orders_by_customer):,}")
        b.metric("Repeat customer share", f"{repeat.mean() * 100:.1f}%" if len(repeat) else "—")
        c.metric("Sales from repeat buyers", f"{orders_by_customer.loc[repeat, 'sales'].sum() / orders_by_customer['sales'].sum() * 100:.1f}%" if orders_by_customer["sales"].sum() else "—")
        d.metric("Sales per customer", money(orders_by_customer["sales"].mean()))
        a, b = st.columns(2)
        with a:
            heading("Customer purchase frequency", "Distinct orders per identified customer")
            freq = orders_by_customer["orders"].clip(upper=8).value_counts().sort_index().rename_axis("orders").reset_index(name="customers")
            freq["orders"] = freq["orders"].astype(str).replace("8", "8+")
            fig = px.bar(freq, x="orders", y="customers", color_discrete_sequence=[TEAL])
            fig.update_layout(xaxis_title="Orders per customer", yaxis_title="Customers")
            st.plotly_chart(style(fig, 330), use_container_width=True)
        with b:
            heading("Customer sales distribution", "Top customers by recorded sales")
            top_customer = orders_by_customer.nlargest(12, "sales").sort_values("sales")
            fig = px.bar(top_customer, x="sales", y=top_customer["customer_id"].astype("Int64").astype(str), orientation="h", color_discrete_sequence=["#8c6bb1"])
            fig.update_layout(xaxis_tickprefix="PKR ", xaxis_tickformat="~s", yaxis_title="Customer ID")
            st.plotly_chart(style(fig, 330), use_container_width=True)
        if "Customer Since" in view:
            tenure = view[view["Customer Since"].notna() & (view["Customer Since"].astype(str) != "Unknown")].groupby("Customer Since", as_index=False).agg(customers=("customer_id", "nunique"), sales=("grand_total", "sum")).sort_values("Customer Since")
            if not tenure.empty:
                heading("Customer acquisition cohorts", "Customer-since month, as recorded in the source")
                fig = px.bar(tenure, x="Customer Since", y="customers", color="sales", color_continuous_scale=["#cceee9", TEAL], hover_data=["sales"])
                fig.update_layout(xaxis_tickangle=-30, coloraxis_colorbar_title="Sales PKR")
                st.plotly_chart(style(fig, 310), use_container_width=True)

with tab_data:
    heading("Dataset health", "Missing fields and population counts from the selected view")
    valid = view[view["item_id"].notna()] if "item_id" in view else view
    known_category = valid["category_name_1"].ne("Unknown").mean() * 100 if len(valid) else 0
    known_status = valid["status"].ne("Unknown").mean() * 100 if len(valid) else 0
    known_dates = valid["created_at"].notna().mean() * 100 if len(valid) else 0
    a, b, c = st.columns(3)
    a.metric("Category coverage", f"{known_category:.1f}%")
    b.metric("Status coverage", f"{known_status:.1f}%")
    c.metric("Usable date coverage", f"{known_dates:.1f}%")
    missing = pd.DataFrame({"Field": ["Category", "Status", "Order date", "SKU", "Payment method", "Customer ID"], "Missing": [valid["category_name_1"].eq("Unknown").sum(), valid["status"].eq("Unknown").sum(), valid["created_at"].isna().sum(), valid["sku"].eq("Unknown").sum(), valid["payment_method"].eq("Unknown").sum(), valid["customer_id"].isna().sum() if "customer_id" in valid else len(valid)]})
    missing["Coverage gap"] = missing["Missing"] / max(len(valid), 1) * 100
    a, b = st.columns([1.2, 1])
    with a:
        missing_sorted = missing.sort_values("Coverage gap")
        fig = px.bar(missing_sorted, x="Coverage gap", y="Field", orientation="h", color="Coverage gap", color_continuous_scale=["#f6d8a8", "#e76f51"], text=missing_sorted["Coverage gap"].map(lambda x: f"{x:.1f}%"))
        fig.update_layout(coloraxis_showscale=False, xaxis_ticksuffix="%", xaxis_range=[0, 100])
        st.plotly_chart(style(fig, 300), use_container_width=True)
    with b:
        st.markdown('<div class="warning"><b>Interpretation note</b><br>The notebook’s summary counts 584,524 populated rows and 464,051 fully blank trailing rows, plus five columns that are entirely empty. Its later mean imputation creates numeric values in those blank rows. The dashboard drops fully blank rows, preserves genuine missing values, and flags unknown categories so sales are not attributed to an invented category.</div>', unsafe_allow_html=True)
        st.markdown('<div class="insight"><b>Notebook findings retained:</b><br>• Mobiles &amp; Tablets leads known categories by transaction count and sales.<br>• November is the strongest calendar month in the notebook.<br>• Canceled orders are about 19% of the populated rows before filters.<br>• Quantity and grand total move together, as expected for line-level order amounts.</div>', unsafe_allow_html=True)
    st.download_button("Download filtered rows as CSV", data=view.to_csv(index=False).encode("utf-8-sig"), file_name="ecommerce_filtered_transactions.csv", mime="text/csv")

st.markdown("---")
st.caption("Pakistan E-commerce Store Insights · Built from the accompanying notebook and its transaction schema · Currency values are shown in PKR")
