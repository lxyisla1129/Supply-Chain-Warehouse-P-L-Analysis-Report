import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from utils import WAREHOUSE_NAME_CODE_MAPPING, WAREHOUSE_CODE_MAPPING, calculate_mom, format_mom


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="P&L Analysis",
    layout="wide",
)

st.title("P&L Analysis Dashboard")
st.caption(
    "Internal-use warehouse financial and operational "
    "efficiency analysis"
)


# ============================================================
# SESSION STATE KEYS
# These keys must match the Data Upload page exactly
# ============================================================

FINANCIAL_SESSION_KEY = "warehouse_profit"
INVENTORY_SESSION_KEY = "inventory_data"
OUTBOUND_SESSION_KEY = "outbound_data"
INBOUND_SESSION_KEY = "inbound_data"
LABOR_SESSION_KEY = "labor_data"
WAREHOUSE_COST_SESSION_KEY = "dataset_cost"


# ============================================================
# COLUMN CONFIGURATION
# Change these based on the actual columns in your DataFrames
# ============================================================

# ------------------------------------------------------------
# Financial data columns
# ------------------------------------------------------------

FINANCIAL_DATE_COL = "入账日期"
FINANCIAL_WAREHOUSE_COL = "仓编码"
FINANCIAL_ACCOUNT_COL = "损益科目"
FINANCIAL_AMOUNT_COL = "不含税金额CNY"

# Values found inside the financial-account column
REVENUE_ACCOUNT_VALUE = "收入"
COST_ACCOUNT_VALUE = "直接成本"
PROFIT_ACCOUNT_VALUE = "贡献利润"


# ------------------------------------------------------------
# Inventory data columns
# ------------------------------------------------------------

INVENTORY_MONTH_COL = "month"
INVENTORY_WAREHOUSE_COL = "warehouse_code"
INVENTORY_UNITS_COL = "units"


# ------------------------------------------------------------
# Outbound data columns
# ------------------------------------------------------------

OUTBOUND_MONTH_COL = "month"
OUTBOUND_WAREHOUSE_COL = "warehouse_code"
OUTBOUND_UNITS_COL = "units"
OUTBOUND_ORDERS_COL = "order_num"


# ------------------------------------------------------------
# Inbound data columns
# ------------------------------------------------------------

INBOUND_MONTH_COL = "month"
INBOUND_WAREHOUSE_COL = "warehouse_code"
INBOUND_UNITS_COL = "units"


# ------------------------------------------------------------
# Labor data columns
# ------------------------------------------------------------

LABOR_MONTH_COL = "month"
LABOR_WAREHOUSE_COL = "warehouse_code"
LABOR_HC_COL = "HC"
LABOR_REGULAR_HOURS_COL = "regular_hours"
LABOR_OT_HOURS_COL = "ot_hours"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def safe_divide(
    numerator: pd.Series,
    denominator: pd.Series,
) -> pd.Series:
    """Return NaN when the denominator is zero."""

    return np.where(
        denominator != 0,
        numerator / denominator,
        np.nan,
    )


def normalize_month(series: pd.Series) -> pd.Series:
    """Convert date or month values into YYYY-MM strings."""

    normalized = (
        pd.to_datetime(
            series,
            errors="coerce",
        )
        .dt.to_period("M")
        .astype(str)
    )

    return normalized.replace("NaT", np.nan)


def require_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    dataset_name: str,
) -> None:
    """Show missing columns and stop execution."""

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        st.error(
            f"{dataset_name} is missing required columns:"
        )

        st.write(missing_columns)

        with st.expander(
            f"Available columns in {dataset_name}"
        ):
            st.write(dataframe.columns.tolist())

        st.stop()


