import pandas as pd
import streamlit as st
from utils import calculate_mom, format_mom, highlight_profit, WAREHOUSE_CODE_MAPPING, WAREHOUSE_NAME_MAPPING

st.set_page_config(
    page_title="Warehouse Profit",
    layout="wide"
)

st.title("Warehouse P&L Dashboard")

if "warehouse_profit" not in st.session_state:
    st.warning(
        "Warehouse Profit data is not loaded. "
        "Please upload and process the files on the Data Upload page."
    )

    if st.button(
        "Go to Data Upload",
        type="primary",
        key="go_to_upload_page",
    ):
        st.switch_page("pages/0_Data_Upload.py")

    st.stop()

warehouse_profit = st.session_state["warehouse_profit"].copy()


# 先做权限过滤
# warehouse_profit = filter_by_warehouse(
#     warehouse_profit,
#     warehouse_column="仓编码",
#     access=access
# )
warehouse_profit = warehouse_profit.drop(columns = ['仓名称'])

warehouse_profit["仓名称 Warehouse Name"] = (
        warehouse_profit["仓编码"]
        .map(WAREHOUSE_CODE_MAPPING)
        .fillna(warehouse_profit["仓编码"])
    )

# Filters
# filter_col1, filter_col2 = st.columns([1, 2])

warehouse_options = sorted(
    warehouse_profit["仓名称 Warehouse Name"]
    .dropna()
    .astype(str)
    .unique()
)

# with filter_col1:
selected_warehouses = st.sidebar.multiselect(
        "Warehouse",
        options=warehouse_options,
        default=warehouse_options,
    )

filtered_raw = warehouse_profit[
    warehouse_profit["仓名称 Warehouse Name"]
    .astype(str)
    .isin(selected_warehouses)
].copy()

date_values = filtered_raw["入账日期"].dropna()

if not date_values.empty:
    month_options = sorted(
        date_values
        .dt.to_period("M")
        .astype(str)
        .unique(),
        reverse=True,
    )

    selected_months = st.sidebar.multiselect(
        "Month",
        options=month_options,
        default=month_options,
    )

    if selected_months:
        filtered_raw = filtered_raw[
            filtered_raw["入账日期"]
            .dt.to_period("M")
            .astype(str)
            .isin(selected_months)
        ].copy()

filtered_raw["Business Type"] = "仓配 Warehousing & Distribution"

filtered_raw.loc[
    filtered_raw["国际产品细分类"].eq(
        "国际物流-海外仓配-海外仓产品"
    ),
    "Business Type"
] = "纯仓 Pure Warehouse"

warehouse_profit_pivot = filtered_raw.pivot_table(
    index=[
        "入账日期",
        "仓编码",
        "仓名称 Warehouse Name",
        "Business Type"
    ],
    columns= "损益科目",
    values="不含税金额CNY",
    aggfunc="sum",
    fill_value=0
)

# warehouse_profit_pivot.columns = [
#     "_".join(str(value)
#              for value in column
#              if pd.notna(value)
#              )
#              for column in warehouse_profit_pivot.columns
# ]

warehouse_profit_pivot = (
    warehouse_profit_pivot
    .reset_index()
)

total_df = (
    warehouse_profit_pivot
    .groupby(
        [
            "入账日期",
            "仓编码",
            "仓名称 Warehouse Name"
        ],
        as_index=False
    )
    .sum(numeric_only=True)
)

total_df["Business Type"] = "总计 Total"

warehouse_profit_pivot = pd.concat(
    [
        warehouse_profit_pivot,
        total_df
    ],
    ignore_index=True
)

warehouse_profit_pivot = warehouse_profit_pivot.sort_values(by = ['入账日期', '仓编码'], ascending = [True, True])

# 去除 columns.name，否则表头可能显示“损益科目”
warehouse_profit_pivot.columns.name = None

detail_translation = {
    "入账日期": "月份 Date",
    "仓编码": "仓编码 Warehouse Code",
    "仓名称 Warehouse Name": "仓名称 Warehouse Name",
    "Business Type": "产品分类 Business Type",
    "国际架构_营业税金及附加": "营业税金及附加 Business Operation Tax & Surcharges",
    "收入": "收入 Revenue",
    "毛利": "毛利 Gross Profit",
    "直接成本": "直接成本 Direct Cost",
    "贡献利润": "贡献利润 Contribution Profit",
    "费用": "费用 Expenses",
    "间接成本": "间接成本 Indirect Cost",
    "成本：国际手工调整项-历史": "成本：国际手工调整项-历史 Adjust Cost (historical data)"
}

