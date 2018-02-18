#! -*- coding: utf-8 -*-
from main.funcs import howlong
from report_printer.libs.const import POSITION_REPORT_2017
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from main.models import MedicalRegister


class CapitationAmbulatoryCarePage(ReportPage):
    """
    Лист подушевой норматив по амбулаторной помощи
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
            capitation = MedicalRegister.calculate_capitation(3, mo_code)
            if capitation[0]:
                self.data[mo_code] = capitation[1]

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for mo_code, item in self.data.items():
            sheet.set_position(POSITION_REPORT_2017[mo_code], 2)
            sheet.write(item['adult']['population']+item['child']['population'], 'c')
            sheet.write(item['adult']['accepted']+item['child']['accepted'])


class CapitationAcuteCarePage(ReportPage):
    """
    Лист подушевой норматив по скорой помощи
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
            capitation = MedicalRegister.calculate_capitation(4, mo_code)
            if capitation[0]:
                self.data[mo_code] = capitation[1]

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for mo_code, item in self.data.items():
            sheet.set_position(POSITION_REPORT_2017[mo_code], 2)
            sheet.write(item['adult']['population']+item['child']['population'], 'c')
            sheet.write(item['adult']['accepted']+item['child']['accepted'])


