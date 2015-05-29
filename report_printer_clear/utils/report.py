#! -*- coding: utf-8 -*-

from report_printer_clear.utils.excel_writer import ExcelBook
from tfoms.func import YEAR, PERIOD
from report_printer.const import MONTH_NAME


class Report():

    def __init__(self, template=''):
        self.template = template
        self.pages = []

    def add_page(self, page):
        self.pages.append(page)

    def print_pages(self, parameters):
        book = ExcelBook(parameters.path_to_dir, parameters.report_name)
        book.create_book(self.template)
        for page in self.pages:
            sheet = book.get_sheet(page.page_number)
            page.calculate(parameters)
            page.print_page(sheet, parameters)
        book.close()


class ReportParameters():

    def __init__(self):
        self.template = ''
        self.registry_year = YEAR
        self.registry_period = PERIOD
        self.date_string = u'{month} {year} года'.\
            format(month=MONTH_NAME[self.registry_period],
                   year=self.registry_year)
        self.organization_code = ''
        self.report_name = ''
        self.path_to_dir = ''