warehouse_profit_pivot = warehouse_profit_pivot.rename(columns=detail_translation)

warehouse_profit_pivot["毛利率 Gross Profit Margin"] = warehouse_profit_pivot["毛利 Gross Profit"] / warehouse_profit_pivot["收入 Revenue"] 

column_priority = {
    "收入 Revenue": 1,
    "直接成本 Direct Cost": 2,
    "间接成本 Indirect Cost": 3,
    "毛利 Gross Profit": 4,
    "毛利率 Gross Profit Margin": 5,
    "费用 Expenses": 6,
    "营业税金及附加 Tax & Surcharges": 7,
    "贡献利润 Contribution Profit": 8,
    "成本：国际手工调整项-历史 Adjust Cost (historical data)": 9
}

fixed_columns = [
    "月份 Date",
    "仓编码 Warehouse Code",
    "仓名称 Warehouse Name",
    "产品分类 Business Type"
]

financial_columns = [
    col
    for col in warehouse_profit_pivot.columns
    if col not in fixed_columns
]

financial_columns = sorted(
    financial_columns,
    key=lambda x: column_priority.get(x, 999)
)

warehouse_profit_pivot = warehouse_profit_pivot[
    fixed_columns + financial_columns
]

# format

# def highlight_margin(value):
#     if pd.isna(value):
#         return ""

#     if value >= 0.20:
#         return (
#             "background-color: #d9ead3;"
#             "color: #274e13;"
#             "font-weight: bold;"
#         )

#     if value >= 0:
#         return (
#             "background-color: #fff2cc;"
#             "color: #7f6000;"
#             "font-weight: bold;"
#         )

#     return (
#         "background-color: #f4cccc;"
#         "color: #990000;"
#         "font-weight: bold;"
#     )

number_columns = (
    warehouse_profit_pivot
    .select_dtypes(include="number")
    .columns
    .tolist()
)

margin_column = "毛利率 Gross Profit Margin"

format_dict = {
    col: "¥{:,.0f}"
    for col in number_columns
    if col != margin_column
}

format_dict[margin_column] = "{:.2%}"

styled_df = (
    warehouse_profit_pivot
    .style
    .format(
        format_dict,
        na_rep="-"
    )
    .map(
        highlight_profit,
        subset=[
            "毛利 Gross Profit",
            "贡献利润 Contribution Profit",
            "毛利率 Gross Profit Margin"
        ]
    )
)

st.subheader("Warehouse Performance Summary")

# =========================================================
# Prepare data for KPI cards and trends
# =========================================================

date_col = "月份 Date"
warehouse_col = "仓编码 Warehouse Code"
warehouse_name_col = "仓名称 Warehouse Name"
business_type_col = "产品分类 Business Type"

revenue_col = "收入 Revenue"
cost_col = "直接成本 Direct Cost"
gross_profit_col = "毛利 Gross Profit"
profit_col = "贡献利润 Contribution Profit"
gross_margin_col = "毛利率 Gross Profit Margin"


# Make sure required columns are numeric
metric_columns = [
    revenue_col,
    cost_col,
    gross_profit_col,
    profit_col,
    gross_margin_col,
]

for col in metric_columns:
    if col in warehouse_profit_pivot.columns:
        warehouse_profit_pivot[col] = pd.to_numeric(
            warehouse_profit_pivot[col],
            errors="coerce",
        )


warehouse_profit_pivot[date_col] = pd.to_datetime(
    warehouse_profit_pivot[date_col],
    errors="coerce",
)


# Use Total rows only to avoid double counting
dashboard_df = warehouse_profit_pivot[
    warehouse_profit_pivot[business_type_col].eq("总计 Total")
].copy()


# Sort chronologically
dashboard_df = dashboard_df.sort_values(
    by=[warehouse_col, date_col]
)

warehouse_options_for_cards = sorted(
    dashboard_df[warehouse_col]
    .dropna()
    .astype(str)
    .unique()
)

selected_card_warehouse = st.selectbox(
    "Select a warehouse for KPI cards",
    options=warehouse_options_for_cards,
)


warehouse_card_df = (
    dashboard_df[
        dashboard_df[warehouse_col]
        .astype(str)
        .eq(selected_card_warehouse)
    ]
    .sort_values(date_col)
)

