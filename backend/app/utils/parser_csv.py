import csv
import re
from datetime import datetime
from typing import List, Dict
import io
import logging

logger = logging.getLogger(__name__)

def parse_bank_statement_csv(content: str) -> List[Dict]:
    operations = []
    logger.info("Starting CSV parsing (index-based)")
    
    if content.startswith('\ufeff'):
        content = content[1:]
    
    csv_file = io.StringIO(content)
    reader = csv.reader(csv_file, delimiter=';', quotechar='"')
    
    rows = list(reader)
    if not rows:
        logger.error("No rows found")
        return operations
    
    logger.info(f"Total rows: {len(rows)}")
    logger.info(f"Header row: {rows[0] if rows else 'None'}")
    
    # Skip header row
    data_rows = rows[1:] if len(rows) > 1 else []
    logger.info(f"Data rows: {len(data_rows)}")
    
    if not data_rows:
        logger.warning("No data rows after header")
        return operations
    
    # Define column indices based on the sample
    # 0: date, 1: doc_no, 2: op_code, 3: currency, 4: bank_code,
    # 5: counterparty_name, 6: unp, 7: account, 8: debit, 9: credit,
    # 10: smp_date, 11: purpose
    DATE_IDX = 0
    DEBIT_IDX = 8
    CREDIT_IDX = 9
    COUNTERPARTY_IDX = 5
    UNP_IDX = 6
    PURPOSE_IDX = 11
    
    for idx, row in enumerate(data_rows, start=1):
        # Ensure row has enough columns
        if len(row) < 12:
            logger.debug(f"Row {idx}: insufficient columns ({len(row)}), skipping")
            continue
        
        date_str = row[DATE_IDX].strip()
        if not date_str:
            logger.debug(f"Row {idx}: empty date, skipping")
            continue
        
        if not re.match(r'\d{2}\.\d{2}\.\d{4}', date_str):
            logger.debug(f"Row {idx}: invalid date format '{date_str}', skipping")
            continue
        
        try:
            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
        except ValueError as e:
            logger.debug(f"Row {idx}: date parse error {e}, skipping")
            continue
        
        debit_str = row[DEBIT_IDX].strip() if len(row) > DEBIT_IDX else ''
        credit_str = row[CREDIT_IDX].strip() if len(row) > CREDIT_IDX else ''
        
        if not debit_str and not credit_str:
            logger.debug(f"Row {idx}: no debit/credit, skipping")
            continue
        
        debit = 0.0
        credit = 0.0
        if debit_str:
            try:
                debit = float(debit_str.replace(',', ''))
            except ValueError:
                logger.debug(f"Row {idx}: debit conversion failed for '{debit_str}'")
        if credit_str:
            try:
                credit = float(credit_str.replace(',', ''))
            except ValueError:
                logger.debug(f"Row {idx}: credit conversion failed for '{credit_str}'")
        
        is_income = None
        amount = 0.0
        if credit > 0:
            is_income = True
            amount = credit
        elif debit > 0:
            is_income = False
            amount = debit
        else:
            logger.debug(f"Row {idx}: amount is zero, skipping")
            continue
        
        counterparty = row[COUNTERPARTY_IDX].strip() if len(row) > COUNTERPARTY_IDX else ''
        unp = row[UNP_IDX].strip() if len(row) > UNP_IDX else ''
        purpose = row[PURPOSE_IDX].strip() if len(row) > PURPOSE_IDX else ''
        
        if not purpose:
            purpose = f"Payment by agreement {row[1] if len(row) > 1 else ''}"
        
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
        logger.info(f"Row {idx}: added operation: {date_obj} amount={amount} income={is_income}")
    
    logger.info(f"Parsed {len(operations)} operations out of {len(data_rows)} data rows")
    return operations
