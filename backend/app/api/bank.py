from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.bank_statement import BankStatement
from app.models.company import Company
from app.models.kudir import KUDiREntry
from app.utils.parser_txt import parse_bank_statement_txt
from app.utils.parser_docx import parse_bank_statement_docx
from app.utils.parser_xlsx import parse_bank_statement_xlsx
from app.utils.parser_csv import parse_bank_statement_csv
from datetime import datetime
import uuid
import os

router = APIRouter()

@router.post("/upload")
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    company = db.query(Company).first()
    if not company:
        raise HTTPException(status_code=400, detail="Company not found. Please create company first.")

    ext = os.path.splitext(file.filename.lower())[1]
    content = await file.read()

    if ext == '.txt':
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('cp1251')
        operations = parse_bank_statement_txt(text)
    elif ext == '.docx':
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            operations = parse_bank_statement_docx(tmp_path)
        finally:
            os.unlink(tmp_path)
    elif ext in ('.xlsx', '.xls'):
        import tempfile
        suffix = '.xlsx' if ext == '.xlsx' else '.xls'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            operations = parse_bank_statement_xlsx(tmp_path)
        finally:
            os.unlink(tmp_path)
    elif ext == '.csv':
        try:
            text = content.decode('utf-8')
        except UnicodeDecodeError:
            text = content.decode('cp1251')
        operations = parse_bank_statement_csv(text)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    if not operations:
        raise HTTPException(status_code=400, detail="No operations found.")

    saved = []
    for op in operations:
        stmt = BankStatement(
            id=str(uuid.uuid4()),
            company_id=company.id,
            transaction_date=datetime.strptime(op['date'], '%Y-%m-%d').date(),
            amount=op['amount'],
            counterparty=op['counterparty'],
            purpose=op['purpose'],
            is_income=op['is_income'],
            file_name=file.filename
        )
        db.add(stmt)
        if op['is_income']:
            dt = datetime.strptime(op['date'], '%Y-%m-%d')
            quarter = (dt.month - 1)//3 + 1
            period = f"Q{quarter}-{dt.year}"
            kudir = KUDiREntry(
                id=str(uuid.uuid4()),
                company_id=company.id,
                entry_date=dt.date(),
                income_amount=op['amount'],
                expense_amount=0,
                source="bank",
                source_id=stmt.id,
                period=period
            )
            db.add(kudir)
        saved.append({
            'date': op['date'],
            'amount': op['amount'],
            'type': 'Доход' if op['is_income'] else 'Расход',
            'counterparty': op['counterparty'],
            'purpose': op['purpose']
        })
    db.commit()
    return {
        "message": f"File {file.filename} processed",
        "operations_count": len(operations),
        "operations": saved
    }
