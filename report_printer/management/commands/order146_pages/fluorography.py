#! -*- coding: utf-8 -*-
from main.funcs import howlong
from main.models import MedicalRegister
from report_printer.libs.const import POSITION_REPORT_2017
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage


class FluorographyPage(ReportPage):
    """
    Лист флюорография (доплата в ГП2 за счёт других больниц)
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = {}
        organizations = MedicalRegister.objects.filter(
            year=parameters.registry_year,
            period=parameters.registry_period,
            is_active=True,
            type=1
        ).values_list('organization_code', flat=True).distinct()
        for mo_code in organizations:
            fluorography = MedicalRegister.calculate_fluorography(mo_code)
            if fluorography[0]:
                self.data[mo_code] = fluorography[1]

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for mo_code, item in self.data.items():
            sheet.set_position(POSITION_REPORT_2017[mo_code], 2)
            sheet.write(item['adult']['population']+item['child']['population'], 'c')
            sheet.write(item['adult']['population'], 'c')
            sheet.write(item['child']['population'], 'c')
            sheet.write(item['adult']['accepted']+item['child']['accepted'], 'c')
            sheet.write(item['adult']['accepted'], 'c')
            sheet.write(item['child']['accepted'])
