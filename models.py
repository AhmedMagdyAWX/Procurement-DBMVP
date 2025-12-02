# models.py
from sqlalchemy import Column, Integer, String, DateTime, func
from db import Base


class ExampleItem(Base):
    __tablename__ = "example_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
