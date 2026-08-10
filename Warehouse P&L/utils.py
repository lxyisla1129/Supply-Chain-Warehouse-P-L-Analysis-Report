import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

def highlight_profit(value):
    if pd.isna(value):
        return ""

    if value > 0:
        return (
            "background-color: #d9ead3;"
            "color: #274e13;"
            "font-weight: bold;"
        )

    if value < 0:
        return (
            "background-color: #f4cccc;"
            "color: #990000;"
            "font-weight: bold;"
        )

    return ""

def highlight_cost_mom(value):
    if pd.isna(value):
        return ""

    # Cost increased → bad
    if value > 0:
        return (
            "background-color: #f4cccc;"
            "color: #990000;"
            "font-weight: bold;"
        )

    # Cost decreased → good
    if value < 0:
        return (
            "background-color: #d9ead3;"
            "color: #274e13;"
            "font-weight: bold;"
        )

    return ""

def calculate_mom(current_value, previous_value):
    if (
        pd.isna(current_value)
        or pd.isna(previous_value)
        or previous_value == 0
    ):
        return None

    return current_value / abs(previous_value) - 1

def format_mom(value):
    if value is None or pd.isna(value):
        return "No prior month"

    return f"{value:+.1%} MoM"

def read_data(file):
    if file is None:
        raise ValueError("No file was uploaded.")

    file_name = file.name.lower()

    # 每次读取前重置文件指针
    file.seek(0)

    if file_name.endswith(".csv"):
        # 尝试常见编码
        for encoding in ["gb18030", "utf-8-sig", "utf-8"]:
            try:
                file.seek(0)
                return pd.read_csv(
                    file,
                    encoding=encoding,
                    low_memory=False
                )
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(
            "Unable to decode the uploaded CSV file."
        )

    if file_name.endswith(".xlsx"):
        file.seek(0)
        return pd.read_excel(
            file,
            engine="openpyxl"
        )

    if file_name.endswith(".xls"):
        file.seek(0)
        return pd.read_excel(
            file,
            engine="xlrd"
        )

    raise ValueError(
        f"Unsupported file type: {file.name}"
    )

@st.cache_data
def load_warehouse_profit(file):
    df = pd.read_excel(file)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    df = df[df['仓编码'].isin(['C0000000578', 'C0000000579', 'C0000008149', 'C0000009307'])]

    df["入账日期"] = pd.to_datetime(
        df["入账日期"],
        errors="coerce"
    )

    df["不含税金额CNY"] = pd.to_numeric(
        df["不含税金额CNY"],
        errors="coerce"
    ).fillna(0)

    return df

@st.cache_data
def load_warehouse_cost(cost_file, mapping_file):
    df = pd.read_excel(cost_file)
    mapping = pd.read_excel(mapping_file)

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
    )

    mapping.columns = (
        mapping.columns
        .astype(str)
        .str.strip()
    )

    df['warehouse_name'] = df['部门段_EBS'].str.split('-', n=3).str[3]
    df= df[df['warehouse_name'].isin(['美国洛杉矶中小件2号仓', '美国洛杉矶大件1号仓', '美国洛杉矶中小件4号仓', '美国洛杉矶大件5号仓'])].copy()

    df["日期_day"] = pd.to_datetime(
        df["日期_day"],
        errors="coerce"
    )

    df["净额"] = pd.to_numeric(
        df["净额"],
        errors="coerce"
    ).fillna(0)

    dataset_cost = pd.merge(
        df,
        mapping,
        left_on="管报科目名称",
        right_on="成本科目",
        how="left"
    )

    dataset_cost["对应成本拆分内容"] = (
        dataset_cost["对应成本拆分内容"]
        .astype(str)
        .str.strip()
    )

    dataset_cost = dataset_cost.drop(columns='成本科目', errors="coerce")

    dataset_cost = (
        dataset_cost
        .groupby(
            [
                "日期_day",
                "warehouse_name",
                "对应成本拆分内容",
                "管报科目名称",
            ],
            as_index=False
        )["净额"]
        .sum()
    )

    dataset_cost["Month"] = dataset_cost["日期_day"].dt.strftime("%Y-%m")

    return dataset_cost

