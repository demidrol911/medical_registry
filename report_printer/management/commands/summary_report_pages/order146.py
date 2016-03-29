#! -*- coding: utf-8 -*-
from django.db import connection
from decimal import Decimal
from main.funcs import howlong
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage


class Order146Page(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 4

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = '''
            SELECT
                -- Вид помощи
                CASE WHEN pe.term_fk = 3 AND ms.reason_fk = 1
                          AND ms.division_fk in (443, 399, 401, 403, 444)
                       THEN 2 -- по поводу заболевания (первич. )

                     WHEN (pe.term_fk = 3 AND ms.reason_fk in (2, 3, 8)
                           AND ms.division_fk in (443, 399, 401, 403, 444))
                           OR  ms.group_fk = 4
                           --Новые коды по профосмотру взрослых
                           OR  ms.code in ('019214', '019215', '019216', '019217')
                           OR  ms.code in ('019001', '019021', '019023', '019022', '019024')
                           OR  ms.code  = '019107'
                           --Новые коды по диспансеризации детей сирот в стац. учреждениях
                           OR ms.code in ('119020', '119021', '119022', '119023',
                                 '119024', '119025', '119026', '119027',
                                 '119028', '119029', '119030', '119031')
                           --Новые коды по диспансеризации детей сирот без попечения родителей
                           OR  ms.code in ('119220', '119221', '119222', '119223',
                                 '119224', '119225', '119226', '119227',
                                 '119228', '119229', '119230', '119231')
                           --Новые коды по профосмотрам несовершеннолетних
                           OR ms.code in ('119080', '119081', '119082', '119083',
                                 '119084', '119085', '119086', '119087',
                                 '119088', '119089', '119090', '119091')
                           OR  ms.code in ('119101', '119119', '119120')
                           OR  ms.code =  '119151'
                       THEN 3 -- Профилактика (первич. )


                     WHEN pe.term_fk = 3 AND ms.reason_fk = 5
                          AND ms.group_fk is NULL
                          AND ms.division_fk in (443, 399, 401, 403, 444)
                       THEN 4 -- Неотложка (первич.)

                     WHEN ms.group_fk = 19
                       THEN 5 -- Стоматология

                     WHEN pe.term_fk = 2
                          AND ms.group_fk is null
                          AND msd.term_fk = 12
                       THEN 6 -- Дневной стационар (на дому)

                     WHEN pe.term_fk = 3 AND ms.reason_fk = 1
                          AND (ms.group_fk != 19 OR ms.group_fk is NULL)
                          AND ms.division_fk not in (443, 399, 401, 403, 444)
                       THEN 9 -- по поводу заболевания (спец.)

                     WHEN (pe.term_fk = 3
                           AND (ms.group_fk is NULL OR ms.group_fk = 24)
                           AND ms.reason_fk in (2, 3, 8)
                           AND ms.division_fk not in (443, 399, 401, 403, 444))
                              OR ms.code = '019020'
                              OR ms.code in ('019108', '019106', '019105', '019104', '019103', '019102')
                              OR ms.code in ('019114', '019113', '019112', '019111', '019110', '019109')
                              OR ms.subgroup_fk in (9, 10, 8, 11)
                       THEN 10 -- профилактика (спец. )


                     WHEN (pe.term_fk = 3 AND ms.reason_fk = 5
                           AND ms.group_fk is NULL
                           AND ms.division_fk not in (443, 399, 401, 403, 444)
                           ) OR ms.group_fk = 31
                       THEN 11 -- Неотложка (спец.)

                     WHEN ms.code in ('049021', '149021')
                       THEN 12 -- Гемодиализ в поликлинике

                     WHEN ms.code in ('049022', '149022')
                       THEN 13 -- Перитонеальный диализ в поликлинике

                     WHEN (pe.term_fk = 2
                           AND ms.group_fk is NULL
                           AND msd.term_fk in (10, 11))
                           OR ms.group_fk = 28
                       THEN 14 -- Дневной стационар (при стационаре  и поликлинике)

                     WHEN ms.group_fk = 17
                       THEN 15 -- ЭКО

                     WHEN pe.term_fk = 1
                          AND (ms.group_fk not in (17, 3, 5)
                               OR ms.group_fk is NULL)
                       THEN 17 -- Стационар

                     WHEN ms.code in ('049023', '149023')
                       THEN 18 -- Гемодиализ в стационаре

                     WHEN ms.code in ('049024', '149024')
                       THEN 19 -- Перитонеальный диализ в стационаре

                     WHEN pe.term_fk = 4
                       THEN 20 -- Скорая медицинская помощь

                     ELSE 0
                END AS term,

                -- Количество пациентов
                COUNT(DISTINCT CASE WHEN ms.code in (
                                                '019201', '019214',
                                                '019215', '019001',
                                                '019020'
                                         )
                                         OR ms.subgroup_fk not in (12, 13, 14, 17)
                                         OR ms.subgroup_fk in (9, 10, 8, 11)
                                      THEN NULL

                                    ELSE (
                                       CASE WHEN (ms.group_fk is null OR ms.group_fk = 24)
                                                  AND pe.term_fk = 3
                                              THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk is null AND pe.term_fk = 4
                                              THEN (2, 0, 0, ms.division_fk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk is null AND pe.term_fk = 1
                                              THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk is null AND pe.term_fk = 2
                                              THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk = 19 and subgroup_fk is NOT NULL
                                              THEN (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk != 19 and subgroup_fk is NULL
                                              THEN (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk,  ms.code ilike '0%%')
                                            WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL
                                              THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%%')
                                       END
                                    )
                               END
                     ) AS patient,

                COUNT(DISTINCT CASE WHEN ms.code ilike '0%%'
                                      THEN (
                                            CASE WHEN ms.code in ('019201', '019214', '019215',  '019001', '019020' )
                                                     OR ms.subgroup_fk not in  (12, 13, 14, 17)
                                                     OR ms.subgroup_fk in (9, 10, 8, 11)
                                                   THEN NULL

                                                 ELSE (
                                                     CASE WHEN (ms.group_fk is NULL OR ms.group_fk = 24)
                                                                AND pe.term_fk = 3
                                                            THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk, pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk is null and pe.term_fk = 4
                                                            THEN (2, 0, 0, ms.division_fk,  pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk is null AND pe.term_fk = 1
                                                            THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk is null AND pe.term_fk = 2
                                                            THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk = 19 and subgroup_fk is NOT NULL
                                                            THEN (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk != 19 and subgroup_fk is NULL
                                                            THEN (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk, ms.code ilike '0%%')
                                                          WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL
                                                            THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk, ms.code ilike '0%%')
                                                     END
                                                 )
                                            END
                                      )
                                    ELSE NULL
                               END
                      ) AS patient_adult,

                COUNT(DISTINCT CASE WHEN ms.code ilike '1%%'
                                      THEN (
                                            CASE WHEN ms.code in ('019201', '019214', '019215',  '019001', '019020')
                                                      OR ms.subgroup_fk not in  (12, 13, 14, 17)
                                                      OR ms.subgroup_fk in (9, 10, 8, 11)
                                                   THEN NULL
                                                 ELSE (
                                                      CASE WHEN (ms.group_fk is NULL OR ms.group_fk = 24)
                                                                 AND pe.term_fk = 3
                                                             THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk, pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk is null AND pe.term_fk = 4
                                                             THEN (2, 0, 0, ms.division_fk, pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk is null AND pe.term_fk = 1
                                                             THEN (3, 0, 0, ms.tariff_profile_fk, pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk is null AND pe.term_fk = 2
                                                             THEN (3, 0, 0, ms.tariff_profile_fk, pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk = 19 AND subgroup_fk is NOT NULL
                                                             THEN (ms.group_fk, 0, 0, ms.subgroup_fk, pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk != 19 and subgroup_fk is NULL
                                                             THEN (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk, ms.code ilike '0%%')
                                                           WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL
                                                             THEN (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk, ms.code ilike '0%%')
                                                      END
                                                 )
                                            END
                                      )
                                    ELSE NULL
                               END
                     ) AS patient_children,

                -- Количество обращений
                COUNT(DISTINCT CASE WHEN ms.subgroup_fk = 12
                                         OR ((
                                                SELECT
                                                    COUNT(ps1.id_pk)
                                                FROM provided_service ps1
                                                    JOIN medical_service ms1
                                                       ON ms1.id_pk = ps1.code_fk
                                                WHERE ps1.event_fk = ps.event_fk
                                                      AND (ms1.group_fk != 27
                                                           OR ms1.group_fk is NULL)
                                              )>1
                                            AND ms.reason_fk = 1 AND pe.term_fk = 3
                                            AND (ms.group_fk is NULL OR ms.group_fk = 24
                                         ))
                                      THEN pe.id_pk
                               END
                     ) AS treatments,
                COUNT(DISTINCT CASE WHEN ms.code ilike '0%%'
                                      THEN (
                                          CASE WHEN ms.subgroup_fk=12
                                                    OR ((
                                                           SELECT
                                                               COUNT(ps1.id_pk)
                                                           FROM provided_service ps1
                                                               JOIN medical_service ms1
                                                                  ON ms1.id_pk = ps1.code_fk
                                                           WHERE ps1.event_fk = ps.event_fk
                                                               AND (ms1.group_fk != 27 OR ms1.group_fk is null)
                                                         )>1
                                                        AND ms.reason_fk = 1 AND pe.term_fk = 3
                                                        AND (ms.group_fk is null OR ms.group_fk = 24)
                                                    )
                                                 THEN pe.id_pk
                                          END
                                      )
                               END
                     ) AS treatments_adult,
                COUNT(DISTINCT CASE WHEN ms.code ilike '1%%'
                                      THEN (
                                          CASE WHEN ms.subgroup_fk=12
                                                    OR ((
                                                           SELECT
                                                               COUNT(ps1.id_pk)
                                                           FROM provided_service ps1
                                                               JOIN medical_service ms1
                                                                  ON ms1.id_pk = ps1.code_fk
                                                           WHERE ps1.event_fk = ps.event_fk
                                                               AND (ms1.group_fk != 27 OR ms1.group_fk is null)
                                                         )>1
                                                        AND ms.reason_fk = 1 AND pe.term_fk = 3
                                                        AND (ms.group_fk is null OR ms.group_fk = 24)
                                                    )
                                                 THEN pe.id_pk
                                          END
                                      )
                               END
                     ) AS treatments_children,

                -- Количество услуг
                COUNT(DISTINCT CASE WHEN ms.group_fk = 19
                                         AND ms.subgroup_fk is NULL
                                      THEN NULL
                                    ELSE ps.id_pk
                               END
                     ) AS services,
                COUNT(DISTINCT CASE WHEN ms.code ilike '0%%'
                                      THEN (
                                          CASE WHEN ms.group_fk = 19
                                                    AND ms.subgroup_fk is NULL
                                                 THEN NULL
                                               ELSE ps.id_pk
                                          END
                                      )
                               END
                     ) AS services_adult,
                COUNT(DISTINCT CASE WHEN ms.code ilike '1%%'
                                      THEN (
                                          CASE WHEN ms.group_fk = 19
                                                    AND ms.subgroup_fk is NULL
                                                 THEN NULL
                                               ELSE ps.id_pk
                                          END
                                      )
                               END
                     ) AS services_children,

                -- Количество дней
                SUM(CASE WHEN ms.group_fk = 19
                           THEN ps.quantity*ms.uet
                         WHEN ps.quantity is NULL
                           THEN 1
                         ELSE ps.quantity
                    END) AS quantity,
                SUM(CASE WHEN ms.code ilike '0%%'
                           THEN (
                               CASE WHEN ms.group_fk = 19
                                      THEN ps.quantity*ms.uet
                                    WHEN ps.quantity is NULL
                                      THEN 1
                                    ELSE ps.quantity
                               END
                           )
                         ELSE 0
                    END) AS quantity_adult,

                SUM(CASE WHEN ms.code ilike '1%%'
                           THEN (
                               CASE WHEN ms.group_fk = 19
                                      THEN ps.quantity*ms.uet
                                    WHEN ps.quantity is NULL
                                      THEN 1
                                    ELSE ps.quantity
                               END
                           )
                         ELSE 0
                    END) AS quantity_children,


                -- Принятая сумма
                SUM(CASE WHEN ps.payment_kind_fk=2
                           THEN 0
                         ELSE ps.accepted_payment
                    END) as accepted_payment,
                SUM(CASE WHEN ms.code ilike '0%%'
                           THEN (
                                CASE WHEN ps.payment_kind_fk=2
                                       THEN 0 else ps.accepted_payment
                                END
                           )
                         ELSE 0
                    END) AS accepted_payment_adult,

                SUM(CASE WHEN ms.code ilike '1%%'
                           THEN (
                                CASE WHEN ps.payment_kind_fk=2
                                       THEN 0
                                     ELSE ps.accepted_payment
                                END
                           ) ELSE 0
                    END) AS accepted_payment_children


            FROM medical_register mr
                JOIN medical_register_record mrr
                   ON mr.id_pk = mrr.register_fk
                JOIN provided_event pe
                   ON mrr.id_pk = pe.record_fk
                JOIN provided_service ps
                   ON ps.event_fk = pe.id_pk
                JOIN medical_organization mo
                   ON ps.organization_fk = mo.id_pk
                JOIN medical_organization dep
                   ON ps.department_fk = dep.id_pk
                JOIN medical_service ms
                   ON ms.id_pk = ps.code_fk
                JOIN patient pt
                   ON pt.id_pk = mrr.patient_fk
                LEFT JOIN medical_division msd
                   ON msd.id_pk = pe.division_fk
            WHERE mr.is_active
                  AND mr.year = %(year)s
                  AND mr.period = %(period)s
                  AND mo.code = %(organization)s
                  and ps.payment_type_fk = 2
                  and (ms.group_fk != 27 OR ms.group_fk is NULL)
            GROUP BY term
            ORDER BY term
            '''

        self.data = self.__run_query(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

    def print_page(self, sheet, parameters):
        sheet.set_style({})
        sheet.write_cell(2, 0, parameters.report_name)
        sheet.write_cell(3, 10, u'за %s г.' % parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        total = [Decimal(0)]*15
        for row in self.data:
            if row[0]:
                sheet.set_position(8 + int(row[0]), 3)
                for idx, value in enumerate(row[1:]):
                    sheet.write(value, 'c')
                    total[idx] += Decimal(value)
        policlinic_capitation = parameters.policlinic_capitation
        ambulance_capitation = parameters.ambulance_capitation
        if policlinic_capitation[0]:
            sheet.set_position(31, 15)
            adult = policlinic_capitation[1]['adult']['accepted']
            child = policlinic_capitation[1]['child']['accepted']
            total[12] += adult + child
            total[13] += adult
            total[14] += child

            sheet.write(adult+child, 'c')
            sheet.write(adult, 'c')
            sheet.write(child, 'r')

        if ambulance_capitation[0]:
            sheet.set_position(32, 15)
            child = ambulance_capitation[1]['adult']['accepted']
            adult = ambulance_capitation[1]['child']['accepted']
            total[12] += adult + child
            total[13] += adult
            total[14] += child

            sheet.write(adult+child, 'c')
            sheet.write(adult, 'c')
            sheet.write(child, 'r')

        sheet.set_position(33, 3)
        for value in total:
            sheet.write(value, 'c')

    def __run_query(self, query, parameters):
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        return [row for row in cursor.fetchall()]

