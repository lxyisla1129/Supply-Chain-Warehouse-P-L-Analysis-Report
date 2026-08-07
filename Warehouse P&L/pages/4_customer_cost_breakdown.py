import streamlit as st
from utils import calculate_mom, highlight_profit, WAREHOUSE_NAME_MAPPING, WAREHOUSE_MAPPING

st.set_page_config(
    page_title="Customer Cost Breakdown",
    layout="wide"
)

st.title("Customer Cost Breakdown Dashboard")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from utils import read_data

if "cost_breakdown" not in st.session_state:
    st.warning(
        "Warehouse Operation data is not loaded. "
        "Please upload and process the files on the Data Upload page."
    )

    if st.button(
        "Go to Data Upload",
        type="primary",
        key="go_to_upload_page",
    ):
        st.switch_page("pages/0_Data_Upload.py")

    st.stop()

result = st.session_state["cost_breakdown"].copy()

result["warehouse_name"] = (
        result["warehouse_code"]
        .map(WAREHOUSE_MAPPING)
        .fillna(result["warehouse_code"])
    )

if "dataset_cost" not in st.session_state:
    st.warning("Please upload the Warehouse Cost file on the Data Upload page.")
    st.stop()

dataset_cost = st.session_state["dataset_cost"].copy()

dataset_cost["warehouse_name"] = (
        dataset_cost["warehouse_name"]
        .map(WAREHOUSE_NAME_MAPPING)
        .fillna(result["warehouse_name"])
    )

# st.write(dataset_cost.head(20))
# st.stop()

dataset_cost_category = dataset_cost.groupby(['Month', 'warehouse_name', '对应成本拆分内容'],as_index=False)['净额'].sum()

cost_wide = (
    dataset_cost_category
    .pivot_table(
        index=[
            "Month",
            "warehouse_name",
        ],
        columns="对应成本拆分内容",
        values="净额",
        aggfunc="sum",
        fill_value=0
    )
    .reset_index()
)
# st.write(cost_wide.head(20))


cost_wide.columns.name = None

final_data = result.merge(cost_wide, left_on= ["month",
        "warehouse_name",], right_on=["Month",
        "warehouse_name",], how="left").drop(columns=["Month"], errors="coerce").sort_values(by = ["month", "warehouse_code"], ascending = [False, True])

# st.write(final_data.head(20))
# st.write(final_data.columns.tolist())
# st.stop()

final_data = final_data[
    [
        "month",
        "warehouse_code",
        "warehouse_name",
        "owner_no",
        "owner_name",
        "iv_size_rate",
        "weighted_outbound",
        "weighted_ib_ob",
        "hc_ratio",
        "人员费用 \nPersonnel – Management Staff",
        "其他 Other",
        "叉车费用 Forklift Expenses",
        "房租/物业/保险/税金/网络 \nRent/Property/Insurance/Taxes/Internet",
        "折旧 Depreciation",
        "日常费用 Daily Expense",
        "水费 Water Expense",
        "特定客户分摊\nCustomer-specific Allocation",
        "电费 Electricity Expense",
        "耗材费用 Consumables",
        "配送费用 Distribution Expense",
    ]
].copy()

final_data["Rent Cost Breakdown"] = final_data["房租/物业/保险/税金/网络 \nRent/Property/Insurance/Taxes/Internet"] * final_data["iv_size_rate"]
final_data["Labor Breakdown"] = final_data["人员费用 \nPersonnel – Management Staff"] * final_data["hc_ratio"]
final_data["Consumerable Breakdown"] = final_data["耗材费用 Consumables"] * final_data["weighted_ib_ob"]
final_data["Equipment Breakdown"] = final_data["叉车费用 Forklift Expenses"] * final_data["weighted_ib_ob"]
final_data["Distribution Expense Breakdown"] = final_data["配送费用 Distribution Expense"] * final_data["weighted_outbound"]
final_data["Daily Expense Related Breakdown"] = (final_data["其他 Other"] + final_data["日常费用 Daily Expense"] + final_data["水费 Water Expense"] + final_data["特定客户分摊\nCustomer-specific Allocation"]+ final_data["电费 Electricity Expense"]) * (0.2 * final_data["iv_size_rate"] + 0.4 * final_data["hc_ratio"] + 0.4 * final_data["weighted_outbound"])
final_data["Depreciation Breakdown"] = final_data["折旧 Depreciation"] * (0.2 * final_data["iv_size_rate"] + 0.4 * final_data["hc_ratio"] + 0.4 * final_data["weighted_outbound"])
# final_data["Total Cost"] = final_data["Rent Cost Breakdown"] + final_data["Labor Breakdown"] + final_data["Consumerable Breakdown"] + final_data["Equipment Breakdown"] + final_data["Distribution Expense Breakdown"]+ final_data["Daily Expense Related Breakdown"] + final_data["Depreciation Breakdown"]

