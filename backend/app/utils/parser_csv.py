import csv
import re
from datetime import datetime
from typing import List, Dict
from io import StringIO

def parse_bank_statement_csv(content: str) -> List[Dict]:
    """
    Парсит выписку в формате CSV.
    Ожидает, что в файле есть колонки с датой, суммой, назначением и т.д.
    """
    operations = []
    # Определяем разделитель: если есть ; значит, это CSV с разделителем ;
    # Если есть , то используем запятую
    reader = None
    try:
        # Пробуем прочитать с разделителем ; (обычно в белорусских банках)
        csv_reader = csv.DictReader(StringIO(content), delimiter=';')
        # Попробуем получить поля
        if csv_reader.fieldnames:
            reader = csv_reader
        else:
            # Пробуем с запятой
            csv_reader = csv.DictReader(StringIO(content), delimiter=',')
            if csv_reader.fieldnames:
                reader = csv_reader
    except Exception:
        # Если не удалось, возможно, файл без заголовков, пробуем просто разбить строки
        lines = content.splitlines()
        for line in lines:
            parts = line.split(';') if ';' in line else line.split(',')
            # Определяем, есть ли дата в одной из колонок
            for part in parts:
                if re.match(r'\d{2}\.\d{2}\.\d{4}', part.strip()):
                    # Нашли дату
                    date_str = part.strip()
                    date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
                    # Ищем сумму
                    amount = None
                    for p in parts:
                        clean = p.replace(' ', '').replace(',', '.').replace('"', '')
                        if re.match(r'^[\d.]+$', clean) and float(clean) > 0:
                            amount = float(clean)
                            break
                    if amount is None:
                        continue
                    # Определяем, доход или расход (по контексту, например, кредит/дебет)
                    is_income = None
                    # Ищем назначение
                    purpose_parts = [p for p in parts if not re.match(r'\d{2}\.\d{2}\.\d{4}', p) and not re.match(r'^[\d.]+$', p)]
                    purpose = ' '.join(purpose_parts).strip() if purpose_parts else ''
                    # Грубо определяем тип по наличию слов "кредит" или "дебет"
                    if 'кредит' in purpose.lower() or 'поступление' in purpose.lower():
                        is_income = True
                    elif 'дебет' in purpose.lower() or 'списание' in purpose.lower():
                        is_income = False
                    # Если не определилось, считаем доходом, если сумма положительная и нет явного расхода
                    if is_income is None:
                        is_income = True  # по умолчанию доход
                    operations.append({
                        'date': date_obj.isoformat(),
                        'amount': amount,
                        'is_income': is_income,
                        'counterparty': purpose,
                        'purpose': purpose,
                        'counterparty_unp': ''
                    })
        return operations

    if reader is None:
        # Если не удалось определить заголовки, попробуем обработать строки как списки
        for row in csv.reader(StringIO(content), delimiter=';'):
            # ищем дату
            date_val = None
            amount_val = None
            for cell in row:
                if re.match(r'\d{2}\.\d{2}\.\d{4}', cell.strip()):
                    date_val = cell.strip()
                if re.match(r'^[\d.,]+$', cell.replace(' ', '')):
                    clean = cell.replace(' ', '').replace(',', '.')
                    try:
                        amount_val = float(clean)
                    except:
                        pass
            if date_val and amount_val:
                date_obj = datetime.strptime(date_val, '%d.%m.%Y').date()
                # Определим тип по контексту, но просто используем как доход
                is_income = True
                operations.append({
                    'date': date_obj.isoformat(),
                    'amount': amount_val,
                    'is_income': is_income,
                    'counterparty': ' '.join(row),
                    'purpose': ' '.join(row),
                    'counterparty_unp': ''
                })
        return operations

    # Если есть заголовки, ищем колонки по ключевым словам
    fieldnames = reader.fieldnames
    date_col = None
    amount_col = None
    purpose_col = None
    for col in fieldnames:
        col_lower = col.lower()
        if 'дата' in col_lower or 'date' in col_lower:
            date_col = col
        if 'сумм' in col_lower or 'amount' in col_lower or 'дебе' in col_lower or 'креди' in col_lower:
            amount_col = col
        if 'назнач' in col_lower or 'purpose' in col_lower or 'описа' in col_lower or 'коммент' in col_lower:
            purpose_col = col

    for row in reader:
        # Если не нашли колонки, используем первую как дату, вторую как сумму
        if date_col is None:
            date_col = fieldnames[0]
        if amount_col is None:
            amount_col = fieldnames[1] if len(fieldnames) > 1 else fieldnames[0]
        if purpose_col is None:
            purpose_col = fieldnames[-1] if len(fieldnames) > 2 else ''

        date_str = row.get(date_col, '').strip()
        if not date_str:
            continue
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        except:
            continue
        amount_str = row.get(amount_col, '').replace(' ', '').replace(',', '.').replace('"', '')
        try:
            amount = float(amount_str)
        except:
            continue
        if amount == 0:
            continue
        purpose = row.get(purpose_col, '').strip() if purpose_col else ''
        is_income = True
        # Если в назначении есть "дебет" или "списание" или это отрицательная сумма, то расход
        if ('дебет' in purpose.lower() or 'списание' in purpose.lower() or 'расход' in purpose.lower() or amount < 0):
            is_income = False
            if amount < 0:
                amount = abs(amount)
        operations.append({
            'date': date_obj.isoformat(),
            'amount': amount,
            'is_income': is_income,
            'counterparty': purpose,
            'purpose': purpose,
            'counterparty_unp': ''
        })
    return operations
