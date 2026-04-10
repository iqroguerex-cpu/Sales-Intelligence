import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuration & Theming
st.set_page_config(page_title="IQROGUEREX Sales Insights", layout="wide", page_icon="📊")

# Custom CSS for a sleek dark professional look
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.8rem; color: #00d4ff; }
    .main { background-color: #0E1117; }
    div.stButton > button:first-child { background-color: #00d4ff; color:white; }
    </style>
""", unsafe_allow_html=True)

# 2. Data Connection
# Updated URL based on your repo structure
DATA_URL = "https://raw.githubusercontent.com/iqroguerex-cpu/sales-dashboard/main/sales_data.csv"

@st.cache_data
def load_data():
    try:
        data = pd.read_csv(DATA_URL)
        data["Order_Date"] = pd.to_datetime(data["Order_Date"])
        data["Total_Sales"] = data["Quantity"] * data["Price"]
        return data
    except Exception as e:
        st.error(f"Error connecting to GitHub data: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR FILTERS ---
    st.sidebar.image("https://via.placeholder.com/150x50?text=IQROGUEREX", use_container_width=True)
    st.sidebar.title("Control Panel")
    
    min_date, max_date = df["Order_Date"].min(), df["Order_Date"].max()
    
    date_range = st.sidebar.date_input("Timeframe", [min_date, max_date], min_value=min_date, max_value=max_date)
    
    region = st.sidebar.multiselect("Geography", options=df["Region"].unique(), default=df["Region"].unique())
    category = st.sidebar.multiselect("Product Category", options=df["Category"].unique(), default=df["Category"].unique())

    # Filter Logic
    if len(date_range) == 2:
        mask = (df["Order_Date"] >= pd.Timestamp(date_range[0])) & \
               (df["Order_Date"] <= pd.Timestamp(date_range[1])) & \
               (df["Region"].isin(region)) & \
               (df["Category"].isin(category))
        f_df = df.loc[mask]
    else:
        f_df = df

    # --- HEADER ---
    st.title("📊 Sales Performance Analytics")
    st.markdown(f"**Enterprise:** IQROGUEREX | **Report Period:** {date_range[0]} to {date_range[-1]}")
    st.divider()

    # --- KPI METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    rev = f_df["Total_Sales"].sum()
    orders = f_df["Order_ID"].nunique()
    avg_val = rev / orders if orders > 0 else 0
    cust = f_df["Customer_Name"].nunique()

    col1.metric("Gross Revenue", f"${rev:,.2f}")
    col2.metric("Order Volume", f"{orders:,}")
    col3.metric("Avg. Order Value", f"${avg_val:,.2f}")
    col4.metric("Active Customers", f"{cust:,}")

    st.write("")

    # --- VISUALIZATIONS ---
    c1, c2 = st.columns([6, 4])

    with c1:
        st.subheader("📈 Revenue Trend Line")
        trend_df = f_df.resample('M', on='Order_Date').sum(numeric_only=True).reset_index()
        fig_trend = px.line(trend_df, x="Order_Date", y="Total_Sales", 
                            markers=True, template="plotly_dark",
                            color_discrete_sequence=["#00d4ff"])
        fig_trend.update_layout(xaxis_title="", yaxis_title="Revenue ($)")
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("🎯 Category Market Share")
        fig_pie = px.pie(f_df, values="Total_Sales", names="Category", 
                         hole=0.5, template="plotly_dark")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("📍 Regional Performance")
        reg_df = f_df.groupby("Region")["Total_Sales"].sum().reset_index()
        fig_reg = px.bar(reg_df, x="Region", y="Total_Sales", 
                         color="Total_Sales", color_continuous_scale="Blues",
                         template="plotly_dark")
        st.plotly_chart(fig_reg, use_container_width=True)

    with c4:
        st.subheader("🏆 Top 5 Strategic Accounts")
        top_c = f_df.groupby("Customer_Name")["Total_Sales"].sum().nlargest(5).reset_index()
        st.table(top_c.style.format({"Total_Sales": "${:,.2f}"}))

    # --- EXPORT ---
    st.divider()
    csv = f_df.to_csv(index=False).encode("utf-8")
    st.download_button("📩 Export Filtered Dataset", data=csv, file_name="IQ_Sales_Report.csv", mime="text/csv")
