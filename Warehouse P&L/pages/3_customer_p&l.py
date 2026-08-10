import streamlit as st
from utils import calculate_mom, read_data, highlight_profit, load_customer_pnl

st.set_page_config(
    page_title="Customer P&L",
    layout="wide"
)

st.title("Customer P&L Dashboard")

import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

# Read processed Customer P&L data from the shared upload page
if "customer_profit" not in st.session_state:
    st.warning(
        "Customer P&L data is not loaded. "
        "Please upload and process the files on the Data Upload page."
    )

    if st.button(
        "Go to Data Upload",
        type="primary",
        key="go_to_upload_page",
    ):
        st.switch_page("pages/0_Data_Upload.py")

    st.stop()

customer_profit = st.session_state["customer_profit"].copy()

outbound_data = (
    st.session_state["outbound_data"]
    .copy()
)

inbound_data = (
    st.session_state["inbound_data"]
    .copy()
)

filter_col1, filter_col2, filter_col3 = st.columns(3)

month_options = sorted(
    customer_profit["Month"]
    .dropna()
    .unique(),
    reverse=True
)

warehouse_options = sorted(
    customer_profit["warehouse_name"]
    .dropna()
    .unique()
)

customer_options = sorted(
    customer_profit["customer_name"]
    .dropna()
    .unique()
)

with filter_col1:
    selected_months = st.multiselect(
        "Month",
        options=month_options,
        default=month_options[:2],
        format_func=lambda x: pd.Timestamp(x).strftime("%Y-%m")
    )

with filter_col2:
    selected_warehouses = st.multiselect(
        "Warehouse",
        options=warehouse_options,
        default=warehouse_options
    )

with filter_col3:
    selected_customers = st.multiselect(
        "Customer Name",
        options=customer_options
    )

filtered_customer_profit = customer_profit.copy()

if selected_months:
    filtered_customer_profit = filtered_customer_profit[
        filtered_customer_profit["Month"].isin(
            selected_months
        )
    ]

if selected_warehouses:
    filtered_customer_profit = filtered_customer_profit[
        filtered_customer_profit["warehouse_name"].isin(
            selected_warehouses
        )
    ]

if selected_customers:
    filtered_customer_profit = filtered_customer_profit[
        filtered_customer_profit["customer_name"].isin(
            selected_customers
        )
    ]

# KPI Cards

chart_tab, customer_tab, monthly_tab, exception_tab = st.tabs(
    [
        "Customer Profit Chart",
        "Customer Detail",
        "Monthly Detail",
        "Exception Customer Detail"
    ]
)

