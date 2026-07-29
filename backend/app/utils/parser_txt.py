import re
from datetime import datetime
from typing import List, Dict

def parse_bank_statement_txt(content: str) -> List[Dict]:
    operations = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        date_match = re.search(r'\*\*(\d{2}\.\d{2}\.\d{4})\*\*', line)
        if date_match:
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            
            debit_match = re.search(r'\*\*([\d,]+\.\d{2})\*\*.*?\*\*([\d,]+\.\d{2})\*\*', line)
            if debit_match:
                debit_str = debit_match.group(1).replace(',', '')
                credit_str = debit_match.group(2).replace(',', '')
                debit = float(debit_str) if debit_str else 0.0
                credit = float(credit_str) if credit_str else 0.0
            else:
                debit, credit = 0.0, 0.0
            
            purpose = ''
            counterparty_name = ''
            counterparty_unp = ''
            
            temp_i = i + 1
            while temp_i < len(lines) and temp_i < i + 10:
                temp_line = lines[temp_i].strip()
                if 'УНП' in temp_line:
                    unp_match = re.search(r'УНП[:\s]+(\d+)', temp_line)
                    if unp_match:
                        counterparty_unp = unp_match.group(1)
                    counterparty_name = temp_line.replace('УНП:', '').strip()
                if 'ОПЛАТА' in temp_line or 'НАЛОГ' in temp_line or 'СТРАХОВЫЕ' in temp_line:
                    purpose = temp_line.strip()
                temp_i += 1
            
            if not purpose:
                purpose_parts = []
                temp_i = i + 1
                while temp_i < len(lines) and temp_i < i + 8:
                    temp_line = lines[temp_i].strip()
                    if temp_line and '|' not in temp_line and '***' not in temp_line:
                        if 'УНП' not in temp_line and not re.match(r'\d{2}\.\d{2}\.\d{4}', temp_line):
                            purpose_parts.append(temp_line.strip())
                    temp_i += 1
                purpose = ' '.join(purpose_parts).strip()
            
            is_income = None
            amount = 0.0
            if credit > 0:
                is_income = True
                amount = credit
            elif debit > 0:
                is_income = False
                amount = debit
            
            if amount == 0:
                i += 1
                continue
            
            operations.append({
                'date': date_obj.isoformat(),
                'amount': amount,
                'is_income': is_income,
                'counterparty': counterparty_name or 'Unknown counterparty',
                'purpose': purpose or 'No purpose',
                'counterparty_unp': counterparty_unp,
                'debit': debit,
                'credit': credit
            })
        i += 1
    
    return operations
