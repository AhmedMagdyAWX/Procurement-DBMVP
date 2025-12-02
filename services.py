# services.py
from typing import List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import select, func

from models import (
    Company,
    CompanyType,
    Capability,
    CompanyCapability,
    Project,
    ProjectStatus,
    ProjectRequirement,
    PrequalificationResponse,
    PrequalificationStatus,
)


# --------------------
# Companies
# --------------------

def create_company(
    db: Session,
    name: str,
    company_type: CompanyType,
    country: str | None = None,
    city: str | None = None,
    website: str | None = None,
    description: str | None = None,
    size_category: str | None = None,
) -> Company:
    company = Company(
        name=name,
        company_type=company_type,
        country=country,
        city=city,
        website=website,
        description=description,
        size_category=size_category,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


def list_companies(db: Session, company_type: CompanyType | None = None) -> List[Company]:
    stmt = select(Company).order_by(Company.name.asc())
    if company_type:
        stmt = stmt.where(Company.company_type == company_type)
    return list(db.scalars(stmt))


# --------------------
# Capabilities
# --------------------

def create_capability(
    db: Session,
    name: str,
    description: str | None = None,
) -> Capability:
    cap = Capability(name=name, description=description)
    db.add(cap)
    db.commit()
    db.refresh(cap)
    return cap


def list_capabilities(db: Session) -> List[Capability]:
    stmt = select(Capability).order_by(Capability.name.asc())
    return list(db.scalars(stmt))


def add_capability_to_company(
    db: Session,
    company_id: int,
    capability_id: int,
    experience_years: float | None = None,
    typical_project_size_m2: float | None = None,
    typical_contract_value_million: float | None = None,
) -> CompanyCapability:
    # upsert-like: check if exists
    stmt = select(CompanyCapability).where(
        CompanyCapability.company_id == company_id,
        CompanyCapability.capability_id == capability_id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        existing.experience_years = experience_years
        existing.typical_project_size_m2 = typical_project_size_m2
        existing.typical_contract_value_million = typical_contract_value_million
        db.commit()
        db.refresh(existing)
        return existing

    cc = CompanyCapability(
        company_id=company_id,
        capability_id=capability_id,
        experience_years=experience_years,
        typical_project_size_m2=typical_project_size_m2,
        typical_contract_value_million=typical_contract_value_million,
    )
    db.add(cc)
    db.commit()
    db.refresh(cc)
    return cc


def list_company_capabilities(db: Session, company_id: int) -> List[CompanyCapability]:
    stmt = select(CompanyCapability).where(CompanyCapability.company_id == company_id)
    return list(db.scalars(stmt))


# --------------------
# Projects
# --------------------

def create_project(
    db: Session,
    developer_company_id: int,
    name: str,
    location: str | None = None,
    project_type: str | None = None,
    description: str | None = None,
    built_up_area_m2: float | None = None,
    estimated_budget_million: float | None = None,
    status: ProjectStatus = ProjectStatus.OPEN,
) -> Project:
    project = Project(
        developer_company_id=developer_company_id,
        name=name,
        location=location,
        project_type=project_type,
        description=description,
        built_up_area_m2=built_up_area_m2,
        estimated_budget_million=estimated_budget_million,
        status=status,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, developer_company_id: int | None = None) -> List[Project]:
    stmt = select(Project).order_by(Project.created_at.desc())
    if developer_company_id:
        stmt = stmt.where(Project.developer_company_id == developer_company_id)
    return list(db.scalars(stmt))


def add_project_requirement(
    db: Session,
    project_id: int,
    capability_id: int,
    min_experience_years: float | None = None,
    min_contract_value_million: float | None = None,
) -> ProjectRequirement:
    req = ProjectRequirement(
        project_id=project_id,
        capability_id=capability_id,
        min_experience_years=min_experience_years,
        min_contract_value_million=min_contract_value_million,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def list_project_requirements(db: Session, project_id: int) -> List[ProjectRequirement]:
    stmt = select(ProjectRequirement).where(ProjectRequirement.project_id == project_id)
    return list(db.scalars(stmt))


# --------------------
# Prequalification
# --------------------

def create_or_update_prequalification_response(
    db: Session,
    project_id: int,
    contractor_company_id: int,
    status: PrequalificationStatus = PrequalificationStatus.INTERESTED,
    notes: str | None = None,
) -> PrequalificationResponse:
    stmt = select(PrequalificationResponse).where(
        PrequalificationResponse.project_id == project_id,
        PrequalificationResponse.contractor_company_id == contractor_company_id,
    )
    existing = db.scalars(stmt).first()
    if existing:
        existing.status = status
        existing.notes = notes
        db.commit()
        db.refresh(existing)
        return existing

    resp = PrequalificationResponse(
        project_id=project_id,
        contractor_company_id=contractor_company_id,
        status=status,
        notes=notes,
    )
    db.add(resp)
    db.commit()
    db.refresh(resp)
    return resp


def list_prequalification_responses_for_project(
    db: Session,
    project_id: int,
) -> List[PrequalificationResponse]:
    stmt = select(PrequalificationResponse).where(
        PrequalificationResponse.project_id == project_id
    )
    return list(db.scalars(stmt))


# --------------------
# Matching logic
# --------------------

def match_contractors_for_project(
    db: Session,
    project_id: int,
) -> List[Tuple[Company, float, int]]:
    """
    Returns list of (contractor_company, match_score, matched_capabilities_count)
    sorted by score descending.

    Simple scoring:
    - For each required capability, check if contractor has it.
    - Score = number of matched required capabilities.
    """

    project = db.get(Project, project_id)
    if not project:
        return []

    # Get the requirements for this project
    req_stmt = select(ProjectRequirement).where(ProjectRequirement.project_id == project_id)
    requirements = list(db.scalars(req_stmt))
    if not requirements:
        return []

    cc = CompanyCapability
    c = Company
    r = ProjectRequirement

    # Join contractors with capabilities and requirements
    join_stmt = (
        select(
            c,
            func.count(r.id).label("matched_count"),
        )
        .join(cc, c.id == cc.company_id)
        .join(r, cc.capability_id == r.capability_id)
        .where(c.company_type == CompanyType.CONTRACTOR)
        .where(r.project_id == project_id)
        .group_by(c.id)
    )

    rows = db.execute(join_stmt).all()

    results: List[Tuple[Company, float, int]] = []
    for company, matched_count in rows:
        score = float(matched_count)  # simple score = matched requirements count
        results.append((company, score, matched_count))

    # sort by score descending
    results.sort(key=lambda t: t[1], reverse=True)
    return results
