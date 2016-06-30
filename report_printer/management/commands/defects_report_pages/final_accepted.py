#! -*- coding: utf-8 -*-

from report_printer.libs.excel_loader import XlsxExcelLoader, XlsExcelLoader
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from report_printer.libs.const import POSITION_REPORT
from report_printer.management.commands.summary_report import SogazMekGeneralPage
from tfoms.func import calculate_capitation, calculate_fluorography
from report_printer.libs.report import ReportParameters

import os
import re


class FinalAcceptedPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = {}
        path_to_dir = u'c:/work/defects'
        border = {'top': 6, 'bottom': 45, 'left': 5, 'right': 6}
        hospital_idx = [0, 2, 3, 4, 6]
        day_hospital_idx = [8, 10, 12]
        clinic_idx = [1, 15, 16, 17, 18, 22, 23, 25, 27, 29, 31, 32, 34, 36, 38]
        ambulance_idx = [20, 21]
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
                mo_code = excel_loader.get_cell(0, 4, 1)[:6]

                parameters = ReportParameters()
                parameters.organization_code = mo_code
                parameters.policlinic_capitation = calculate_capitation(3, mo_code)
                parameters.ambulance_capitation = calculate_capitation(4, mo_code)
                parameters.fluorography = calculate_fluorography(mo_code)
                parameters.fluorography_total = self.__calculate_total(parameters.fluorography[1])
                parameters.policlinic_capitation_total = self.__calculate_total(parameters.policlinic_capitation[1])
                parameters.ambulance_capitation_total = self.__calculate_total(parameters.ambulance_capitation[1])

                sogaz_med_general = SogazMekGeneralPage()
                sogaz_med_general.calculate(parameters)
                self.data[mo_code] = {
                    'hospital': self.calculate_total(sum_by_term, hospital_idx),
                    'day_hospital': self.calculate_total(sum_by_term, day_hospital_idx),
                    'clinic': self.calculate_total(sum_by_term, clinic_idx),
                    'ambulance': self.calculate_total(sum_by_term, ambulance_idx),
                    'accepted': sogaz_med_general.get_accepted_sum()
                }
                counter += 1
                print self.data[mo_code]
            else:
                print u'НЕ ПОДОШЕЛ', file_from_dir
        print counter

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for mo_code in self.data:
            sheet.set_position(POSITION_REPORT[mo_code]+2, 2)
            sheet.write(self.data[mo_code]['hospital'], 'c')
            sheet.write(self.data[mo_code]['day_hospital'], 'c')
            sheet.write(self.data[mo_code]['clinic'], 'c')
            sheet.write(self.data[mo_code]['ambulance'], 'c')
            sheet.write(self.data[mo_code]['accepted'], 'c')

    def calculate_total(self, sum_by_term, idx_list):
        total = 0
        for idx in idx_list:
            total += sum_by_term[idx][0] + sum_by_term[idx][1]
        return total

    def __calculate_total(self, capitation):
        result = 0
        for key in capitation:
            result += capitation[key].get('accepted', 0)
        return result
