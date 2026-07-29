from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bank_statement import BankStatement
from app.models.company import Company
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found. Please create company first.")

    content = await file.read()
    
    statement = BankStatement(
        id=str(uuid.uuid4()),
        company_id=company.id,
        transaction_date=datetime.now().date(),
        amount=0,
        counterparty="Placeholder",
        purpose="Placeholder",
        is_income=None,
        file_name=file.filename
    )
    db.add(statement)
    db.commit()
    return {"message": f"File {file.filename} uploaded", "id": statement.id}
