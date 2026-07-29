from sqlalchemy import Column, String, Numeric, Date, Boolean, DateTime, func, ForeignKey
from app.database import Base
import uuid

class BankStatement(Base):
    __tablename__ = "bank_statements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    counterparty = Column(String(255))
    purpose = Column(String(500))
    is_income = Column(Boolean, nullable=True)
    imported_at = Column(DateTime, server_default=func.now())
    file_name = Column(String(255))