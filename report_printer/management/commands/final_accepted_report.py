#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from defects_report_pages.final_accepted import FinalAcceptedPage
from report_printer.libs.report import Report
from report_printer.libs.report import ReportParameters
from medical_service_register.path import REESTR_DIR, REESTR_EXP


class Command(BaseCommand):

    def handle(self, *args, **options):
        report = Report(template='order725.xls')
        report.add_page(FinalAcceptedPage())
        parameters = ReportParameters()

        path_to_dir = REESTR_DIR
        parameters.path_to_dir = path_to_dir % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'Отчет по Приказу № 725 (СОГАЗ-Мед)'

        report.print_pages(parameters)