breakdown_columns = [
    "Rent Cost Breakdown",
    "Labor Breakdown",
    "Consumerable Breakdown",
    "Equipment Breakdown",
    "Distribution Expense Breakdown",
    "Daily Expense Related Breakdown",
    "Depreciation Breakdown",
]

# Ensure all breakdown columns are numeric
final_data[breakdown_columns] = (
    final_data[breakdown_columns]
    .apply(pd.to_numeric, errors="coerce")
    .fillna(0)
)

# Sum across columns; NaN will not cause the total to disappear
final_data["Total Cost"] = (
    final_data[breakdown_columns]
    .sum(axis=1)
)

# final_data = final_data[["month", "warehouse_code", "warehouse_name", "owner_no", "owner_name", "Rent Cost Breakdown","Labor Breakdown", "Consumerable Breakdown", "Equipment Breakdown", "Distribution Expense Breakdown", "Daily Expense Related Breakdown", "Depreciation Breakdown", "Total Cost"]].fillna(0).reset_index(drop=True)
# st.write(final_data.head(20))

final_data = final_data[
    [
        "month",
        "warehouse_code",
        "warehouse_name",
        "owner_no",
        "owner_name",
        *breakdown_columns,
        "Total Cost",
    ]
].reset_index(drop=True)

month_options = sorted(
    final_data["month"]
    .dropna()
    .unique(),
    reverse=True
)

warehouse_options = sorted(
    final_data["warehouse_name"]
    .dropna()
    .unique()
)

customer_options = sorted(
    final_data["owner_name"]
    .dropna()
    .unique()
)

filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    selected_months = st.multiselect(
        "Month 月份",
        options=month_options,
        default=month_options[:2],
        format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m")
    )

with filter_col2:
    selected_warehouses = st.multiselect(
        "Warehouse 仓库",
        options=warehouse_options,
        default=warehouse_options
    )

with filter_col3:
    selected_customers = st.multiselect(
        "Customer Name 客户",
        options=customer_options
    )

filtered_final_data = final_data.copy()

if selected_months:
    filtered_final_data = filtered_final_data[
        filtered_final_data["month"].isin(selected_months)
    ]

if selected_warehouses:
    filtered_final_data = filtered_final_data[
        filtered_final_data["warehouse_name"].isin(selected_warehouses)
    ]

if selected_customers:
    filtered_final_data = filtered_final_data[
        filtered_final_data["owner_name"].isin(selected_customers)
    ]

if filtered_final_data.empty:
    st.warning("No data is available for the selected filters.")
    st.stop()

# ============================================================
# COST CATEGORY CONFIGURATION
# ============================================================

cost_columns = [
    "Rent Cost Breakdown",
    "Labor Breakdown",
    "Consumerable Breakdown",
    "Equipment Breakdown",
    "Distribution Expense Breakdown",
    "Daily Expense Related Breakdown",
    "Depreciation Breakdown",
]

cost_name_mapping = {
    "Rent Cost Breakdown": "租金等 Rent",
    "Labor Breakdown": "人力成本 Labor",
    "Consumerable Breakdown": "耗材费用 Consumables",
    "Equipment Breakdown": "设备费用 Equipment",
    "Distribution Expense Breakdown": "配送费 Distribution",
    "Daily Expense Related Breakdown": "日常费用/其他 Daily/ Other",
    "Depreciation Breakdown": "折旧 Depreciation",
}

for column in cost_columns + ["Total Cost"]:
    filtered_final_data[column] = pd.to_numeric(
        filtered_final_data[column],
        errors="coerce"
    ).fillna(0)

