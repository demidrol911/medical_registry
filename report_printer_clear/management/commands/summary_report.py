from django.core.management.base import BaseCommand
from report_printer_clear.management.commands.summary_report_pages.sanctions_identify import SanctionsIdentifyPage

from summary_report_pages.order146 import Order146Page
from summary_report_pages.sanctions_reference import SanctionsReferencePage
from summary_report_pages.services_by_division import (
    AcceptedServicesPage, InvoicedServicesPage, NotAcceptedServicesPage
)
from summary_report_pages.services_by_sanctions import SanctionsPage
from summary_report_pages.sogaz_mek_detailed import SogazMekDetailedPage
from summary_report_pages.sogaz_mek_general import SogazMekGeneralPage
from report_printer_clear.utils.report import Report, ReportParameters
from report_printer_clear.utils.wizard import AutomaticReportsWizard

ACCEPTED_SERVICES_PAGE = 1
INVOICED_SERVICES_PAGE = 2
NOT_ACCEPTED_SERVICES_PAGE = 3
REPORT_TYPE = ACCEPTED_SERVICES_PAGE


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.template = 'reestr_201501.xls'

        report = Report()
        if REPORT_TYPE == ACCEPTED_SERVICES_PAGE:
            report.add_page(AcceptedServicesPage())
        elif REPORT_TYPE == INVOICED_SERVICES_PAGE:
            report.add_page(InvoicedServicesPage())
        elif REPORT_TYPE == NOT_ACCEPTED_SERVICES_PAGE:
            report.add_page(NotAcceptedServicesPage())
        report.add_page(SanctionsPage())
        report.add_page(SanctionsReferencePage())
        report.add_page(SanctionsIdentifyPage())
        report.add_page(Order146Page())
        report.add_page(SogazMekDetailedPage())
        report.add_page(SogazMekGeneralPage())

        report_wizard = AutomaticReportsWizard(report, parameters)
        report_wizard.create_reports(600)
