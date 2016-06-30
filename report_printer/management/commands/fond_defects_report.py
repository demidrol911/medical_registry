#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.defects_report_pages.fond_defects import FondDefectsPage
from report_printer.libs.report import Report
from report_printer.libs.report import ReportParameters
from medical_service_register.path import REESTR_DIR


class Command(BaseCommand):

    def handle(self, *args, **options):
        report = Report(template='defect.xls', suffix=u'дефекты')
        report.add_page(FondDefectsPage())
        parameters = ReportParameters()

        path_to_dir = REESTR_DIR
        parameters.path_to_dir = path_to_dir % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'дефекты_фонд'

        report.print_pages(parameters)
