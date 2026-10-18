from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Streamlit Sales Dashboard", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.8rem; padding-bottom: 2rem;}
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #172554, #1e3a8a);
        border: 1px solid #334155;
        padding: 1rem;
        border-radius: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def create_sample_data() -> pd.DataFrame:
    """Create repeatable sample sales data for the dashboard."""
    rng = np.random.default_rng(seed=42)
    dates = pd.date_range(end=date.today(), periods=180, freq="D")
    regions = ["North", "South", "East", "West"]
    products = ["Laptop", "Phone", "Tablet"]

    rows = []
    for day in dates:
        for region in regions:
            for product in products:
                units = int(rng.integers(5, 35))
                price = {"Laptop": 900, "Phone": 600, "Tablet": 400}[product]
                rows.append(
                    {
                        "date": day,
                        "region": region,
                        "product": product,
                        "units": units,
                        "revenue": units * price,
                    }
                )

    return pd.DataFrame(rows)


st.title("📊 Streamlit Sales Dashboard")
st.write(
    "Explore sample sales data with interactive filters. "
    "Changing a widget reruns the script and refreshes the results. "
    "Use the tabs to explore 12 interactive charts, including animated views."
)

sales_data = create_sample_data()

with st.sidebar:
    st.header("Dashboard filters")
    selected_regions = st.multiselect(
        "Regions",
        options=sorted(sales_data["region"].unique()),
        default=sorted(sales_data["region"].unique()),
    )
    selected_products = st.multiselect(
        "Products",
        options=sorted(sales_data["product"].unique()),
        default=sorted(sales_data["product"].unique()),
    )
    days_to_show = st.slider("Days to display", min_value=7, max_value=180, value=90)

cutoff_date = sales_data["date"].max() - timedelta(days=days_to_show - 1)
filtered_data = sales_data[
    sales_data["date"].ge(cutoff_date)
    & sales_data["region"].isin(selected_regions)
    & sales_data["product"].isin(selected_products)
]

if filtered_data.empty:
    st.info("Select at least one region and one product to display the dashboard.")
