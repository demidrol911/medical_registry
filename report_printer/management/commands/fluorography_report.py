#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.libs.report import Report
from report_printer.libs.report import ReportParameters
from tfoms.models import MedicalOrganization
from medical_service_register.path import REESTR_DIR

from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from report_printer.libs.const import MONTH_NAME


class FluorographyPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                select
                mo.id_pk,
                CASE WHEN mo.id_pk is null and f.insurance_policy_fk is not null THEN 'НЕ ПРИКРЕПЛЕНЫ'
                         WHEN f.insurance_policy_fk is null THEN 'НЕ ИДЕНТИФИЦИРОВАНЫ'
                         ELSE mo.name
                END AS organization_name,
                count(distinct f.id_pk) AS count_services,
                count(distinct f.insurance_policy_fk) AS count_patients
                from fluorography f
                left join medical_organization mo ON mo.code = f.attachment_code and mo.parent_fk is null
                where date = format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE
                group by mo.id_pk, organization_name
                order by mo.id_pk, organization_name
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year
        ))

    def print_page(self, sheet, parameters):
        titles = (
            u'МО',
            u'Подали',
            u'Пациентов',
            u'Тариф',
            u'Сумма'
        )
        sheet.set_style(VALUE_STYLE)
        for title in titles[:-1]:
            sheet.write(title, 'c')
        sheet.write(titles[-1], 'r')
        for data_on_mo in self.data:
            sheet.write(data_on_mo.organization_name, 'c')
            sheet.write(data_on_mo.count_services, 'c')
            sheet.write(data_on_mo.count_patients, 'r')


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_DIR % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'флюорография в ГП2 по больницам за %s' % MONTH_NAME[parameters.registry_period]

        report = Report()
        report.add_page(FluorographyPage())
        report.print_pages(parameters)
