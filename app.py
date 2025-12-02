# app.py
import streamlit as st
from db import init_db

st.set_page_config(
    page_title="My Platform",
    page_icon="🧠",
    layout="wide",
)

# Initialize DB (creates tables if not exist)
init_db()

st.title("My Platform (Skeleton)")
st.write("Welcome! This is the base skeleton connected to PostgreSQL via SQLAlchemy.")

st.markdown(
    """
    Use the sidebar to navigate between pages.
    
    For now, there is just an **Example CRUD** page.
    Once your real platform idea is defined, we'll add proper pages and entities.
    """
)
