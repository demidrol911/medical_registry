#! -*- coding: utf-8 -*-

from report_printer_clear.utils.excel_writer import ExcelBook
from tfoms.func import YEAR, PERIOD
from report_printer.const import MONTH_NAME


class Report():

    def __init__(self, template='', suffix=''):
        self.template = template
        self.suffix = suffix
        self.by_department = False
        self.pages = []
        self.filename = ''

    def set_by_department(self, flag):
        self.by_department = flag

    def is_by_department(self):
        return self.by_department

    def add_page(self, page):
        self.pages.append(page)

    def print_pages(self, parameters):
        with ExcelBook(parameters.path_to_dir + ('/'+self.suffix if self.suffix else ''),
                       parameters.report_name + ('_'+self.suffix if self.suffix else '')) as book:
            book.create_book(self.template)
            for page in self.pages:
                sheet = book.get_sheet(page.page_number)
                page.calculate(parameters)
                page.print_page(sheet, parameters)
            self.filename = book.get_filename()

    def get_filename(self):
        return self.filename


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