overview_tab, rank_tab, trend_tab, breakdown_tab, detail_tab = st.tabs(
    [
        "Cost Overview",
        "Top Customer Cost Composition",
        "Monthly Customer Cost Trend by Category",
        "Cost Breakdown",
        "Detail Table",
    ]
)

# ============================================================
# KPI CARDS
# ============================================================

with overview_tab:

    total_cost = filtered_final_data["Total Cost"].sum()

    customer_count = filtered_final_data["owner_no"].nunique()

    warehouse_count = filtered_final_data["warehouse_name"].nunique()

    average_customer_cost = (
        total_cost / customer_count
        if customer_count > 0
        else 0
    )

    largest_cost_category = (
        filtered_final_data[cost_columns]
        .sum()
        .idxmax()
    )

    largest_cost_value = (
        filtered_final_data[cost_columns]
        .sum()
        .max()
    )

    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.metric(
            "Total Allocated Cost 总分摊成本",
            f"${total_cost:,.2f}"
        )

    with kpi_col2:
        st.metric(
            "Customers 客户数量",
            f"{customer_count:,}"
        )

    with kpi_col3:
        st.metric(
            "Average Cost / Customer 客户平均成本",
            f"${average_customer_cost:,.2f}"
        )

    with kpi_col4:
        st.metric(
            "Largest Cost Category 最大成本类别",
            cost_name_mapping.get(
                largest_cost_category,
                largest_cost_category
            ),
            delta=f"${largest_cost_value:,.2f}",
            delta_color="off"
        )


# ============================================================
# MONTHLY COST TREND
# ============================================================