with chart_tab:
    customer_chart_df = (
        filtered_customer_profit
        .groupby(
            [
                "customer_code",
                "customer_name",
            ],
            as_index=False
        )[
            [
                "Income",
                "Cost",
                "Profit",
            ]
        ]
        .sum()
        .sort_values(
            "Profit",
            ascending=False
        )
    )

    customer_chart_df["Margin"] = np.where(
        customer_chart_df["Income"] != 0,
        customer_chart_df["Profit"]
        / customer_chart_df["Income"],
        np.nan
    )

    chart_limit = st.slider(
        "Number of customers to display",
        min_value=1,
        max_value=min(
            50,
            max(5, len(customer_chart_df))
        ),
        value=min(
            20,
            max(5, len(customer_chart_df))
        )
    )

    top_profit_df = (
        customer_chart_df[customer_chart_df['Profit'] > 0]
        .sort_values("Profit", ascending=False)
    ).head(chart_limit)

    top_loss_df = (
        customer_chart_df[customer_chart_df['Profit'] < 0]
        .sort_values("Profit", ascending=True)
    ).head(chart_limit)

    top_income_df = (
        customer_chart_df
        .sort_values("Income", ascending=False)
    ).head(chart_limit)

    profit_tab, loss_tab, income_tab = st.tabs(
            [
                "Top Profitable Customers",
                "Top Loss-Making Customers",
                "Top Income Customers",
            ]
        )
    
    with profit_tab:
        if top_profit_df.empty:
            st.info("No profitable customers are available for the selected filters.")
        else:
            fig_profit = px.bar(
                top_profit_df,
                x="customer_name",
                y="Profit",
                hover_data={
                    "customer_code": True,
                    "Income": ":,.0f",
                    "Cost": ":,.0f",
                    "Profit": ":,.0f",
                    "Margin": ":.1%",
                },
                title=(
                    f"Top {len(top_profit_df)} "

                    "Profitable Customers"
                ),
                labels={
                    "customer_name": "Customer",
                    "Profit": "Profit",
                }
            )

            fig_profit.update_layout(
                xaxis_tickangle=-45,
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                )
            )

            fig_profit.update_yaxes(
                tickprefix="¥",
                tickformat=",.0f"
            )

            st.plotly_chart(
                fig_profit,
                use_container_width=True
            )

    with loss_tab:
        if top_loss_df.empty:
            st.info("No loss-making customers are available for the selected filters.")
        else:
            fig_loss = px.bar(
                top_loss_df,
                x="customer_name",
                y="Profit",
                hover_data={
                    "customer_code": True,
                    "Income": ":,.0f",
                    "Cost": ":,.0f",
                    "Profit": ":,.0f",
                    "Margin": ":.1%",
                },
                title=(
                    f"Top {len(top_loss_df)} "
                    "Profitable Customers"
                ),
                labels={
                    "customer_name": "Customer",
                    "Profit": "Profit",
                }
            )

            fig_loss.update_layout(
                xaxis_tickangle=-45,
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                )
            )

            fig_loss.update_yaxes(
                tickprefix="¥",
                tickformat=",.0f"
            )

            st.plotly_chart(
                fig_loss,
                use_container_width=True
            )
    with income_tab:
        if top_income_df.empty:
            st.info("No Income data are available for the selected filters.")
        else:
            fig_income = px.bar(
                top_income_df,
                x="customer_name",
                y="Income",
                hover_data={
                    "customer_code": True,
                    "Income": ":,.0f",
                    "Cost": ":,.0f",
                    "Profit": ":,.0f",
                    "Margin": ":.1%",
                },
                title=(
                    f"Top {len(top_income_df)} "
                    "High Income Customers"
                ),
                labels={
                    "customer_name": "Customer",
                    "Income": "Income",
                }
            )

            fig_income.update_layout(
                xaxis_tickangle=-45,
                margin=dict(
                    l=10,
                    r=10,
                    t=50,
                    b=10
                )
            )

            fig_income.update_yaxes(
                tickprefix="¥",
                tickformat=",.0f"
            )

            st.plotly_chart(
                fig_income,
                use_container_width=True
            )

with customer_tab:
    customer_summary = (
        filtered_customer_profit
        .groupby(
            [
                "warehouse_name",
                "customer_code",
                "customer_name",
            ],
            as_index=False
        )[
            [
                "Income",
                "Cost",
                "Profit",
            ]
        ]
        .sum()
    )

    customer_summary["Margin"] = np.where(
        customer_summary["Income"] != 0,
        customer_summary["Profit"]
        / customer_summary["Income"],
        np.nan
    )

    customer_summary = (
        customer_summary
        .rename(
            columns={
                "warehouse_name": "仓库 Warehouse",
                "customer_code": "客户编码 Customer Code",
                "customer_name": "客户名称 Customer",
                "Income": "收入 Revenue",
                "Cost": "成本 Cost",
                "Profit": "利润 Profit",
                "Margin": "利润率 Margin",
            }
        )
        .sort_values(
            [
                "仓库 Warehouse",
                "利润 Profit",
            ],
            ascending=[
                True,
                False,
            ]
        )
    )

    styled_df = (
    customer_summary
    .style
    .map(
        highlight_profit,
        subset=["利润 Profit", "利润率 Margin"]
    )
    .format(
        {
            "收入 Revenue": "¥{:,.0f}",
            "成本 Cost": "¥{:,.0f}",
            "利润 Profit": "¥{:,.0f}",
            "利润率 Margin": "{:.1%}",
        },
        na_rep="-"
    )
    )

    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "收入 Revenue": st.column_config.NumberColumn(
                "收入 Revenue",
                format="¥%,.0f"
            ),
            "成本 Cost": st.column_config.NumberColumn(
                "成本 Cost",
                format="¥%,.0f"
            ),
            "利润 Profit": st.column_config.NumberColumn(
                "利润 Profit",
                format="¥%,.0f"
            ),
            "利润率 Margin": st.column_config.NumberColumn(
                "利润率 Margin",
                format="%.1f%%"
            ),
        }
    )

