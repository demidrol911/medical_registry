from report_printer_clear.utils.page import ReportPage


class SogazMekGeneralPage(ReportPage):

    def __init__(self):
        self.data = ''
        self.page_number = 6

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        pass
