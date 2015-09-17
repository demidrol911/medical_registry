#! -*- coding: utf-8 -*-
from report_printer_clear.utils.page import ReportPage
from django.db import connection
from main.funcs import dictfetchall, howlong
from decimal import Decimal
from copy import deepcopy
from report_printer.excel_style import (
    VALUE_STYLE,
    TITLE_STYLE,
    TOTAL_STYLE,
    WARNING_STYLE
)


class GeneralServicesPage(ReportPage):
    COUNT_CELL_IN_ACT = 28
    STATISTIC_FIELDS = [
        ('patients_adult', int),
        ('patients_child', int),
        ('events_adult', int),
        ('events_child', int),
        ('services_adult', int),
        ('services_child', int),
        ('quantities_adult', Decimal),
        ('quantities_child', Decimal),
        ('tariffs_adult', Decimal),
        ('tariffs_child', Decimal),
        ('curation_coefficient_adult', Decimal),
        ('curation_coefficient_child', Decimal),
        ('stomatology_coefficient_adult', Decimal),
        ('stomatology_coefficient_child', Decimal),
        ('mobile_coefficient_adult', Decimal),
        ('mobile_coefficient_child', Decimal),
        ('fap_coefficient_adult', Decimal),
        ('fap_coefficient_child', Decimal),
        ('xray_or_neurology_coefficient_adult', Decimal),
        ('xray_or_neurology_coefficient_child', Decimal),
        ('cardiology_coefficient_adult', Decimal),
        ('cardiology_coefficient_child', Decimal),
        ('pso_to_rsc_or_pediatrics_coefficient_adult', Decimal),
        ('pso_to_rsc_or_pediatrics_coefficient_child', Decimal),
        ('cpg_coefficient_adult', Decimal),
        ('cpg_coefficient_child', Decimal),
        ('accepted_payment_adult', Decimal),
        ('accepted_payment_child', Decimal)
    ]

    CAPITATION_PRINT_TITLES = (
        u'0 - 1 год мужчина',
        u'0 - 1 год женщина',
        u'1 - 4 год мужчина',
        u'1 - 4 год женщина',
        u'5 - 17 год мужчина',
        u'5 - 17 год женщина',
        u'18 - 59 год мужчина',
        u'18 - 54 год женщина',
        u'60 лет и старше мужчина',
        u'55 лет и старше год женщина'
    )

    def __init__(self):
        self.data = None
        self.page_number = 0
        self.policlinic_capitation = None
        self.ambulance_capitation = None

    @howlong
    def calculate(self, parameters):
        query = self._construct_query()
        self.data = self._run_query(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code,
            payment_type=parameters.payment_type_list,
            department=parameters.departments
        ))

        if parameters.policlinic_capitation[0]:
            self.policlinic_capitation = self._convert_capitation(parameters.policlinic_capitation[1])
        else:
            self.policlinic_capitation = []
        print parameters.ambulance_capitation
        if parameters.ambulance_capitation[0]:
            self.ambulance_capitation = self._convert_capitation(parameters.ambulance_capitation[1])
        else:
            self.ambulance_capitation = []

    def _construct_query(self):
        query = '''
        WITH all_data AS (
            SELECT
                CASE WHEN pe.term_fk = 1 AND ms.group_fk IS NULL
                       THEN '1'
                     WHEN pe.term_fk = 1 AND ms.group_fk IS NOT NULL
                       THEN '10'
                     WHEN pe.term_fk = 2 AND ms.group_fk IS NULL
                       THEN '2'
                     WHEN pe.term_fk = 2 AND ms.group_fk IS NOT NULL
                       THEN '20'
                     WHEN pe.term_fk = 3 AND (ms.group_fk IS NULL OR ms.group_fk = 24)
                          AND ps.payment_kind_fk = 2
                       THEN '30'
                     WHEN pe.term_fk = 3 AND (ms.group_fk IS NULL OR ms.group_fk = 24)
                          AND (ps.payment_kind_fk != 2 OR ps.payment_kind_fk IS NULL)
                       THEN '31'
                     WHEN pe.term_fk = 3 AND ms.group_fk NOT IN (24, 19)
                       THEN '32'
                     WHEN ms.group_fk = 7
                       THEN '41'
                     WHEN ms.group_fk in (25, 26)
                       THEN '42'
                     WHEN pe.term_fk IS NULL AND ms.group_fk NOT IN (7, 25, 26)
                       THEN '43'
                     WHEN pe.term_fk = 4
                       THEN '5'
                     WHEN ms.group_fk = 19
                       THEN '60'
                END AS act_order,

                CASE
                    WHEN pe.term_fk IS NULL AND (ms.group_fk != 7 OR ms.group_fk IS NULL)
                      THEN 'Диспансеризация'
                    WHEN ms.group_fk = 7 AND pe.end_date >= '2015-06-01'
                      THEN 'Диспансеризация взрослых после 1.06.2015'
                    WHEN ms.group_fk = 7 AND pe.end_date < '2015-06-01'
                      THEN 'Диспансеризация взрослых до 1.06.2015'
                    WHEN pe.term_fk = 3 AND (ms.group_fk != 19 OR ms.group_fk IS NULL)
                      THEN (
                        CASE
                            WHEN ps.payment_kind_fk = 2
                              THEN 'Поликлиника (подушевое)'
                            ELSE 'Поликлиника (за единицу объёма)'
                        END
                    )
                    ELSE (
                        CASE WHEN pe.comment ILIKE '%%P493'
                               THEN mst_event.name || ' (федеральный бюджет)'
                             ELSE mst_event.name
                        END
                        )
                END AS term_group_name,

                CASE
                    WHEN ms.group_fk IS NULL OR ms.group_fk = 24
                      THEN (
                        CASE
                            WHEN pe.term_fk = 2
                              THEN term_day_hospital.name
                            WHEN pe.term_fk = 3
                              THEN (
                                -- Кейс для выбора наименование подгруппы в акте в поликлинике
                                CASE
                                    WHEN ms.reason_fk = 1
                                         AND (ms.group_fk IS NULL OR ms.group_fk = 24)
                                      THEN
                                        CASE
                                            WHEN (
                                                SELECT
                                                  COUNT(DISTINCT ps_i.id_pk)
                                                FROM provided_service ps_i
                                                  JOIN medical_service ms_i
                                                     ON ps_i.code_fk = ms_i.id_pk
                                                WHERE
                                                  ps_i.event_fk = pe.id_pk
                                                  AND (ms_i.group_fk = 24 OR ms_i.group_fk is null)
                                                  AND ms_i.reason_fk = 1
                                               ) > 1 THEN 'Поликлиника (заболевание)'
                                            WHEN (
                                                SELECT
                                                  COUNT(DISTINCT ps_i.id_pk)
                                                FROM provided_service ps_i
                                                  JOIN medical_service ms_i
                                                     ON ps_i.code_fk = ms_i.id_pk
                                                WHERE
                                                  ps_i.event_fk = pe.id_pk
                                                  AND (ms_i.group_fk = 24 OR ms_i.group_fk is null)
                                                  AND ms_i.reason_fk = 1
                                               ) = 1 THEN 'Поликлиника (разовые)'
                                            ELSE (
                                                SELECT
                                                  COUNT(DISTINCT ps_i.id_pk)
                                                FROM provided_service ps_i
                                                  JOIN medical_service ms_i
                                                     ON ps_i.code_fk = ms_i.id_pk
                                                WHERE
                                                  ps_i.event_fk = pe.id_pk
                                                  AND (ms_i.group_fk = 24 OR ms_i.group_fk is null)
                                                  AND ms_i.reason_fk = 1
                                            )::VARCHAR
                                        END
                                    WHEN ms.reason_fk = 2
                                      THEN 'Поликлиника (профосмотр)'
                                    WHEN ms.reason_fk = 3
                                      THEN 'Поликлиника (прививка)'
                                    WHEN ms.reason_fk = 5
                                      THEN 'Поликлиника (неотложка)'
                                    WHEN ms.reason_fk = 8
                                      THEN 'Поликлиника (с иными целями)'
                                END)
                        END)
                    WHEN ms.group_fk IS NOT NULL
                      THEN (
                        CASE
                            WHEN ms.group_fk = 7
                              THEN
                                CASE (
                                        SELECT
                                          code
                                        FROM provided_service
                                          JOIN medical_service
                                             ON code_fk = medical_service.id_pk
                                        WHERE
                                          event_fk = pe.id_pk
                                          AND code IN ('019021', '019023', '019022', '019024')
                                        LIMIT 1
                                     )
                                    WHEN '019021'
                                      THEN 'I группа диспанс. мужчины'
                                    WHEN '019022'
                                      THEN 'I группа диспанс. женщины'
                                    WHEN '019023'
                                      THEN 'II группа диспанс. мужчины'
                                    WHEN '019024'
                                      THEN 'II группа диспанс. женщины'
                                    ELSE 'Диспансеризация'
                                END
                            WHEN ms.group_fk = 19 OR ms.subgroup_fk IN (12, 13, 14, 17)
                              THEN 'Стоматология'
                            ELSE msg.name
                        END
                    )
                END AS term_subgroup_name,

                CASE WHEN ms.group_fk IS NULL
                          OR ms.group_fk = 24
                       THEN (
                         CASE
                            WHEN pe.term_fk in (1, 2)
                              THEN tp.name
                            WHEN pe.term_fk = 3
                              THEN md_policlinic.name
                            WHEN pe.term_fk = 4
                              THEN mssg.name
                            WHEN pe.term_fk IS NULL
                              THEN 'Поликлиника'
                            ELSE 'НЕИЗВЕСТНОЕ ОТДЕЛЕНИЕ'
                            END
                       )
                     WHEN ms.group_fk IS NOT NULL
                       THEN (
                         -- Разбивка стоматологии
                         CASE
                             WHEN ms.group_fk = 19
                               THEN (
                                 SELECT
                                    "name"
                                 FROM medical_service_subgroup
                                 WHERE id_pk = (
                                   SELECT
                                      MAX(subgroup_fk)
                                   FROM medical_service
                                     JOIN provided_service
                                        ON code_fk = medical_service.id_pk
                                   WHERE
                                     event_fk = pe.id_pk
                                     AND payment_type_fk = 2
                               )
                             )
                            -- Разбивка диспансеризации
                            WHEN ms.group_fk = 7
                              THEN (
                                CASE ms.code
                                    WHEN '019021'
                                      THEN 'Прием врача-терапевта итоговый (I группа - мужчины)'
                                    WHEN '019022'
                                      THEN 'Прием врача-терапевта итоговый  (I группа - женщины)'
                                    WHEN '019023'
                                      THEN 'Прием врача-терапевта итоговый  (II группа - мужчины)'
                                    WHEN '019024'
                                      THEN 'Прием врача-терапевта итоговый (II группа - женщины)'
                                    WHEN '019002'
                                      THEN 'Опрос (анкетирование)'
                                    ELSE 'Прочие услуги (ислледования, анализы)'
                                END)
                            WHEN ms.group_fk IN (11, 12, 13)
                              THEN (
                                CASE
                                    WHEN ms.subgroup_fk IS NULL
                                      THEN ms.name
                                    ELSE mssg.name || (
                                      CASE
                                          WHEN p.gender_fk = 1
                                            THEN ', мальчики'
                                          WHEN p.gender_fk = 2
                                            THEN ', девочки'
                                      END)
                                END)
                            WHEN ms.group_fk = 20
                              THEN ms.vmp_group || ' (' || tp.name || ') ' || ms.name
                            ELSE (
                              CASE
                                  WHEN ms.subgroup_fk IS NULL
                                    THEN ms.name
                                  ELSE mssg.name
                              END)
                         END)
                END AS profile_name,

                -- Всякие нужные для статистики данные
                ms.code like '1%%' AS is_children_profile,
                ms.group_fk AS service_group_id,
                ms.code AS service_code,
                ms.reason_fk AS service_reason_id,
                mr.organization_code AS organization_code,
                ROUND(ps.tariff, 2) AS service_tariff,
                ROUND(CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                           WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                           WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                      END, 2) AS service_accepted_payment,
                ROUND(ps.provided_tariff, 2) AS service_provided_tariff,

                CASE
                    WHEN ms.group_fk = 19
                      THEN ps.quantity*ms.uet
                    ELSE ps.quantity
                END AS service_quantity,

                p.id_pk AS patient_id,
                pe.id_pk AS event_id,
                ps.id_pk AS service_id,

                CASE WHEN ms.group_fk = 19 AND ms.subgroup_fk IS NULL
                       THEN True
                     ELSE False
                END AS is_stomatology_services,

                CASE
                    WHEN (pe.term_fk = 3 AND ms.reason_fk = 1 AND (ms.group_fk = 24 OR ms.group_fk is null)
                         AND (SELECT
                                 COUNT(DISTINCT ps_i.id_pk)
                              FROM provided_service ps_i
                                JOIN medical_service ms_i
                                   ON ps_i.code_fk = ms_i.id_pk
                              WHERE
                                ps_i.event_fk = pe.id_pk
                                AND (ms_i.group_fk = 24 OR ms_i.group_fk is null)
                                AND ms_i.reason_fk = 1
                              ) > 1
                            )
                         OR (ms.group_fk = 19 AND ms.subgroup_fk = 12)
                      THEN True
                    ELSE False
                END AS is_treatment,

                CASE
                    WHEN (pe.term_fk = 3 AND ps.payment_kind_fk = 2) or pe.term_fk = 4
                      THEN True
                    ELSE False
                END AS is_capitation,

                ----- Коеффициенты
                -- Коеффициент Курации
                ROUND(CASE
                          WHEN psc_curation.id_pk IS NOT NULL
                               AND psc.coefficient_fk IN (8, 9, 10, 11, 12)
                            THEN 0.25*ps.tariff*tc.value
                          ELSE 0
                      END, 2) +
                ROUND(CASE
                          WHEN psc_curation.id_pk IS NOT NULL
                            THEN 0.25*ps.tariff
                          ELSE 0
                      END, 2) AS curation_coefficient,


                -- Неотложка у зубника
                ROUND(CASE WHEN tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS stomatology_coefficient,


                -- Мобильные бригады
                ROUND(CASE WHEN tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS mobile_coefficient,

                -- АООД рентгенотерапия
                ROUND(CASE WHEN tc.id_pk = 19 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS xray_coefficient,

                -- КПГ неврология
                ROUND(CASE WHEN tc.id_pk = 16 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS neurology_coefficient,

                -- Клинико-профильные группы
                ROUND(CASE WHEN tc.id_pk in (8, 9, 10, 11, 12) THEN tc.value*ps.tariff ELSE 0 END, 2) AS cpg_coefficient,

                -- КПГ кардиология
                ROUND(CASE WHEN tc.id_pk = 17 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS cardiology_coefficient,

                -- КПГ Педиатрия
                ROUND(CASE WHEN tc.id_pk = 18 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS pediatrics_coefficient,

                -- Перевод из ПСО в РСЦ
                ROUND(CASE WHEN tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END, 2) AS pso_to_rsc_coefficient

            FROM provided_service ps
              JOIN provided_event pe
                 ON pe.id_pk = ps.event_fk
              JOIN medical_register_record mrr
                 ON mrr.id_pk = pe.record_fk
              JOIN medical_register mr
                 ON mr.id_pk = mrr.register_fk
              JOIN medical_service ms
                 ON ms.id_pk = ps.code_fk
              JOIN patient p
                 ON p.id_pk = mrr.patient_fk
              JOIN medical_organization department
                 ON department.id_pk = ps.department_fk

              LEFT JOIN medical_division md_day_hospital
                 ON md_day_hospital.id_pk = pe.division_fk
              LEFT join medical_service_term term_day_hospital
                 ON term_day_hospital.id_pk = md_day_hospital.term_fk
              LEFT join medical_service_term mst_day_hospital
                 ON mst_day_hospital.id_pk = md_day_hospital.term_fk
              LEFT JOIN tariff_profile tp
                 ON tp.id_pk = ms.tariff_profile_fk
              LEFT JOIN medical_division md_policlinic
                 ON md_policlinic.id_pk = ms.division_fk

            LEFT JOIN medical_service_term mst_event
                ON mst_event.id_pk = pe.term_fk
            LEFT JOIN medical_service_reason msr
                ON msr.id_pk = ms.reason_fk

            LEFT join medical_service_group msg
                ON msg.id_pk = ms.group_fk
            LEFT JOIN medical_service_subgroup mssg
                ON mssg.id_pk = ms.subgroup_fk

            LEFT JOIN provided_service_coefficient psc_curation
                ON psc_curation.service_fk = ps.id_pk
                   AND psc_curation.coefficient_fk = 7
            LEFT JOIN provided_service_coefficient psc
                ON psc.service_fk = ps.id_pk
                   AND psc.coefficient_fk != 7
            LEFT JOIN tariff_coefficient tc
                ON tc.id_pk = psc.coefficient_fk
            WHERE mr.is_active
              AND mr.year = %(year)s
              AND mr.period = %(period)s
              AND mr.organization_code = %(organization)s
              AND (ms.group_fk != 27 or ms.group_fk IS NULL)
              AND ps.payment_type_fk = ANY(%(payment_type)s)
              AND department.old_code = ANY(%(department)s)
        )

        SELECT
            act_order,
            term_group_name,
            term_subgroup_name,
            profile_name,

            COALESCE(COUNT(DISTINCT CASE WHEN NOT is_children_profile THEN patient_id END), 0) AS patients_adult,
            COALESCE(COUNT(DISTINCT CASE WHEN is_children_profile THEN patient_id END), 0) AS patients_child,

            COALESCE(COUNT(DISTINCT CASE WHEN NOT is_children_profile AND is_treatment THEN event_id END), 0) AS events_adult,
            COALESCE(COUNT(DISTINCT CASE WHEN is_children_profile AND is_treatment THEN event_id END), 0) AS events_child,

            COALESCE(COUNT(DISTINCT CASE WHEN NOT is_children_profile
                                           THEN (
                                               CASE WHEN is_stomatology_services
                                                      THEN NULL
                                                    ELSE service_id
                                               END)
                                    END), 0) AS services_adult,
            COALESCE(COUNT(DISTINCT CASE WHEN is_children_profile
                                           THEN (
                                               CASE WHEN is_stomatology_services
                                                      THEN NULL
                                                    ELSE service_id
                                               END)
                                    END), 0) AS services_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN service_quantity END), 0) AS quantities_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN service_quantity END), 0) AS quantities_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN service_tariff END), 0) AS tariffs_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN service_tariff END), 0) AS tariffs_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN curation_coefficient END), 0) AS curation_coefficient_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN curation_coefficient END), 0) AS curation_coefficient_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN stomatology_coefficient END), 0) AS stomatology_coefficient_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN stomatology_coefficient END), 0) AS stomatology_coefficient_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN mobile_coefficient END), 0) AS mobile_coefficient_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN mobile_coefficient END), 0) AS mobile_coefficient_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN cpg_coefficient END), 0) AS cpg_coefficient_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN cpg_coefficient END), 0) AS cpg_coefficient_child,

            COALESCE(SUM(CASE
                             WHEN NOT is_children_profile
                               THEN (
                                  CASE
                                      WHEN organization_code = '280005'
                                        THEN xray_coefficient
                                      WHEN organization_code = '280064'
                                        THEN neurology_coefficient
                                      ELSE 0
                                  END)
                             ELSE 0
                         END), 0)  AS xray_or_neurology_coefficient_adult,

            COALESCE(SUM(CASE
                             WHEN is_children_profile
                               THEN (
                                  CASE
                                      WHEN organization_code = '280005'
                                        THEN xray_coefficient
                                      WHEN organization_code = '280064'
                                        THEN neurology_coefficient
                                      ELSE 0
                                  END)
                             ELSE 0
                         END), 0) AS xray_or_neurology_coefficient_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile THEN cardiology_coefficient END), 0) AS cardiology_coefficient_adult,
            COALESCE(SUM(CASE WHEN is_children_profile THEN cardiology_coefficient END), 0) AS cardiology_coefficient_child,

            COALESCE(SUM(CASE
                             WHEN NOT is_children_profile
                               THEN (
                                  CASE
                                      WHEN organization_code = '280064'
                                        THEN pediatrics_coefficient
                                      ELSE pso_to_rsc_coefficient
                                  END)
                             ELSE 0
                         END), 0)  AS pso_to_rsc_or_pediatrics_coefficient_adult,

            COALESCE(SUM(CASE
                             WHEN is_children_profile
                               THEN (
                                  CASE
                                      WHEN organization_code = '280064'
                                        THEN pediatrics_coefficient
                                      ELSE pso_to_rsc_coefficient
                                  END)
                             ELSE 0
                         END), 0) AS pso_to_rsc_or_pediatrics_coefficient_child,


            0 AS fap_coefficient_adult,
            0 AS fap_coefficient_child,

            COALESCE(SUM(CASE WHEN NOT is_children_profile AND NOT is_capitation THEN service_accepted_payment END), 0) AS accepted_payment_adult,
            COALESCE(SUM(CASE WHEN is_children_profile AND NOT is_capitation THEN service_accepted_payment END), 0) AS accepted_payment_child

        FROM all_data

        GROUP BY act_order, term_group_name, term_subgroup_name, profile_name
        ORDER BY act_order, term_group_name, term_subgroup_name NULLS FIRST, profile_name
        '''

        return query

    def _run_query(self, query, parameters):
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        return dictfetchall(cursor)

    def _convert_capitation(self, capitation_data):
        convert_capitation = [
            deepcopy(self._reset_total())
            for _ in range(0, 10)]

        age_groups = [
            'men1', 'fem1', 'men2', 'fem2', 'men3', 'fem3',
            'men4', 'fem4', 'men5', 'fem5'
        ]
        for index, age_group in enumerate(age_groups):
            item = capitation_data[age_group]
            if age_group in ('men1', 'fem1', 'men2', 'fem2', 'men3', 'fem3'):
                convert_capitation[index]['patients_child'] = item['population']
                convert_capitation[index]['quantities_child'] = item['basic_tariff']
                convert_capitation[index]['tariffs_child'] = item['tariff']
                convert_capitation[index]['fap_coefficient_child'] = item['coeff']
                convert_capitation[index]['accepted_payment_child'] = item['accepted']
            if age_group in ('men4', 'fem4', 'men5', 'fem5'):
                convert_capitation[index]['patients_adult'] = item['population']
                convert_capitation[index]['quantities_adult'] = item['basic_tariff']
                convert_capitation[index]['tariffs_adult'] = item['tariff']
                convert_capitation[index]['fap_coefficient_adult'] = item['coeff']
                convert_capitation[index]['accepted_payment_adult'] = item['accepted']

        return convert_capitation

    def print_page(self, sheet, parameters):
        sheet.write_cell(0, 3, u'Сводная справка  по  дефектам за ' + parameters.date_string)
        sheet.write_cell(3, 0, parameters.organization_code+' '+parameters.report_name)
        sheet.write_cell(2, 0, parameters.organization_code+' '+parameters.report_name)
        sheet.write_cell(2, 9, u'за ' + parameters.date_string)
        sheet.write_cell(3, 0, u'Частичный реестр: %s' % ','.join(parameters.partial_register))
        sheet.set_position(7, 0)

        latest_term_group = ''
        latest_term_subgroup = ''
        total_by_term_group = self._reset_total()
        total_by_mo = self._reset_total()
        totals_by_term = {
            u'Поликлиника (подушевое)': {u'on': False, u'total': self._reset_total()},
            u'Поликлиника (за единицу объёма)': {u'on': False, u'total': self._reset_total()},
            u'Диспансеризация взрослых после 1.06.2015': {u'on': False, u'total': self._reset_total()},
            u'Диспансеризация взрослых до 1.06.2015': {u'on': False, u'total': self._reset_total()},
            u'Скорая помощь': {u'on': False, u'total': self._reset_total()}
        }

        for item in self.data:
            is_changed_term_group = latest_term_group != item['term_group_name']
            is_changed_term_subgroup = latest_term_subgroup != item['term_subgroup_name']
            if (is_changed_term_group or is_changed_term_subgroup) and (latest_term_group != ''):
                self._print_total(sheet, u'Итого', total_by_term_group)
                self._accumulate_total(total_by_term_group, total_by_mo)
                total_by_term_group = self._reset_total()

            # включить аккумулятор
            if item['term_group_name'] in totals_by_term \
                    and not totals_by_term[item['term_group_name']][u'on']:
                totals_by_term[item['term_group_name']][u'on'] = True
            # аккумулируем
            if item['term_group_name'] in totals_by_term \
                    and totals_by_term[item['term_group_name']][u'on']:
                self._accumulate_total(item, totals_by_term[item['term_group_name']][u'total'])
            # выключить аккумулятор
            if is_changed_term_group \
                    and latest_term_group in totals_by_term \
                    and totals_by_term[latest_term_group][u'on']:
                totals_by_term[latest_term_group][u'on'] = False
                self._print_total(sheet, u'Итого по ' + latest_term_group,
                                  totals_by_term[latest_term_group][u'total'])

            if is_changed_term_group:
                latest_term_group = item['term_group_name']
                sheet.set_style(TITLE_STYLE)
                if latest_term_group in (u'Диспансеризация', u'Поликлиника'):
                    pass
                else:
                    sheet.write(latest_term_group, 'r', self.COUNT_CELL_IN_ACT)

            if is_changed_term_subgroup:
                latest_term_subgroup = item['term_subgroup_name']
                sheet.set_style(TITLE_STYLE)
                sheet.write(latest_term_subgroup, 'r', self.COUNT_CELL_IN_ACT)

            sheet.set_style(VALUE_STYLE)
            sheet.write(item['profile_name'], 'c')
            self._print_item(sheet, item)
            self._accumulate_total(item, total_by_term_group)

        self._accumulate_total(total_by_term_group, total_by_mo)

        self._print_total(sheet, u'Итого', total_by_term_group)
        if latest_term_group in totals_by_term \
                and totals_by_term[latest_term_group][u'on']:
            totals_by_term[latest_term_group][u'on'] = False
            self._print_total(sheet, u'Итого по ' + latest_term_group,
                              totals_by_term[latest_term_group][u'total'])
        self._print_total(sheet, u'Итого по МО', total_by_mo)

        total_by_policlinic_capitation = self._accumulate_capitaion_total(self.policlinic_capitation)
        total_by_ambulance_capitation = self._accumulate_capitaion_total(self.ambulance_capitation)
        self._accumulate_total(total_by_policlinic_capitation, total_by_mo)
        self._accumulate_total(total_by_ambulance_capitation, total_by_mo)

        self._print_capitation(sheet, u'Подушевой норматив по амбул. мед. помощи', self.policlinic_capitation)
        self._print_total(sheet, u'Итого по подушевому нормативу', total_by_policlinic_capitation)
        self._print_capitation(sheet, u'Подушевой норматив по скорой мед. помощи', self.ambulance_capitation)
        self._print_total(sheet, u'Итого по подушевому нормативу', total_by_ambulance_capitation)
        if self.policlinic_capitation or self.ambulance_capitation:
            self._print_total(sheet, u'Итого по МО c подушевым', total_by_mo)

    def _reset_total(self):
        return deepcopy({field_name: field_type(0) for field_name, field_type in self.STATISTIC_FIELDS})

    def _accumulate_total(self, subtotal, total):
        for field_name, field_type in self.STATISTIC_FIELDS:
            total[field_name] = field_type(total[field_name]) + field_type(subtotal[field_name] or 0)

    def _accumulate_capitaion_total(self, capitation_data):
        total = self._reset_total()
        for item in capitation_data:
            self._accumulate_total(item, total)
        return total

    def _print_item(self, sheet, item):
        for field_name, _ in self.STATISTIC_FIELDS[:-1]:
            sheet.write(item[field_name], 'c')
        sheet.write(item[self.STATISTIC_FIELDS[-1][0]], 'r')

    def _print_total(self, sheet, title, total):
        if total == self._reset_total():
            pass
        else:
            sheet.set_style(TOTAL_STYLE)
            sheet.write(title, 'c')
            self._print_item(sheet, total)
            sheet.increment_row_index()

    def _print_capitation(self, sheet, title, capitation_data):
        if capitation_data:
            sheet.set_style(TITLE_STYLE)
            sheet.write(title, 'r', self.COUNT_CELL_IN_ACT)
            sheet.set_style(VALUE_STYLE)
            for index, field_name in enumerate(self.CAPITATION_PRINT_TITLES):
                sheet.write(field_name, 'c')
                self._print_item(sheet, capitation_data[index])
