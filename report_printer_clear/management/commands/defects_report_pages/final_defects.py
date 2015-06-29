#! -*- coding: utf-8 -*-

from report_printer_clear.utils.excel_loader import XlsxExcelLoader, XlsExcelLoader
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage

import os
import re


class FinalDefectsPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        path_to_dir = u'C:\дефекты_май'
        border = {'top': 6, 'bottom': 38, 'left': 3, 'right': 34}
        counter = 0
        unique_mo_names = []
        filename_pattern = re.compile(ur'^(?P<mo>[\D1234]+?)(?:_?)(?P<sequence_number>\d?)\.(?P<ext>xlsx|xls)$')
        for file_from_dir in os.listdir(path_to_dir):
            filename_match = filename_pattern.match(file_from_dir)
            if filename_match:
                mo_name = filename_match.group('mo')
                if mo_name not in unique_mo_names:
                    unique_mo_names.append(mo_name)
                else:
                    print u'ДУБЛИКАТ', mo_name
                    break
                print file_from_dir
                if filename_match.group('ext') == 'xlsx':
                    excel_loader = XlsxExcelLoader(os.path.join(path_to_dir, file_from_dir))
                elif filename_match.group('ext') == 'xls':
                    excel_loader = XlsExcelLoader(os.path.join(path_to_dir, file_from_dir))
                sum_by_term = excel_loader.load(0, border)

                if self.data:
                    self.data = calculate_sum_data(self.data, sum_by_term)
                else:
                    self.data = sum_by_term
                counter += 1

            else:
                print u'НЕ ПОДОШЕЛ', file_from_dir
        print counter

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for idx, item in enumerate(self.data):
            sheet.set_position(5 + idx, 2)
            for value in item:
                sheet.write(value, 'c')


def calculate_sum_data(sum_data, data):
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            sum_data[i][j] += value
    return sum_data

