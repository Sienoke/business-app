import re
from datetime import datetime
from typing import List, Dict, Optional

def parse_bank_statement(content: str) -> List[Dict]:
    """
    Парсит выписку из Белгазпромбанка (текстовый формат с таблицей).
    Возвращает список операций.
    """
    operations = []
    lines = content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Ищем строку с датой операции (формат ДД.ММ.ГГГГ в начале строки)
        # Пример: "**14.07.2026** | **1648** | **01** | **OLMPBY2X** | ..."
        date_match = re.search(r'\*\*(\d{2}\.\d{2}\.\d{4})\*\*', line)
        if date_match:
            date_str = date_match.group(1)
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            
            # Извлекаем сумму по дебету или кредиту
            debit_match = re.search(r'\*\*([\d,]+\.\d{2})\*\*.*?\*\*([\d,]+\.\d{2})\*\*', line)
            if debit_match:
                debit_str = debit_match.group(1).replace(',', '')
                credit_str = debit_match.group(2).replace(',', '')
                debit = float(debit_str) if debit_str else 0.0
                credit = float(credit_str) if credit_str else 0.0
            else:
                # Если сумма в другой строке, пытаемся найти позже
                debit, credit = 0.0, 0.0
                # Ищем строки с дебетом/кредитом в следующих строках
                temp_i = i + 1
                while temp_i < len(lines) and temp_i < i + 5:
                    temp_line = lines[temp_i].strip()
                    # Ищем сумму в формате с двумя десятичными знаками
                    amount_match = re.search(r'(\d{1,3}(?: \d{3})*,\d{2})', temp_line)
                    if amount_match:
                        amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
                        # Определяем доход или расход по контексту
                        if 'дебет' in temp_line.lower() or 'debit' in temp_line.lower():
                            debit = float(amount_str)
                        elif 'кредит' in temp_line.lower() or 'credit' in temp_line.lower():
                            credit = float(amount_str)
                    temp_i += 1
            
            # Ищем назначение платежа в следующих строках
            purpose = ''
            counterparty_unp = ''
            counterparty_name = ''
            
            temp_i = i + 1
            while temp_i < len(lines) and temp_i < i + 10:
                temp_line = lines[temp_i].strip()
                if not temp_line:
                    temp_i += 1
                    continue
                
                # Ищем УНП
                unp_match = re.search(r'УНП[:\s]+(\d+)', temp_line)
                if unp_match:
                    counterparty_unp = unp_match.group(1)
                    # Остальная часть строки - название контрагента
                    counterparty_name = temp_line.replace(f'УНП: {counterparty_unp}', '').strip()
                
                # Если строка не содержит УНП и не является пустой, это может быть назначение платежа
                if 'УНП' not in temp_line and 'дебет' not in temp_line.lower() and 'кредит' not in temp_line.lower():
                    if 'ОПЛАТА' in temp_line or 'оплата' in temp_line or 'НАЛОГ' in temp_line or 'налог' in temp_line:
                        purpose = temp_line.strip()
                
                # Если строка содержит назначение платежа (обычно после УНП и названия)
                if counterparty_name and not purpose and temp_line and 'УНП' not in temp_line:
                    if 'ОПЛАТА' in temp_line or 'оплата' in temp_line or 'НАЛОГ' in temp_line or 'налог' in temp_line:
                        purpose = temp_line.strip()
                
                temp_i += 1
            
            # Если назначение не найдено, собираем все строки после операции
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
            
            # Определяем тип операции: доход (кредит) или расход (дебет)
            is_income = None
            amount = 0.0
            
            if credit > 0:
                is_income = True
                amount = credit
            elif debit > 0:
                is_income = False
                amount = debit
            
            # Если сумма не найдена, пропускаем операцию
            if amount == 0:
                i += 1
                continue
            
            # Формируем запись
            operation = {
                'date': date_obj.isoformat(),
                'amount': amount,
                'is_income': is_income,
                'counterparty': counterparty_name or 'Неизвестный контрагент',
                'purpose': purpose or 'Без назначения',
                'counterparty_unp': counterparty_unp,
                'debit': debit,
                'credit': credit
            }
            operations.append(operation)
        
        i += 1
    
    # Если парсер не нашёл ни одной операции, пробуем альтернативный подход
    if not operations:
        # Ищем операции в формате: дата, сумма, назначение
        lines_clean = [line for line in lines if line.strip()]
        for i, line in enumerate(lines_clean):
            # Ищем дату и сумму в одном формате
            date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', line)
            amount_match = re.search(r'(\d{1,3}(?: \d{3})*,\d{2})', line)
            if date_match and amount_match:
                try:
                    date_obj = datetime.strptime(date_match.group(1), '%d.%m.%Y').date()
                    amount_str = amount_match.group(1).replace(' ', '').replace(',', '.')
                    amount = float(amount_str)
                    
                    # Определяем доход или расход по контексту
                    is_income = None
                    if 'дебет' in line.lower() or 'списание' in line.lower() or 'расход' in line.lower():
                        is_income = False
                    elif 'кредит' in line.lower() or 'поступление' in line.lower() or 'зачисление' in line.lower():
                        is_income = True
                    
                    # Ищем назначение
                    purpose = line.replace(date_match.group(1), '').replace(amount_match.group(1), '').strip()
                    if 'дебет' in purpose.lower() or 'кредит' in purpose.lower():
                        purpose = ''
                    
                    # Ищем контрагента в следующей строке
                    counterparty_name = ''
                    if i + 1 < len(lines_clean):
                        next_line = lines_clean[i + 1]
                        if 'УНП' in next_line:
                            counterparty_name = next_line.replace('УНП:', '').strip()
                    
                    if amount > 0:
                        operation = {
                            'date': date_obj.isoformat(),
                            'amount': amount,
                            'is_income': is_income,
                            'counterparty': counterparty_name or 'Неизвестный контрагент',
                            'purpose': purpose or 'Без назначения',
                            'counterparty_unp': '',
                            'debit': amount if is_income is False else 0,
                            'credit': amount if is_income is True else 0
                        }
                        operations.append(operation)
                except Exception:
                    continue
    
    return operations
