#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from sogaz_registry_bill_pages.sogaz_registry_bill import SogazRegistryBillPage
from report_printer_clear.utils.report import Report
from report_printer_clear.utils.wizard import AutomaticReportsWizard


class Command(BaseCommand):

    def handle(self, *args, **options):
        report = Report(template='sogaz_registry_bill.xls', suffix=u'реестр_счетов')
        report.add_page(SogazRegistryBillPage())

        report_wizard = AutomaticReportsWizard([report])
        report_wizard.create_reports(104)
