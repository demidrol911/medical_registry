#! -*- coding: utf-8 -*-
from main.funcs import howlong
from main.models import MedicalOrganization
from report_printer.libs.page import ReportPage
from report_printer.libs.excel_style import VALUE_STYLE
from django.db import connection
from main.funcs import dictfetchall


class FondDefectsPage(ReportPage):
    ERRORS_ORDER = [
        50, 51, 52, 53, 54, 55, 133, 56, 57, 58, 59,
        60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70,
        71, 72, 73, 74, 75
    ]

    def __init__(self):
        self.data_detail = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data_detail = None
        detail_query = FondDefectsPage.get_detail_query()
        cur = connection.cursor()
        cur.execute(detail_query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year
        ))
        self.data_detail = dictfetchall(cur)

    @staticmethod
    def get_general_query():
        query = '''
                SELECT
                    COUNT(DISTINCT CASE WHEN not T1.is_children THEN
                         ) AS visit_all_adult,
                    COUNT(DISTINCT CASE WHEN T1.is_children
                                          THEN (

                                          )
                                          END
                        ) AS visit_all_children,

                    COUNT(DISTINCT CASE WHEN not T1.is_children
                                             AND T1.is_accepted
                                          THEN (
                                             CASE WHEN T1.service_group = 19
                                                       AND T1.service_subgroup is NULL
                                                    THEN NULL
                                                  ELSE T1.service_id
                                             END
                                          )
                                   END
                        ) AS visit_accept_adult,
                    COUNT(DISTINCT CASE WHEN T1.is_children
                                             AND T1.is_accepted
                                          THEN (
                                             CASE WHEN T1.service_group = 19
                                                       AND T1.service_subgroup is NULL
                                                    THEN NULL
                                                  ELSE T1.service_id
                                             END
                                          )
                                   END
                        ) AS visit_accept_children,

                    COUNT(DISTINCT CASE WHEN T1.is_excluded
                                          THEN (
                                             CASE WHEN T1.service_group = 19
                                                     AND T1.service_subgroup is NULL
                                                    THEN NULL
                                                  ELSE T1.service_id
                                             END
                                          )
                                   END
                        ) AS visit_exclude,

                    COUNT(DISTINCT CASE WHEN T1.is_excluded AND (T1.error_old_code != 'ZD' or T1.error_old_code IS NULL)
                                          THEN CASE WHEN T1.service_group in (25, 26)
                                                      THEN T1.service_id
                                                    WHEN T1.service_group in (19)
                                                         AND T1.stomatology_reason is NULL
                                                      THEN NULL
                                                    ELSE T1.event_id
                                                END
                                   END
                        ) AS treatment_exclude,

                    SUM(CASE WHEN T1.is_excluded
                               THEN T1.count_days
                             ELSE 0
                        END
                        ) AS count_days_exclude,

                    SUM(CASE WHEN T1.is_excluded
                               THEN T1.uet
                             ELSE 0
                        END
                        ) AS uet_exclude

                FROM ({inner_query}) AS T1
                '''.format(inner_query=FondDefectsPage.get_inner_query())
        return query

    @staticmethod
    def get_detail_query():
        query = '''
                SELECT
                    T1.failure_cause,
                    SUM(CASE WHEN T1.is_excluded THEN T1.sanc END) AS total_defects
                FROM ({inner_query}) AS T1
                WHERE T1.is_excluded
                GROUP BY T1.failure_cause
                '''.format(inner_query=FondDefectsPage.get_inner_query())
        return query

    @staticmethod
    def get_inner_query():
        query = '''
                SELECT
                    CASE WHEN T.is_accepted
                           THEN NULL
                         WHEN T.is_excluded
                           THEN CASE WHEN T.error in (145, 128)
                                       THEN 55
                                     WHEN T.error = 127
                                       THEN 133
                                     ELSE T.error
                                END
                    END AS failure_cause,
                    T.*

                FROM (
                    SELECT
                        ps.id_pk AS service_id,
                        pe.id_pk AS event_id,
                        pe.term_fk AS term,
                        ms.group_fk AS service_group,
                        ms.code AS service_code,
                        ms.reason_fk AS service_reason,
                        ms.subgroup_fk AS service_subgroup,
                        mo.id_pk AS organization_id,
                        me.failure_cause_fk AS error,
                        me.old_code AS error_old_code,

                        ps.quantity AS COUNT_days,
                        ps.quantity*ms.uet AS uet,
                        ps.payment_type_fk = 2 AS is_accepted,
                        ps.payment_type_fk = 3 AS is_excluded,
                        ms.code like '1%%' AS is_children,
                        pe.end_date as event_end_date,
                        (CASE WHEN ps.payment_kind_fk = 2 THEN 0 ELSE ps.provided_tariff END) AS sanc


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
                        LEFT JOIN provided_service_sanction pss
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
                        LEFT JOIN medical_error me
                                ON me.id_pk = pss.error_fk
                        WHERE
                           mr.is_active
                           AND mr.period = %(period)s
                           AND mr.year = %(year)s
                           AND (ms.group_fk != 27
                                OR ms.group_fk is null
                                )
                    ) AS T
        '''
        return query

    def print_page(self, sheet, parameters):
        sheet.write_cell(0, 3, u'Сводная справка  по  дефектам за ' + parameters.date_string)
        sheet.write_cell(3, 0, parameters.organization_code+' '+parameters.report_name)
        sheet.set_style(VALUE_STYLE)

        for data in self.data_detail:
            failure_cause = data['failure_cause']

            if failure_cause is None:
                continue

            column_index = FondDefectsPage.ERRORS_ORDER.index(failure_cause)
            sheet.set_position(5, 7 + column_index)
            sheet.write(data['total_defects'], 'c')
