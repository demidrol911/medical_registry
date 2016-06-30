#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.management.commands.defects_report_pages.defects import DefectsPage
from report_printer.management.commands.summary_report_pages.sanctions_identify import SanctionsIdentifyPage

from summary_report_pages.sanctions_reference import SanctionsReferencePage
from summary_report_pages.services_by_division import AcceptedServicesPage, InvoicedServicesPage
from summary_report_pages.services_by_sanctions import SanctionsPage
from summary_report_pages.sogaz_mek_detailed import SogazMekDetailedPage
from summary_report_pages.sogaz_mek_general import SogazMekGeneralPage
from report_printer.libs.report import Report
from report_printer.libs.wizard import AutomaticReportsWizard
from main.logger import LOGGING_DIR
from datetime import datetime
import os


class Command(BaseCommand):

    def handle(self, *args, **options):

        report_accepted = Report(template='registry_account.xls')

        if 'by_departments' in args:
            print u'Выгрузка по подразделениям'
            report_accepted.set_by_department()

        report_accepted.add_page(AcceptedServicesPage())
        report_accepted.add_page(SanctionsPage())
        report_accepted.add_page(SanctionsReferencePage())
        report_accepted.add_page(SanctionsIdentifyPage())
        report_accepted.add_page(SogazMekDetailedPage())
        report_accepted.add_page(SogazMekGeneralPage())

        report_invoiced = Report(template='registry_account.xls', suffix=u'поданные')
        report_invoiced.add_page(InvoicedServicesPage())

        report_defects = Report(template='defect.xls', suffix=u'дефекты')
        report_defects.add_page(DefectsPage())

        report_wizard_final = AutomaticReportsWizard(
            [report_accepted,
             report_invoiced,
             report_defects]
        )
        report_wizard_final.create_reports(8)

        report_wizard_preliminary = AutomaticReportsWizard([report_accepted])
        report_wizard_preliminary.create_reports(3)

        if report_wizard_preliminary.completed_reports or report_wizard_final.completed_reports:
            printers_reports_log = open(os.path.join(LOGGING_DIR, 'printers_reports.txt'), 'a+')
            separator = u'\r\n'
            message = str(datetime.now())
            if report_wizard_preliminary.completed_reports:
                message += separator + u'Предварительные:' + separator
                for report_name in report_wizard_preliminary.completed_reports:
                    message += report_name + separator

            if report_wizard_final.completed_reports:
                message += separator + u'Итоговые:' + separator
                for report_name in report_wizard_final.completed_reports:
                    message += report_name + separator

            printers_reports_log.write(message.encode('cp1251'))
            printers_reports_log.close()
