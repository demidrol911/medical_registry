from django.core.management.base import BaseCommand
from report_printer_clear.management.commands.defects_report_pages.defects import DefectsPage
from report_printer_clear.utils.report import Report, ReportParameters
from report_printer_clear.utils.wizard import AutomaticReportsWizard


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.template = 'defect.xls'

        report = Report()
        report.add_page(DefectsPage())

        report_wizard = AutomaticReportsWizard(report, parameters)
        report_wizard.create_reports(6)
