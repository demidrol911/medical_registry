from main.models import MedicalOrganization
from report_printer.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage
from tfoms.func import FAILURE_CAUSES


class SanctionCheckSumsPage(ReportPage):

    def __init__(self):
        self.data = ''
        self.page_number = 1

    def calculate(self, parameters):
        query = '''
                SELECT
                    mo.id_pk,
                    pfc.number,
                    me.failure_cause_fk AS failure_cause_id,
                    COUNT(distinct ps.id_pk) AS count_errors

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
                    JOIN provided_service_sanction pss
                       ON pss.service_fk = ps.id_pk
                          AND pss.is_active
                          AND pss.type_fk = 1
                          AND pss.error_fk = (
                              SELECT inner_me.id_pk
                              FROM medical_error inner_me
                                  JOIN provided_service_sanction inner_pss
                                     ON inner_me.id_pk = inner_pss.error_fk
                                        AND inner_pss.service_fk = ps.id_pk

                              WHERE inner_pss.is_active
                                  AND inner_pss.type_fk = 1
                              ORDER BY inner_me.weight DESC
                              LIMIT 1
                        )
                    JOIN medical_error me
                       ON me.id_pk = pss.error_fk
                    JOIN payment_failure_cause pfc
                       ON pfc.id_pk = me.failure_cause_fk
                WHERE mr.is_active
                   AND mr.period = %(period)s
                   AND mr.year = %(year)s
                   AND mr.organization_code = %(organization)s
                   AND pss.is_active
                   AND pss.type_fk = 1
                   AND ps.payment_type_fk = 3
                   AND (ms.group_fk != 27
                        OR ms.group_fk is null
                       )
                  GROUP BY mo.id_pk, pfc.number, failure_cause_id
                  ORDER BY pfc.number ASC
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

    def print_page(self, sheet, parameters):
        sheet.write_cell(0, 0, parameters.report_name)
        sheet.write_cell(0, 1, parameters.date_string)
        sheet.set_position(5, 0)
        sheet.set_style(VALUE_STYLE)
        for item in self.data:
            failure_cause_info = FAILURE_CAUSES[item.failure_cause_id]
            sheet.write(failure_cause_info['number'], 'c')
            sheet.write(failure_cause_info['name'], 'c')
            sheet.write(item.count_errors, 'r')
