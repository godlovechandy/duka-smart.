
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ---------- Configuration ----------
st.set_page_config(
    page_title="DukaSmart | Sales",
    page_icon="📊",
    layout="wide",
)

DATA_DIR = Path("data")
DATA_FILE = DATA_DIR / "sales.csv"

CURRENCY = "TSh"


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        padding: 16px !important;
        border-radius: 12px !important;
    }

    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] label p {
        color: #cbd5e1 !important;
    }

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: #ffffff !important;
    }

    div[data-testid="stMetricDelta"] {
        color: #cbd5e1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- Demo data ----------
def create_demo_data():
    """Create clearly fictional transactions for development."""
    rng = np.random.default_rng(42)

    products = {
        "Rice": 3000,
        "Sugar": 2500,
        "Cooking Oil": 5000,
        "Maize Flour": 1800,
        "Soap": 1500,
    }

    dates = pd.date_range(
        end=pd.Timestamp.today().normalize(),
        periods=60,
        freq="D",
    )

    rows = []

    for i in range(180):
        product = rng.choice(list(products.keys()))
        date = rng.choice(dates)
        quantity = int(rng.integers(1, 9))

        rows.append(
            {
                "date": date,
                "order_id": f"ORD-{i + 1:04d}",
                "product": product,
                "quantity": quantity,
                "unit_price": products[product],
            }
        )

    return pd.DataFrame(rows)


def load_sales():
    """Load the CSV, creating demo data if it does not exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists():
        create_demo_data().to_csv(DATA_FILE, index=False)

    df = pd.read_csv(DATA_FILE)

    required = {
        "date",
        "order_id",
        "product",
        "quantity",
        "unit_price",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required CSV columns: {', '.join(sorted(missing))}"
        )

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["quantity"] = pd.to_numeric(
        df["quantity"], errors="coerce"
    )
    df["unit_price"] = pd.to_numeric(
        df["unit_price"], errors="coerce"
    )

    # Reject invalid records instead of silently reporting bad figures.
    valid = (
        df["date"].notna()
        & df["order_id"].notna()
        & df["product"].notna()
        & df["quantity"].gt(0)
        & df["unit_price"].ge(0)
        & df["quantity"].notna()
        & df["unit_price"].notna()
    )

    df = df.loc[valid].copy()

    if df.empty:
        raise ValueError("No valid sales records were found.")

    df["quantity"] = df["quantity"].astype(int)
    df["sales"] = df["quantity"] * df["unit_price"]

    return df


# ---------- Page header ----------




st.markdown(
    """
    <style>
    .duka-title {
        text-align: center;
        color: #007BFF;
        font-size: 52px;
        font-weight: 900;
        margin: 0;
    }
    .duka-tagline {
        text-align: center;
        color: #0056D6;
        font-size: 22px;
        font-weight: 800;
        margin-top: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="duka-title">DukaSmart</h1>', unsafe_allow_html=True)
st.markdown(
    '<p class="duka-tagline">Track Sales. Discover top products. make Smarter decisions.</p>',
    unsafe_allow_html=True,
)
st.write("")


st.caption("Shop sales intelligence")
st.info(
    "DEMO MODE — figures are fictional. "
    "Replace data/sales.csv with authorized business data when testing "
    "with a real shop."
)

try:
    sales = load_sales()
except (ValueError, OSError, pd.errors.ParserError) as exc:
    st.error(f"Unable to load sales data: {exc}")
    st.stop()


# ---------- Sidebar filters ----------
st.sidebar.header("Report filters")


uploaded_file = st.sidebar.file_uploader(
    "Upload sales CSV",
    type=["csv"],
    help="Choose a CSV file containing your shop's sales records."
)

if uploaded_file is not None:
    st.sidebar.success(f"Selected: {uploaded_file.name}")
else:
    st.sidebar.caption(
        "Demo data is active until you upload a CSV."
    )

filtered = sales.copy()

if uploaded_file is not None:
    try:
        uploaded_sales = pd.read_csv(uploaded_file)

        required_columns = [
            "date",
            "order_id",
            "product",
            "quantity",
            "unit_price",
        ]

        missing_columns = [
            col for col in required_columns
            if col not in uploaded_sales.columns
        ]

        if missing_columns:
            st.error(
                "CSV is missing required columns: "
                + ", ".join(missing_columns)
            )
            st.stop()

        uploaded_sales = uploaded_sales[required_columns].copy()

        uploaded_sales["date"] = pd.to_datetime(
            uploaded_sales["date"], errors="coerce"
        )

        uploaded_sales["quantity"] = pd.to_numeric(
            uploaded_sales["quantity"], errors="coerce"
        )

        uploaded_sales["unit_price"] = pd.to_numeric(
            uploaded_sales["unit_price"], errors="coerce"
        )

        uploaded_sales["order_id"] = (
            uploaded_sales["order_id"].astype("string").str.strip()
        )
        uploaded_sales["product"] = (
            uploaded_sales["product"].astype("string").str.strip()
        )

        if uploaded_sales.empty:
            st.error("The uploaded CSV contains no sales records.")
            st.stop()

        if uploaded_sales[
            ["date", "order_id", "product", "quantity", "unit_price"]
        ].isna().any().any():
            st.error(
                "Some required values are missing or invalid. "
                "Check dates, order IDs, products, quantities and prices."
            )
            st.stop()

        if not (
            np.isfinite(uploaded_sales["quantity"]).all()
            and np.isfinite(uploaded_sales["unit_price"]).all()
        ):
            st.error("Quantities and prices must be finite numbers.")
            st.stop()

        if (
            (uploaded_sales["quantity"] <= 0).any()
            or (uploaded_sales["quantity"] % 1 != 0).any()
        ):
            st.error("Every quantity must be a positive whole number.")
            st.stop()

        if (uploaded_sales["unit_price"] < 0).any():
            st.error("Unit prices cannot be negative.")
            st.stop()

        uploaded_sales["quantity"] = uploaded_sales["quantity"].astype(int)
        uploaded_sales["sales"] = (
            uploaded_sales["quantity"] * uploaded_sales["unit_price"]
        )

        filtered = uploaded_sales
    except (ValueError, TypeError, OSError, pd.errors.ParserError) as exc:
        st.error(f"Unable to use uploaded CSV: {exc}")
        st.stop()


# ---------- KPI cards ----------
total_sales = filtered["sales"].sum()
total_orders = filtered["order_id"].nunique()
total_units = filtered["quantity"].sum()

average_order_value = (
    total_sales / total_orders if total_orders else 0
)

st.subheader("Sales overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Sales",
    f"TSh {total_sales:,.0f}"
)

col2.metric(
    "Orders",
    f"{total_orders:,}"
)

col3.metric(
    "Units Sold",
    f"{total_units:,}"
)

col4.metric(
    "Average Order Value",
    f"TSh {average_order_value:,.0f}"
)

# ---------- Charts ----------
st.subheader("Sales performance")

daily = (
    filtered.assign(day=filtered["date"].dt.date)
    .groupby("day", as_index=False)["sales"]
    .sum()
)

product_sales = (
    filtered.groupby("product", as_index=False)["sales"]
    .sum()
    .sort_values("sales", ascending=True)
)
#Business insights: Sales over time and sales by product are displayed side by side for easy comparison and analysis.
st.subheader("Business insights")
st.markdown("#### Top 5 Most Sold Products")

if filtered.empty:
    st.info(
        "No sales data available for the selected filters. ")
else:
    top_products = (
        filtered.groupby("product", as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            sales=("sales", "sum"),
        )
        .sort_values(by=["units_sold", "product"], ascending=[False, True])
        .head(5)
        .reset_index(drop=True) 
    )

    top_products.index=top_products.index + 1 
    top_products.index.name="Rank"

    st.dataframe(
        top_products.rename(columns={"product": "Product", "units_sold": "Units Sold", "sales": "Sales (TSh)"}),
        use_container_width=True,
    )

left, right = st.columns(2)

with left:
    st.markdown("**Sales over time**")

    fig_trend = px.line(
        daily,
        x="day",
        y="sales",
        markers=True,
        labels={
            "day": "Date",
            "sales": "Sales (TSh)",
        },
    )

    fig_trend.update_layout(
        margin=dict(l=10, r=10, t=20, b=10),
        yaxis_tickformat=",",
    )

    st.plotly_chart(fig_trend, use_container_width=True)

with right:
    st.markdown("**Sales by product**")

    fig_products = px.bar(
        product_sales,
        x="sales",
        y="product",
        orientation="h",
        labels={
            "product": "Product",
            "sales": "Sales (TSh)",
        },
        text="sales",
    )
    fig_products.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        cliponaxis=False,
        hovertemplate=(
            "Product: %{y}<br>"
            "Sales: TSh %{x:,.0f}"
            "<extra></extra>"
        ),

    )

    fig_products.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Sales (TSh)",
        yaxis_title="Product",
        showlegend=False,
    )

    st.plotly_chart(fig_products, use_container_width=True)


# ---------- Transaction table ----------
st.subheader("Transactions")

display = filtered.sort_values("date", ascending=False).copy()
display["date"] = display["date"].dt.strftime("%Y-%m-%d")
display["unit_price"] = display["unit_price"].map(
    lambda x: f"{CURRENCY} {x:,.0f}"
)
display["sales"] = display["sales"].map(
    lambda x: f"{CURRENCY} {x:,.0f}"
)

st.dataframe(
    display[
        ["date", "order_id", "product", "quantity",
         "unit_price", "sales"]
    ],
    use_container_width=True,
    hide_index=True,
)

# Export the underlying filtered records with numeric values.
csv_bytes = filtered.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download filtered sales (CSV)",
    data=csv_bytes,
    file_name="dukas_mart_sales_report.csv",
    mime="text/csv",
)

st.caption(
    "DukaSmart prototype · Sales is sales value, not net profit."
)
