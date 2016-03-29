#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.libs.report import Report
from report_printer.libs.report import ReportParameters
from tfoms.models import MedicalOrganization
from medical_service_register.path import REESTR_EXP

from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from report_printer.libs.const import MONTH_NAME


class AttachmentStat(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                select
                    mo.id_pk, mo.name AS organization_name,
                    COUNT(distinct CASE WHEN mo.id_pk = att_mo.id_pk THEN p.id_pk END) AS count_att_current_mo,
                    COUNT(distinct CASE WHEN mo.id_pk != att_mo.id_pk THEN p.id_pk END) AS count_att_other_mo,
                    COUNT(DISTINCT CASE WHEN att_mo.id_pk is null tHEN p.id_pk END) AS count_not_att,
                    COUNT(distinct p.id_pk) AS total
                from
                     provided_service ps
                     JOIN provided_event pe
                        on ps.event_fk = pe.id_pk
                     JOIN medical_register_record mrr
                        on mrr.id_pk = pe.record_fk
                     JOIN medical_register mr
                        on mr.id_pk = mrr.register_fk
                     JOIN medical_organization dep
                        on dep.id_pk = ps.department_fk
                     JOIN medical_register_status mrs
                        on mrs.id_pk = mr.status_fk
                     JOIN patient p
                        on p.id_pk = mrr.patient_fk
                     join medical_organization mo
                        ON mo.id_pk = ps.organization_fk
                     left JOIN medical_organization att_mo
                        ON att_mo.code = p.attachment_code and att_mo.parent_fk is null

                where mr.is_active
                        and mr.period = %(period)s
                        and mr.year = %(year)s
                        group by mo.id_pk, mo.name
                        order by mo.name
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year
        ))

    def print_page(self, sheet, parameters):
        titles = (
            u'МО',
            u'Прикреплено к мо',
            u'Прикреплено к другой мо',
            u'Не прикреплено',
            u'Итого'
        )
        sheet.set_style(VALUE_STYLE)
        for title in titles[:-1]:
            sheet.write(title, 'c')
        sheet.write(titles[-1], 'r')
        for data_on_mo in self.data:
            sheet.write(data_on_mo.organization_name, 'c')
            sheet.write(data_on_mo.count_att_current_mo, 'c')
            sheet.write(data_on_mo.count_att_other_mo, 'c')
            sheet.write(data_on_mo.count_not_att, 'c')
            sheet.write(data_on_mo.total, 'r')


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'статистика по прикреплению в реестрах за %s' % MONTH_NAME[parameters.registry_period]

        report = Report()
        report.add_page(AttachmentStat())
        report.print_pages(parameters)