@st.cache_data
def load_customer_pnl(cost_file, income_file, mapping_file):

    WAREHOUSE_CODES = [
    "C0000000578",
    "C0000000579",
    "C0000008149",
    "C0000009307",]

    WAREHOUSE_MAPPING = {
    "C0000000578": "LAX1",
    "C0000000579": "LAX2",
    "C0000008149": "LAX4",
    "C0000009307": "LAX5",}
    
    cost = read_data(cost_file)

    income = read_data(income_file)

    customer_mapping = pd.read_excel(mapping_file)

    # -------------------------
    # 1. Filter warehouses
    # -------------------------
    customer_cost = cost[
        cost["仓编码"].isin(WAREHOUSE_CODES)
    ].copy()

    customer_income = income[
        income["仓编码"].isin(WAREHOUSE_CODES)
    ].copy()

    # -------------------------
    # 2. Convert dates
    # -------------------------
    customer_cost["入账日期"] = pd.to_datetime(
        customer_cost["入账日期"],
        errors="coerce"
    )

    customer_income["入账日期"] = pd.to_datetime(
        customer_income["入账日期"],
        errors="coerce"
    )

    # Normalize dates to month
    customer_cost["Month"] = (
        customer_cost["入账日期"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    customer_income["Month"] = (
        customer_income["入账日期"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    # -------------------------
    # 3. Aggregate separately
    # -------------------------
    # st.write(customer_income.columns.tolist())
    # st.write(customer_cost.columns.tolist())
    
    # st.stop()

    income_summary = (
        customer_income
        .groupby(
            [
                "Month",
                "仓编码",
                "商家编码",
            ],
            as_index=False
        )["金额不含税CN"]
        .sum()
        .rename(
            columns={
                "仓编码": "warehouse_code",
                "商家编码": "customer_code",
                "金额不含税CN": "Income",
            }
        )
    )

    cost_summary = (
        customer_cost
        .groupby(
            [
                "Month",
                "仓编码",
                "商家编码",
            ],
            as_index=False
        )["不含税金额CNY"]
        .sum()
        .rename(
            columns={
                "仓编码": "warehouse_code",
                "商家编码": "customer_code",
                "不含税金额CNY": "Cost",
            }
        )
    )

    # -------------------------
    # 4. Merge income and cost
    # -------------------------
    customer_profit = pd.merge(
        income_summary,
        cost_summary,
        on=[
            "Month",
            "warehouse_code",
            "customer_code",
        ],
        how="outer"
    )

    customer_profit[["Income", "Cost"]] = (
        customer_profit[["Income", "Cost"]]
        .fillna(0)
    )

    # -------------------------
    # 5. Add customer names
    # -------------------------

    customer_mapping = customer_mapping[
        ~customer_mapping["customer_name"].str.contains(
            "Test|test|测试",
            case=False,
            na=False
        )
    ]

    mapping_df = (
        customer_mapping[
            ["customer_code", "customer_name"]
        ]
        .drop_duplicates(subset=["customer_code"])
        .copy()
    )

    # mapping_df = mapping_df[~mapping_df["customer_name"].constains(
    #     r"test|Test|TEST|测试",
    #     case=False,
    #     na=False
    # )]

    customer_profit = pd.merge(
        customer_profit,
        mapping_df,
        on="customer_code",
        how="left"
    )

    customer_profit["customer_name"] = (
        customer_profit["customer_name"]
        .fillna(customer_profit["customer_code"])
    )

    # -------------------------
    # 6. Calculate P&L
    # -------------------------
    customer_profit["Profit"] = (
        customer_profit["Income"]
        - customer_profit["Cost"]
    )

    customer_profit["Margin"] = np.where(
        customer_profit["Income"] != 0,
        customer_profit["Profit"]
        / customer_profit["Income"],
        np.nan
    )

    customer_profit["warehouse_name"] = (
        customer_profit["warehouse_code"]
        .map(WAREHOUSE_MAPPING)
        .fillna(customer_profit["warehouse_code"])
    )

    customer_profit = customer_profit.sort_values(
        by=[
            "Month",
            "warehouse_name",
            "Profit",
        ],
        ascending=[
            False,
            True,
            False,
        ]
    ).reset_index(drop=True)

    return customer_profit

def calc_share(df, column):
    return (
        df[column]
        / df.groupby(
            ["month", "warehouse_code"]
        )[column]
        .transform("sum")
    )

@st.cache_data
def operation_data_breakdown(inventory_file, outbound_file, inbound_file, labor_file):
    
    inventory_data = read_data(inventory_file)
    outbound_data = read_data(outbound_file)
    inbound_data = read_data(inbound_file)
    labor_data = read_data(labor_file)

    
    inventory_data ["iv_size_rate"] = calc_share(inventory_data, "volumn")
    outbound_data ["ob_size_rate"] = calc_share(outbound_data, "order_num")
    inbound_data ["ib_size_rate"] = calc_share(inbound_data, "volumn")

    operation_data = pd.merge(
        inventory_data,
        outbound_data,
        on=[
            "month",
            "warehouse_code",
            "customer_code",
        ],
        how="left")
    
    operation_data = pd.merge(
        operation_data,
        inbound_data,
        on=[
            "month",
            "warehouse_code",
            "customer_code",
        ],
        how="left")
    
    operation_data = operation_data.drop(columns=["customer_name_y", "customer_name"], errors="coerce")

    operation_data = (
        operation_data
        .fillna(0)
    )

    operation_data = operation_data.rename(columns ={ 
        "customer_name_x": "customer_name",
        "volumn_x": "volumn_iv",
        "sku_x": "sku_iv",
        "units_x": "units_iv",
        "volumn_y": "volumn_ob",
        "sku_y": "sku_ob",
        "units_y": "units_ob",
        "volumn": "volumn_ib",
        "sku": "sku_ib",
        "units": "units_ib",
    })
    
    # st.write(operation_data.head(20))
    # st.write(operation_data.columns.tolist())
    # st.stop()

    operation_data["weighted_ib_ob"] = (
        0.5 * (
            calc_share(operation_data, "units_ib")
                +
            calc_share(operation_data, "units_ob")
        )
        +
        0.5 * (
            calc_share(operation_data, "sku_ib")
            +
            calc_share(operation_data, "sku_ob")
        )
        )

    # inventory for hc
    operation_data["weighted_inventory"] = (
        0.3 * (
            calc_share(operation_data, "sku_iv")
            +
            calc_share(operation_data, "volumn_iv")
        ) 
        + 
        0.4 * (
            calc_share(operation_data, "units_iv")
        )
    )

    # outbound for hc
    operation_data['weighted_outbound'] = (
        0.3 * (
            calc_share(operation_data, "order_num")
                +
            calc_share(operation_data, "units_ob")
        ) 
        + 
        0.2 * (
            calc_share(operation_data, "sku_ob")
            +
            calc_share(operation_data, "volumn_ob")
        )
    )

    # inbound for
    operation_data["weighted_inbound"] = (
        0.35 * (
            calc_share(operation_data, "volumn_ib")
            +
            calc_share(operation_data, "units_ib")
        )
        +
        0.3 * (
            calc_share(operation_data, "sku_ib")
        )
    )
    
    inventory_hc = labor_data[labor_data["parent_group_name"] == "在库"][["month", "warehouse_code", "HC"]].rename(columns={"HC": "Inventory HC"})
    inbound_hc = labor_data[labor_data["parent_group_name"] == "入库"][["month", "warehouse_code", "HC"]].rename(columns={"HC": "Inbound HC"})
    outbound_hc = labor_data[labor_data["parent_group_name"] == "出库"][["month", "warehouse_code", "HC"]].rename(columns={"HC": "Outbound HC"})

    result = operation_data.merge(inventory_hc, on=["month", "warehouse_code"], how="left")
    result = result.merge(inbound_hc, on=["month", "warehouse_code"], how="left")
    result = result.merge(outbound_hc, on=["month", "warehouse_code"], how="left")

    # st.write(result.head(20))
    # st.stop()

    result["Inventory HC Allocated"] = round((
    result["Inventory HC"]
    * result["weighted_inventory"]),0)

    result["Outbound HC Allocated"] = round((
    result["Outbound HC"]
    * result["weighted_outbound"]),0)

    result["Inbound HC Allocated"] = round((
    result["Inbound HC"]
    * result["weighted_inbound"]),0)

    result["Total HC"] = result["Inventory HC Allocated"] + result["Outbound HC Allocated"] + result["Inbound HC Allocated"]
    result["hc_ratio"] = calc_share(result, "Total HC")

    result = result.sort_values(by = ['month', 'warehouse_code','customer_name'], ascending = True).reset_index(drop=True)

    # st.write(result.head(20))

    return result

    # st.write(operation_data.columns.tolist())
    # st.stop()

WAREHOUSE_CODE_MAPPING = {
    "C0000000578": "LAX1",
    "C0000000579": "LAX2",
    "C0000008149": "LAX4",
    "C0000009307": "LAX5",
}

WAREHOUSE_NAME_MAPPING = {
    "美国洛杉矶大件1号仓": "LAX1",
    "美国洛杉矶中小件2号仓": "LAX2",
    "美国洛杉矶中小件4号仓": "LAX4",
    "美国洛杉矶大件5号仓": "LAX5",
}

WAREHOUSE_NAME_CODE_MAPPING = {
    "美国洛杉矶大件1号仓": "C0000000578",
    "美国洛杉矶中小件2号仓": "C0000000579",
    "美国洛杉矶中小件4号仓": "C0000008149",
    "美国洛杉矶大件5号仓": "C0000009307",
}

WAREHOUSE_CODES = [
    "C0000000578",
    "C0000000579",
    "C0000008149",
    "C0000009307",
]

WAREHOUSE_MAPPING = {
    "C0000000578": "LAX1",
    "C0000000579": "LAX2",
    "C0000008149": "LAX4",
    "C0000009307": "LAX5",
}
