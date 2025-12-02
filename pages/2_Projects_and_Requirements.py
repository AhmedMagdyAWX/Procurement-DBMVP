# pages/2_Projects_and_Requirements.py

import streamlit as st

from db import get_db
from models import CompanyType, ProjectStatus
from services import (
    list_companies,
    list_capabilities,
    create_project,
    list_projects,
    add_project_requirement,
    list_project_requirements,
)

st.title("Projects & Requirements")

st.markdown(
    """
This page lets **developers** create projects and define the
**capability requirements** that contractors must have.

Later, the matching engine will use these requirements to rank contractors.
"""
)

db = next(get_db())

# ---------------------------------------
# 1) Choose developer
# ---------------------------------------
st.subheader("1. Select developer company")

developers = list_companies(db, company_type=CompanyType.DEVELOPER)

if not developers:
    st.warning("No developer companies found. Go to **Companies & Capabilities** page and create at least one Developer.")
    st.stop()

dev_options = {f"[{c.id}] {c.name}": c.id for c in developers}
selected_dev_label = st.selectbox(
    "Developer",
    options=list(dev_options.keys()),
)
selected_dev_id = dev_options[selected_dev_label]

selected_dev = next((d for d in developers if d.id == selected_dev_id), None)
st.info(f"Selected developer: **{selected_dev.name}**")


# ---------------------------------------
# 2) Create new project for this developer
# ---------------------------------------
st.subheader("2. Create a new project")

project_type_default_options = [
    "",
    "Residential Compound",
    "Residential Towers",
    "Commercial Mall",
    "Mixed-use",
    "Industrial",
    "Infrastructure",
]

status_options_map = {
    "Draft": ProjectStatus.DRAFT,
    "Open": ProjectStatus.OPEN,
    "Closed": ProjectStatus.CLOSED,
}

with st.form("create_project_form"):
    name = st.text_input("Project name", help="e.g. New Cairo Residential Compound")
    location = st.text_input("Location", help="City / Area, e.g. New Cairo, 6th of October, etc.")
    project_type = st.selectbox("Project type", options=project_type_default_options)
    description = st.text_area("Short description", height=100)

    col1, col2 = st.columns(2)
    with col1:
        built_up_area_m2 = st.number_input(
            "Built-up area (m²)",
            min_value=0.0,
            step=1000.0,
            format="%.2f",
        )
    with col2:
        estimated_budget_million = st.number_input(
            "Estimated budget (million)",
            min_value=0.0,
            step=10.0,
            format="%.2f",
        )

    status_label = st.selectbox(
        "Initial status",
        options=list(status_options_map.keys()),
        index=1,  # default to "Open"
    )
    submitted_project = st.form_submit_button("Create project")

    if submitted_project:
        if not name.strip():
            st.error("Project name is required.")
        else:
            try:
                project = create_project(
                    db=db,
                    developer_company_id=selected_dev_id,
                    name=name.strip(),
                    location=location.strip() or None,
                    project_type=project_type or None,
                    description=description.strip() or None,
                    built_up_area_m2=built_up_area_m2 or None,
                    estimated_budget_million=estimated_budget_million or None,
                    status=status_options_map[status_label],
                )
                st.success(f"Project **{project.name}** created for developer **{selected_dev.name}**.")
            except Exception as e:
                st.error(f"Could not create project: {e}")


st.markdown("---")

# ---------------------------------------
# 3) List projects for this developer
# ---------------------------------------
st.subheader("3. Projects for this developer")

projects = list_projects(db, developer_company_id=selected_dev_id)

if not projects:
    st.info("No projects created yet for this developer.")
    st.stop()

capabilities = list_capabilities(db)
cap_options = {cap.name: cap.id for cap in capabilities} if capabilities else {}

for proj in projects:
    with st.expander(f"[{proj.id}] {proj.name}  ({proj.status.value})", expanded=False):
        st.write(f"**Location:** {proj.location or '-'}")
        st.write(f"**Type:** {proj.project_type or '-'}")
        st.write(f"**BUA:** {proj.built_up_area_m2 or '-'} m²")
        st.write(f"**Budget:** {proj.estimated_budget_million or '-'} million")
        st.write(f"**Description:** {proj.description or '-'}")

        st.markdown("### Requirements")

        # Show existing requirements
        reqs = list_project_requirements(db, project_id=proj.id)

        if not reqs:
            st.info("No requirements defined yet for this project.")
        else:
            for r in reqs:
                st.write(
                    f"- **{r.capability.name}** "
                    f"(min exp: {r.min_experience_years or '-'} years, "
                    f"min contract value: {r.min_contract_value_million or '-'} million)"
                )

        st.markdown("#### Add new requirement")

        if not capabilities:
            st.warning("No capabilities defined yet. Go to **Companies & Capabilities** page and create some.")
        else:
            with st.form(f"add_req_form_{proj.id}"):
                selected_cap_name = st.selectbox(
                    "Capability",
                    options=list(cap_options.keys()),
                    key=f"cap_select_proj_{proj.id}",
                )
                selected_cap_id = cap_options[selected_cap_name]

                colr1, colr2 = st.columns(2)
                with colr1:
                    min_exp_years = st.number_input(
                        "Minimum experience (years)",
                        min_value=0.0,
                        step=0.5,
                        key=f"min_exp_{proj.id}",
                    )
                with colr2:
                    min_contract_value = st.number_input(
                        "Minimum similar contract value (million)",
                        min_value=0.0,
                        step=5.0,
                        key=f"min_value_{proj.id}",
                    )

                submitted_req = st.form_submit_button("Add requirement")

                if submitted_req:
                    try:
                        add_project_requirement(
                            db=db,
                            project_id=proj.id,
                            capability_id=selected_cap_id,
                            min_experience_years=min_exp_years or None,
                            min_contract_value_million=min_contract_value or None,
                        )
                        st.success("Requirement added. Collapse and expand again to refresh.")
                    except Exception as e:
                        st.error(f"Could not add requirement: {e}")
