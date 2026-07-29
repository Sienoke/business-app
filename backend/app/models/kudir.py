from sqlalchemy import Column, String, Numeric, Date, DateTime, func, ForeignKey
from app.database import Base
import uuid

class KUDiREntry(Base):
    __tablename__ = "kudir_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    income_amount = Column(Numeric(12,2), nullable=False, default=0)
    expense_amount = Column(Numeric(12,2), nullable=False, default=0)
    source = Column(String(50))
    source_id = Column(String(36))
    period = Column(String(20))

    created_at = Column(DateTime, server_default=func.now())