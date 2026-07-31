from sqlalchemy.orm import Session
from app.models.employee import Employee
from app.models.company import Company
from app.models.settings import AvgSalary
from datetime import date

def calculate_employee_cost(employee: Employee, company: Company, avg_salary: float = None) -> dict:
    """
    Calculate full cost and net pay for an employee.
    All rates are taken from company settings.
    """
    gross = float(employee.salary)
    
    # Get rates from company (stored as percentages, e.g., 13.0 for 13%)
    income_tax_rate = float(company.income_tax_rate) / 100
    fszn_employee_rate = float(company.fszn_employee_rate) / 100
    fszn_employer_rate = float(company.fszn_employer_rate) / 100
    belgosstrakh_rate = float(company.belgosstrakh_rate) / 100
    
    # Income tax (from salary)
    income_tax = gross * income_tax_rate
    
    # FSZN employee (deducted from salary)
    fszn_employee = gross * fszn_employee_rate
    
    # Net pay (what employee receives)
    net_pay = gross - income_tax - fszn_employee
    
    # FSZN employer (paid by company on top of salary)
    fszn_employer = gross * fszn_employer_rate
    
    # Belgosstrakh (paid by company on top of salary)
    # Special rule for CEO: if gross < avg_salary, use avg_salary as base
    belgosstrakh_base = gross
    if employee.is_ceo and avg_salary and gross < avg_salary:
        belgosstrakh_base = avg_salary
    belgosstrakh = belgosstrakh_base * belgosstrakh_rate
    
    total_cost = gross + fszn_employer + belgosstrakh
    
    return {
        'gross': gross,
        'income_tax': income_tax,
        'fszn_employee': fszn_employee,
        'net_pay': net_pay,
        'fszn_employer': fszn_employer,
        'belgosstrakh': belgosstrakh,
        'total_cost': total_cost
    }

def calculate_all_employees_cost(db: Session, company_id: str, month: date) -> dict:
    """
    Calculate cost for all employees for a given month.
    Returns dict with employee_id as key and cost breakdown as value.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return {}
    
    # Get average salary for the month (if any)
    avg_salary_record = db.query(AvgSalary).filter(AvgSalary.month == month.replace(day=1)).first()
    avg_salary = float(avg_salary_record.amount) if avg_salary_record else None
    
    employees = db.query(Employee).filter(Employee.company_id == company_id).all()
    result = {}
    for emp in employees:
        result[emp.id] = calculate_employee_cost(emp, company, avg_salary)
    return result
