#! -*- coding: utf-8 -*-

from report_printer.libs.excel_writer import ExcelBook
from tfoms.func import YEAR, PERIOD
from report_printer.libs.const import MONTH_NAME


class Report():

    _by_department = False

    def __init__(self, template='', suffix=''):
        self.template = template
        self.suffix = suffix
        self.pages = []
        self.filename = ''

    def set_by_department(self):
        self._by_department = True

    def is_by_department(self):
        return self._by_department

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