if warehouse_card_df.empty:
    st.warning("No warehouse data available.")

else:
    current_row = warehouse_card_df.iloc[-1]

    previous_row = (
        warehouse_card_df.iloc[-2]
        if len(warehouse_card_df) >= 2
        else None
    )

    current_revenue = current_row[revenue_col]
    current_cost = current_row[cost_col]
    current_gross_profit = current_row[gross_profit_col]
    current_profit = current_row[profit_col]
    current_margin = current_row[gross_margin_col]

    if previous_row is not None:
        revenue_mom = calculate_mom(
            current_revenue,
            previous_row[revenue_col],
        )

        cost_mom = calculate_mom(
            current_cost,
            previous_row[cost_col],
        )

        gross_profit_change = (
            current_gross_profit
            - previous_row[gross_profit_col]
        )

        # Absolute change is clearer when profit crosses zero
        profit_change = (
            current_profit
            - previous_row[profit_col]
        )

        margin_change = (
            current_margin
            - previous_row[gross_margin_col]
        )

    else:
        revenue_mom = None
        cost_mom = None
        gross_profit_change = None
        profit_change = None
        margin_change = None

    warehouse_name = current_row.get(
        warehouse_name_col,
        "",
    )

    current_month = current_row[date_col]

    st.subheader(
        f"{selected_card_warehouse} — {warehouse_name}"
    )

    if pd.notna(current_month):
        st.caption(
            f"Latest accounting month: "
            f"{current_month:%Y-%m}"
        )

    card1, card2, card3, card4, card5 = st.columns(5)

    card1.metric(
        label="Revenue",
        value=f"¥{current_revenue:,.0f}",
        delta=format_mom(revenue_mom),
    )

    card2.metric(
        label="Direct Cost",
        value=f"¥{current_cost:,.0f}",
        delta=format_mom(cost_mom),
        delta_color="inverse",
    )

    card3.metric(
        label="Gross Profit",
        value=f"¥{current_gross_profit:,.0f}",
        delta=(
            f"¥{gross_profit_change:+,.0f} vs prior month"
            if gross_profit_change is not None
            else "No prior month"
        ),
    )

    card4.metric(
        label="Contribution Profit",
        value=f"¥{current_profit:,.0f}",
        delta=(
            f"¥{profit_change:+,.0f} vs prior month"
            if profit_change is not None
            else "No prior month"
        ),
    )

    card5.metric(
        label="Gross Profit Margin",
        value=(
            f"{current_margin:.2%}"
            if pd.notna(current_margin)
            else "-"
        ),
        delta=(
            f"{margin_change:+.2%} pts"
            if margin_change is not None
            else "No prior month"
        ),
    )
# =========================================================
# Monthly trend
# =========================================================

st.subheader("Monthly Trend")

trend_metric_mapping = {
    "Revenue": revenue_col,
    "Direct Cost": cost_col,
    "Gross Profit": gross_profit_col,
    "Contribution Profit": profit_col,
    "Gross Profit Margin": gross_margin_col,
}

selected_trend_metric = st.selectbox(
    "Select trend metric",
    options=list(trend_metric_mapping.keys()),
)

trend_value_col = trend_metric_mapping[
    selected_trend_metric
]

trend_source = dashboard_df[
    dashboard_df[warehouse_name_col]
    .astype(str)
    .isin(selected_warehouses)
].copy()

trend_source["Month"] = (
    trend_source[date_col]
    .dt.strftime("%Y-%m")
)


if trend_value_col == gross_margin_col:
    trend_df = trend_source.pivot_table(
        index="Month",
        columns=warehouse_name_col,
        values=trend_value_col,
        aggfunc="mean",
    )
else:
    trend_df = trend_source.pivot_table(
        index="Month",
        columns=warehouse_name_col,
        values=trend_value_col,
        aggfunc="sum",
    )

trend_df = trend_df.sort_index()

if trend_df.empty:
    st.info("No monthly trend data is available.")
else:
    st.line_chart(
        trend_df,
        use_container_width=True
    )

st.subheader("Warehouse Profit Details")

st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "月份 Date": st.column_config.DateColumn(
            "月份 Date",
            format="YYYY-MM"
        ),
        "MoM": st.column_config.NumberColumn(
            "MoM",
            format="%.1f%%",
            width="small",
        ),
    }
)