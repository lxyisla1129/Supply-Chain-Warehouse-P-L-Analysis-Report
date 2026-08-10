import pandas as pd
import streamlit as st
import plotly.express as px
from utils import calculate_mom, highlight_profit, WAREHOUSE_NAME_MAPPING, highlight_cost_mom
from st_aggrid import AgGrid, GridOptionsBuilder



st.set_page_config(
    page_title="Warehouse Operation Cost",
    layout="wide"
)

st.title("Warehouse Operation Cost Dashboard")

if "dataset_cost" not in st.session_state:
    st.warning(
        "Warehouse cost data is not loaded. "
        "Please upload and process the files on the Data Upload page."
    )

    if st.button(
        "Go to Data Upload",
        type="primary",
        key="go_to_upload_page",
    ):
        st.switch_page("pages/0_Data_Upload.py")

    st.stop()

dataset_cost = st.session_state["dataset_cost"].copy()

# 先做权限过滤
# warehouse_profit = filter_by_warehouse(
#     warehouse_profit,
#     warehouse_column="仓编码",
#     access=access
# )


# Sidebar filters

dataset_cost["仓名称 Warehouse Name"] = (
        dataset_cost["warehouse_name"]
        .map(WAREHOUSE_NAME_MAPPING)
        .fillna(dataset_cost["warehouse_name"])
    )

dataset_cost = dataset_cost.drop(columns = ['warehouse_name'])

warehouse_options = sorted(
    dataset_cost["仓名称 Warehouse Name"]
    .dropna()
    .astype(str)
    .unique()
)

selected_warehouses = st.sidebar.multiselect(
    "Warehouse",
    options=warehouse_options,
    default=warehouse_options
)

filtered_raw = dataset_cost[
    dataset_cost["仓名称 Warehouse Name"]
    .astype(str)
    .isin(selected_warehouses)
].copy()

date_values = filtered_raw["日期_day"].dropna()

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
            filtered_raw["日期_day"]
            .dt.to_period("M")
            .astype(str)
            .isin(selected_months)
        ].copy()

# date_values = filtered_raw["日期_day"].dropna()

# if not date_values.empty:
#     min_date = date_values.min().date()
#     max_date = date_values.max().date()

#     selected_dates = st.sidebar.date_input(
#         "Date Range",
#         value=(min_date, max_date)
#     )

#     if len(selected_dates) == 2:
#         start_date, end_date = selected_dates

#         filtered_raw = filtered_raw[
#             filtered_raw["日期_day"]
#             .dt.date
#             .between(start_date, end_date)
#         ]

category_options = sorted(
    dataset_cost["对应成本拆分内容"]
    .dropna()
    .unique()
)

selected_categories = st.sidebar.multiselect(
    "Cost Category",
    options=category_options,
    default=category_options
)

filtered_cost = dataset_cost[dataset_cost["仓名称 Warehouse Name"].isin(selected_warehouses) 
                             & dataset_cost["对应成本拆分内容"].isin(selected_categories)
                             & dataset_cost["Month"].isin(selected_months)].copy()

if filtered_cost.empty:
    st.warning("No data is available.")
    st.stop()

# 1. Cost percentage pie chart

st.header("Cost Structure")

# Select one month for all four warehouse pies
month_options = sorted(dataset_cost["Month"].dropna().unique())

selected_month = st.selectbox(
    "Select Month",
    options=month_options,
    index=len(month_options) - 1,
    format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m")
)

month_cost = dataset_cost[
    dataset_cost["Month"].eq(selected_month)
].copy()

warehouses = [
    "LAX1",
    "LAX2",
    "LAX4",
    "LAX5",
]

# warehouse_labels = {
#     "美国洛杉矶大件1号仓": "LAX1",
#     "美国洛杉矶中小件2号仓": "LAX2",
#     "美国洛杉矶中小件4号仓": "LAX4",
#     "美国洛杉矶大件5号仓": "LAX5",
# }

st.subheader(
    f"Cost Structure by Warehouse — "
    f"{pd.Timestamp(selected_month):%Y-%m}"
)

