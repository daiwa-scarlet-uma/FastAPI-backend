# pyservice/models.py

from sqlalchemy import Column, Integer, String
from .db import Base

class Item(Base):
    __tablename__ = "items"

    id    = Column(Integer, primary_key=True, index=True)
    name  = Column(String, index=True, nullable=False)
    price = Column(Integer, nullable=False)
