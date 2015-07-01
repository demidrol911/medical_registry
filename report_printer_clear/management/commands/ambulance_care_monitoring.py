#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_EXP
from ambulance_care_pages.ambulance_care import AmbulanceCareALLPage, \
    AmbulanceSpecializedPage, AmbulanceMedicalPage, AmbulanceParamedicPage
from report_printer_clear.utils.report import Report, ReportParameters


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        path_to_dir = REESTR_EXP
        parameters.path_to_dir = path_to_dir % (
            parameters.registry_year,
            parameters.registry_period
        )
        report_all = Report(template='ambulance_care_monitoring.xls')
        report_all.add_page(AmbulanceCareALLPage())

        report_specialized = Report(template='ambulance_care_monitoring.xls')
        report_specialized.add_page(AmbulanceSpecializedPage())

        report_medical = Report(template='ambulance_care_monitoring.xls')
        report_medical.add_page(AmbulanceMedicalPage())

        report_paramedic = Report(template='ambulance_care_monitoring.xls')
        report_paramedic.add_page(AmbulanceParamedicPage())

        parameters.report_name = u'скорая помощь_свод'
        report_all.print_pages(parameters)

        parameters.report_name = u'скорая помощь_специализированная'
        report_specialized.print_pages(parameters)

        parameters.report_name = u'скорая помощь_врачебная'
        report_medical.print_pages(parameters)

        parameters.report_name = u'скорая помощь_фельдшерская'
        report_paramedic.print_pages(parameters)