def prepare_dataframe_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Strip spaces from dataframe column names."""

    dataframe = dataframe.copy()

    dataframe.columns = (
        dataframe.columns
        .astype(str)
        .str.strip()
    )

    return dataframe


# ============================================================
# CHECK DATA FROM DATA UPLOAD PAGE
# ============================================================

required_session_data = {
    FINANCIAL_SESSION_KEY: "Warehouse Financial Data",
    INVENTORY_SESSION_KEY: "Inventory Data",
    OUTBOUND_SESSION_KEY: "Outbound Data",
    INBOUND_SESSION_KEY: "Inbound Data",
    LABOR_SESSION_KEY: "Labor Data",
    WAREHOUSE_COST_SESSION_KEY: "Warehouse Cost Data",
}

missing_session_data = [
    label
    for key, label in required_session_data.items()
    if key not in st.session_state
]

if missing_session_data:
    st.warning(
        "Some required data has not been processed "
        "on the Data Upload page."
    )

    for item in missing_session_data:
        st.write(f"- {item}")

    st.caption(
        "Select the files and click the corresponding Process button "
        "on the Data Upload page before opening this dashboard."
    )

    if st.button(
        "Go to Data Upload",
        type="primary",
        key="go_to_data_upload",
    ):
        st.switch_page("pages/0_Data_Upload.py")

    st.stop()


# ============================================================
# READ DATAFRAMES FROM SESSION STATE
# ============================================================

financial_raw = prepare_dataframe_columns(
    st.session_state[FINANCIAL_SESSION_KEY]
)

inventory_raw = prepare_dataframe_columns(
    st.session_state[INVENTORY_SESSION_KEY]
)

outbound_raw = prepare_dataframe_columns(
    st.session_state[OUTBOUND_SESSION_KEY]
)

inbound_raw = prepare_dataframe_columns(
    st.session_state[INBOUND_SESSION_KEY]
)

labor_raw = prepare_dataframe_columns(
    st.session_state[LABOR_SESSION_KEY]
)

warehouse_cost_raw = prepare_dataframe_columns(
    st.session_state[WAREHOUSE_COST_SESSION_KEY]
)



# st.write(warehouse_cost_raw.head(20))
# st.stop()

# ============================================================
# DEBUG / COLUMN CHECK
# ============================================================

with st.expander("Data Column Check"):
    debug_col1, debug_col2 = st.columns(2)

    with debug_col1:
        st.markdown("#### Financial Data")
        st.write(financial_raw.columns.tolist())

        st.markdown("#### Inventory Data")
        st.write(inventory_raw.columns.tolist())

        st.markdown("#### Outbound Data")
        st.write(outbound_raw.columns.tolist())

    with debug_col2:
        st.markdown("#### Inbound Data")
        st.write(inbound_raw.columns.tolist())

        st.markdown("#### Labor Data")
        st.write(labor_raw.columns.tolist())

        st.markdown("#### Available Session Keys")
        st.write(list(st.session_state.keys()))


# ============================================================
# VALIDATE REQUIRED COLUMNS
# ============================================================

require_columns(
    financial_raw,
    [
        FINANCIAL_DATE_COL,
        FINANCIAL_WAREHOUSE_COL,
        FINANCIAL_ACCOUNT_COL,
        FINANCIAL_AMOUNT_COL,
    ],
    "Financial data",
)

require_columns(
    inventory_raw,
    [
        INVENTORY_MONTH_COL,
        INVENTORY_WAREHOUSE_COL,
        INVENTORY_UNITS_COL,
    ],
    "Inventory data",
)

require_columns(
    outbound_raw,
    [
        OUTBOUND_MONTH_COL,
        OUTBOUND_WAREHOUSE_COL,
        OUTBOUND_UNITS_COL,
        OUTBOUND_ORDERS_COL,
    ],
    "Outbound data",
)

require_columns(
    inbound_raw,
    [
        INBOUND_MONTH_COL,
        INBOUND_WAREHOUSE_COL,
        INBOUND_UNITS_COL,
    ],
    "Inbound data",
)

require_columns(
    labor_raw,
    [
        LABOR_MONTH_COL,
        LABOR_WAREHOUSE_COL,
        LABOR_REGULAR_HOURS_COL,
        LABOR_OT_HOURS_COL,
        LABOR_HC_COL,
    ],
    "Labor data",
)

warehouse_cost_raw['warehouse_code'] = warehouse_cost_raw['warehouse_name'].map(WAREHOUSE_NAME_CODE_MAPPING)

# st.write(warehouse_cost_raw.head(20))
# st.stop()

require_columns(
    warehouse_cost_raw,
    [
        "Month",
        "warehouse_code",
        "对应成本拆分内容",
        "净额",
    ],
    "Warehouse cost data",
)

# ============================================================
# PREPARE FINANCIAL DATA
# ============================================================

financial_data = financial_raw.copy()

financial_data["month"] = normalize_month(
    financial_data[FINANCIAL_DATE_COL]
)

financial_data["warehouse_code"] = (
    financial_data[FINANCIAL_WAREHOUSE_COL]
    .astype(str)
    .str.strip()
)

financial_data["financial_account"] = (
    financial_data[FINANCIAL_ACCOUNT_COL]
    .astype(str)
    .str.strip()
)

financial_data["financial_amount"] = pd.to_numeric(
    financial_data[FINANCIAL_AMOUNT_COL],
    errors="coerce",
).fillna(0)

financial_data = financial_data.dropna(
    subset=[
        "month",
        "warehouse_code",
    ]
)

financial_summary = (
    financial_data
    .pivot_table(
        index=[
            "month",
            "warehouse_code",
        ],
        columns="financial_account",
        values="financial_amount",
        aggfunc="sum",
        fill_value=0,
    )
    .reset_index()
)

financial_summary.columns.name = None

for financial_column in [
    REVENUE_ACCOUNT_VALUE,
    COST_ACCOUNT_VALUE,
    PROFIT_ACCOUNT_VALUE,
]:
    if financial_column not in financial_summary.columns:
        financial_summary[financial_column] = 0

financial_summary = financial_summary.rename(
    columns={
        REVENUE_ACCOUNT_VALUE: "Revenue",
        COST_ACCOUNT_VALUE: "Total Cost",
        PROFIT_ACCOUNT_VALUE: "Profit",
    }
)

financial_summary = financial_summary[
    [
        "month",
        "warehouse_code",
        "Revenue",
        "Total Cost",
        "Profit",
    ]
]


# ============================================================
# PREPARE INVENTORY DATA
# ============================================================

inventory_data = inventory_raw.copy()

inventory_data["month"] = normalize_month(
    inventory_data[INVENTORY_MONTH_COL]
)

inventory_data["warehouse_code"] = (
    inventory_data[INVENTORY_WAREHOUSE_COL]
    .astype(str)
    .str.strip()
)

inventory_data[INVENTORY_UNITS_COL] = pd.to_numeric(
    inventory_data[INVENTORY_UNITS_COL],
    errors="coerce",
).fillna(0)

inventory_data = inventory_data.dropna(
    subset=[
        "month",
        "warehouse_code",
    ]
)

inventory_summary = (
    inventory_data
    .groupby(
        [
            "month",
            "warehouse_code",
        ],
        as_index=False,
    )
    .agg(
        inventory_units=(
            INVENTORY_UNITS_COL,
            "sum",
        )
    )
)


# ============================================================
# PREPARE OUTBOUND DATA
# ============================================================

outbound_data = outbound_raw.copy()

outbound_data["month"] = normalize_month(
    outbound_data[OUTBOUND_MONTH_COL]
)

outbound_data["warehouse_code"] = (
    outbound_data[OUTBOUND_WAREHOUSE_COL]
    .astype(str)
    .str.strip()
)

for column in [
    OUTBOUND_UNITS_COL,
    OUTBOUND_ORDERS_COL,
]:
    outbound_data[column] = pd.to_numeric(
        outbound_data[column],
        errors="coerce",
    ).fillna(0)

outbound_data = outbound_data.dropna(
    subset=[
        "month",
        "warehouse_code",
    ]
)

outbound_summary = (
    outbound_data
    .groupby(
        [
            "month",
            "warehouse_code",
        ],
        as_index=False,
    )
    .agg(
        outbound_units=(
            OUTBOUND_UNITS_COL,
            "sum",
        ),
        outbound_orders=(
            OUTBOUND_ORDERS_COL,
            "sum",
        ),
    )
)


# ============================================================
# PREPARE INBOUND DATA
# ============================================================

inbound_data = inbound_raw.copy()

inbound_data["month"] = normalize_month(
    inbound_data[INBOUND_MONTH_COL]
)

inbound_data["warehouse_code"] = (
    inbound_data[INBOUND_WAREHOUSE_COL]
    .astype(str)
    .str.strip()
)

inbound_data[INBOUND_UNITS_COL] = pd.to_numeric(
    inbound_data[INBOUND_UNITS_COL],
    errors="coerce",
).fillna(0)

inbound_data = inbound_data.dropna(
    subset=[
        "month",
        "warehouse_code",
    ]
)

inbound_summary = (
    inbound_data
    .groupby(
        [
            "month",
            "warehouse_code",
        ],
        as_index=False,
    )
    .agg(
        inbound_units=(
            INBOUND_UNITS_COL,
            "sum",
        )
    )
)


# ============================================================
# COMBINE OPERATION DATA
# ============================================================

operation_summary = inventory_summary.merge(
    outbound_summary,
    on=[
        "month",
        "warehouse_code",
    ],
    how="outer",
)

operation_summary = operation_summary.merge(
    inbound_summary,
    on=[
        "month",
        "warehouse_code",
    ],
    how="outer",
)

operation_numeric_columns = [
    "inventory_units",
    "outbound_units",
    "outbound_orders",
    "inbound_units",
]

operation_summary[operation_numeric_columns] = (
    operation_summary[operation_numeric_columns]
    .apply(
        pd.to_numeric,
        errors="coerce",
    )
    .fillna(0)
)

# ============================================================
# PREPARE LABOR / WORKING-HOUR DATA
# ============================================================

labor_data = labor_raw.copy()

labor_data["month"] = normalize_month(
    labor_data[LABOR_MONTH_COL]
)

labor_data["warehouse_name"] = (
    labor_data[LABOR_WAREHOUSE_COL]
    .astype(str)
    .str.strip()
)

for column in [
    LABOR_REGULAR_HOURS_COL,
    LABOR_OT_HOURS_COL,
    LABOR_HC_COL,
]:
    labor_data[column] = pd.to_numeric(
        labor_data[column],
        errors="coerce",
    ).fillna(0)

labor_data["Working Hours"] = (
    labor_data[LABOR_REGULAR_HOURS_COL]
    + labor_data[LABOR_OT_HOURS_COL]
)

labor_summary = (
    labor_data
    .dropna(
        subset=[
            "month",
            "warehouse_name",
        ]
    )
    .groupby(
        [
            "month",
            "warehouse_code",
        ],
        as_index=False,
    )
    .agg(
        regular_hours=(
            LABOR_REGULAR_HOURS_COL,
            "sum",
        ),
        OT_Hours=(
            LABOR_OT_HOURS_COL,
            "sum",
        ),
        Working_Hours=(
            "Working Hours",
            "sum",
        ),
        HC=(
            LABOR_HC_COL,
            "sum",
        ),
    )
    .rename(
        columns={
            "OT_Hours": "OT Hours",
            "Working_Hours": "Working Hours",
        }
    )
)

# ============================================================
# PREPARE LABOR COST FROM WAREHOUSE COST CATEGORY DATA
# ============================================================

warehouse_cost_data = warehouse_cost_raw.copy()

warehouse_cost_data["month"] = normalize_month(
    warehouse_cost_data["Month"]
)

warehouse_cost_data["warehouse_code"] = (
    warehouse_cost_data["warehouse_code"]
    .astype(str)
    .str.strip()
)

warehouse_cost_data["净额"] = pd.to_numeric(
    warehouse_cost_data["净额"],
    errors="coerce",
).fillna(0)

warehouse_cost_data["对应成本拆分内容"] = (
    warehouse_cost_data["对应成本拆分内容"]
    .astype(str)
    .str.strip()
)

# Match personnel/labor category
warehouse_cost_data["cost_category_clean"] = (
    warehouse_cost_data["对应成本拆分内容"]
    .astype(str)
    .str.replace(r"\s+", " ", regex=True)
    .str.replace("–", "-", regex=False)
    .str.strip()
)

labor_category = (
    "人员费用 Personnel - Management Staff"
)

labor_cost_data = warehouse_cost_data[
    warehouse_cost_data["cost_category_clean"]
    .eq(labor_category)
].copy()


labor_cost_summary = (
    labor_cost_data
    .groupby(
        [
            "month",
            "warehouse_code",
        ],
        as_index=False,
    )["净额"]
    .sum()
    .rename(
        columns={
            "净额": "Labor Cost",
        }
    )
)

labor_summary = labor_summary.merge(
    labor_cost_summary,
    on=[
        "month",
        "warehouse_code",
    ],
    how="left",
)

labor_summary["Labor Cost"] = pd.to_numeric(
    labor_summary["Labor Cost"],
    errors="coerce",
).fillna(0)

# ============================================================
# MERGE ALL DATA
# ============================================================

analysis_data = financial_summary.merge(
    operation_summary,
    on=[
        "month",
        "warehouse_code",
    ],
    how="outer",
)

analysis_data["warehouse_name"] = (
    analysis_data["warehouse_code"]
    .map(WAREHOUSE_CODE_MAPPING)
    .fillna(analysis_data["warehouse_code"])
)

analysis_data = analysis_data.merge(
    labor_summary,
    on=[
        "month",
        "warehouse_code",
    ],
    how="outer",
)

numeric_columns = [
    "Revenue",
    "Total Cost",
    "Profit",
    "inventory_units",
    "outbound_units",
    "outbound_orders",
    "inbound_units",
    "Working Hours",
    "Labor Cost",
    "HC",
    "OT Hours",
]

for column in numeric_columns:
    if column not in analysis_data.columns:
        analysis_data[column] = 0

    analysis_data[column] = pd.to_numeric(
        analysis_data[column],
        errors="coerce",
    ).fillna(0)


# ============================================================
# CALCULATE KPIs
# ============================================================

analysis_data["Cost per Unit"] = safe_divide(
    analysis_data["Total Cost"],
    analysis_data["outbound_units"],
)

analysis_data["Cost per Order"] = safe_divide(
    analysis_data["Total Cost"],
    analysis_data["outbound_orders"],
)

analysis_data["UPPH"] = safe_divide(
    analysis_data["outbound_units"],
    analysis_data["Working Hours"],
)

analysis_data["Labor Cost / Revenue"] = safe_divide(
    analysis_data["Labor Cost"],
    analysis_data["Revenue"],
)

# analysis_data["Sell-through Rate"] = safe_divide(
#     analysis_data["outbound_units"],
#     analysis_data["inventory_units"],
# )

analysis_data["Revenue per Unit"] = safe_divide(
    analysis_data["Revenue"],
    analysis_data["outbound_units"],
)

analysis_data["Profit per Unit"] = safe_divide(
    analysis_data["Profit"],
    analysis_data["outbound_units"],
)

analysis_data["Labor Cost per Unit"] = safe_divide(
    analysis_data["Labor Cost"],
    analysis_data["outbound_units"],
)

analysis_data["Labor Cost per Order"] = safe_divide(
    analysis_data["Labor Cost"],
    analysis_data["outbound_orders"],
)

analysis_data["Gross Margin"] = safe_divide(
    analysis_data["Profit"],
    analysis_data["Revenue"],
)

analysis_data["OT Rate"] = safe_divide(
    analysis_data["OT Hours"],
    analysis_data["Working Hours"],
)

analysis_data["month_date"] = pd.to_datetime(
    analysis_data["month"],
    format="%Y-%m",
    errors="coerce",
)

analysis_data = (
    analysis_data
    .sort_values(
        [
            "month_date",
            "warehouse_name",
        ]
    )
    .reset_index(drop=True)
)

analysis_data = (
    analysis_data
    .sort_values(
        [
            "warehouse_name",
            "month_date",
        ]
    )
    .reset_index(drop=True)
)

mom_kpi_columns = [
    "Cost per Unit",
    "Cost per Order",
    "UPPH",
    "Labor Cost / Revenue",
    # "Sell-through Rate",
    "outbound_units",
    "outbound_orders",
    "inbound_units",
    "Working Hours",
    "Labor Cost",
    "HC",
]

for column in mom_kpi_columns:
    previous_column = f"Previous {column}"
    mom_column = f"{column} MoM"

    analysis_data[previous_column] = (
        analysis_data
        .groupby("warehouse_name")[column]
        .shift(1)
    )

    analysis_data[mom_column] = analysis_data.apply(
        lambda row: calculate_mom(
            row[column],
            row[previous_column],
        ),
        axis=1,
    )

st.session_state["pnl_analysis_data"] = (
    analysis_data.copy()
)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def display_number(value, prefix="", decimals=2):
    if pd.isna(value):
        return "-"

    return f"{prefix}{value:,.{decimals}f}"


def display_percentage(value):
    if pd.isna(value):
        return "-"

    return f"{value:.1%}"


def calculate_summary_kpis(dataframe):
    """
    Recalculate weighted KPIs from summed numerators and denominators.

    Do not average warehouse-level ratios because that would give
    small and large warehouses equal weight.
    """

    revenue = dataframe["Revenue"].sum()
    total_cost = dataframe["Total Cost"].sum()
    profit = dataframe["Profit"].sum()

    outbound_units = dataframe["outbound_units"].sum()
    outbound_orders = dataframe["outbound_orders"].sum()
    inventory_units = dataframe["inventory_units"].sum()

    working_hours = dataframe["Working Hours"].sum()
    labor_cost = dataframe["Labor Cost"].sum()
    ot_hours = dataframe["OT Hours"].sum()
    hc = dataframe["HC"].sum()

    return {
        "Revenue": revenue,
        "Total Cost": total_cost,
        "Profit": profit,
        "Outbound Units": outbound_units,
        "Outbound Orders": outbound_orders,
        "Inventory Units": inventory_units,
        "Working Hours": working_hours,
        "Labor Cost": labor_cost,
        "OT Hours": ot_hours,
        "HC": hc,

        "Cost per Unit": (
            total_cost / outbound_units
            if outbound_units != 0
            else np.nan
        ),

        "Cost per Order": (
            total_cost / outbound_orders
            if outbound_orders != 0
            else np.nan
        ),

        "UPPH": (
            outbound_units / working_hours
            if working_hours != 0
            else np.nan
        ),

        "Labor Cost / Revenue": (
            labor_cost / revenue
            if revenue != 0
            else np.nan
        ),

        # "Sell-through Rate": (
        #     outbound_units / inventory_units
        #     if inventory_units != 0
        #     else np.nan
        # ),

        "Gross Margin": (
            profit / revenue
            if revenue != 0
            else np.nan
        ),

        "Labor Cost per Unit": (
            labor_cost / outbound_units
            if outbound_units != 0
            else np.nan
        ),

        "OT Rate": (
            ot_hours / working_hours
            if working_hours != 0
            else np.nan
        ),
    }


def calculate_summary_mom(
    current_summary,
    previous_summary,
    metric,
):
    if previous_summary is None:
        return None

    return calculate_mom(
        current_summary.get(metric),
        previous_summary.get(metric),
    )


# ============================================================
# MONTH AND WAREHOUSE FILTERS
# ============================================================

st.markdown("---")
st.subheader("Filters")

month_options = sorted(
    analysis_data["month"]
    .dropna()
    .unique(),
    reverse=True,
)

warehouse_options = sorted(
    analysis_data["warehouse_name"]
    .dropna()
    .astype(str)
    .unique(),
)

filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    selected_months = st.multiselect(
        "Months for Trend, Comparison, and Detail",
        options=month_options,
        default=month_options,
        key="pnl_analysis_month_filter",
    )

with filter_col2:
    selected_warehouses = st.multiselect(
        "Warehouses",
        options=warehouse_options,
        default=warehouse_options,
        key="pnl_analysis_warehouse_filter",
    )

filtered_data = analysis_data.copy()

if selected_months:
    filtered_data = filtered_data[
        filtered_data["month"].isin(selected_months)
    ]

if selected_warehouses:
    filtered_data = filtered_data[
        filtered_data["warehouse_name"].isin(
            selected_warehouses
        )
    ]

if filtered_data.empty:
    st.warning(
        "No data is available for the selected filters."
    )
    st.stop()


# ============================================================
# KPI CONFIGURATION
# ============================================================

kpi_options = {
    "Cost per Unit": "Cost per Unit",
    "Cost per Order": "Cost per Order",
    "UPPH": "UPPH",
    "Labor Cost / Revenue": "Labor Cost / Revenue",
    # "Sell-through Rate": "Sell-through Rate",
    "Labor Cost per Unit": "Labor Cost per Unit",
    "Gross Margin": "Gross Margin",
    "OT Rate": "OT Rate",
}

percentage_kpis = [
    "Labor Cost / Revenue",
    # "Sell-through Rate",
    "Gross Margin",
    "OT Rate",
]

currency_kpis = [
    "Cost per Unit",
    "Cost per Order",
    "Labor Cost per Unit",
]

cost_kpis = [
    "Cost per Unit",
    "Cost per Order",
    "Labor Cost / Revenue",
    "Labor Cost per Unit",
    "OT Rate",
]


# ============================================================
# TABS
# ============================================================

overview_tab, trend_tab, comparison_tab, detail_tab = st.tabs(
    [
        "KPI Overview",
        "Monthly Trend",
        "Warehouse Comparison",
        "Detail Table",
    ]
)


# ============================================================
# KPI OVERVIEW
# ============================================================

with overview_tab:
    st.subheader("West Region and Warehouse KPI Overview")

    overview_month = st.selectbox(
        "Select Overview Month",
        options=month_options,
        index=0,
        key="overview_month_selector",
    )

    overview_month_date = pd.to_datetime(
        overview_month,
        format="%Y-%m",
        errors="coerce",
    )

    previous_month = (
        overview_month_date
        - pd.DateOffset(months=1)
    ).strftime("%Y-%m")

    current_month_data = analysis_data[
        analysis_data["month"].eq(overview_month)
    ].copy()

    previous_month_data = analysis_data[
        analysis_data["month"].eq(previous_month)
    ].copy()

    if selected_warehouses:
        current_month_data = current_month_data[
            current_month_data["warehouse_name"].isin(
                selected_warehouses
            )
        ]

        previous_month_data = previous_month_data[
            previous_month_data["warehouse_name"].isin(
                selected_warehouses
            )
        ]

    if current_month_data.empty:
        st.info(
            "No KPI data is available for the selected month."
        )

    else:
        # ====================================================
        # WEST REGION SUMMARY
        # ====================================================

        st.markdown(
            f"## West Region — {overview_month}"
        )

        west_current = calculate_summary_kpis(
            current_month_data
        )

        west_previous = (
            calculate_summary_kpis(previous_month_data)
            if not previous_month_data.empty
            else None
        )

        west_col1, west_col2, west_col3, west_col4 = (
            st.columns(4)
        )

        with west_col1:
            st.metric(
                "Cost per Unit",
                display_number(
                    west_current["Cost per Unit"],
                    prefix="¥",
                ),
                delta=format_mom(
                    calculate_summary_mom(
                        west_current,
                        west_previous,
                        "Cost per Unit",
                    )
                ),
                delta_color="inverse",
            )

        with west_col2:
            st.metric(
                "Cost per Order",
                display_number(
                    west_current["Cost per Order"],
                    prefix="¥",
                ),
                delta=format_mom(
                    calculate_summary_mom(
                        west_current,
                        west_previous,
                        "Cost per Order",
                    )
                ),
                delta_color="inverse",
            )

        with west_col3:
            st.metric(
                "UPPH",
                display_number(
                    west_current["UPPH"]
                ),
                delta=format_mom(
                    calculate_summary_mom(
                        west_current,
                        west_previous,
                        "UPPH",
                    )
                ),
            )

        with west_col4:
            st.metric(
                "Labor Cost / Revenue",
                display_percentage(
                    west_current[
                        "Labor Cost / Revenue"
                    ]
                ),
                delta=format_mom(
                    calculate_summary_mom(
                        west_current,
                        west_previous,
                        "Labor Cost / Revenue",
                    )
                ),
                delta_color="inverse",
            )

        # with west_col5:
        #     st.metric(
        #         "Sell-through Rate",
        #         display_percentage(
        #             west_current[
        #                 "Sell-through Rate"
        #             ]
        #         ),
        #         delta=format_mom(
        #             calculate_summary_mom(
        #                 west_current,
        #                 west_previous,
        #                 "Sell-through Rate",
        #             )
        #         ),
        #     )

        west_volume_col1, west_volume_col2, west_volume_col3, \
            west_volume_col4, west_volume_col5 = st.columns(5)

        with west_volume_col1:
            st.metric(
                "Outbound Units",
                display_number(
                    west_current["Outbound Units"],
                    decimals=0,
                ),
                delta=format_mom(
                                    calculate_summary_mom(
                                        west_current,
                                        west_previous,
                                        "Outbound Units",
                                    )
                                ),
            )

        with west_volume_col2:
            st.metric(
                "Outbound Orders",
                display_number(
                    west_current["Outbound Orders"],
                    decimals=0,
                ),
                delta=format_mom(
                                                    calculate_summary_mom(
                                                        west_current,
                                                        west_previous,
                                                        "Outbound Orders",
                                                    )
                                                ),
            )

        with west_volume_col3:
            st.metric(
                "Working Hours",
                display_number(
                    west_current["Working Hours"],
                    decimals=1,
                ),
                delta=format_mom(
                                                                    calculate_summary_mom(
                                                                        west_current,
                                                                        west_previous,
                                                                        "Working Hours",
                                                                    )
                                                                ),
                                                                delta_color="inverse",
            )

        with west_volume_col4:
            st.metric(
                "HC",
                display_number(
                    west_current["HC"],
                    decimals=1,
                ),
                delta=format_mom(
                                                                                    calculate_summary_mom(
                                                                                        west_current,
                                                                                        west_previous,
                                                                                        "HC",
                                                                                    )
                                                                                ),
                                                                                delta_color="inverse",
            )

        with west_volume_col5:
            st.metric(
                "Labor Cost",
                display_number(
                    west_current["Labor Cost"],
                    prefix="¥",
                ),
                delta=format_mom(
                                                                                    calculate_summary_mom(
                                                                                        west_current,
                                                                                        west_previous,
                                                                                        "Labor Cost",
                                                                                    )
                                                                                ),
                                                                                delta_color="inverse",
            )

        st.markdown("---")

        # ====================================================
        # EACH WAREHOUSE
        # ====================================================

        st.markdown("## Warehouse Breakdown")

        current_warehouses = sorted(
            current_month_data["warehouse_name"]
            .dropna()
            .unique()
        )

        for warehouse in current_warehouses:
            warehouse_current_data = current_month_data[
                current_month_data["warehouse_name"].eq(
                    warehouse
                )
            ]

            warehouse_previous_data = previous_month_data[
                previous_month_data["warehouse_name"].eq(
                    warehouse
                )
            ]

            warehouse_current = calculate_summary_kpis(
                warehouse_current_data
            )

            warehouse_previous = (
                calculate_summary_kpis(
                    warehouse_previous_data
                )
                if not warehouse_previous_data.empty
                else None
            )

            with st.container(border=True):
                st.markdown(f"### {warehouse}")

                col1, col2, col3, col4 = (
                    st.columns(4)
                )

                with col1:
                    st.metric(
                        "Cost per Unit",
                        display_number(
                            warehouse_current[
                                "Cost per Unit"
                            ],
                            prefix="¥",
                        ),
                        delta=format_mom(
                            calculate_summary_mom(
                                warehouse_current,
                                warehouse_previous,
                                "Cost per Unit",
                            )
                        ),
                        delta_color="inverse",
                    )

                with col2:
                    st.metric(
                        "Cost per Order",
                        display_number(
                            warehouse_current[
                                "Cost per Order"
                            ],
                            prefix="¥",
                        ),
                        delta=format_mom(
                            calculate_summary_mom(
                                warehouse_current,
                                warehouse_previous,
                                "Cost per Order",
                            )
                        ),
                        delta_color="inverse",
                    )

                with col3:
                    st.metric(
                        "UPPH",
                        display_number(
                            warehouse_current["UPPH"]
                        ),
                        delta=format_mom(
                            calculate_summary_mom(
                                warehouse_current,
                                warehouse_previous,
                                "UPPH",
                            )
                        ),
                    )

                with col4:
                    st.metric(
                        "Labor Cost / Revenue",
                        display_percentage(
                            warehouse_current[
                                "Labor Cost / Revenue"
                            ]
                        ),
                        delta=format_mom(
                            calculate_summary_mom(
                                warehouse_current,
                                warehouse_previous,
                                "Labor Cost / Revenue",
                            )
                        ),
                        delta_color="inverse",
                    )

                # with col5:
                #     st.metric(
                #         "Sell-through Rate",
                #         display_percentage(
                #             warehouse_current[
                #                 "Sell-through Rate"
                #             ]
                #         ),
                #         delta=format_mom(
                #             calculate_summary_mom(
                #                 warehouse_current,
                #                 warehouse_previous,
                #                 "Sell-through Rate",
                #             )
                #         ),
                #     )

                volume_col1, volume_col2, volume_col3, \
                    volume_col4, volume_col5 = st.columns(5)

                with volume_col1:
                    st.metric(
                        "Outbound Units",
                        display_number(
                            warehouse_current[
                                "Outbound Units"
                            ],
                            decimals=0,
                        ),
                        delta=format_mom(
                                                    calculate_summary_mom(
                                                        warehouse_current,
                                                        warehouse_previous,
                                                        "Outbound Units",
                                                    )
                                                ),
                    )

                with volume_col2:
                    st.metric(
                        "Outbound Orders",
                        display_number(
                            warehouse_current[
                                "Outbound Orders"
                            ],
                            decimals=0,
                        ),
                        delta=format_mom(
                                                                            calculate_summary_mom(
                                                                                warehouse_current,
                                                                                warehouse_previous,
                                                                                "Outbound Orders",
                                                                            )
                                                                        ),
                    )

                with volume_col3:
                    st.metric(
                        "Working Hours",
                        display_number(
                            warehouse_current[
                                "Working Hours"
                            ],
                            decimals=1,
                        ),
                        delta=format_mom(
                                                                                                    calculate_summary_mom(
                                                                                                        warehouse_current,
                                                                                                        warehouse_previous,
                                                                                                        "Working Hours",
                                                                                                    )
                                                                                                ),
                                                                                                delta_color="inverse",
                    )

                with volume_col4:
                    st.metric(
                        "HC",
                        display_number(
                            warehouse_current["HC"],
                            decimals=1,
                        ),
                        delta=format_mom(
                                                                                                                            calculate_summary_mom(
                                                                                                                                warehouse_current,
                                                                                                                                warehouse_previous,
                                                                                                                                "HC",
                                                                                                                            )
                                                                                                                        ),
                                                                                                                        delta_color="inverse",
                    )

                with volume_col5:
                    st.metric(
                        "Labor Cost",
                        display_number(
                            warehouse_current[
                                "Labor Cost"
                            ],
                            prefix="¥",
                        ),
                        delta=format_mom(
                                                                                                                                                    calculate_summary_mom(
                                                                                                                                                        warehouse_current,
                                                                                                                                                        warehouse_previous,
                                                                                                                                                        "Labor Cost",
                                                                                                                                                    )
                                                                                                                                                ),
                                                                                                                                                delta_color="inverse",
                    )


# ============================================================
# MONTHLY TREND
# ============================================================

with trend_tab:
    st.subheader("Monthly KPI Trend")

    trend_filter_col1, trend_filter_col2 = st.columns(2)

    with trend_filter_col1:
        selected_trend_kpi = st.selectbox(
            "Select KPI",
            options=list(kpi_options.keys()),
            key="monthly_trend_kpi",
        )

    with trend_filter_col2:
        selected_trend_warehouses = st.multiselect(
            "Select Warehouses",
            options=warehouse_options,
            default=selected_warehouses,
            key="monthly_trend_warehouses",
        )

    trend_column = kpi_options[selected_trend_kpi]

    trend_data = filtered_data.copy()

    if selected_trend_warehouses:
        trend_data = trend_data[
            trend_data["warehouse_name"].isin(
                selected_trend_warehouses
            )
        ]

    trend_data = (
        trend_data[
            [
                "month",
                "warehouse_name",
                trend_column,
            ]
        ]
        .dropna(subset=[trend_column])
        .sort_values("month")
    )

    if trend_data.empty:
        st.info("No monthly trend data is available.")

    else:
        trend_chart = px.line(
            trend_data,
            x="month",
            y=trend_column,
            color="warehouse_name",
            markers=True,
            title=(
                f"Monthly {selected_trend_kpi} "
                "by Warehouse"
            ),
            labels={
                "month": "Month",
                "warehouse_name": "Warehouse",
                trend_column: selected_trend_kpi,
            },
        )

        trend_chart.update_layout(
            height=600,
            hovermode="x unified",
            legend_title_text="Warehouse",
        )

        trend_chart.update_xaxes(
            type="category",
            categoryorder="array",
            categoryarray=sorted(
                trend_data["month"].unique()
            ),
        )

        if trend_column in percentage_kpis:
            trend_chart.update_yaxes(
                tickformat=".1%"
            )

        elif trend_column in currency_kpis:
            trend_chart.update_yaxes(
                tickprefix="¥",
                tickformat=",.2f",
            )

        else:
            trend_chart.update_yaxes(
                tickformat=",.2f"
            )

        st.plotly_chart(
            trend_chart,
            use_container_width=True,
        )


# ============================================================
# WAREHOUSE COMPARISON
# ============================================================

with comparison_tab:
    st.subheader("Warehouse Comparison")

    comparison_month = st.selectbox(
        "Select Comparison Month",
        options=month_options,
        key="comparison_month_selector",
    )

    comparison_source = analysis_data[
        analysis_data["month"].eq(comparison_month)
    ].copy()

    if selected_warehouses:
        comparison_source = comparison_source[
            comparison_source["warehouse_name"].isin(
                selected_warehouses
            )
        ]

    if comparison_source.empty:
        st.info(
            "No comparison data is available for "
            "the selected month."
        )

    else:
        kpi_comparison_tab, operation_comparison_tab = (
            st.tabs(
                [
                    "Efficiency KPI",
                    "Operational Volume",
                ]
            )
        )

        # ----------------------------------------------------
        # KPI COMPARISON
        # ----------------------------------------------------

        with kpi_comparison_tab:
            selected_comparison_kpi = st.selectbox(
                "Select KPI",
                options=list(kpi_options.keys()),
                key="warehouse_comparison_kpi",
            )

            comparison_column = kpi_options[
                selected_comparison_kpi
            ]

            kpi_comparison = (
                comparison_source[
                    [
                        "warehouse_name",
                        comparison_column,
                    ]
                ]
                .dropna(subset=[comparison_column])
                .sort_values(
                    comparison_column,
                    ascending=False,
                )
            )

            kpi_chart = px.bar(
                kpi_comparison,
                x="warehouse_name",
                y=comparison_column,
                text=comparison_column,
                title=(
                    f"{selected_comparison_kpi} "
                    f"Comparison — {comparison_month}"
                ),
                labels={
                    "warehouse_name": "Warehouse",
                    comparison_column: (
                        selected_comparison_kpi
                    ),
                },
            )

            if comparison_column in percentage_kpis:
                kpi_chart.update_yaxes(
                    tickformat=".1%"
                )

                kpi_chart.update_traces(
                    texttemplate="%{y:.1%}",
                    textposition="outside",
                )

            elif comparison_column in currency_kpis:
                kpi_chart.update_yaxes(
                    tickprefix="¥",
                    tickformat=",.2f",
                )

                kpi_chart.update_traces(
                    texttemplate="¥%{y:,.2f}",
                    textposition="outside",
                )

            else:
                kpi_chart.update_yaxes(
                    tickformat=",.2f"
                )

                kpi_chart.update_traces(
                    texttemplate="%{y:,.2f}",
                    textposition="outside",
                )

            kpi_chart.update_layout(
                height=550,
            )

            st.plotly_chart(
                kpi_chart,
                use_container_width=True,
            )

        # ----------------------------------------------------
        # OPERATIONAL VOLUME COMPARISON
        # ----------------------------------------------------

        with operation_comparison_tab:
            operational_metric_mapping = {
                "Inventory Units": "inventory_units",
                "Inbound Units": "inbound_units",
                "Outbound Units": "outbound_units",
                "Outbound Orders": "outbound_orders",
                "Working Hours": "Working Hours",
                "Regular Hours": "regular_hours",
                "OT Hours": "OT Hours",
                "HC": "HC",
                "Revenue": "Revenue",
                "Total Cost": "Total Cost",
                "Labor Cost": "Labor Cost",
            }

            selected_operation_metrics = st.multiselect(
                "Select Operational Metrics",
                options=list(
                    operational_metric_mapping.keys()
                ),
                default=[
                    "Outbound Units",
                    "Outbound Orders",
                    "Working Hours",
                    "HC",
                ],
                key="operational_comparison_metrics",
            )

            if not selected_operation_metrics:
                st.info(
                    "Please select at least one metric."
                )

            else:
                selected_columns = [
                    operational_metric_mapping[label]
                    for label in selected_operation_metrics
                ]

                operation_comparison = (
                    comparison_source[
                        [
                            "warehouse_name",
                            *selected_columns,
                        ]
                    ]
                    .melt(
                        id_vars="warehouse_name",
                        value_vars=selected_columns,
                        var_name="Metric",
                        value_name="Value",
                    )
                )

                reverse_metric_mapping = {
                    value: label
                    for label, value
                    in operational_metric_mapping.items()
                }

                operation_comparison["Metric"] = (
                    operation_comparison["Metric"]
                    .map(reverse_metric_mapping)
                )

                operation_chart = px.bar(
                    operation_comparison,
                    x="warehouse_name",
                    y="Value",
                    color="Metric",
                    barmode="group",
                    title=(
                        "Warehouse Operational Volume "
                        f"Comparison — {comparison_month}"
                    ),
                    labels={
                        "warehouse_name": "Warehouse",
                        "Value": "Value",
                    },
                )

                operation_chart.update_layout(
                    height=600,
                    legend_title_text="Metric",
                )

                operation_chart.update_yaxes(
                    tickformat=",.0f"
                )

                st.plotly_chart(
                    operation_chart,
                    use_container_width=True,
                )

                st.caption(
                    "Metrics with very different scales may be "
                    "easier to compare individually."
                )


# ============================================================
# DETAIL TABLE
# ============================================================

with detail_tab:
    st.subheader("P&L Analysis Detail")

    detail_columns = [
        "month",
        "warehouse_code",
        "warehouse_name",
        "Revenue",
        "Total Cost",
        "Profit",
        "inventory_units",
        "inbound_units",
        "outbound_units",
        "outbound_orders",
        "regular_hours",
        "Working Hours",
        "Labor Cost",
        "HC",
        "OT Hours",
        "Cost per Unit",
        "Cost per Unit MoM",
        "Cost per Order",
        "Cost per Order MoM",
        "UPPH",
        "UPPH MoM",
        "Labor Cost / Revenue",
        "Labor Cost / Revenue MoM",
        # "Sell-through Rate",
        # "Sell-through Rate MoM",
        "Labor Cost per Unit",
        "Gross Margin",
        "OT Rate",
    ]

    detail_columns = [
        column
        for column in detail_columns
        if column in filtered_data.columns
    ]

    detail_table = (
        filtered_data[detail_columns]
        .sort_values(
            [
                "month",
                "warehouse_name",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .rename(
            columns={
                "month": "Month",
                "warehouse_code": "Warehouse Code",
                "warehouse_name": "Warehouse",
                "inventory_units": "Inventory Units",
                "inbound_units": "Inbound Units",
                "outbound_units": "Outbound Units",
                "outbound_orders": "Outbound Orders",
                "regular_hours": "Regular Hours",
            }
        )
    )

    currency_columns = [
        "Revenue",
        "Total Cost",
        "Profit",
        "Labor Cost",
        "Cost per Unit",
        "Cost per Order",
        "Labor Cost per Unit",
    ]

    percentage_columns = [
        "Labor Cost / Revenue",
        # "Sell-through Rate",
        "Gross Margin",
        "OT Rate",
        "Cost per Unit MoM",
        "Cost per Order MoM",
        "UPPH MoM",
        "Labor Cost / Revenue MoM",
        # "Sell-through Rate MoM",
    ]

    integer_columns = [
        "Inventory Units",
        "Inbound Units",
        "Outbound Units",
        "Outbound Orders",
    ]

    formatting = {
        column: "¥{:,.2f}"
        for column in currency_columns
        if column in detail_table.columns
    }

    formatting.update(
        {
            column: "{:.1%}"
            for column in percentage_columns
            if column in detail_table.columns
        }
    )

    formatting.update(
        {
            column: "{:,.0f}"
            for column in integer_columns
            if column in detail_table.columns
        }
    )

    for column in [
        "Regular Hours",
        "Working Hours",
        "OT Hours",
        "HC",
    ]:
        if column in detail_table.columns:
            formatting[column] = "{:,.1f}"

    if "UPPH" in detail_table.columns:
        formatting["UPPH"] = "{:,.2f}"

    st.dataframe(
        detail_table.style.format(
            formatting,
            na_rep="-",
        ),
        use_container_width=True,
        hide_index=True,
        height=650,
    )

    csv_data = detail_table.to_csv(
        index=False,
    ).encode("utf-8-sig")

    st.download_button(
        "Download P&L Analysis CSV",
        data=csv_data,
        file_name="pnl_analysis.csv",
        mime="text/csv",
    )

# ============================================================
# DETAIL TABLE
# ============================================================

with detail_tab:
    st.subheader("P&L Analysis Detail")

    detail_columns = [
        "month",
        "warehouse_code",
        "warehouse_name",
        "Revenue",
        "Total Cost",
        "Profit",
        "inventory_units",
        "inbound_units",
        "outbound_units",
        "outbound_orders",
        "regular_hours",
        "Working Hours",
        "Labor Cost",
        "HC",
        "OT Hours",
        "Cost per Unit",
        "Cost per Unit MoM",
        "Cost per Order",
        "Cost per Order MoM",
        "UPPH",
        "UPPH MoM",
        "Labor Cost / Revenue",
        "Labor Cost / Revenue MoM",
        "Sell-through Rate",
        "Sell-through Rate MoM",
        "Labor Cost per Unit",
        "Gross Margin",
        "OT Rate",
    ]

    detail_columns = [
        column
        for column in detail_columns
        if column in filtered_data.columns
    ]

    detail_table = (
        filtered_data[detail_columns]
        .sort_values(
            [
                "month",
                "warehouse_name",
            ],
            ascending=[
                False,
                True,
            ],
        )
        .rename(
            columns={
                "month": "Month",
                "warehouse_code": "Warehouse Code",
                "warehouse_name": "Warehouse",
                "inventory_units": "Inventory Units",
                "inbound_units": "Inbound Units",
                "outbound_units": "Outbound Units",
                "outbound_orders": "Outbound Orders",
                "regular_hours": "Regular Hours",
            }
        )
    )

    currency_columns = [
        "Revenue",
        "Total Cost",
        "Profit",
        "Labor Cost",
        "Cost per Unit",
        "Cost per Order",
        "Labor Cost per Unit",
    ]

    percentage_columns = [
        "Labor Cost / Revenue",
        "Sell-through Rate",
        "Gross Margin",
        "OT Rate",
        "Cost per Unit MoM",
        "Cost per Order MoM",
        "UPPH MoM",
        "Labor Cost / Revenue MoM",
        "Sell-through Rate MoM",
    ]

    integer_columns = [
        "Inventory Units",
        "Inbound Units",
        "Outbound Units",
        "Outbound Orders",
    ]

    formatting = {
        column: "¥{:,.2f}"
        for column in currency_columns
        if column in detail_table.columns
    }

    formatting.update(
        {
            column: "{:.1%}"
            for column in percentage_columns
            if column in detail_table.columns
        }
    )

    formatting.update(
        {
            column: "{:,.0f}"
            for column in integer_columns
            if column in detail_table.columns
        }
    )

    for column in [
        "Regular Hours",
        "Working Hours",
        "OT Hours",
        "HC",
    ]:
        if column in detail_table.columns:
            formatting[column] = "{:,.1f}"

    if "UPPH" in detail_table.columns:
        formatting["UPPH"] = "{:,.2f}"

    st.dataframe(
        detail_table.style.format(
            formatting,
            na_rep="-",
        ),
        use_container_width=True,
        hide_index=True,
        height=650,
    )

    csv_data = detail_table.to_csv(
        index=False,
    ).encode("utf-8-sig")

    st.download_button(
        "Download P&L Analysis CSV",
        data=csv_data,
        file_name="pnl_analysis.csv",
        mime="text/csv",
    )

warehouse_profit = st.session_state["warehouse_profit"].copy()

customer_cost_raw = (
    st.session_state["customer_cost_raw"]
    .copy()
)

customer_income_raw = (
    st.session_state["customer_income_raw"]
    .copy()
)

warehouse_cost = st.session_state["dataset_cost"].copy()

from io import BytesIO
import zipfile

warehouse_mapping = {
    "LAX1": "C0000000578",
    "LAX2": "C0000000579",
    "LAX4": "C0000008149",
    "LAX5": "C0000009307",
}


def to_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return output.getvalue()


zip_buffer = BytesIO()

with zipfile.ZipFile(
    zip_buffer,
    "w",
    zipfile.ZIP_DEFLATED,
) as zf:

    for warehouse_name, warehouse_code in warehouse_mapping.items():

        # Warehouse P&L
        df = warehouse_profit[
            warehouse_profit["仓编码"] == warehouse_code
        ]

        zf.writestr(
            f"{warehouse_name}_Warehouse_P&L.xlsx",
            to_excel(df),
        )

        # Customer P&L
        df = customer_cost_raw[
            customer_cost_raw["仓编码"] == warehouse_code
        ]

        zf.writestr(
            f"{warehouse_name}_Customer_Cost.xlsx",
            to_excel(df),
        )

        df = customer_income_raw[
                customer_income_raw["仓编码"] == warehouse_code
            ]
        
        zf.writestr(
            f"{warehouse_name}_Customer_Income.xlsx",
            to_excel(df),
        )

        # Operation Cost
        warehouse_mapping = {
        "美国洛杉矶大件1号仓": "C0000000578",
        "美国洛杉矶中小件2号仓": "C0000000579",
        "美国洛杉矶中小件4号仓": "C0000008149",
        "美国洛杉矶大件5号仓": "C0000009307",
    }
        operation_cost = st.session_state["operation_cost"].copy()
        operation_cost['warehouse_name'] = operation_cost['部门段_EBS'].str.split('-', n=3).str[3]
        operation_cost= operation_cost[operation_cost['warehouse_name'].isin(['美国洛杉矶中小件2号仓', '美国洛杉矶大件1号仓', '美国洛杉矶中小件4号仓', '美国洛杉矶大件5号仓'])].copy()

        operation_cost["warehouse_code"] = (
            operation_cost["warehouse_name"]
            .map(warehouse_mapping)
        )

        df = operation_cost[
            operation_cost["warehouse_code"] == warehouse_code
        ]

        zf.writestr(
            f"{warehouse_name}_Operation_Cost.xlsx",
            to_excel(df),
        )

zip_buffer.seek(0)

st.download_button(
    "Download Warehouse Files",
    data=zip_buffer,
    file_name="Warehouse_Source_Data.zip",
    mime="application/zip",
    type="primary",
)
st.stop()