with trend_tab:
    st.subheader(
        "Customer Monthly Cost Trend by Category "
    )

    trend_source = filtered_final_data.copy()

    # --------------------------------------------------------
    # Prepare data
    # --------------------------------------------------------

    trend_source["month"] = pd.to_datetime(
        trend_source["month"],
        errors="coerce",
    )

    for column in cost_columns:
        trend_source[column] = pd.to_numeric(
            trend_source[column],
            errors="coerce",
        ).fillna(0)

    trend_source = trend_source.dropna(
        subset=[
            "month",
            "warehouse_name",
            "owner_no",
            "owner_name",
        ]
    )

    if trend_source.empty:
        st.info("No customer trend data is available.")
        st.stop()

    # --------------------------------------------------------
    # Select warehouse first
    # --------------------------------------------------------

    selector_col1, selector_col2, selector_col3 = st.columns(3)

    warehouse_options_for_trend = sorted(
        trend_source["warehouse_name"]
        .dropna()
        .astype(str)
        .unique()
    )

    with selector_col1:
        selected_trend_warehouse = st.selectbox(
            "Select Warehouse",
            options=warehouse_options_for_trend,
            key="customer_category_trend_warehouse",
        )

    warehouse_trend_source = trend_source[
        trend_source["warehouse_name"]
        .astype(str)
        .eq(selected_trend_warehouse)
    ].copy()

    # --------------------------------------------------------
    # Customer options depend on selected warehouse
    # --------------------------------------------------------

    customer_options_for_trend = (
        warehouse_trend_source[
            [
                "owner_no",
                "owner_name",
            ]
        ]
        .drop_duplicates()
        .sort_values("owner_name")
    )

    customer_label_mapping = dict(
        zip(
            customer_options_for_trend["owner_no"].astype(str),
            customer_options_for_trend["owner_name"].astype(str),
        )
    )

    with selector_col2:
        selected_trend_customer = st.selectbox(
            "Select Customer",
            options=customer_options_for_trend[
                "owner_no"
            ].astype(str).tolist(),
            format_func=lambda customer_code: (
                customer_label_mapping.get(
                    customer_code,
                    customer_code,
                )
            ),
            key="customer_category_trend_customer",
        )

    # --------------------------------------------------------
    # Category selector
    # --------------------------------------------------------

    category_display_mapping = {
        column: cost_name_mapping.get(column, column)
        for column in cost_columns
    }

    with selector_col3:
        selected_trend_categories = st.multiselect(
            "Select Cost Categories",
            options=cost_columns,
            default=cost_columns,
            format_func=lambda column: (
                category_display_mapping.get(
                    column,
                    column,
                )
            ),
            key="customer_category_trend_categories",
        )

    if not selected_trend_categories:
        st.info("Please select at least one cost category.")
        st.stop()

    # --------------------------------------------------------
    # Filter selected customer
    # --------------------------------------------------------

    customer_trend_source = warehouse_trend_source[
        warehouse_trend_source["owner_no"]
        .astype(str)
        .eq(selected_trend_customer)
    ].copy()

    selected_customer_name = customer_label_mapping.get(
        selected_trend_customer,
        selected_trend_customer,
    )

    # --------------------------------------------------------
    # Aggregate one row per month
    # --------------------------------------------------------

    customer_monthly_category = (
        customer_trend_source
        .groupby(
            "month",
            as_index=False,
        )[selected_trend_categories]
        .sum()
        .sort_values("month")
    )

    customer_monthly_category["Month"] = (
        customer_monthly_category["month"]
        .dt.to_period("M")
        .astype(str)
    )

    # Convert wide data to long data for Plotly
    customer_monthly_long = (
        customer_monthly_category
        .melt(
            id_vars=["Month"],
            value_vars=selected_trend_categories,
            var_name="Cost Category",
            value_name="Allocated Cost",
        )
    )

    customer_monthly_long["Cost Category"] = (
        customer_monthly_long["Cost Category"]
        .map(category_display_mapping)
    )

    if customer_monthly_long.empty:
        st.info(
            "No monthly category cost is available for "
            "the selected customer."
        )

    else:
        category_trend_chart = px.line(
            customer_monthly_long,
            x="Month",
            y="Allocated Cost",
            color="Cost Category",
            markers=True,
            title=(
                f"{selected_trend_warehouse} — "
                f"{selected_customer_name} "
                "Monthly Cost by Category"
            ),
            labels={
                "Month": "Month",
                "Allocated Cost": "Allocated Cost",
                "Cost Category": "Cost Category",
            },
        )

        category_trend_chart.update_layout(
            xaxis_title="Month",
            yaxis_title="Allocated Cost (¥)",
            legend_title_text="Cost Category",
            hovermode="x unified",
            height=650,
        )

        category_trend_chart.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=sorted(
                customer_monthly_long["Month"].unique()
            ),
        )

        category_trend_chart.update_yaxes(
            tickprefix="¥",
            tickformat=",.0f",
        )

        category_trend_chart.update_traces(
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "Month: %{x}<br>"
                "Cost: ¥%{y:,.2f}"
                "<extra></extra>"
            )
        )

        st.plotly_chart(
            category_trend_chart,
            use_container_width=True,
        )

        # ----------------------------------------------------
        # Optional detail table
        # ----------------------------------------------------

        with st.expander("View Customer Monthly Category Cost"):
            category_detail_table = (
                customer_monthly_category
                .drop(columns=["month"])
                .rename(
                    columns={
                        **category_display_mapping,
                    }
                )
            )

            currency_columns_for_trend = [
                category_display_mapping[column]
                for column in selected_trend_categories
            ]

            st.dataframe(
                category_detail_table.style.format(
                    {
                        column: "¥{:,.2f}"
                        for column in currency_columns_for_trend
                    },
                    na_rep="-",
                ),
                use_container_width=True,
                hide_index=True,
            )

# ============================================================
# CUSTOMER COST SUMMARY
# ============================================================

    customer_cost_summary = (
        filtered_final_data
        .groupby(
            [
                "owner_no",
                "owner_name",
            ],
            as_index=False
        )[cost_columns + ["Total Cost"]]
        .sum()
    )

    customer_cost_summary = customer_cost_summary.sort_values(
        "Total Cost",
        ascending=False
    )


# ============================================================
# TOP CUSTOMER COST BAR CHART
# ============================================================

