from sqlalchemy import Column, String, Numeric, Date, DateTime, func, Boolean, ForeignKey
from app.database import Base
import uuid

class Employee(Base):
    __tablename__ = "employees"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    full_name = Column(String(200), nullable=False)
    position = Column(String(100))
    salary = Column(Numeric(12,2), nullable=False)
    hire_date = Column(Date, nullable=False)
    contract_number = Column(String(50))
    passport_data = Column(String(255))
    premium_percent = Column(Numeric(5,2), default=0.00)
    is_ceo = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())