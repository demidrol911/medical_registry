#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer_clear.management.commands.defects_report_pages.defects import DefectsPage
from report_printer_clear.utils.report import Report
from report_printer_clear.utils.report import ReportParameters
from tfoms.func import get_mo_name
from medical_service_register.path import REESTR_EXP


class Command(BaseCommand):

    def handle(self, *args, **options):
        report = Report(template='defect.xls', suffix=u'дефекты')
        report.add_page(DefectsPage())

        organization_code = args[0]

        parameters = ReportParameters()

        path_to_dir = REESTR_EXP

        parameters.path_to_dir = path_to_dir % (
            parameters.registry_year,
            parameters.registry_period
        )

        parameters.organization_code = organization_code
        parameters.report_name = get_mo_name(organization_code).\
            replace('"', '').strip()

        report.print_pages(parameters)
