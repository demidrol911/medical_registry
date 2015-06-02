#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_EXP
from report_printer_clear.management.commands.final_report_pages.final_report import FinalReportPage
from report_printer_clear.utils.report import Report, ReportParameters


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'сверка'

        report = Report('recon.xls')
        report.add_page(FinalReportPage())
        report.print_pages(parameters)

