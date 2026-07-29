import csv
import re
from datetime import datetime
from typing import List, Dict
import io

def parse_bank_statement_csv(content: str) -> List[Dict]:
    operations = []
    
    csv_file = io.StringIO(content)
    reader = csv.DictReader(csv_file, delimiter=';', quotechar='"')
    
    for row in reader:
        date_str = row.get('Документ - Дата', '').strip()
        if not date_str:
            continue
        
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
            continue
        
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            continue
        
        debit_str = row.get('Номинал - Дебет', '').strip()
        credit_str = row.get('Номинал - Кредит', '').strip()
        
        if not debit_str and not credit_str:
            continue
        
        debit = 0.0
        credit = 0.0
        if debit_str:
            debit = float(debit_str.replace(',', ''))
        if credit_str:
            credit = float(credit_str.replace(',', ''))
        
        is_income = None
        amount = 0.0
        if credit > 0:
            is_income = True
            amount = credit
        elif debit > 0:
            is_income = False
            amount = debit
        else:
            continue
        
        counterparty = row.get('Корреспондент - Название', '').strip()
        unp = row.get('Корреспондент - УНП', '').strip()
        purpose = row.get('Назначение платежа', '').strip()
        
        if not purpose:
            purpose = f"Payment by agreement {row.get('Документ - №', '')}"
        
        operations.append({
            'date': date_obj.isoformat(),
            'amount': amount,
            'is_income': is_income,
            'counterparty': counterparty or 'Unknown counterparty',
            'purpose': purpose or 'No purpose',
            'counterparty_unp': unp,
            'debit': debit,
            'credit': credit
        })
    
    return operations