with rank_tab:
    # chart_col1, chart_col2 = st.columns(2)

    # with chart_col1:
    #     st.subheader("Top Customers by Cost 客户成本排名")

    top_n = st.slider(
            "Number of customers to display",
            min_value=5,
            max_value=min(
                30,
                max(5, len(customer_cost_summary))
            ),
            value=min(
                10,
                max(5, len(customer_cost_summary))
            )
        )

    top_customers = customer_cost_summary.head(top_n)

    #     top_customer_chart = px.bar(
    #         top_customers.sort_values(
    #             "Total Cost",
    #             ascending=True
    #         ),
    #         x="Total Cost",
    #         y="owner_name",
    #         orientation="h",
    #         title=f"Top {top_n} Customers by Allocated Cost"
    #     )

    #     top_customer_chart.update_layout(
    #         xaxis_title="Allocated Cost ($)",
    #         yaxis_title="Customer",
    #         height=max(450, top_n * 35)
    #     )

    #     top_customer_chart.update_traces(
    #         hovertemplate=(
    #             "Customer: %{y}<br>"
    #             "Cost: $%{x:,.2f}"
    #             "<extra></extra>"
    #         )
    #     )

    #     st.plotly_chart(
    #         top_customer_chart,
    #         use_container_width=True
    #     )


    # ============================================================
    # OVERALL COST COMPOSITION DONUT
    # ============================================================

    # with chart_col2:
    #     # st.subheader("Cost Composition 成本构成")

    #     # category_totals = (
    #     #     filtered_final_data[cost_columns]
    #     #     .sum()
    #     #     .reset_index()
    #     # )

    #     # category_totals.columns = [
    #     #     "Cost Category",
    #     #     "Allocated Cost",
    #     # ]

    #     # category_totals["Cost Category"] = (
    #     #     category_totals["Cost Category"]
    #     #     .map(cost_name_mapping)
    #     # )

    #     # category_totals = category_totals[
    #     #     category_totals["Allocated Cost"] != 0
    #     # ]

    #     # composition_chart = px.pie(
    #     #     category_totals,
    #     #     names="Cost Category",
    #     #     values="Allocated Cost",
    #     #     hole=0.45,
    #     #     title="Overall Cost Composition"
    #     # )

    #     # composition_chart.update_traces(
    #     #     textposition="inside",
    #     #     textinfo="percent+label",
    #     #     hovertemplate=(
    #     #         "%{label}<br>"
    #     #         "$%{value:,.2f}<br>"
    #     #         "%{percent}"
    #     #         "<extra></extra>"
    #     #     )
    #     # )

    #     # st.plotly_chart(
    #     #     composition_chart,
    #     #     use_container_width=True
    #     # )

    #     px.treemap(
    #     top_customers,
    #     path=["owner_name"],
    #     values="Total Cost",
    # )
    # with chart_col2:
    st.subheader("Customer Cost Composition 客户成本构成")

    treemap_chart = px.treemap(
            top_customers,
            path=["owner_name"],
            values="Total Cost",
            title=f"Top {top_n} Customer Cost Composition",
            custom_data=[
                "owner_no",
                "Total Cost",
            ],
        )

    treemap_chart.update_traces(
            texttemplate=(
                "<b>%{label}</b><br>"
                "¥%{value:,.0f}"
            ),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Customer Code: %{customdata[0]}<br>"
                "Allocated Cost: ¥%{value:,.2f}"
                "<extra></extra>"
            ),
        )

    treemap_chart.update_layout(
            height=max(450, top_n * 35),
            margin=dict(
                l=10,
                r=10,
                t=50,
                b=10,
            ),
        )

    st.plotly_chart(
            treemap_chart,
            use_container_width=True,
        )


# ============================================================
# STACKED COST BREAKDOWN BY CUSTOMER
# ============================================================

