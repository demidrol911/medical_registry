#! -*- coding: utf-8 -*-
from servces_by_divison_general import GeneralServicesPage


class AcceptedServicesPage(GeneralServicesPage):

    def __init__(self):
        super(AcceptedServicesPage, self).__init__()

    def calculate(self, parameters):
        parameters.payment_type_list = [2, ]
        parameters.include_fluorography = True
        super(AcceptedServicesPage, self).calculate(parameters)


class InvoicedServicesPage(GeneralServicesPage):

    def __init__(self):
        super(InvoicedServicesPage, self).__init__()

    def calculate(self, parameters):
        parameters.payment_type_list = [2, 3]
        parameters.include_fluorography = False
        super(InvoicedServicesPage, self).calculate(parameters)


class NotAcceptedServicesPage(GeneralServicesPage):

    def __init__(self):
        super(NotAcceptedServicesPage, self).__init__()

    def calculate(self, parameters):
        parameters.payment_type_list = [3, ]
        parameters.include_fluorography = False
        super(NotAcceptedServicesPage, self).calculate(parameters)