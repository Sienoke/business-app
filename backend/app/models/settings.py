from sqlalchemy import Column, String, Numeric, Date, DateTime, func
from app.database import Base
import uuid

class AvgSalary(Base):
    __tablename__ = "avg_salaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    month = Column(Date, nullable=False, unique=True)
    amount = Column(Numeric(12,2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())