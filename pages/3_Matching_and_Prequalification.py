# pages/3_Matching_and_Prequalification.py

import streamlit as st

from db import get_db
from models import CompanyType, PrequalificationStatus
from services import (
    list_companies,
    list_projects,
    list_project_requirements,
    match_contractors_for_project,
    list_prequalification_responses_for_project,
    create_or_update_prequalification_response,
)

st.title("Matching & Prequalification")

st.markdown(
    """
This page helps you **match contractors** to a specific project based on its
**requirements and capabilities**, and manage **prequalification decisions**.
"""
)

db = next(get_db())

# ---------------------------------------
# 1) Select developer
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
# 2) Select project for this developer
# ---------------------------------------
st.subheader("2. Select project")

projects = list_projects(db, developer_company_id=selected_dev_id)

if not projects:
    st.warning("This developer has no projects yet. Go to **Projects & Requirements** page and create one.")
    st.stop()

proj_options = {f"[{p.id}] {p.name} ({p.status.value})": p.id for p in projects}
selected_proj_label = st.selectbox(
    "Project",
    options=list(proj_options.keys()),
)
selected_proj_id = proj_options[selected_proj_label]
selected_project = next((p for p in projects if p.id == selected_proj_id), None)

st.markdown(
    f"""
**Project details**

- **Name:** {selected_project.name}  
- **Location:** {selected_project.location or '-'}  
- **Type:** {selected_project.project_type or '-'}  
- **BUA:** {selected_project.built_up_area_m2 or '-'} m²  
- **Budget:** {selected_project.estimated_budget_million or '-'} million  
- **Status:** {selected_project.status.value}  
"""
)

# Show project requirements
st.markdown("### Project requirements")

reqs = list_project_requirements(db, project_id=selected_proj_id)
if not reqs:
    st.warning("No requirements defined yet for this project. Matching will not be effective.")
else:
    for r in reqs:
        st.write(
            f"- **{r.capability.name}** "
            f"(min exp: {r.min_experience_years or '-'} years, "
            f"min contract value: {r.min_contract_value_million or '-'} million)"
        )

st.markdown("---")

# ---------------------------------------
# 3) Run matching
# ---------------------------------------
st.subheader("3. Matching contractors for this project")

if st.button("Run matching", type="primary"):
    st.session_state["run_matching"] = True

if st.session_state.get("run_matching", False):
    matches = match_contractors_for_project(db, project_id=selected_proj_id)

    if not matches:
        st.info("No matching contractors found for this project based on current requirements and capabilities.")
    else:
        st.success(f"Found **{len(matches)}** matching contractor(s). Ranked by score.")

        # Load existing prequalification responses for this project
        existing_resps = list_prequalification_responses_for_project(db, project_id=selected_proj_id)
        resp_by_contractor = {r.contractor_company_id: r for r in existing_resps}

        # status label mapping
        status_label_to_enum = {
            "Interested": PrequalificationStatus.INTERESTED,
            "Submitted": PrequalificationStatus.SUBMITTED,
            "Shortlisted": PrequalificationStatus.SHORTLISTED,
            "Rejected": PrequalificationStatus.REJECTED,
        }
        status_enum_to_label = {v: k for k, v in status_label_to_enum.items()}

        for company, score, matched_count in matches:
            existing_resp = resp_by_contractor.get(company.id)

            with st.expander(
                f"[{company.id}] {company.name} – Score: {score:.2f} (matched {matched_count} requirement(s))",
                expanded=False,
            ):
                st.write(f"**Location:** {(company.city or '-')}, {(company.country or '-')}")
                st.write(f"**Website:** {company.website or '-'}")
                st.write(f"**Size:** {company.size_category or '-'}")
                st.write(f"**Description:** {company.description or '-'}")

                if existing_resp:
                    st.info(
                        f"Current prequalification status: **{status_enum_to_label.get(existing_resp.status, 'Unknown')}**"
                    )
                    existing_notes = existing_resp.notes or ""
                else:
                    existing_notes = ""

                st.markdown("#### Set / update prequalification decision")

                status_label_default = (
                    status_enum_to_label.get(existing_resp.status)
                    if existing_resp
                    else "Interested"
                )

                status_label = st.selectbox(
                    "Prequalification status",
                    options=list(status_label_to_enum.keys()),
                    index=list(status_label_to_enum.keys()).index(status_label_default),
                    key=f"status_{selected_proj_id}_{company.id}",
                )
                notes = st.text_area(
                    "Notes (optional)",
                    value=existing_notes,
                    key=f"notes_{selected_proj_id}_{company.id}",
                )

                if st.button(
                    "Save decision",
                    key=f"save_decision_{selected_proj_id}_{company.id}",
                ):
                    try:
                        resp = create_or_update_prequalification_response(
                            db=db,
                            project_id=selected_proj_id,
                            contractor_company_id=company.id,
                            status=status_label_to_enum[status_label],
                            notes=notes.strip() or None,
                        )
                        st.success(
                            f"Decision saved: {company.name} → {status_label} "
                            f"(response id: {resp.id})"
                        )
                    except Exception as e:
                        st.error(f"Could not save decision: {e}")
else:
    st.info("Click **Run matching** to see ranked contractors for this project.")
