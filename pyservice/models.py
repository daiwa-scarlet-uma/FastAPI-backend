from sqlalchemy import Column, Integer
from .db import Base

class Operation(Base):
    __tablename__ = "operations"
    id     = Column(Integer, primary_key=True, index=True)
    a      = Column(Integer, nullable=False)
    b      = Column(Integer, nullable=False)
    result = Column(Integer, nullable=False)