for start in range(0, len(warehouses), 2):
    chart_columns = st.columns(2)

    for column, warehouse in zip(
        chart_columns,
        warehouses[start:start + 2]
    ):
        pie_data = (
            month_cost[
                month_cost["仓名称 Warehouse Name"].eq(warehouse)
            ]
            .groupby(
                "对应成本拆分内容",
                as_index=False
            )["净额"]
            .sum()
            .sort_values("净额", ascending=False)
        )

        all_categories = sorted(
            dataset_cost["对应成本拆分内容"]
            .dropna()
            .unique()
            )
        
        color_list = ( px.colors.qualitative.Plotly + px.colors.qualitative.Light24 )
        
        category_colors = {
            category: color_list[index % len(color_list)]
            for index, category in enumerate(all_categories)
            }

        with column:
            if pie_data.empty or pie_data["净额"].sum() == 0:
                st.info(
                    f"No data for {warehouse}"
                )
                continue

            fig = px.pie(
                pie_data,
                names="对应成本拆分内容",
                values="净额",
                color="对应成本拆分内容",
                color_discrete_map=category_colors,
                hole=0.45,
                title=warehouse
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Cost: ¥%{value:,.0f}<br>"
                    "Share: %{percent}"
                    "<extra></extra>"
                )
            )

            fig.update_layout(
                height=420,
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                ),
                legend_title_text="Cost Category"
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"cost_pie_{warehouse}_{selected_month}"
            )

st.header("Cost Category Performance")

warehouse_col = "仓名称 Warehouse Name"
date_col = "Month"

dashboard_df = filtered_cost.copy()

dashboard_df[date_col] = pd.to_datetime(
    dashboard_df[date_col],
    errors="coerce"
)

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
    key="kpi_warehouse_selector"
)

warehouse_card_df = (
    dashboard_df[
        dashboard_df[warehouse_col]
        .astype(str)
        .eq(selected_card_warehouse)
    ]
    .sort_values(date_col)
    .copy()
)

if warehouse_card_df.empty:
    st.warning("No warehouse data available.")
    st.stop()

monthly_category = (
    warehouse_card_df
    .groupby(
        [
            "Month",
            "对应成本拆分内容",
        ],
        as_index=False
    )["净额"]
    .sum()
    .sort_values(
        [
            "对应成本拆分内容",
            "Month",
        ]
    )
)

monthly_category["Month"] = pd.to_datetime(
    monthly_category["Month"],
    format="%Y-%m"
)

latest_month = monthly_category["Month"].max()
previous_month = latest_month - pd.DateOffset(months=1)

latest_category = (
    monthly_category[
        monthly_category["Month"].eq(latest_month)
    ]
    .set_index("对应成本拆分内容")["净额"]
)

previous_category = (
    monthly_category[
        monthly_category["Month"].eq(previous_month)
    ]
    .set_index("对应成本拆分内容")["净额"]
)

st.caption(
    f"Latest month: {latest_month:%Y-%m} | "
    f"Comparison month: {previous_month:%Y-%m}"
)

card_categories = (
    latest_category
    .sort_values(ascending=False)
    .index
    .tolist()
)

# Four cards per row
for start in range(0, len(card_categories), 4):
    row_categories = card_categories[start:start + 4]
    card_columns = st.columns(4)

    for card, category in zip(card_columns, row_categories):
        current_cost = latest_category.get(category, 0)
        previous_cost = previous_category.get(category, pd.NA)

        mom = calculate_mom(
            current_cost,
            previous_cost
        )

        card.metric(
            label=category,
            value=f"¥{current_cost:,.0f}",
            delta=(
                f"{mom:+.1%} MoM"
                if mom is not None
                else "No prior month"
            ),
            # Cost increase is generally unfavorable
            delta_color="inverse"
        )


st.header("Warehouse Category Monthly Trend")

# Make a copy to avoid changing the original dataframe
# trend_source = filtered_cost.copy()

# # Make sure Month is a datetime column
# trend_source["Month"] = pd.to_datetime(
#     trend_source["Month"],
#     errors="coerce",
# )

# # Make sure cost is numeric
# trend_source["净额"] = pd.to_numeric(
#     trend_source["净额"],
#     errors="coerce",
# )

# # Remove rows missing required values
# trend_source = trend_source.dropna(
#     subset=[
#         "Month",
#         "仓名称 Warehouse Name",
#         "对应成本拆分内容",
#         "净额",
#     ]
# )

# Aggregate cost by month, warehouse, and cost category
warehouse_options_for_trends = sorted(
    dashboard_df[warehouse_col]
    .dropna()
    .astype(str)
    .unique()
)

selected_trend_warehouse = st.selectbox(
    "Select a warehouse for Monthly Trend",
    options=warehouse_options_for_trends,
    key="trend_warehouse_selector"
)

