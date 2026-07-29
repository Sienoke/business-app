from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bank_statement import BankStatement
from app.models.company import Company
from app.models.kudir import KUDiREntry
from app.utils.parser_bank import parse_bank_statement
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found. Please create company first.")

    # Читаем содержимое файла
    content = await file.read()
    try:
        text_content = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            text_content = content.decode('cp1251')  # для Windows-1251
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File encoding not supported. Please use UTF-8 or Windows-1251.")

    # Парсим выписку
    operations = parse_bank_statement(text_content)
    
    if not operations:
        raise HTTPException(status_code=400, detail="No operations found in the file. Please check file format.")

    # Сохраняем каждую операцию в базу данных
    saved_operations = []
    for op in operations:
        statement = BankStatement(
            id=str(uuid.uuid4()),
            company_id=company.id,
            transaction_date=datetime.strptime(op['date'], '%Y-%m-%d').date(),
            amount=op['amount'],
            counterparty=op['counterparty'],
            purpose=op['purpose'],
            is_income=op['is_income'],
            file_name=file.filename
        )
        db.add(statement)
        
        # Если операция - доход, добавляем запись в КУДиР
        if op['is_income'] is True:
            # Определяем период (квартал)
            dt = datetime.strptime(op['date'], '%Y-%m-%d')
            quarter = (dt.month - 1) // 3 + 1
            period = f"Q{quarter}-{dt.year}"
            
            kudir_entry = KUDiREntry(
                id=str(uuid.uuid4()),
                company_id=company.id,
                entry_date=dt.date(),
                income_amount=op['amount'],
                expense_amount=0,
                source="bank",
                source_id=statement.id,
                period=period
            )
            db.add(kudir_entry)
        
        saved_operations.append({
            'date': op['date'],
            'amount': op['amount'],
            'type': 'Доход' if op['is_income'] else 'Расход',
            'counterparty': op['counterparty'],
            'purpose': op['purpose']
        })
    
    db.commit()
    
    return {
        "message": f"File {file.filename} processed successfully",
        "operations_count": len(operations),
        "operations": saved_operations
    }