else:
    total_revenue = filtered_data["revenue"].sum()
    total_units = filtered_data["units"].sum()
    average_daily_revenue = (
        filtered_data.groupby("date")["revenue"].sum().mean()
    )

    revenue_col, units_col, average_col = st.columns(3)
    revenue_col.metric("Total revenue", f"${total_revenue:,.0f}")
    units_col.metric("Units sold", f"{total_units:,}")
    average_col.metric("Average daily revenue", f"${average_daily_revenue:,.0f}")

    filtered_data = filtered_data.copy()
    filtered_data["weekday"] = filtered_data["date"].dt.day_name()
    filtered_data["week"] = (
        filtered_data["date"].dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d")
    )
    weekday_order = [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    daily = (
        filtered_data.groupby("date", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units", "sum"))
    )
    by_product = (
        filtered_data.groupby("product", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units", "sum"))
        .sort_values("revenue", ascending=False)
    )
    by_region = (
        filtered_data.groupby("region", as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units", "sum"))
        .sort_values("revenue", ascending=True)
    )
    by_week_product = (
        filtered_data.groupby(["week", "product"], as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units", "sum"))
        .sort_values("week")
    )
    by_week_region_product = (
        filtered_data.groupby(["week", "region", "product"], as_index=False)
        .agg(revenue=("revenue", "sum"), units=("units", "sum"))
        .sort_values("week")
    )
    heatmap_data = (
        filtered_data.pivot_table(
            index="weekday", columns="product", values="revenue", aggfunc="sum"
        )
        .reindex(weekday_order)
        .fillna(0)
    )

    overview_tab, breakdown_tab, details_tab, animation_tab = st.tabs(
        ["📈 Trends", "🧩 Breakdowns", "🔎 Distributions", "🎞️ Animations"]
    )

    with overview_tab:
        st.subheader("1. Daily revenue")
        st.plotly_chart(
            px.line(
                daily, x="date", y="revenue", markers=True,
                title="Revenue by day", labels={"date": "Date", "revenue": "Revenue ($)"},
            ),
            use_container_width=True,
        )

        st.subheader("2. Daily units sold")
        st.plotly_chart(
            px.area(
                daily, x="date", y="units",
                title="Units sold by day", labels={"date": "Date", "units": "Units"},
            ),
            use_container_width=True,
        )

        st.subheader("3. Revenue by product")
        st.plotly_chart(
            px.bar(
                by_product, x="product", y="revenue", color="product",
                title="Total revenue by product",
                labels={"product": "Product", "revenue": "Revenue ($)"},
                text_auto=",.0f",
            ),
            use_container_width=True,
        )

    with breakdown_tab:
        st.subheader("4. Revenue by region")
        st.plotly_chart(
            px.bar(
                by_region, x="revenue", y="region", color="region", orientation="h",
                title="Total revenue by region",
                labels={"region": "Region", "revenue": "Revenue ($)"},
                text_auto=",.0f",
            ),
            use_container_width=True,
        )

        st.subheader("5. Product revenue share")
        st.plotly_chart(
            px.pie(
                by_product, names="product", values="revenue", hole=0.55,
                title="Share of revenue by product",
            ),
            use_container_width=True,
        )

        st.subheader("6. Region revenue share")
        st.plotly_chart(
            px.pie(
                by_region, names="region", values="revenue",
                title="Revenue mix by region",
            ),
            use_container_width=True,
        )

    with details_tab:
        st.subheader("7. Units sold versus revenue")
        st.plotly_chart(
            px.scatter(
                filtered_data, x="units", y="revenue", color="product",
                symbol="region", hover_data=["date"], opacity=0.7,
                title="Daily product sales by region",
                labels={"units": "Units sold", "revenue": "Revenue ($)"},
            ),
            use_container_width=True,
        )

        st.subheader("8. Revenue distribution by product")
        st.plotly_chart(
            px.box(
                filtered_data, x="product", y="revenue", color="product",
                points="outliers", title="Daily revenue spread",
                labels={"product": "Product", "revenue": "Revenue ($)"},
            ),
            use_container_width=True,
        )

        st.subheader("9. Units sold distribution")
        st.plotly_chart(
            px.histogram(
                filtered_data, x="units", color="product", marginal="box",
                barmode="overlay", opacity=0.75, nbins=20,
                title="Distribution of units per day and product",
                labels={"units": "Units sold"},
            ),
            use_container_width=True,
        )

        st.subheader("10. Revenue heatmap by weekday and product")
        st.plotly_chart(
            go.Figure(
                data=go.Heatmap(
                    z=heatmap_data.to_numpy(),
                    x=heatmap_data.columns.tolist(),
                    y=heatmap_data.index.tolist(),
                    colorscale="Blues",
                    colorbar={"title": "Revenue ($)"},
                    hovertemplate="%{y}<br>%{x}<br>$%{z:,.0f}<extra></extra>",
                )
            ).update_layout(title="Revenue patterns by weekday"),
            use_container_width=True,
        )

    with animation_tab:
        st.caption(
            "Press Play on a chart to animate the weekly sales data. "
            "The animation controls are built into Plotly."
        )

        st.subheader("11. Animated weekly revenue by product")
        st.plotly_chart(
            px.bar(
                by_week_product, x="product", y="revenue", color="product",
                animation_frame="week", range_y=[0, by_week_product["revenue"].max() * 1.1],
                title="Weekly revenue by product",
                labels={"product": "Product", "revenue": "Revenue ($)", "week": "Week"},
            ),
            use_container_width=True,
        )

        st.subheader("12. Animated weekly product and region performance")
        st.plotly_chart(
            px.scatter(
                by_week_region_product, x="revenue", y="units", color="product",
                symbol="region", size="revenue", animation_frame="week",
                range_x=[0, by_week_region_product["revenue"].max() * 1.1],
                range_y=[0, by_week_region_product["units"].max() * 1.1],
                size_max=45, title="Weekly revenue and units by region",
                labels={
                    "revenue": "Revenue ($)", "units": "Units sold",
                    "week": "Week", "product": "Product", "region": "Region",
                },
            ),
            use_container_width=True,
        )

    st.subheader("Filtered sales data")
    st.dataframe(filtered_data, use_container_width=True, hide_index=True)