warehouse_trend_df = (
    dashboard_df[
        dashboard_df[warehouse_col]
        .astype(str)
        .eq(selected_trend_warehouse)
    ]
    .sort_values(date_col)
    .copy()
)

warehouse_trend_df["Month"] = (
    pd.to_datetime(
        warehouse_trend_df["Month"],
        errors="coerce",
    )
    .dt.to_period("M")
    .dt.to_timestamp()
)

if warehouse_trend_df.empty:
    st.warning("No warehouse data available.")
    st.stop()

monthly_cost = (
    warehouse_trend_df
    .groupby(
        [
            "Month",
            "仓名称 Warehouse Name",
            "对应成本拆分内容",
        ],
        as_index=False,
    )["净额"]
    .sum()
    .rename(
        columns={
            "净额": "Cost",
            "对应成本拆分内容": "Cost Category",
        }
    )
    .sort_values(
        [
            "仓名称 Warehouse Name",
            "Cost Category",
            "Month",
        ]
    )
)

# st.write(
#     monthly_cost.head(20)
# )
# st.stop()

if monthly_cost.empty:
    st.info("No monthly cost trend data is available.")

else:

    if monthly_cost.empty:
        st.info(
            "No data is available for the selected warehouse "
            "and cost categories."
        )

    else:
        monthly_trend_chart = px.line(
            monthly_cost,
            x="Month",
            y="Cost",
            color="Cost Category",
            color_discrete_sequence=px.colors.qualitative.Set2,
            markers=True,
            title=(
                f"{selected_trend_warehouse} "
                "Monthly Cost Trend by Category"
            ),
            labels={
                "Month": "Month",
                "Cost": "Cost (¥)",
                "Cost Category": "Cost Category",
            },
        )

        monthly_trend_chart.update_layout(
            xaxis_title="Month",
            yaxis_title="Cost (¥)",
            hovermode="x unified",
            legend_title_text="Cost Category",
        )

        monthly_trend_chart.update_xaxes(
            tickformat="%Y-%m",
            dtick="M1",
            ticklabelmode="period",
        )

        monthly_trend_chart.update_yaxes(
            tickprefix="¥",
            tickformat=",.0f",
        )

        monthly_trend_chart.update_traces(
            hovertemplate=(
                "Month: %{x|%Y-%m}<br>"
                "Cost: ¥%{y:,.2f}"
                "<extra></extra>"
            )
        )

        st.plotly_chart(
            monthly_trend_chart,
            use_container_width=True,
        )

    # -----------------------------------------------------
    # Detail table
    # -----------------------------------------------------

    with st.expander("View Monthly Category Cost Data"):
        display_monthly_cost = (
            monthly_cost
            .sort_values(
                [
                    "Month",
                    "Cost Category",
                ]
            )
            .copy()
        )

        st.dataframe(
            display_monthly_cost,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Month": st.column_config.DateColumn(
                    "Month",
                    format="YYYY-MM",
                ),
                "Cost": st.column_config.NumberColumn(
                    "Cost",
                    format="¥%.2f",
                ),
            },
        )

st.header("Cost Tables")

tab1, tab2, tab3 = st.tabs(
    [
        "Category Summary",
        "Account Detail",
        "Monthly Detail",
    ]
)


# Table 1: Category summary
with tab1:
    category_table = (
        filtered_cost
        .groupby(
            "对应成本拆分内容",
            as_index=False
        )["净额"]
        .sum()
    )

    total_cost = category_table["净额"].sum()

    category_table["占比 / Share"] = (
        category_table["净额"]
        .div(total_cost)
        if total_cost != 0
        else 0
    )

    category_table = (
        category_table
        .rename(
            columns={
                "对应成本拆分内容": (
                    "成本类别 Cost Category"
                ),
                "净额": "成本 Cost",
            }
        )
        .sort_values(
            "成本 Cost",
            ascending=False
        )
    )

    st.dataframe(
        category_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "成本 Cost": (
                st.column_config.NumberColumn(
                    "成本 Cost",
                    format="¥%,.0f"
                )
            ),
            "占比 / Share": (
                st.column_config.NumberColumn(
                    "占比 Share",
                    format="percent"
                )
            ),
        }
    )


