from sqlalchemy import Column, String, Numeric, DateTime, func
from app.database import Base
import uuid

class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    unp = Column(String(9), unique=True, nullable=False)
    usn_rate = Column(Numeric(5,2), nullable=False, default=6.00)
    income_tax_rate = Column(Numeric(5,2), nullable=False, default=13.00)
    fszn_employee_rate = Column(Numeric(5,2), nullable=False, default=1.00)
    fszn_employer_rate = Column(Numeric(5,2), nullable=False, default=34.00)
    belgosstrakh_rate = Column(Numeric(5,2), nullable=False, default=0.60)
    reserve_fund_percent = Column(Numeric(5,2), nullable=False, default=5.00)
    base_value = Column(Numeric(10,2), nullable=False, default=45.00)
    usn_revenue_limit = Column(Numeric(15,2), nullable=False, default=3735000.00)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())