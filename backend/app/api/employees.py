from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.employee import Employee
from app.models.company import Company
from app.models.settings import AvgSalary
from app.services.payroll import calculate_employee_cost, calculate_all_employees_cost
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uuid

router = APIRouter()

# Schemas
class EmployeeCreate(BaseModel):
    full_name: str
    position: str
    salary: float
    hire_date: date
    contract_number: Optional[str] = None
    passport_data: Optional[str] = None
    premium_percent: Optional[float] = 0.0
    is_ceo: bool = False

class EmployeeResponse(BaseModel):
    id: str
    full_name: str
    position: str
    salary: float
    hire_date: date
    contract_number: Optional[str]
    passport_data: Optional[str]
    premium_percent: float
    is_ceo: bool

class EmployeeCostResponse(BaseModel):
    employee_id: str
    full_name: str
    gross: float
    income_tax: float
    fszn_employee: float
    net_pay: float
    fszn_employer: float
    belgosstrakh: float
    total_cost: float

# Endpoints
@router.post("/", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found. Please create company first.")
    
    db_employee = Employee(
        id=str(uuid.uuid4()),
        company_id=company.id,
        full_name=employee.full_name,
        position=employee.position,
        salary=employee.salary,
        hire_date=employee.hire_date,
        contract_number=employee.contract_number,
        passport_data=employee.passport_data,
        premium_percent=employee.premium_percent,
        is_ceo=employee.is_ceo
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

@router.get("/", response_model=List[EmployeeResponse])
def list_employees(db: Session = Depends(get_db)):
    employees = db.query(Employee).all()
    return employees

@router.get("/cost", response_model=List[EmployeeCostResponse])
def get_employee_costs(year: int, month: int, db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    month_date = date(year, month, 1)
    costs = calculate_all_employees_cost(db, company.id, month_date)
    
    result = []
    for emp_id, cost_data in costs.items():
        employee = db.query(Employee).filter(Employee.id == emp_id).first()
        if employee:
            result.append({
                'employee_id': emp_id,
                'full_name': employee.full_name,
                **cost_data
            })
    return result

@router.get("/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.delete("/{employee_id}")
def delete_employee(employee_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return {"message": "Employee deleted"}
