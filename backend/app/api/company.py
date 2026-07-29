from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.company import Company
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CompanyCreate(BaseModel):
    name: str
    unp: str
    usn_rate: Optional[float] = 6.0
    income_tax_rate: Optional[float] = 13.0
    fszn_employee_rate: Optional[float] = 1.0
    fszn_employer_rate: Optional[float] = 34.0
    belgosstrakh_rate: Optional[float] = 0.6
    reserve_fund_percent: Optional[float] = 5.0
    base_value: Optional[float] = 45.0
    usn_revenue_limit: Optional[float] = 3735000.0

class CompanyResponse(BaseModel):
    id: str
    name: str
    unp: str
    usn_rate: float
    income_tax_rate: float
    fszn_employee_rate: float
    fszn_employer_rate: float
    belgosstrakh_rate: float
    reserve_fund_percent: float
    base_value: float
    usn_revenue_limit: float

@router.post("/", response_model=CompanyResponse)
def create_company(company: CompanyCreate, db: Session = Depends(get_db)):
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

@router.get("/", response_model=CompanyResponse)
def get_company(db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company