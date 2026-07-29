import csv
import re
from datetime import datetime
from typing import List, Dict
import io
import logging

logger = logging.getLogger(__name__)

def detect_dialect(sample: str) -> str:
    if ';' in sample:
        return ';'
    elif ',' in sample:
        return ','
    return ';'

def parse_bank_statement_csv(content: str) -> List[Dict]:
    operations = []
    
    if content.startswith('\ufeff'):
        content = content[1:]
    
    lines = [line.strip() for line in content.split('\n') if line.strip()]
    if not lines:
        return operations
    
    delimiter = detect_dialect(lines[0])
    
    csv_file = io.StringIO(content)
    reader = csv.DictReader(csv_file, delimiter=delimiter, quotechar='"')
    
    headers = reader.fieldnames
    if not headers:
        return operations
    
    date_col = None
    debit_col = None
    credit_col = None
    counterparty_col = None
    unp_col = None
    purpose_col = None
    
    for h in headers:
        h_clean = h.strip().lower()
        if 'дат' in h_clean or 'date' in h_clean:
            date_col = h
        elif 'дебет' in h_clean or 'debit' in h_clean:
            debit_col = h
        elif 'кредит' in h_clean or 'credit' in h_clean:
            credit_col = h
        elif 'назван' in h_clean or 'контрагент' in h_clean or 'counterparty' in h_clean:
            counterparty_col = h
        elif 'унп' in h_clean or 'unp' in h_clean:
            unp_col = h
        elif 'назначен' in h_clean or 'purpose' in h_clean or 'платеж' in h_clean:
            purpose_col = h
    
    if not date_col and len(headers) >= 1:
        date_col = headers[0]
    if not debit_col and len(headers) >= 8:
        debit_col = headers[7]
    if not credit_col and len(headers) >= 9:
        credit_col = headers[8]
    if not counterparty_col and len(headers) >= 6:
        counterparty_col = headers[5]
    if not unp_col and len(headers) >= 7:
        unp_col = headers[6]
    if not purpose_col and len(headers) >= 12:
        purpose_col = headers[11]
    
    if not date_col or (not debit_col and not credit_col):
        logger.error(f"Cannot detect columns. Headers: {headers}")
        return operations
    
    for row in reader:
        date_str = row.get(date_col, '').strip()
        if not date_str:
            continue
        
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
            continue
        
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError:
            continue
        
        debit_str = row.get(debit_col, '').strip() if debit_col else ''
        credit_str = row.get(credit_col, '').strip() if credit_col else ''
        
        if not debit_str and not credit_str:
            continue
        
        debit = 0.0
        credit = 0.0
        if debit_str:
            debit_str_clean = debit_str.replace(' ', '').replace(',', '.')
            try:
                debit = float(debit_str_clean)
            except ValueError:
                debit = 0.0
        if credit_str:
            credit_str_clean = credit_str.replace(' ', '').replace(',', '.')
            try:
                credit = float(credit_str_clean)
            except ValueError:
                credit = 0.0
        
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
        
        counterparty = row.get(counterparty_col, '').strip() if counterparty_col else ''
        unp = row.get(unp_col, '').strip() if unp_col else ''
        purpose = row.get(purpose_col, '').strip() if purpose_col else ''
        
        if not purpose:
            purpose = f"Payment by agreement {row.get('Document - No', '')}"
        
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
