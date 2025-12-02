# pages/1_Companies_and_Capabilities.py

import streamlit as st

from db import get_db
from models import CompanyType
from services import (
    create_company,
    list_companies,
    create_capability,
    list_capabilities,
    add_capability_to_company,
    list_company_capabilities,
)

st.title("Companies & Capabilities")

st.markdown(
    """
This page lets you define **capabilities** (what companies are good at)  
and manage **developers / contractors** with their specializations.
"""
)

tab_caps, tab_companies = st.tabs(["⚙️ Capabilities", "🏢 Companies"])


# ---------------------------------------------------------
# TAB 1: CAPABILITIES
# ---------------------------------------------------------
with tab_caps:
    st.subheader("Create a new capability")

    with st.form("create_capability_form"):
        cap_name = st.text_input("Capability name", help="e.g. Residential High-Rise, Villas Compounds, Hospitals")
        cap_desc = st.text_area("Description", help="Optional notes about this capability.")
        submitted_cap = st.form_submit_button("Add capability")

        if submitted_cap:
            if not cap_name.strip():
                st.error("Capability name is required.")
            else:
                db = next(get_db())
                try:
                    create_capability(db, name=cap_name.strip(), description=cap_desc.strip() or None)
                    st.success(f"Capability **{cap_name}** created.")
                except Exception as e:
                    st.error(f"Could not create capability: {e}")

    st.markdown("---")
    st.subheader("Existing capabilities")

    db = next(get_db())
    caps = list_capabilities(db)

    if not caps:
        st.info("No capabilities defined yet. Create one above.")
    else:
        for cap in caps:
            st.write(f"- **{cap.name}** – {cap.description or '_No description_'}")


# ---------------------------------------------------------
# TAB 2: COMPANIES
# ---------------------------------------------------------
with tab_companies:
    st.subheader("Create a new company")

    company_type_label = st.radio(
        "Company type",
        options=["Developer", "Contractor"],
        horizontal=True,
        help="Developers create projects. Contractors bid / prequalify for them.",
    )
    company_type = CompanyType.DEVELOPER if company_type_label == "Developer" else CompanyType.CONTRACTOR

    size_options = ["", "Small", "Medium", "Large", "Mega"]

    with st.form("create_company_form"):
        name = st.text_input("Company name")
        country = st.text_input("Country", value="Egypt")
        city = st.text_input("City")
        website = st.text_input("Website")
        size_category = st.selectbox("Size category (optional)", options=size_options)
        description = st.text_area("Short description", height=80)

        submitted_company = st.form_submit_button("Create company")

        if submitted_company:
            if not name.strip():
                st.error("Company name is required.")
            else:
                db = next(get_db())
                try:
                    create_company(
                        db=db,
                        name=name.strip(),
                        company_type=company_type,
                        country=country.strip() or None,
                        city=city.strip() or None,
                        website=website.strip() or None,
                        description=description.strip() or None,
                        size_category=size_category or None,
                    )
                    st.success(f"{company_type_label} **{name}** created.")
                except Exception as e:
                    st.error(f"Could not create company: {e}")

    st.markdown("---")

    # Filter & list companies
    st.subheader("Existing companies")

    company_filter_label = st.selectbox(
        "Filter by company type",
        options=["All", "Developers only", "Contractors only"],
        index=0,
    )

    filter_type: CompanyType | None
    if company_filter_label == "Developers only":
        filter_type = CompanyType.DEVELOPER
    elif company_filter_label == "Contractors only":
        filter_type = CompanyType.CONTRACTOR
    else:
        filter_type = None

    db = next(get_db())
    companies = list_companies(db, company_type=filter_type)

    all_capabilities = list_capabilities(db)

    if not companies:
        st.info("No companies found yet.")
    else:
        for comp in companies:
            with st.expander(f"[{comp.id}] {comp.name} ({comp.company_type.value})", expanded=False):
                st.write(f"**Location:** {(comp.city or '')}, {(comp.country or '')}")
                st.write(f"**Website:** {comp.website or '-'}")
                st.write(f"**Size:** {comp.size_category or '-'}")
                st.write(f"**Description:** {comp.description or '-'}")

                st.markdown("### Capabilities")

                # Show current capabilities
                company_caps = list_company_capabilities(db, company_id=comp.id)
                if not company_caps:
                    st.info("No capabilities assigned yet.")
                else:
                    for cc in company_caps:
                        st.write(
                            f"- **{cc.capability.name}** "
                            f"(exp: {cc.experience_years or '-'} years, "
                            f"typical contract: {cc.typical_contract_value_million or '-'} M, "
                            f"size: {cc.typical_project_size_m2 or '-'} m²)"
                        )

                st.markdown("#### Add / update capability")

                if not all_capabilities:
                    st.warning("You need to create capabilities in the first tab before assigning them.")
                else:
                    cap_options = {cap.name: cap.id for cap in all_capabilities}
                    selected_cap_name = st.selectbox(
                        f"Capability for {comp.name}",
                        options=list(cap_options.keys()),
                        key=f"cap_select_{comp.id}",
                    )
                    selected_cap_id = cap_options[selected_cap_name]

                    exp_years = st.number_input(
                        "Experience (years)",
                        min_value=0.0,
                        step=0.5,
                        key=f"exp_years_{comp.id}",
                    )
                    typical_size = st.number_input(
                        "Typical project size (m²)",
                        min_value=0.0,
                        step=100.0,
                        key=f"size_{comp.id}",
                    )
                    typical_value = st.number_input(
                        "Typical contract value (million)",
                        min_value=0.0,
                        step=1.0,
                        key=f"value_{comp.id}",
                    )

                    if st.button("Save capability for this company", key=f"save_cap_{comp.id}"):
                        try:
                            add_capability_to_company(
                                db=db,
                                company_id=comp.id,
                                capability_id=selected_cap_id,
                                experience_years=exp_years or None,
                                typical_project_size_m2=typical_size or None,
                                typical_contract_value_million=typical_value or None,
                            )
                            st.success("Capability saved for this company. Scroll up or collapse/expand to refresh.")
                        except Exception as e:
                            st.error(f"Could not save capability: {e}")
