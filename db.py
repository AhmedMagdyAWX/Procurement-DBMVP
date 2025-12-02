# db.py
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

# In Streamlit Cloud, you'll set this in:
# Settings -> Secrets -> add key: DB_URL
DATABASE_URL = st.secrets["DB_URL"]

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency-style generator to get a DB session.
    Use it like:
        db = next(get_db())
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Import models and create tables in the DB.
    Call this once at startup from app.py.
    """
    import models  # noqa: F401  # Ensure models are registered
    Base.metadata.create_all(bind=engine)