with monthly_tab:

    inbound_summary = (
        inbound_data
        .groupby(
            [
                "month",
                "warehouse_code",
                "customer_code",
            ],
            as_index=False
        )
        .agg(
            inbound_units=("units", "sum")
        )
        .rename(
            columns={
                "month": "Month",
                # "owner_no": "customer_code",
            }
        )
    )

    # st.write(inbound_summary.head(20))
    # st.stop()

    outbound_summary = (
        outbound_data
        .groupby(
            [
                "month",
                "warehouse_code",
                "customer_code",
            ],
            as_index=False
        )
        .agg(
            outbound_units=("units", "sum"),
            outbound_orders=("order_num", "sum"),
        )
        .rename(
            columns={
                "month": "Month",
                # "owner_no": "customer_code",
            }
        )
    )

    inbound_summary["Month"] = pd.to_datetime(
    inbound_summary["Month"]).dt.to_period("M").dt.to_timestamp()

    outbound_summary["Month"] = pd.to_datetime(
    outbound_summary["Month"]).dt.to_period("M").dt.to_timestamp()

    filtered_customer_profit = filtered_customer_profit.merge(
            inbound_summary,
            on=[
                "Month",
                "warehouse_code",
                "customer_code",
            ],
            how="left"
        )

    # st.write(filtered_customer_profit.head())
    # st.stop()
    
    filtered_customer_profit = filtered_customer_profit.merge(
            outbound_summary,
            on=[
                "Month",
                "warehouse_code",
                "customer_code",
            ],
            how="left"
        )

    monthly_customer_table = (
        filtered_customer_profit
        .rename(
            columns={
                "Month": "月份 Month",
                "warehouse_name": "仓库 Warehouse",
                "customer_code": "客户编码 Customer Code",
                "customer_name": "客户名称 Customer",
                "Income": "收入 Revenue",
                "Cost": "成本 Cost",
                "Profit": "利润 Profit",
                "Margin": "利润率 Margin",
                "inbound_units": "入库件数 Inbound Units",
                "outbound_units": "出库件数 Outbound Units",
                "outbound_orders": "出库单量 Outbound Orders",
            }
        )
        [
            [
                "月份 Month",
                "仓库 Warehouse",
                "客户编码 Customer Code",
                "客户名称 Customer",
                "收入 Revenue",
                "成本 Cost",
                "利润 Profit",
                "利润率 Margin",
                "入库件数 Inbound Units",
                "出库件数 Outbound Units",
                "出库单量 Outbound Orders",
            ]
        ]
        .sort_values(
            [
                "月份 Month",
                "仓库 Warehouse",
                "客户编码 Customer Code",
                
            ],
            ascending=[
                True,
                True,
                True,
            ]
        )
    )

    group_columns = [
        "仓库 Warehouse",
        "客户编码 Customer Code",
    ]
    
    monthly_customer_table["上月利润 Previous Month Profit"] = (
        monthly_customer_table.groupby(group_columns)
        ["利润 Profit"]
        .shift(1)
    )

    monthly_customer_table[
        "上月入库 Previous Inbound"
    ] = (
        monthly_customer_table
        .groupby(group_columns)[
            "入库件数 Inbound Units"
        ]
        .shift(1)
    )

    monthly_customer_table[
        "上月出库 Previous Outbound"
    ] = (
        monthly_customer_table
        .groupby(group_columns)[
            "出库件数 Outbound Units"
        ]
        .shift(1)
    )

    monthly_customer_table[
        "上月订单 Previous Orders"
    ] = (
        monthly_customer_table
        .groupby(group_columns)[
            "出库单量 Outbound Orders"
        ]
        .shift(1)
    )
    
    monthly_customer_table["利润 Profit MoM"] = monthly_customer_table.apply(
        lambda row: calculate_mom(
            row["利润 Profit"],
            row["上月利润 Previous Month Profit"]
        ),
        axis=1
    )

    monthly_customer_table["入库 IB Unit MoM"] = (
        monthly_customer_table.apply(
            lambda row: calculate_mom(
                row["入库件数 Inbound Units"],
                row["上月入库 Previous Inbound"]
            ),
            axis=1
        )
    )

    monthly_customer_table["出库 OB Unit MoM"] = (
        monthly_customer_table.apply(
            lambda row: calculate_mom(
                row["出库件数 Outbound Units"],
                row["上月出库 Previous Outbound"]
            ),
            axis=1
        )
    )

    monthly_customer_table["订单 OB Order MoM"] = (
        monthly_customer_table.apply(
            lambda row: calculate_mom(
                row["出库单量 Outbound Orders"],
                row["上月订单 Previous Orders"]
            ),
            axis=1
        )
    )

    monthly_customer_table = monthly_customer_table.fillna(0)

    styled_df = (
    monthly_customer_table
    .style
    .map(
        highlight_profit,
        subset=["利润 Profit", "利润率 Margin", "利润 Profit MoM",
                            "入库 IB Unit MoM",
                            "出库 OB Unit MoM",
                            "订单 OB Order MoM"
                            ]
    )
    .format(
        {
            "收入 Revenue": "¥{:,.0f}",
            "成本 Cost": "¥{:,.0f}",
            "利润 Profit": "¥{:,.0f}",
            "利润率 Margin": "{:.1%}",
            "上月利润 Previous Month Profit": "¥{:,.0f}",
            "上月入库 Previous Inbound": "{:,.0f}",
            "上月出库 Previous Outbound": "{:,.0f}",
            "上月订单 Previous Orders": "{:,.0f}",
            "入库件数 Inbound Units": "{:,.0f}",
            "出库件数 Outbound Units": "{:,.0f}",
            "出库单量 Outbound Orders": "{:,.0f}",
            "平均每单件数 Units / Order": "{:,.2f}",
            
            "利润 Profit MoM": "{:.1%}",
            "入库 IB Unit MoM": "{:.1%}",
            "出库 OB Unit MoM": "{:.1%}",
            "订单 OB Order MoM": "{:.1%}",
        },
        na_rep="-"
    )
    )

    st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True,
    height=650,
    column_config={
        "月份 Month": st.column_config.DateColumn(
            "月份 Month",
            format="YYYY-MM",
        ),
        "利润 Profit MoM": st.column_config.NumberColumn(
            "利润 Profit MoM",
            format="percent",
        ),
        "入库 IB Unit MoM": st.column_config.NumberColumn(
            "入库 IB Unit MoM",
            format="percent",
        ),
        "出库 OB Unit MoM": st.column_config.NumberColumn(
            "出库 OB Unit MoM",
            format="percent",
        ),
        "订单 OB Order MoM": st.column_config.NumberColumn(
            "订单 OB Order MoM",
            format="percent",
        ),
    },
    )

with exception_tab:
    exception_data = monthly_customer_table[
    (monthly_customer_table["收入 Revenue"] < 0)
    |
    (monthly_customer_table["成本 Cost"] < 0)
][[
                "月份 Month",
                "仓库 Warehouse",
                "客户编码 Customer Code",
                "客户名称 Customer",
                "收入 Revenue",
                "成本 Cost",
                "利润 Profit"]].copy()
    
    st.dataframe(
        exception_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "月份 Month": st.column_config.DateColumn(
                "月份 Month",
                format="YYYY-MM"
            ),
        }
    )
