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
    # Проверяем, что есть компания
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Сначала создайте компанию в настройках")

    # Читаем файл (пока просто сохраняем как пример)
    content = await file.read()
    # Здесь будет парсер TXT, но для MVP просто сохраняем запись-заглушку
    statement = BankStatement(
        id=str(uuid.uuid4()),
        company_id=company.id,
        transaction_date=datetime.now().date(),
        amount=0,  # заглушка
        counterparty="Заглушка",
        purpose="Заглушка",
        is_income=None,
        file_name=file.filename
    )
    db.add(statement)
    db.commit()
    return {"message": f"Файл {file.filename} загружен", "id": statement.id}