#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from summary_report_pages.sanctions_reference import SanctionsReferencePage
from summary_report_pages.services_by_sanctions import SanctionsPage
from report_printer.libs.report import Report
from report_printer.libs.wizard import AutomaticReportsWizard
from registry_import_new.sender import Sender
from medical_service_register.path import REESTR_EXP
from tfoms.func import YEAR, PERIOD


class Command(BaseCommand):

    def handle(self, *args, **options):

        report_accepted = Report(template='registry_mek.xls', suffix=u'ошибки')

        sanction_page = SanctionsPage()
        sanction_page.page_number = 0
        report_accepted.add_page(sanction_page)

        sanction_ref_page = SanctionsReferencePage()
        sanction_ref_page.page_number = 1
        report_accepted.add_page(sanction_ref_page)

        report_wizard_preliminary = AutomaticReportsWizard([report_accepted])
        report_wizard_preliminary.create_reports(104)

        sender = Sender()
        for report_name in report_wizard_preliminary.completed_reports:
            org_code = report_name[:6]
            sender.set_recipient(org_code)
            sender.send_file(u'{path}/ошибки/{file_name}'.
                             format(path=REESTR_EXP % (YEAR, PERIOD), file_name=report_name))


