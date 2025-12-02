# models.py
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Enum,
    ForeignKey,
    Float,
    DateTime,
    func,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from db import Base


class CompanyType(enum.Enum):
    DEVELOPER = "developer"
    CONTRACTOR = "contractor"


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    company_type = Column(Enum(CompanyType), nullable=False, index=True)

    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    size_category = Column(String(50), nullable=True)  # "small", "medium", "large" etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    capabilities = relationship(
        "CompanyCapability",
        back_populates="company",
        cascade="all, delete-orphan",
    )
    projects = relationship(
        "Project",
        back_populates="developer",
        cascade="all, delete-orphan",
    )
    prequalification_responses = relationship(
        "PrequalificationResponse",
        back_populates="contractor",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name} type={self.company_type.value}>"


class Capability(Base):
    __tablename__ = "capabilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    company_capabilities = relationship(
        "CompanyCapability",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    project_requirements = relationship(
        "ProjectRequirement",
        back_populates="capability",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Capability id={self.id} name={self.name}>"


class CompanyCapability(Base):
    __tablename__ = "company_capabilities"
    __table_args__ = (
        UniqueConstraint("company_id", "capability_id", name="uq_company_capability"),
    )

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    capability_id = Column(Integer, ForeignKey("capabilities.id", ondelete="CASCADE"), nullable=False)

    experience_years = Column(Float, nullable=True)  # e.g. 5.0 years
    typical_project_size_m2 = Column(Float, nullable=True)
    typical_contract_value_million = Column(Float, nullable=True)  # in million EGP/USD, etc.

    company = relationship("Company", back_populates="capabilities")
    capability = relationship("Capability", back_populates="company_capabilities")

    def __repr__(self) -> str:
        return f"<CompanyCapability company_id={self.company_id} capability_id={self.capability_id}>"


class ProjectStatus(enum.Enum):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    developer_company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    project_type = Column(String(100), nullable=True)  # e.g. "Residential", "Commercial"
    description = Column(Text, nullable=True)

    built_up_area_m2 = Column(Float, nullable=True)
    estimated_budget_million = Column(Float, nullable=True)

    status = Column(Enum(ProjectStatus), nullable=False, default=ProjectStatus.DRAFT)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    developer = relationship("Company", back_populates="projects")
    requirements = relationship(
        "ProjectRequirement",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    prequalification_responses = relationship(
        "PrequalificationResponse",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} name={self.name} status={self.status.value}>"


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    capability_id = Column(
        Integer,
        ForeignKey("capabilities.id", ondelete="CASCADE"),
        nullable=False,
    )

    min_experience_years = Column(Float, nullable=True)
    min_contract_value_million = Column(Float, nullable=True)

    project = relationship("Project", back_populates="requirements")
    capability = relationship("Capability", back_populates="project_requirements")

    def __repr__(self) -> str:
        return f"<ProjectRequirement project_id={self.project_id} capability_id={self.capability_id}>"


class PrequalificationStatus(enum.Enum):
    INTERESTED = "interested"
    SUBMITTED = "submitted"
    REJECTED = "rejected"
    SHORTLISTED = "shortlisted"


class PrequalificationResponse(Base):
    __tablename__ = "prequalification_responses"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "contractor_company_id",
            name="uq_project_contractor_response",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    contractor_company_id = Column(
        Integer,
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )

    status = Column(Enum(PrequalificationStatus), nullable=False, default=PrequalificationStatus.INTERESTED)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    project = relationship("Project", back_populates="prequalification_responses")
    contractor = relationship("Company", back_populates="prequalification_responses")

    def __repr__(self) -> str:
        return f"<PrequalificationResponse project_id={self.project_id} contractor_company_id={self.contractor_company_id}>"
