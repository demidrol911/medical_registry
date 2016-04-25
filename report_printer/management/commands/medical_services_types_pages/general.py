from abc import abstractmethod

from django.db import connection

from main.funcs import dictfetchall
from main.funcs import howlong
from report_printer.libs.const import POSITION_REPORT
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage


class MedicalServiceTypePage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = self.get_query()
        cursor = connection.cursor()
        cursor.execute(query, dict(year=parameters.registry_year,
                                   period=parameters.registry_period))
        self.data = dictfetchall(cursor)
        cursor.close()

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        for service_group, position, order_field in self.get_output_order_fields():
            current_items = []
            for item in self.data:
                if item['group_field'] == service_group:
                    current_items.append(item)

            for item in current_items:
                sheet.set_position(POSITION_REPORT[item['mo_code']], position)
                for field in order_field:
                    sheet.write(item[field], 'c')

    @abstractmethod
    def get_query(self):
        pass

    @staticmethod
    def get_general_query():
        query = '''
                WITH registry_services AS (
                    SELECT
                        pt.gender_fk AS patient_gender,
                        pe.term_fk AS service_term,
                        ms.tariff_profile_fk AS service_tariff_profile,
                        ms.reason_fk AS service_reason,
                        ms.division_fk AS service_division,
                        ms.group_fk AS service_group,
                        ms.subgroup_fk AS service_subgroup,
                        ms.code ILIKE '0%%' AS is_adult,
                        ms.code AS service_code,

                        CASE WHEN ms.group_fk = 19
                               THEN ms.uet * ps.quantity
                             ELSE ps.quantity
                        END AS service_quantity,

                        CASE WHEN (pe.term_fk = 3 AND ps.payment_kind_fk = 2) OR pe.term_fk = 4
                               THEN True
                             ELSE False
                        END AS is_capitation,

                        ps.id_pk AS service_id,
                        pe.id_pk AS event_id,
                        ROUND(ps.tariff, 2) AS service_tariff,
                        ROUND(ps.accepted_payment, 2) AS service_accepted,
                        ROUND(ps.calculated_payment, 2) AS service_calculated,
                        mr.organization_code AS mo_code,
                        pt.id_pk AS patient_id,
                        ps.start_date AS service_start_date,
                        ps.end_date AS service_end_date,
                        pe.end_date AS event_end_date,
                        pe.division_fk AS event_division_id

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
                        JOIN patient pt
                           ON pt.id_pk = mrr.patient_fk
                        WHERE mr.is_active
                            AND mr.period = %(period)s
                            AND mr.year = %(year)s
                            AND ps.payment_type_fk = 2
                            AND (ms.group_fk != 27 OR ms.group_fk is NULL)
                            AND (pe.comment NOT ILIKE '%%P493' OR pe.comment IS NULL)
                )
                '''
        return query

    @abstractmethod
    def get_output_order_fields(self):
        pass