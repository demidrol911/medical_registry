#! -*- coding: utf-8 -*-
from main.models import MedicalDivision
from report_printer_clear.utils.excel_style import VALUE_STYLE

from report_printer_clear.utils.page import ReportPage
from report_printer.const import MONTH_NAME


class HospitalDivisionAcceptedPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    md.id_pk,
                    md.code AS division_code,
                    md.name AS division_name,
                    COUNT(DISTINCT CASE WHEN mr.period = %(period)s
                                          THEN pe.id_pk
                                   END
                         ) AS count_hospitalization_in_current_period,
                    COUNT(DISTINCT pe.id_pk) AS count_hospitalization_in_current_year

                FROM medical_register mr
                    JOIN medical_register_record mrr
                       ON mr.id_pk = mrr.register_fk
                    JOIN provided_event pe
                       ON mrr.id_pk = pe.record_fk
                    JOIN provided_service ps
                       ON ps.event_fk = pe.id_pk
                    JOIN medical_organization mo
                       ON ps.organization_fk = mo.id_pk
                    JOIN medical_service ms
                       ON ms.id_pk = ps.code_fk
                    JOIN medical_division md
                       ON md.id_pk = pe.division_fk
                WHERE mr.is_active
                   AND mr.year = %(year)s
                   AND ps.payment_type_fk = 2
                   AND pe.term_fk = 1
                   AND (ms.group_fk != 27
                        OR ms.group_fk is null
                       )
                GROUP BY md.id_pk, md.code, md.name
                '''

        self.data = MedicalDivision.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year
        ))

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        sheet.write(u'Код', 'c')
        sheet.write(u'Наименование', 'c')
        sheet.write(u'за %s' % MONTH_NAME[parameters.registry_period], 'c')
        sheet.write(u'за %d месяцев' % int(parameters.registry_period), 'r')
        for division in self.data:
            sheet.write(division.division_code, 'c')
            sheet.write(division.division_name, 'c')
            sheet.write(division.count_hospitalization_in_current_period, 'c')
            sheet.write(division.count_hospitalization_in_current_year, 'r')
