#! -*- coding: utf-8 -*-
from main.funcs import howlong
from main.models import MedicalOrganization
from report_printer.libs.page import ReportPage
from report_printer.libs.excel_style import VALUE_STYLE


class DefectsPage(ReportPage):
    VISIT = 1
    TREATMENT = 2
    COUNT_DAYS = 3
    UET = 4

    SERVICES_GROUPS = {
        'hospital': [(1, VISIT)],
        'hospital_ambulance': [(2, VISIT)],
        'coronary_angiography': [(3, VISIT)],
        'cerebral_angiography': [(4, VISIT)],
        'gemodialis_hospital': [(5, TREATMENT), (6, COUNT_DAYS)],
        'peritondialis_hospital': [(7, TREATMENT), (8, COUNT_DAYS)],
        'day_hospital': [(9, VISIT), (10, COUNT_DAYS)],
        'gemodialis_day_hospital': [(11, TREATMENT), (12, COUNT_DAYS)],
        'peritondialis_day_hospital': [(13, TREATMENT), (14, COUNT_DAYS)],
        'policlinic_disease': [(15, VISIT), (16, TREATMENT)],
        'policlinic_priventive': [(17, VISIT)],
        'policlinic_ambulance': [(18, VISIT)],
        'adult_exam': [(19, TREATMENT), (20, VISIT)],
        'ambulance': [(21, VISIT)],
        'trombolisis': [(22, VISIT)],
        'mrt': [(23, VISIT)],
        'gemodialis_policlinic': [(24, TREATMENT), (25, COUNT_DAYS)],
        'peritondialis_policlinic': [(26, TREATMENT), (27, COUNT_DAYS)],
        'children_exam': [(28, TREATMENT), (29, VISIT)],
        'prelim_children_exam': [(30, TREATMENT), (31, VISIT)],
        'period_children_exam': [(32, TREATMENT)],
        'clinical_exam': [(33, TREATMENT), (34, VISIT)],
        'usg': [(35, TREATMENT), (36, VISIT)],
        'stom_disease': [(37, TREATMENT), (38, UET)],
        'stom_ambulance': [(39, VISIT), (40, UET)]
    }

    ERRORS_ORDER = [
        50, 51, 52, 53, 54, 55, 133, 56, 57, 58, 59,
        60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70,
        71, 72, 73, 74, 75
    ]

    def __init__(self):
        self.data_general = None
        self.data_detail = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data_general = None
        self.data_detail = None
        general_query = DefectsPage.get_general_query()
        self.data_general = MedicalOrganization.objects.raw(general_query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

        detail_query = DefectsPage.get_detail_query()
        self.data_detail = MedicalOrganization.objects.raw(detail_query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

    @staticmethod
    def get_general_query():
        query = '''
                SELECT
                    mo.id_pk,
                    T1.division_term,

                    COUNT(DISTINCT CASE WHEN not T1.is_children
                                          THEN (
                                             CASE WHEN T1.service_group = 19
                                                     AND T1.service_subgroup is NULL
                                                    THEN NULL
                                                  ELSE T1.service_id
                                             END
                                          )
                                          END
                         ) AS visit_all_adult,
                    COUNT(DISTINCT CASE WHEN T1.is_children
                                          THEN (
                                             CASE WHEN T1.service_group = 19
                                                     AND T1.service_subgroup is NULL
                                                    THEN NULL
                                                  ELSE T1.service_id
                                             END
                                          )
                                          END
                        ) AS visit_all_children,

                    COUNT(DISTINCT CASE WHEN not T1.is_children
                                THEN CASE WHEN T1.service_group in (25, 26)
                                            THEN T1.service_id
                                          WHEN T1.service_group in (19)
                                             AND T1.stomatology_reason is NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 and T1.service_subgroup IS NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                            THEN  T1.service_id
                                          ELSE T1.event_id
                                     END
                                END
                        ) AS treatment_all_adult,
                    COUNT(DISTINCT CASE WHEN T1.is_children
                                THEN CASE WHEN T1.service_group in (25, 26)
                                            THEN T1.service_id
                                          WHEN T1.service_group in (19)
                                             AND T1.stomatology_reason is NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 and T1.service_subgroup IS NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                            THEN  T1.service_id
                                          ELSE T1.event_id
                                     END
                                END
                        ) AS treatment_all_children,

                    SUM(CASE WHEN not T1.is_children
                             THEN T1.count_days
                             ELSE 0
                        END
                        ) AS count_days_all_adult,
                    SUM(CASE WHEN T1.is_children
                             THEN T1.count_days
                             ELSE 0
                        END
                        ) AS count_days_all_children,

                    SUM(CASE WHEN not T1.is_children
                             THEN T1.uet
                             ELSE 0
                        END
                        ) AS uet_all_adult,
                    SUM(CASE WHEN T1.is_children
                             THEN T1.uet ELSE 0
                        END
                        ) AS uet_all_children,


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

                    COUNT(DISTINCT CASE WHEN not T1.is_children
                                             AND T1.is_accepted
                                THEN CASE WHEN T1.service_group in (25, 26)
                                            THEN T1.service_id
                                          WHEN T1.service_group = 19 and T1.service_subgroup IS NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                            THEN T1.service_id
                                          ELSE T1.event_id
                                     END
                                END
                        ) AS treatment_accept_adult,
                    COUNT(DISTINCT CASE WHEN T1.is_children
                                             AND T1.is_accepted
                                THEN CASE WHEN T1.service_group in (25, 26)
                                            THEN T1.service_id
                                          WHEN T1.service_group = 19 and T1.service_subgroup IS NULL
                                            THEN NULL
                                          WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                            THEN T1.service_id
                                          ELSE T1.event_id
                                     END
                                END
                        ) AS treatment_accept_children,

                    SUM(CASE WHEN not T1.is_children
                                  AND T1.is_accepted
                               THEN T1.count_days
                             ELSE 0
                        END
                        ) AS count_days_accept_adult,
                    SUM(CASE WHEN T1.is_children
                                  AND T1.is_accepted
                               THEN T1.count_days
                             ELSE 0
                        END
                        ) AS count_days_accept_children,

                    SUM(CASE WHEN not T1.is_children
                                  AND T1.is_accepted
                               THEN T1.uet
                             ELSE 0 END
                        ) AS uet_accept_adult,
                    SUM(CASE WHEN T1.is_children
                                  AND T1.is_accepted
                               THEN T1.uet
                             ELSE 0 END
                        ) AS uet_accept_children,


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
                                                    WHEN T1.service_group = 19 and T1.service_subgroup IS NULL
                                                      THEN NULL
                                                    WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                                      THEN T1.service_id
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
                    JOIN medical_organization mo
                       ON mo.id_pk = T1.organization_id
                GROUP BY mo.id_pk, T1.division_term
                '''.format(inner_query=DefectsPage.get_inner_query())
        return query

    @staticmethod
    def get_detail_query():
        query = '''
                SELECT
                    mo.id_pk,
                    T1.division_term,
                    T1.failure_cause,

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
                                                    WHEN T1.service_group in (19)
                                                         AND T1.service_subgroup is NULL
                                                      THEN NULL
                                                    WHEN T1.service_group = 19 AND T1.stomatology_reason = 14
                                                      THEN T1.service_id
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
                    JOIN medical_organization mo
                       ON mo.id_pk = T1.organization_id
                WHERE T1.is_excluded
                GROUP BY mo.id_pk, T1.division_term, T1.failure_cause
                '''.format(inner_query=DefectsPage.get_inner_query())
        return query

    @staticmethod
    def get_inner_query():
        query = '''
                SELECT
                    CASE WHEN T.term = 1
                           AND (T.service_group is null
                           OR T.service_group in (1, 2, 20))
                             THEN 'hospital'

                         WHEN T.service_group = 31
                             THEN 'hospital_ambulance'

                         WHEN T.service_group = 32
                             THEN 'coronary_angiography'

                         WHEN T.service_group = 40
                             THEN 'cerebral_angiography'

                         WHEN T.service_code in ('049023', '149023', '049028', '049031', '049034',
                                                 '049035', '049036', '049037', '049038', '049039',
                                                 '049040', '049041', '049042', '149028', '149031',
                                                 '149034', '149035', '149036', '149037', '149038',
                                                 '149039', '149040', '149041', '149042')
                             THEN 'gemodialis_hospital'

                         WHEN T.service_code in ('049024', '149024', '049044', '049047', '049050',
                                                 '149044', '149047', '149050')
                             THEN 'peritondialis_hospital'

                         WHEN T.term = 2
                           AND (T.service_group is null
                           OR T.service_group in (17, 28, 30))
                             THEN 'day_hospital'

                         WHEN T.service_code in ('049027', '049030', '049033', '149027', '149030', '149033')
                             THEN 'gemodialis_day_hospital'

                         WHEN T.service_code in ('049043', '049046', '049049', '149043', '149046', '149049')
                             THEN 'peritondialis_day_hospital'

                         WHEN T.is_policlinic_treatment
                             THEN 'policlinic_disease'

                         WHEN ((T.service_group IS NULL OR T.service_group = 24)
                                AND ((T.term = 3 AND T.service_reason in (2, 3, 8))
                                      OR (T.term = 3 AND  T.service_reason = 1
                                          AND not T.is_policlinic_treatment)
                                    )
                                )
                           OR T.service_group = 4
                             THEN 'policlinic_priventive'

                         WHEN T.term = 3
                           AND T.service_reason = 5
                             THEN 'policlinic_ambulance'

                         WHEN T.service_group = 9
                           AND T.service_code in (
                                  '019214', '019215', '019216',
                                  '019217', '019212', '019201'
                               )
                             THEN 'adult_exam'

                         WHEN T.term = 4 and (T.service_group != 43 or T.service_group IS NULL)
                             THEN 'ambulance'

                        WHEN T.term = 4 and T.service_group = 43
                             THEN 'trombolisis'

                         WHEN T.service_group = 29
                             THEN 'mrt'

                         WHEN T.service_code in ('049021', '149021', '049026', '049029',
                                                 '049032', '149026', '149029', '149032')
                             THEN 'gemodialis_policlinic'

                         WHEN T.service_code in ('049022', '149022', '049045', '049048',
                                                 '149045', '149048')
                             THEN 'peritondialis_policlinic'

                         WHEN T.service_group = 11
                           AND T.service_code in (
                                  '119057', '119058', '119059',
                                  '119060', '119061', '119062',
                                  '119064', '119065', '119066',
                                  '119080', '119081', '119082',
                                  '119083', '119084', '119085',
                                  '119086', '119087', '119088',
                                  '119089', '119090', '119091'
                               )
                             THEN 'children_exam'

                         WHEN T.service_group = 15
                           AND T.service_code in (
                                  '119111', '119110', '119109',
                                  '119107', '119106', '119105',
                                  '119104', '119103', '119102',
                                  '119101', '119119', '119120'
                               )
                             THEN 'prelim_children_exam'

                         WHEN T.service_group = 16
                           AND T.service_code = '119151'
                             THEN 'period_children_exam'

                         WHEN T.service_group in (25, 26, 12, 13)
                           AND T.service_code in (
                                  '019114', '019113', '019112', '019111',
                                  '019110', '019109', '019108', '019107', '019106',
                                  '019105', '019104', '019103', '019102', '119003',
                                  '119004', '119002', '119005', '119006', '119007',
                                  '119008', '119009', '119010', '119020', '119021',
                                  '119022', '119023', '119024', '119025', '119026',
                                  '119027', '119028', '119029', '119030', '119031',
                                  '119202', '119203', '119204', '119205', '119206',
                                  '119207', '119208', '119209', '119210', '119220',
                                  '119221', '119222', '119223', '119224', '119225',
                                  '119226', '119227', '119228', '119229', '119230',
                                  '119231',
                                  '019116', '019115', '019117',
                                  '019025', '019026', '019027', '019028'
                               )
                             THEN 'clinical_exam'

                         WHEN T.service_group in (7)
                            and T.service_code in (
                              '019021', '019023', '019022', '019024', '019025',
                              '019026', '019027', '019028',
                              '019002', '019003', '019004', '019005', '019006',
                              '019007', '019008', '019009', '019010', '019011',
                              '019012', '019013', '019014', '019015', '019016',
                              '019017', '019018', '019019',
                              '019020') and T.event_end_date >= '2015-06-01'
                             THEN 'clinical_exam'

                         WHEN T.service_group in (7)
                            and T.service_code in ('019001', '019021', '019023', '019022', '019024')
                            and T.event_end_date < '2015-06-01'
                             THEN 'clinical_exam'

                         WHEN T.service_group = 41
                           THEN 'usg'

                         WHEN T.service_group = 19
                           AND T.stomatology_reason in (12, 14)
                             THEN 'stom_disease'

                         WHEN T.service_group = 19
                           AND (T.stomatology_reason in (13, 17)
                                  OR T.stomatology_reason is NULL
                                )
                             THEN 'stom_ambulance'

                         ELSE T.service_code
                    END AS division_term,

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

                       (pe.term_fk = 3
                        AND ms.reason_fk = 1
                        AND (ms.group_fk is NULL OR ms.group_fk = 24)
                        AND (
                              SELECT
                                  COUNT(inner_ps.id_pk)
                              FROM provided_service inner_ps
                                  JOIN medical_service inner_ms
                                     ON inner_ms.id_pk = inner_ps.code_fk
                              WHERE
                                 inner_ps.event_fk = ps.event_fk
                                 AND (inner_ms.group_fk is NULL
                                      OR inner_ms.group_fk in (24))
                                 AND inner_ms.reason_fk = 1
                           )>1
                        ) AS is_policlinic_treatment,

                       (SELECT
                            DISTINCT MIN(inner_ms.subgroup_fk)
                        FROM medical_service inner_ms
                        WHERE
                           inner_ms.id_pk in (
                             SELECT
                                 inner_ps.code_fk
                             FROM provided_service inner_ps
                             WHERE
                                inner_ps.event_fk = ps.event_fk
                                AND inner_ps.start_date = ps.start_date
                                AND inner_ps.end_date = ps.end_date
                                AND inner_ps.payment_type_fk = ps.payment_type_fk
                           )
                           AND inner_ms.subgroup_fk is NOT NULL
                           AND inner_ms.group_fk = 19
                       ) AS stomatology_reason

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
                           AND mr.organization_code = %(organization)s
                           AND (ms.group_fk != 27
                                OR ms.group_fk is null
                                )
                           --and (me.id_pk <> 70 or me.id_pk is null)

                    ) AS T
        '''
        return query

    def get_data_general_dict(self):
        total = {}
        for data in self.data_general:
            division = data.division_term
            total[division] = {}
            for row_index, services_group in DefectsPage.SERVICES_GROUPS.get(division, []):
                if services_group == DefectsPage.VISIT:
                    total[division]['visit_all'] = data.visit_all_adult + data.visit_all_children
                    total[division]['visit_accept'] = data.visit_accept_adult + data.visit_accept_children
                    total[division]['visit_exclude'] = data.visit_exclude

                elif services_group == DefectsPage.TREATMENT:
                    total[division]['treatment_all'] = data.treatment_all_adult + data.treatment_all_children
                    total[division]['treatment_accept'] = data.treatment_accept_adult + data.treatment_accept_children
                    total[division]['treatment_exclude'] = data.treatment_exclude

        return total

    def print_page(self, sheet, parameters):
        sheet.write_cell(0, 3, u'Сводная справка  по  дефектам за ' + parameters.date_string)
        sheet.write_cell(3, 0, parameters.organization_code+' '+parameters.report_name)
        sheet.set_style(VALUE_STYLE)

        for data in self.data_general:
            division = data.division_term

            for row_index, services_group in DefectsPage.SERVICES_GROUPS.get(division, []):
                sheet.set_position(4 + row_index, 2)
                if services_group == DefectsPage.VISIT:
                    sheet.write(data.visit_all_adult, 'c')
                    sheet.write(data.visit_all_children, 'c')
                    sheet.write(data.visit_accept_adult, 'c')
                    sheet.write(data.visit_accept_children, 'c')
                    sheet.write(data.visit_exclude, 'c')

                elif services_group == DefectsPage.TREATMENT:
                    sheet.write(data.treatment_all_adult, 'c')
                    sheet.write(data.treatment_all_children, 'c')
                    sheet.write(data.treatment_accept_adult, 'c')
                    sheet.write(data.treatment_accept_children, 'c')
                    sheet.write(data.treatment_exclude, 'c')

                elif services_group == DefectsPage.COUNT_DAYS:
                    sheet.write(data.count_days_all_adult, 'c')
                    sheet.write(data.count_days_all_children, 'c')
                    sheet.write(data.count_days_accept_adult, 'c')
                    sheet.write(data.count_days_accept_children, 'c')
                    sheet.write(data.count_days_exclude, 'c')

                elif services_group == DefectsPage.UET:
                    sheet.write(data.uet_all_adult, 'c')
                    sheet.write(data.uet_all_children, 'c')
                    sheet.write(data.uet_accept_adult, 'c')
                    sheet.write(data.uet_accept_children, 'c')
                    sheet.write(data.uet_exclude, 'c')

        for data in self.data_detail:
            division = data.division_term
            failure_cause = data.failure_cause

            if failure_cause is None:
                continue

            column_index = DefectsPage.ERRORS_ORDER.index(failure_cause)

            for row_index, services_group in DefectsPage.SERVICES_GROUPS.get(division, []):
                sheet.set_position(4 + row_index, 7 + column_index)
                if services_group == DefectsPage.VISIT:
                    sheet.write(data.visit_exclude, 'c')

                elif services_group == DefectsPage.TREATMENT:
                    sheet.write(data.treatment_exclude, 'c')

                elif services_group == DefectsPage.COUNT_DAYS:
                    sheet.write(data.count_days_exclude, 'c')

                elif services_group == DefectsPage.UET:
                    sheet.write(data.uet_exclude, 'c')
