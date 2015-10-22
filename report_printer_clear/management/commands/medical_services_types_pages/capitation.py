#! -*- coding: utf-8 -*-
from main.funcs import howlong
from main.models import MedicalRegister
from const import POSITION_REPORT
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage
from tfoms.func import calculate_capitation


class CapitationAmbulatoryCarePage(ReportPage):

    """
    Отчёт включает в себя:
    Подушевой норматив по амбулаторной помощи
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
            capitation = calculate_capitation(3, mo_code)
            if capitation[0]:
                self.data[mo_code] = capitation[1]

    def print_page(self, sheet, parameters):
        def inc_column(f_sheet, inc):
            f_sheet.set_position(f_sheet.get_row_index(),
                                 f_sheet.get_column_index() + inc)

        sheet.set_style(VALUE_STYLE)
        for mo_code, item in self.data.items():
            sheet.set_position(POSITION_REPORT[mo_code], 2)
            sheet.write(item['men1']['population']
                        +
                        item['fem1']['population'], 'c')
            sheet.write(item['men1']['population'], 'c')
            sheet.write(item['fem1']['population'], 'c')
            inc_column(sheet, 2)
            sheet.write(item['men1']['tariff']
                        +
                        item['fem1']['tariff'], 'c')
            sheet.write(item['men1']['tariff'], 'c')
            sheet.write(item['fem1']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men1']['coeff']
                        +
                        item['fem1']['coeff'], 'c')
            sheet.write(item['men1']['coeff'], 'c')
            sheet.write(item['fem1']['coeff'], 'c')
            sheet.write(item['men1']['accepted']
                        +
                        item['fem1']['accepted'], 'c')
            sheet.write(item['men1']['accepted'], 'c')
            sheet.write(item['fem1']['accepted'], 'c')

            sheet.write(item['men2']['population']
                        +
                        item['fem2']['population'], 'c')
            sheet.write(item['men2']['population'], 'c')
            sheet.write(item['fem2']['population'], 'c')
            inc_column(sheet, 2)
            sheet.write(item['men2']['tariff']
                        +
                        item['fem2']['tariff'], 'c')
            sheet.write(item['men2']['tariff'], 'c')
            sheet.write(item['fem2']['tariff'], 'c')
            sheet.set_position(sheet.get_row_index(),
                               sheet.get_column_index() + 1)
            sheet.write(item['men2']['coeff']
                        +
                        item['fem2']['coeff'], 'c')
            sheet.write(item['men2']['coeff'], 'c')
            sheet.write(item['fem2']['coeff'], 'c')
            sheet.write(item['men2']['accepted']
                        +
                        item['fem2']['accepted'], 'c')
            sheet.write(item['men2']['accepted'], 'c')
            sheet.write(item['fem2']['accepted'], 'c')

            sheet.write(item['men3']['population']
                        +
                        item['fem3']['population'], 'c')
            sheet.write(item['men3']['population'], 'c')
            sheet.write(item['fem3']['population'], 'c')
            inc_column(sheet, 2)
            sheet.write(item['men3']['tariff']
                        +
                        item['fem3']['tariff'], 'c')
            sheet.write(item['men3']['tariff'], 'c')
            sheet.write(item['fem3']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men3']['coeff']
                        +
                        item['fem3']['coeff'], 'c')
            sheet.write(item['men3']['coeff'], 'c')
            sheet.write(item['fem3']['coeff'], 'c')
            sheet.write(item['men3']['accepted']
                        +
                        item['fem3']['accepted'], 'c')
            sheet.write(item['men3']['accepted'], 'c')
            sheet.write(item['fem3']['accepted'], 'c')

            sheet.write(item['men4']['population'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men4']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men4']['coeff'], 'c')
            sheet.write(item['men4']['accepted'], 'c')

            sheet.write(item['fem4']['population'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['fem4']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['fem4']['coeff'], 'c')
            sheet.write(item['fem4']['accepted'], 'c')

            sheet.write(item['men5']['population'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men5']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['men5']['coeff'], 'c')
            sheet.write(item['men5']['accepted'], 'c')

            sheet.write(item['fem5']['population'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['fem5']['tariff'], 'c')
            inc_column(sheet, 1)
            sheet.write(item['fem5']['coeff'], 'c')
            sheet.write(item['fem5']['accepted'], 'c')


class CapitationAcuteCarePage(ReportPage):

    """
    Отчёт включает в себя:
    Подушевой норматив по скорой помощи
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
            capitation = calculate_capitation(4, mo_code)
            if capitation[0]:
                self.data[mo_code] = capitation[1]

    def print_page(self, sheet, parameters):
        def inc_column(f_sheet, inc):
            f_sheet.set_position(f_sheet.get_row_index(),
                                 f_sheet.get_column_index() + inc)

        sheet.set_style(VALUE_STYLE)
        for mo_code, item in self.data.items():
            sheet.set_position(POSITION_REPORT[mo_code], 4)
            sheet.write(item['men1']['population']
                        +
                        item['fem1']['population'], 'c')
            sheet.write(item['men1']['population'], 'c')
            sheet.write(item['fem1']['population'], 'c')
            sheet.write(item['men1']['tariff']
                        +
                        item['fem1']['tariff'], 'c')
            sheet.write(item['men1']['tariff'], 'c')
            sheet.write(item['fem1']['tariff'], 'c')
            inc_column(sheet, 2)

            sheet.write(item['men2']['population']
                        +
                        item['fem2']['population'], 'c')
            sheet.write(item['men2']['population'], 'c')
            sheet.write(item['fem2']['population'], 'c')
            sheet.write(item['men2']['tariff']
                        +
                        item['fem2']['tariff'], 'c')
            sheet.write(item['men2']['tariff'], 'c')
            sheet.write(item['fem2']['tariff'], 'c')
            inc_column(sheet, 2)

            sheet.write(item['men3']['population']
                        +
                        item['fem3']['population'], 'c')
            sheet.write(item['men3']['population'], 'c')
            sheet.write(item['fem3']['population'], 'c')
            sheet.write(item['men3']['tariff']
                        +
                        item['fem3']['tariff'], 'c')
            sheet.write(item['men3']['tariff'], 'c')
            sheet.write(item['fem3']['tariff'], 'c')
            inc_column(sheet, 1)

            sheet.write(item['men4']['population'], 'c')
            sheet.write(item['men4']['tariff'], 'c')
            inc_column(sheet, 1)

            sheet.write(item['fem4']['population'], 'c')
            sheet.write(item['fem4']['tariff'], 'c')
            inc_column(sheet, 1)

            sheet.write(item['men5']['population'], 'c')
            sheet.write(item['men5']['tariff'], 'c')
            inc_column(sheet, 1)

            sheet.write(item['fem5']['population'], 'c')
            sheet.write(item['fem5']['tariff'], 'c')


