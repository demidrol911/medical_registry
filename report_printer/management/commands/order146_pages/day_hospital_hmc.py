#! -*- coding: utf-8 -*-
from main.funcs import howlong
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage
from django.db import connection
from main.funcs import dictfetchall


class DayHospitalHmcPage(ReportPage):
    """
    Лист принятых услуг по высоко-технологичной медицинской помощи
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = '''
                WITH registry_services AS (
                    SELECT
                        pt.gender_fk AS patient_gender,
                        pe.term_fk AS service_term,
                        ms.tariff_profile_fk AS service_tariff_profile,
                        ms.group_fk AS service_group,
                        ms.subgroup_fk AS service_subgroup,
                        ms.code ILIKE '0%%' AS is_adult,
                        ms.code AS service_code,
                        ms.vmp_group AS service_vmp_group,

                        CASE WHEN ms.group_fk = 19
                               THEN ms.uet * ps.quantity
                             ELSE ps.quantity
                        END AS service_quantity,

                        ps.id_pk AS service_id,
                        pe.id_pk AS event_id,
                        ROUND(ps.tariff, 2) AS service_tariff,
                        ROUND(ps.accepted_payment, 2) AS service_accepted,
                        mr.organization_code AS mo_code,
                        pt.id_pk AS patient_id,
                        ps.start_date AS service_start_date,
                        ps.end_date AS service_end_date
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
                )
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_tariff_profile IN (60, 63) THEN 60
                         WHEN service_tariff_profile IN (61, 62) THEN 61
                         ELSE service_tariff_profile
                    END AS group_field,

                    service_vmp_group AS vmp_group,

                    COUNT(DISTINCT (patient_id, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN patient_id
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN patient_id
                                   END) AS count_patients_child,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_quantity) AS count_days,
                    SUM(CASE WHEN is_adult
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_quantity
                        END) AS count_days_child,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                        END) AS total_accepted_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                        END) AS total_accepted_child
                FROM registry_services
                WHERE service_term = 2 and service_group = 20
                GROUP BY mo_code, group_field, vmp_group
                '''

        cursor = connection.cursor()
        cursor.execute(query, dict(year=parameters.registry_year,
                                   period=parameters.registry_period))
        self.data = dictfetchall(cursor)
        cursor.close()

    def print_page(self, sheet, parameters):
        tariff_profile_order = (
            1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
            21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
            39, 40, 41, 42
        )

        fields = ('count_patients',
                  'count_patients_adult',
                  'count_patients_child',

                  'count_services',
                  'count_services_adult',
                  'count_services_child',

                  'count_days',
                  'count_days_adult',
                  'count_days_child',

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')

        mo_order = (('280107', 2, fields), )

        sheet.set_style(VALUE_STYLE)
        sheet.set_position(11, 4)
        for vmp_group in tariff_profile_order:
            for item in self.data:
                if item['vmp_group'] == vmp_group:
                    for mo_code, position, print_fields in mo_order:
                        if item['mo_code'] == mo_code:
                            sheet.set_position(sheet.get_row_index(), position)
                            for field in fields:
                                sheet.write(item[field], 'c')

            sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())