with breakdown_tab:

    breakdown_customer_count = st.slider(
        "Customers shown in cost breakdown",
        min_value=5,
        max_value=min(
            30,
            max(5, len(customer_cost_summary))
        ),
        value=min(
            15,
            max(5, len(customer_cost_summary))
        ),
        key="breakdown_customer_count"
    )

    breakdown_data = customer_cost_summary.head(
        breakdown_customer_count
    )

    breakdown_long = breakdown_data.melt(
        id_vars=[
            "owner_no",
            "owner_name",
        ],
        value_vars=cost_columns,
        var_name="Cost Category",
        value_name="Allocated Cost"
    )

    breakdown_long["Cost Category"] = (
        breakdown_long["Cost Category"]
        .map(cost_name_mapping)
    )

    breakdown_long = breakdown_long[
        breakdown_long["Allocated Cost"] != 0
    ]

    stacked_chart = px.bar(
        breakdown_long,
        x="owner_name",
        y="Allocated Cost",
        color="Cost Category",
        title="Allocated Cost by Customer and Cost Category",
        barmode="stack"
    )

    stacked_chart.update_layout(
        xaxis_title="Customer",
        yaxis_title="Allocated Cost ($)",
        legend_title="Cost Category",
        height=600,
        xaxis_tickangle=-45
    )

    stacked_chart.update_traces(
        hovertemplate=(
            "Customer: %{x}<br>"
            "Cost: $%{y:,.2f}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        stacked_chart,
        use_container_width=True
    )


    # ============================================================
    # 100% STACKED COST STRUCTURE
    # ============================================================

    st.subheader("Customer Cost Structure 客户成本结构")

    customer_percentage_data = breakdown_data.copy()

    for column in cost_columns:
        customer_percentage_data[column] = np.where(
            customer_percentage_data["Total Cost"] != 0,
            customer_percentage_data[column]
            / customer_percentage_data["Total Cost"],
            0
        )

    percentage_long = customer_percentage_data.melt(
        id_vars=[
            "owner_no",
            "owner_name",
        ],
        value_vars=cost_columns,
        var_name="Cost Category",
        value_name="Cost Percentage"
    )

    percentage_long["Cost Category"] = (
        percentage_long["Cost Category"]
        .map(cost_name_mapping)
    )

    percentage_chart = px.bar(
        percentage_long,
        x="owner_name",
        y="Cost Percentage",
        color="Cost Category",
        barmode="stack",
        title="Percentage Cost Structure by Customer"
    )

    percentage_chart.update_layout(
        xaxis_title="Customer",
        yaxis_title="Percentage of Total Cost",
        yaxis_tickformat=".0%",
        legend_title="Cost Category",
        height=600,
        xaxis_tickangle=-45
    )

    percentage_chart.update_traces(
        hovertemplate=(
            "Customer: %{x}<br>"
            "Share: %{y:.1%}"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        percentage_chart,
        use_container_width=True
    )

with detail_tab:
# ============================================================
# MONTHLY CUSTOMER DETAIL TABLE
# ============================================================



    detail_table = (
        filtered_final_data
        .groupby(
            [
                "month",
                "warehouse_name",
                "owner_no",
                "owner_name",
            ],
            as_index=False
        )[cost_columns + ["Total Cost"]]
        .sum()
    )

    detail_table["month"] = pd.to_datetime(
        detail_table["month"]
    ).dt.strftime("%Y-%m")

    detail_table = detail_table.rename(
        columns={
            "month": "月份 Month",
            "warehouse_name": "仓库 Warehouse",
            "owner_no": "客户代码 Customer Code",
            "owner_name": "客户名称 Customer Name",
            **cost_name_mapping,
            "Total Cost": "总分摊成本 Total Allocated Cost",
        }
    )

    detail_table = detail_table.sort_values(
        [
            "月份 Month",
            "仓库 Warehouse",
            "客户名称 Customer Name",
            "总分摊成本 Total Allocated Cost",
        ],
        ascending=[
            False,
            True,
            True,
            False,
        ]
    )

    detail_table["上月成本 Previous Month Cost"] = (
            detail_table.groupby(
                ["仓库 Warehouse",
                "客户名称 Customer Name",
                ]
            )
            ["总分摊成本 Total Allocated Cost"]
            .shift(1)
        )
        
    detail_table["MoM"] = detail_table.apply(
            lambda row: calculate_mom(
                row["总分摊成本 Total Allocated Cost"],
                row["上月成本 Previous Month Cost"]
            ),
            axis=1
        )

    currency_columns = [
        "租金等 Rent",
        "人力成本 Labor",
        "耗材费用 Consumables",
        "设备费用 Equipment",
        "配送费 Distribution",
        "日常费用/其他 Daily/ Other",
        "折旧 Depreciation",
        "总分摊成本 Total Allocated Cost",
        "上月成本 Previous Month Cost",
    ]

    st.dataframe(
    detail_table.style.map(
        highlight_profit,
        subset=["MoM"]
    ).format(
        {
            **{column: "¥{:,.2f}" for column in currency_columns},
            "MoM": "{:.1%}",
        },
        na_rep="-",
    ),
    column_config={
        "MoM": st.column_config.NumberColumn(
            "MoM",
            format="%.1f%%",
            width="small",
        )
        },
    use_container_width=True,
    hide_index=True,
    height=600,
)












    


