from main.models import MedicalOrganization
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from report_printer.libs.const import POSITION_REPORT


class FinalReportPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,
                    mr.organization_code AS organization_code,
                    SUM(ps.tariff) AS tariff,
                    SUM(ps.invoiced_payment) AS invoiced_payment,
                    SUM(ps.accepted_payment) AS accepted_payment,
                    SUM(CASE WHEN ps.payment_kind_fk = 2
                                  AND pe.term_fk = 3
                               THEN ps.accepted_payment
                             ELSE 0
                        END) AS policlinic_capitation,
                    SUM(CASE WHEN pe.term_fk = 4 AND ps.payment_kind_fk = 2
                               THEN ps.accepted_payment
                             ELSE 0
                        END) AS ambulance_capitation

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
                WHERE mr.is_active
                   AND mr.period = %(period)s
                   AND mr.year = %(year)s
                   AND (ms.group_fk != 27
                        OR ms.group_fk is null
                       )
                   AND ps.payment_type_fk = 2
                GROUP BY mo.id_pk, mr.organization_code
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year
        ))

    def print_page(self, sheet, parameters):
        sheet.set_style({'align': 'center'})
        sheet.write_cell(5, 1, parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        for data_on_mo in self.data:
            sheet.set_position(POSITION_REPORT[data_on_mo.organization_code], 2)
            sheet.write(data_on_mo.tariff, 'c')
            sheet.write(data_on_mo.invoiced_payment, 'c')
            sheet.write(data_on_mo.accepted_payment, 'c')
            sheet.write(data_on_mo.policlinic_capitation, 'c')
            sheet.write(data_on_mo.ambulance_capitation)
