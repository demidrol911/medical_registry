#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_EXP
from report_printer_clear.management.commands.final_report_pages.invoiced_and_accepted_cost_page import InvoicedAndAcceptedCostPage
from report_printer_clear.utils.report import Report, ReportParameters


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'предъявленная и принятая к оплате стоимость'

        report = Report('invoiced_and_accepted_cost.xls')
        report.add_page(InvoicedAndAcceptedCostPage())
        report.print_pages(parameters)

