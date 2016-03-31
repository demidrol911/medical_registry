#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.management.commands.targeted_expertise_pages.dead_result_patient import DeadResultPatient
from report_printer.management.commands.targeted_expertise_pages.overdued_nkd_hospitalization import OverduedNkdHospitalization
from report_printer.management.commands.targeted_expertise_pages.doubled_disease import DoubledDisease
from report_printer.management.commands.targeted_expertise_pages.repaid_by_death import RepaidByDeath
from report_printer.management.commands.targeted_expertise_pages.complicated_event import ComplicatedEvent
from report_printer.management.commands.targeted_expertise_pages.oks_onmk import OksOnmkPage
from report_printer.management.commands.targeted_expertise_pages.report import TargetedExpertisePage
from report_printer.libs.report import Report
from report_printer.libs.report import ReportParameters
from medical_service_register.path import REESTR_EXP
from report_printer.libs.const import MONTH_NAME


class Command(BaseCommand):
    """
    Выгружает отчёты и т - файлы по целевым экспертизам за текущий период

    1. Пациенты умершие в стационаре и в дневном стационаре
    2. Случаи с укороченным или удлинённым сроком лечения
    3. Случаи повторного лечения одного и того же заболевания
    4. Услуги оказанные застрахованным за год, полис которых погашен по смерти
    5. Случаи с осложнениями заболевания
    6. Острый коронарный синдромом (ОКС) и острое нарушение мозгового кровообращения (ОНМК)
    """

    def handle(self, *args, **options):
        dead_patient_report = DeadResultPatient()
        dead_patient_report.print_to_excel(printing_into_one_file=True)
        dead_patient_report.print_to_dbf()

        overdued_hkd_hospitalization = OverduedNkdHospitalization()
        overdued_hkd_hospitalization.print_to_excel(printing_into_one_file=True)
        overdued_hkd_hospitalization.print_to_dbf()

        doubled_disease = DoubledDisease()
        doubled_disease.print_to_excel()
        doubled_disease.print_to_dbf()

        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'целевые за %s' % MONTH_NAME[parameters.registry_period]
        report = Report('targeted_expertise.xls')
        report.add_page(TargetedExpertisePage(
            dead_data=dead_patient_report.calculate_statistic(),
            overdued_data=overdued_hkd_hospitalization.calculate_statistic(),
            doubled_data=doubled_disease.calculate_statistic()
        ))
        report.print_pages(parameters)

        repaid_by_death = RepaidByDeath()
        repaid_by_death.print_to_dbf()
        repaid_by_death.print_to_excel()

        complicated_event = ComplicatedEvent()
        complicated_event.print_to_dbf()
        complicated_event.print_to_excel(printing_into_one_file=True)

        oks_onmk = OksOnmkPage()
        oks_onmk.print_to_dbf()
        oks_onmk.print_to_excel()
