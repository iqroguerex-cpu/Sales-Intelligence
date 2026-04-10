import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="IQROGUEREX Sales Insights",
    layout="wide",
    page_icon="📊"
)

# ---------------- STYLE ----------------
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00d4ff; }
    .main { background-color: #0E1117; }
    div.stButton > button:first-child { background-color: #00d4ff; color:white; border:none; }
    </style>
""", unsafe_allow_html=True)

# ---------------- DATA ----------------
GITHUB_URL = "https://raw.githubusercontent.com/iqroguerex-cpu/iqroguerex-cpu/main/sales_data.csv"

@st.cache_data
def load_data():
    try:
        # --- TRY GITHUB FIRST ---
        response = requests.get(GITHUB_URL)

        if response.status_code == 200:
            st.success("✅ Loaded data from GitHub")
            data = StringIO(response.text)
            df = pd.read_csv(data)

        # --- CLEAN DATA ---
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
        df = df.dropna(subset=["Order_Date"])

        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
        df["Price"] = pd.to_numeric(df["Price"], errors="coerce").fillna(0)

        df["Total_Sales"] = df["Quantity"] * df["Price"]

        return df

    except Exception as e:
        st.error("🚨 Data loading failed completely")
        st.exception(e)
        return None

df = load_data()

# ---------------- APP ----------------
if df is not None and not df.empty:

    # SIDEBAR
    st.sidebar.header("📊 Filters")

    min_date = df["Order_Date"].min().date()
    max_date = df["Order_Date"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date)
    )

    region = st.sidebar.multiselect(
        "Region",
        df["Region"].unique(),
        default=df["Region"].unique()
    )

    category = st.sidebar.multiselect(
        "Category",
        df["Category"].unique(),
        default=df["Category"].unique()
    )

    # FILTER
    if isinstance(date_range, tuple):
        start, end = date_range
        f_df = df[
            (df["Order_Date"] >= pd.Timestamp(start)) &
            (df["Order_Date"] <= pd.Timestamp(end)) &
            (df["Region"].isin(region)) &
            (df["Category"].isin(category))
        ]
    else:
        f_df = df

    # TITLE
    st.title("📊 Sales Performance Dashboard")
    st.divider()

    # KPIs
    col1, col2, col3, col4 = st.columns(4)

    revenue = f_df["Total_Sales"].sum()
    orders = f_df["Order_ID"].nunique()
    customers = f_df["Customer_Name"].nunique()
    aov = revenue / orders if orders else 0

    col1.metric("Revenue", f"${revenue:,.0f}")
    col2.metric("Orders", orders)
    col3.metric("Customers", customers)
    col4.metric("AOV", f"${aov:,.2f}")

    # CHARTS
    left, right = st.columns([7, 3])

    with left:
        st.subheader("Revenue Trend")

        trend = f_df.groupby(
            f_df["Order_Date"].dt.to_period("M")
        )["Total_Sales"].sum().reset_index()

        trend["Order_Date"] = trend["Order_Date"].astype(str)

        fig = px.line(
            trend,
            x="Order_Date",
            y="Total_Sales",
            template="plotly_dark",
            markers=True
        )

        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Category Split")

        if not f_df.empty:
            fig2 = px.pie(
                f_df,
                values="Total_Sales",
                names="Category",
                hole=0.4,
                template="plotly_dark"
            )
            st.plotly_chart(fig2, use_container_width=True)

    # TOP CUSTOMERS
    st.subheader("🏆 Top Customers")

    top = (
        f_df.groupby("Customer_Name")["Total_Sales"]
        .sum()
        .nlargest(5)
        .reset_index()
    )

    st.dataframe(top)

    # DOWNLOAD
    csv = f_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download CSV",
        csv,
        "sales_report.csv",
        "text/csv"
    )

else:
    st.error("❌ No data available")
