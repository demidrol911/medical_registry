# -*- coding: utf-8 -*-

import xlrd
import logging
import re

IDENT_TABLE = u'd:/work/medical_service_register/templates/ident_table/table.xls'
MO_CODE_PATTERN = r'^28\d{4}$'

logging.basicConfig(filename='d:/work/medical_register_log/text.log',
                    format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)

logging.info('test info')
logging.warning('test warn')

table = xlrd.open_workbook(IDENT_TABLE)

sheets = table.sheet_names()

mo_code_match_pattern = re.compile(MO_CODE_PATTERN)

completed = []

for sheet_name in sheets:
    work_sheet = table.sheet_by_name(sheet_name)
    rows_count = work_sheet.nrows
    current_row = -1
    while current_row < rows_count-1:
        current_row += 1
        row = work_sheet.row(current_row)
        if mo_code_match_pattern.match(row[1].value) \
                and type(row[3].value) is float \
                and row[3].value > 0:
            completed.append(row[1].value)

print completed

logging.error('test error')