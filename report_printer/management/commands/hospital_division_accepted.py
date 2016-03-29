#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_EXP
from hospital_division_accepted_pages.hospital_division_accepted import \
    HospitalDivisionAcceptedPage
from report_printer.libs.report import Report, ReportParameters


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'круг_стационар'

        report = Report()
        report.add_page(HospitalDivisionAcceptedPage())
        report.print_pages(parameters)
