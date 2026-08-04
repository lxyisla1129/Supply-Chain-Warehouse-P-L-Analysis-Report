# import streamlit as st

# st.set_page_config(
#     page_title="Warehouse P&L Report",
#     page_icon = "📊",
#     layout="wide"
# )

# st.title("Warehouse P&L Performance Report")

# st.write(
#     "Use the sidebar to navigate between warehouse and customer reports."
# )

# col1, col2, col3, col4 = st.columns(4)

# col1.info("Warehouse P&L Overview")
# col2.info("Warehouse Operation Cost")
# col3.info("Customer P&L")
# col4.info("Customer Cost Breakdown")

import streamlit as st

st.set_page_config(
    page_title="Warehouse P&L Analytics",
    layout="wide"
)

st.title("Warehouse P&L Analytics Platform")
st.caption(
    "Warehouse profitability, operating cost, "
    "customer P&L, and customer cost allocation analytics."
)

st.markdown(
    """
    This internal analytics tool consolidates warehouse financial and
    operational data into interactive dashboards. Users can upload the
    required source files once through the **Data Upload** page and then
    review warehouse-level and customer-level performance across the
    different dashboard pages.
    """
)

st.info(
    "Start from the Data Upload page. "
    "You only need to upload the files required for the dashboard "
    "you want to review."
)

st.subheader("Dashboard Modules")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
        ### Warehouse P&L

        Review warehouse revenue, direct cost, gross profit,
        contribution profit, gross margin, monthly trends, and
        business-type performance.

        **Required data:** Warehouse profit file.
        """
    )

    st.markdown(
        """
        ### Warehouse Operation Cost

        Review warehouse cost composition, monthly category trends,
        category-level MoM changes, account details, and raw cost records.

        **Required data:** Warehouse operation cost file and cost-category
        mapping file.
        """
    )

with col2:
    st.markdown(
        """
        ### Customer P&L

        Review customer revenue, cost, profit, margin, profitable customers,
        loss-making customers, monthly performance, and exception records.

        **Required data:** Customer income file, customer cost file,
        and customer mapping file.
        """
    )

    st.markdown(
        """
        ### Customer Cost Breakdown

        Allocate warehouse operating costs to customers using inventory,
        inbound, outbound, and labor-related operational drivers.

        **Required data:** Inventory, inbound, outbound, labor,
        warehouse cost, and cost-category mapping files.
        """
    )

st.subheader("How to Use")

st.markdown(
    """
    1. Open the **Data Upload** page.
    2. Select the relevant module tab.
    3. Upload only the files required for that module.
    4. Click the corresponding **Process Data** button.
    5. Open the dashboard page from the navigation menu.
    6. Use the month, warehouse, customer, and category filters.
    7. Review charts, KPI cards, detailed tables, and downloadable results.
    """
)

if st.button(
    "Go to Data Upload",
    type="primary"
):
    st.switch_page("pages/0_Data_Upload.py")

st.markdown("---")

st.caption(
    "Data remains available while the current Streamlit session is active. "
    "Closing the browser, restarting the application, or session expiration "
    "may require the files to be uploaded again."
)