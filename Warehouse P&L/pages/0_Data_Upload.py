import streamlit as st
import pandas as pd
from utils import load_customer_pnl, load_warehouse_profit, load_warehouse_cost, operation_data_breakdown, read_data

st.set_page_config(
    page_title="Data Upload Center",
    layout="wide",
)

st.title("Data Upload Center")
st.caption("Upload only the files required for the dashboard you want to use.")

profit_tab, warehouse_tab, customer_tab, allocation_tab = st.tabs(
    [
        "Profit",
        "Warehouse Cost",
        "Customer Income & Cost",
        "Customer Cost Allocation",
    ]
)

with profit_tab:
    st.subheader("West Warehouse Profit Files")

    uploaded_file = st.file_uploader(
        "Upload Warehouse Profit Excel",
        type=["xlsx", "xls"]
    )

    if st.button(
        "Process Warehouse Profit Data",
        type="primary",
        key="process_warehouse_profit",
    ):

        if uploaded_file is not None:

            with st.spinner("Processing Warehouse Profit data..."):
                warehouse_profit = load_warehouse_profit(uploaded_file)

                st.session_state["warehouse_profit"] = warehouse_profit

            st.success("Warehouse Profit data is ready!")

        else:
            st.info("Please upload the warehouse profit Excel file.")

with warehouse_tab:
    st.subheader("Warehouse Cost Files")

    col1, col2 = st.columns(2)

    with col1:
        cost_file = st.file_uploader(
        "Upload Warehouse Operation Cost Excel",
        type=["xlsx", "xls"]
        )
        
    with col2:
        mapping_file = st.file_uploader(
            "Upload Cost Category Mapping Excel",
            type=["xlsx", "xls"]
        )

    if st.button(
        "Process Warehouse Cost Data",
        type="primary",
        key="process_warehouse_cost",
    ):
        if all(
            uploaded_file is not None
            for uploaded_file in [
                cost_file,
                mapping_file,
            ]
        ):
            with st.spinner("Processing Warehouse Cost data..."):
                dataset_cost= load_warehouse_cost(
                    cost_file,
                    mapping_file,
                )

                st.session_state["dataset_cost"] = (
                    dataset_cost
                )

                operation_cost = pd.read_excel(cost_file)
                
                st.session_state["operation_cost"] = operation_cost

            st.success("Warehouse cost data is ready.")

        else:
            st.info("Please upload both two files.")

    
with customer_tab:
    st.subheader("Customer Income & Cost Files")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        cost_file = st.file_uploader(
            "Upload Cost File",
            type=["csv", "xlsx", "xls"],
            key="customer_cost_file",
        )

    with col2:
        income_file = st.file_uploader(
            "Upload Income File",
            type=["csv", "xlsx", "xls"],
            key="customer_income_file",
        )

    with col3:
        mapping_file = st.file_uploader(
            "Upload Customer Mapping",
            type=["csv", "xlsx", "xls"],
            key="customer_mapping_file",
        )

    with col4:
        outbound_file = st.file_uploader(
            "Upload outbound File",
            type=["csv", "xlsx", "xls"],
            key="outbound_file_1"
            )
    
    with col5:
        inbound_file = st.file_uploader(
            "Upload inbound File",
            type=["csv", "xlsx", "xls"],
            key="inbound_file_1"
            )

    if st.button(
        "Process Customer P&L Data",
        type="primary",
        key="process_profit",
    ):
        if all(
            uploaded_file is not None
            for uploaded_file in [
                cost_file,
                income_file,
                mapping_file,
                outbound_file,
                inbound_file
            ]
        ):
            with st.spinner("Processing Customer P&L data..."):
                customer_profit = load_customer_pnl(
                    cost_file,
                    income_file,
                    mapping_file,
                )

                st.session_state["customer_profit"] = (
                    customer_profit
                )

                outbound_data = read_data(
                                    outbound_file
                                )

                st.session_state["outbound_data"] = (
                    outbound_data
                )
                
                inbound_data = read_data(
                                    inbound_file
                                )
                st.session_state["inbound_data"] = (
                    inbound_data
                                )

            st.success("Customer Profit data is ready.")

        else:
            st.info("Please upload all three files.")

with allocation_tab:
    st.subheader("Customer Cost Breakdown Files")

    upload_col1, upload_col2, upload_col3, upload_col4 = st.columns(4)

    upload_col5, upload_col6 = st.columns(2)

    with upload_col1:
        inventory_file = st.file_uploader(
            "Upload inventory File",
            type=["csv", "xlsx", "xls"],
            key="inventory_file"
        )

    with upload_col2:
        outbound_file = st.file_uploader(
            "Upload outbound File",
            type=["csv", "xlsx", "xls"],
            key="outbound_file"
        )

    with upload_col3:
        inbound_file = st.file_uploader(
            "Upload inbound File",
            type=["csv", "xlsx", "xls"],
            key="inbound_file"
        )

    with upload_col4:
        labor_file = st.file_uploader(
            "Upload Labor File",
            type=["csv", "xlsx", "xls"],
            key="labor_file"
        )

    with upload_col5:
        cost_file = st.file_uploader(
        "Upload Warehouse Operation Cost Excel",
        type=["xlsx", "xls"],
        key="cost_file"
        )

    with upload_col6:
        mapping_file = st.file_uploader(
        "Upload Cost Category Mapping Excel",
        type=["xlsx", "xls"],
            key="mapping_file"
        )


    if st.button(
        "Process Warehouse Cost Breakdown Data",
        type="primary",
        key="process_cost_breakdown",
    ):
        if all(
            uploaded_file is not None
            for uploaded_file in [
                inventory_file, 
                outbound_file, 
                inbound_file,
                labor_file,
            ]
        ):
            with st.spinner("Processing Warehouse Cost Breakdown data..."):
                cost_breakdown = operation_data_breakdown(
                    inventory_file, 
                    outbound_file, 
                    inbound_file,
                    labor_file,
                )

                st.session_state["cost_breakdown"] = (
                    cost_breakdown
                )
                # Read and save the underlying source datasets
                inventory_data = read_data(
                    inventory_file
                )

                outbound_data = read_data(
                    outbound_file
                )

                inbound_data = read_data(
                    inbound_file
                )

                labor_data = read_data(
                    labor_file
                )
                st.session_state["inventory_data"] = (
                    inventory_data
                )

                st.session_state["outbound_data"] = (
                    outbound_data
                )

                st.session_state["inbound_data"] = (
                    inbound_data
                )

                st.session_state["labor_data"] = (
                    labor_data
                )

                dataset_cost = load_warehouse_cost(cost_file, mapping_file)

                st.session_state["dataset_cost"] = dataset_cost 

            st.success("Customer Cost Breakdown data is ready.")

        else:
            st.info("Please upload all six files.")
