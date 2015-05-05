from report_printer_clear.utils.page import ReportPage


class AcceptedServicesPage(ReportPage):

    def __init__(self):
        self.data = ''
        self.page_number = 0

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        pass


class InvoicedServicesPage(ReportPage):

    def __init__(self):
        self.data = ''
        self.page_number = 0

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        pass


class NotAcceptedServicesPage(ReportPage):
    def __init__(self):
        self.data = ''
        self.page_number = 0

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        pass