# Table 2: Account-level detail
with tab2:
    account_table = (
        filtered_cost
        .groupby(
            [
                "仓名称 Warehouse Name",
                "对应成本拆分内容",
                "管报科目名称",
            ],
            as_index=False
        )["净额"]
        .sum()
        .rename(
            columns={
                "仓名称 Warehouse Name": (
                    "仓库 Warehouse"
                ),
                "对应成本拆分内容": (
                    "成本类别 Cost Category"
                ),
                "管报科目名称": (
                    "成本科目 Cost Account"
                ),
                "净额": "成本 Cost",
            }
        )
        .sort_values(
            ["仓库 Warehouse",
            "成本 Cost"],
            ascending=[False, False]
        )
    )

    st.dataframe(
        account_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "成本 Cost": (
                st.column_config.NumberColumn(
                    "成本 Cost",
                    format="¥%,.0f"
                )
            )
        }
    )


# Table 3: Monthly warehouse/category detail
with tab3:
    monthly_table = (
        filtered_cost
        .groupby(
            [
                "Month",
                "仓名称 Warehouse Name",
                "对应成本拆分内容",
                "管报科目名称"
            ],
            as_index=False
        )["净额"]
        .sum()
        .rename(
            columns={
                "Month": "月份 Month",
                "仓名称 Warehouse Name": (
                    "仓库 Warehouse"
                ),
                "对应成本拆分内容": (
                    "成本类别 Cost Category"
                ),
                "管报科目名称": (
                    "成本科目 Cost Account"
                ),
                "净额": "成本 Cost",
            }
        )
        .sort_values(
            [
                "月份 Month",
                "仓库 Warehouse",
                "成本 Cost",
            ],
            ascending=[
                True,
                True,
                False,
            ]
        )
    )

    monthly_table["Previous Month Cost"] = (
        monthly_table
        .groupby(
            [
                "仓库 Warehouse",
                "成本类别 Cost Category",
                "成本科目 Cost Account",
            ]
        )["成本 Cost"]
        .shift(1)
    )
    
    monthly_table["MoM"] = monthly_table.apply(
        lambda row: calculate_mom(
            row["成本 Cost"],
            row["Previous Month Cost"]
        ),
        axis=1
    )

    monthly_table = (
        monthly_table
        .rename(
            columns={
                # "Month": "月份 Month",
                # "warehouse_name": "仓库 Warehouse",
                # "对应成本拆分内容": "成本类别 Cost Category",
                # "管报科目名称": "成本科目 Cost Account",
                # "净额": "成本 Cost",
                "Previous Month Cost": "上月成本 Previous Month Cost",
            }
        )
        .sort_values(
            [
                "月份 Month",
                "仓库 Warehouse",
                "成本 Cost",
            ],
            ascending=[
                False,
                True,
                False,
            ]
        )
    )

    styled_df = (
    monthly_table
    .style
    .map(
        highlight_cost_mom,
        subset=["MoM"]
    )
    .format(
        {
            "成本 Cost": "¥{:,.0f}",
            "上月成本 Previous Month Cost": "¥{:,.0f}",
            "MoM": "{:.1%}",
        },
        na_rep="-"
    )

    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "月份 Month": st.column_config.DateColumn(
                "月份 Month",
                format="YYYY-MM"
            ),
            "MoM": st.column_config.NumberColumn(
                "MoM",
                # format="%.1f%%",
                width="small",
            ),
            # "成本 Cost": st.column_config.NumberColumn(
            #     "成本 Cost",
            #     format="¥%,.0f"
            # ),
            # "上月成本 Previous Month Cost": (
            #     st.column_config.NumberColumn(
            #         "上月成本 Previous Month Cost",
            #         format="¥%,.0f"
            #     )
            # ),
            # "MoM": st.column_config.NumberColumn(
            #     "MoM",
            #     format="%.1f%%"
            # ),
        }
    )

st.header("Warehouse Operation Cost Data Details")

if "operation_cost" not in st.session_state:
    st.warning("Please upload the Warehouse Cost file on the Data Upload page.")
    st.stop()

operation_cost = st.session_state["operation_cost"].copy()

with st.expander("View Cost Data Detail"):

    gb = GridOptionsBuilder.from_dataframe(operation_cost)

    gb.configure_default_column(
            filter=True,
            sortable=True,
            resizable=True
        )

    gb.configure_pagination(
            enabled=True,
            paginationPageSize=50
        )

    grid_options = gb.build()

    AgGrid(
            operation_cost,
            gridOptions=grid_options,
            height=650,
            fit_columns_on_grid_load=False
        )