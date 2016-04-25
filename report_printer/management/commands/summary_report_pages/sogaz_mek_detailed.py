#! -*- coding: utf-8 -*-
from main.funcs import howlong
from tfoms import func
from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization, ProvidedService
from report_printer.management.commands.defects_report_pages.defects import DefectsPage
from tfoms.func import get_mo_info


class SogazMekDetailedPage(ReportPage):

    def __init__(self):
        self.data = None
        self.hospital_services = None
        self.day_hospital_services = None
        self.policlinic_services = None
        self.ambulance_services = None
        self.pa_services = None
        self.page_number = 4

    @howlong
    def calculate(self, parameters):
        self.data = None
        self.hospital_services = None
        self.day_hospital_services = None
        self.policlinic_services = None
        self.ambulance_services = None
        self.pa_services = None

        defects_page = DefectsPage()
        defects_page.calculate(parameters)
        defects_data = defects_page.get_data_general_dict()

        hospital = (
            ('hospital', 'visit'),
            ('coronary_angiography', 'visit'),
            ('cerebral_angiography', 'visit'),
            ('gemodialis_hospital', 'treatment'),
            ('peritondialis_hospital', 'treatment')
        )

        day_hospital = (
            ('day_hospital', 'visit'),
            ('gemodialis_day_hospital', 'treatment'),
            ('peritondialis_day_hospital', 'treatment')
        )
        policlinic = (
            ('hospital_ambulance', 'visit'),
            ('policlinic_disease', 'treatment'),
            ('policlinic_priventive', 'visit'),
            ('policlinic_ambulance', 'visit'),
            ('adult_exam', 'treatment'),
            ('mrt', 'visit'),
            ('gemodialis_policlinic', 'treatment'),
            ('peritondialis_policlinic', 'treatment'),
            ('children_exam', 'treatment'),
            ('prelim_children_exam', 'treatment'),
            ('period_children_exam', 'treatment'),
            ('clinical_exam', 'treatment'),
            ('stom_disease', 'treatment'),
            ('stom_ambulance', 'visit'),
            ('usg', 'visit')
        )
        ambulance = (
            ('ambulance', 'visit'),
            ('trombolisis', 'visit')
        )

        total_fiels = (
            ('inv_count_hosp', hospital, 'all'),
            ('inv_count_day_hosp', day_hospital, 'all'),
            ('inv_count_policlinic', policlinic, 'all'),
            ('inv_count_ambulance', ambulance, 'all'),

            ('accept_count_hosp', hospital, 'accept'),
            ('accept_count_day_hosp', day_hospital, 'accept'),
            ('accept_count_policlinic', policlinic, 'accept'),
            ('accept_count_ambulance', ambulance, 'accept'),

            ('sanc_count_hosp', hospital, 'exclude'),
            ('sanc_count_day_hosp', day_hospital, 'exclude'),
            ('sanc_count_policlinic', policlinic, 'exclude'),
            ('sanc_count_ambulance', ambulance, 'exclude'),
        )

        self.data = dict()

        for total_field, terms, payment_type in total_fiels:
            self.data[total_field] = 0
            for term, field in terms:
                if term in defects_data:
                    self.data[total_field] += defects_data[term][field + '_' + payment_type]

        query = SogazMekDetailedPage.get_query_statistics()
        stat_obj = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))[0]

        self.data['inv_sum_tariff'] = stat_obj.inv_sum_tariff
        self.data['inv_sum_tariff_other_mo'] = 0
    
        ### Предъявленные услуги
    
        # Сумма предъявленная рассчётная
        self.data['inv_sum_tariff_mo'] = stat_obj.inv_sum_tariff_mo + \
            parameters.policlinic_capitation_total + \
            parameters.ambulance_capitation_total
    
        self.data['inv_sum_tariff_all'] = self.data['inv_sum_tariff_mo']
    
        # Предъявленные реестры счетов за стационар
        self.data['inv_sum_tariff_hosp'] = stat_obj.inv_sum_tariff_hosp
    
        # Предъяыленные реестры счетов за дневной стационар
        self.data['inv_sum_tariff_day_hosp'] = stat_obj.inv_sum_tariff_day_hosp
    
        # Предъявленные реестры счетов за поликлинику
        self.data['inv_sum_tariff_policlinic'] = stat_obj.inv_sum_tariff_policlinic
    
        # Предъявленные реестры счетов по скорой помощи
        self.data['inv_sum_tariff_ambulance'] = stat_obj.inv_sum_tariff_ambulance
    
        ### Принятые услуги
    
        # Сумма принятая к оплате (без подушевого)
        self.data['accept_sum_tariff'] = stat_obj.accept_sum_tariff
    
        # Подушевое по поликлинике
        self.data['accept_sum_policlinic_tariff_capitation'] = parameters.policlinic_capitation_total
    
        # Подушевое по скорой
        self.data['accept_sum_ambulance_tariff_capitation'] = parameters.ambulance_capitation_total

        # Флюорография
        self.data['accept_sum_fluorography'] = parameters.fluorography_total
    
        self.data['accept_sum_tariff_other_mo'] = 0
    
        # Сумма принятая к оплате (с подушевым)
        self.data['accept_sum_tariff_mo'] = self.data['accept_sum_tariff'] +\
            parameters.policlinic_capitation_total + \
            parameters.ambulance_capitation_total + parameters.fluorography_total
    
        # Количество принятых услуг (в акте)
        self.data['accept_count_all'] = self.data['accept_count_hosp'] + self.data['accept_count_day_hosp'] + \
            self.data['accept_count_policlinic'] + self.data['accept_count_ambulance']
        self.data['accept_sum_tariff_all'] = self.data['accept_sum_tariff_mo']
    
        # Принятые реестры счетов за стационар
        self.data['accept_sum_tariff_hosp'] = stat_obj.accept_sum_tariff_hosp
    
        # Принятые реестры отчётов за дневной стационар
        self.data['accept_sum_tariff_day_hosp'] = stat_obj.accept_sum_tariff_day_hosp
    
        # Принятые реестры отчётов за поликлинику
        self.data['accept_sum_tariff_policlinic'] = stat_obj.accept_sum_tariff_policlinic + \
            parameters.policlinic_capitation_total

        self.data['accept_sum_tariff_ambulance'] = stat_obj.accept_sum_tariff_ambulance + \
            parameters.ambulance_capitation_total
    
        ### Снятые с оплаты
    
        # Непринятые к оплате (без подушевого)
        self.data['sanc_sum_tariff'] = stat_obj.sanc_sum_tariff
    
        # Не принятые реестры счетов за стационар
        self.data['sanc_sum_tariff_hosp'] = stat_obj.sanc_sum_tariff_hosp
    
        # Не принятые реестры за дневной стационар
        self.data['sanc_sum_tariff_day_hosp'] = stat_obj.sanc_sum_tariff_day_hosp
    
        # Не принятые реестры за поликлинику
        self.data['sanc_sum_tariff_policlinic'] = stat_obj.sanc_sum_tariff_policlinic
    
        # Не принятые реестры по скорой помощи
        self.data['sanc_sum_tariff_ambulance'] = 0
    
        # Не принятые услуги сверх объема
        self.data['pa_count'] = stat_obj.pa_count
        self.data['pa_sum_tariff'] = stat_obj.pa_sum_tariff
    
        # Не принятые услуги сверх объёма за стационар
        self.data['pa_sum_tariff_hosp'] = stat_obj.pa_sum_tariff_hosp
    
        # Не принятые услуги сверх объёма за дневной стационар
        self.data['pa_sum_tariff_day_hosp'] = stat_obj.pa_sum_tariff_day_hosp
    
        # Не принятые услуги сверх объёма за поликлинику
        self.data['pa_sum_tariff_policlinic'] = stat_obj.pa_sum_tariff_policlinic
    
        # Не подлежит оплате
        self.data['sanc_count_all'] = self.data['sanc_count_hosp'] + self.data['sanc_count_day_hosp'] + \
            self.data['sanc_count_policlinic'] + self.data['sanc_count_ambulance']
        self.data['sanc_sum_tariff_all'] = stat_obj.sanc_sum_tariff_all

        self.hospital_services = ProvidedService.objects.raw(
            SogazMekDetailedPage.get_sanctions_query('hospital'),
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            )
        )

        self.day_hospital_services = ProvidedService.objects.raw(
            SogazMekDetailedPage.get_sanctions_query('day_hospital'),
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            )
        )

        self.policlinic_services = ProvidedService.objects.raw(
            SogazMekDetailedPage.get_sanctions_query('policlinic'),
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            )
        )

        self.ambulance_services = ProvidedService.objects.raw(
            SogazMekDetailedPage.get_sanctions_query('ambulance'),
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            )
        )

        self.pa_services = ProvidedService.objects.raw(
            SogazMekDetailedPage.get_sanctions_query('', is_include_pa=True),
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            )
        )

    @staticmethod
    def get_query_statistics():
        query = '''
                SELECT
                    mo.id_pk,
                    -- Поданные услуги --
                    SUM(T.tariff) AS inv_sum_tariff,  -- сумма предъявленная по основному тарифу

                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                               THEN T.accepted_payment
                             ELSE 0
                        END) +
                    SUM(CASE WHEN T.is_not_paid AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS inv_sum_tariff_mo,    -- сумма предъявленная рассчётная

                    SUM(CASE WHEN T.is_hospital
                               THEN T.tariff
                             ELSE 0
                        END) AS inv_sum_tariff_hosp,  -- сумма по тарифу в стационаре

                    SUM(CASE WHEN T.is_day_hospital
                               THEN T.tariff
                             ELSE 0
                        END) AS inv_sum_tariff_day_hosp, -- сумма по тарифу в дневном стационаре

                    SUM(CASE WHEN T.is_policlinic
                               THEN T.tariff
                             ELSE 0
                        END) AS inv_sum_tariff_policlinic, -- сумма по тарифу в поликлинике

                    SUM(CASE WHEN T.is_ambulance
                               THEN T.tariff
                             ELSE 0
                        END) AS inv_sum_tariff_ambulance, -- сумма по тарифу в скорой

                    -- Принятые услуги
                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                               THEN T.accepted_payment
                             ELSE 0
                        END) AS accept_sum_tariff,

                    SUM(CASE WHEN T.is_paid AND T.is_hospital
                               THEN T.accepted_payment
                             ELSE 0
                        END) AS accept_sum_tariff_hosp, -- принятая сумма в стационаре

                    SUM(CASE WHEN T.is_paid AND T.is_day_hospital
                               THEN T.accepted_payment
                             ELSE 0
                        END) AS accept_sum_tariff_day_hosp, -- принятая сумма в дневном стационаре

                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                                  AND T.is_policlinic
                               THEN T.accepted_payment
                             ELSE 0
                        END) AS accept_sum_tariff_policlinic, -- принятая сумма по поликлинике

                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                                  AND T.is_ambulance
                               THEN T.accepted_payment
                             ELSE 0
                        END) AS accept_sum_tariff_ambulance, -- принятая сумма по скорой

                    -- Не принятые услуги
                    SUM(CASE WHEN T.is_not_paid AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sanc_sum_tariff,   -- сумма санкциий

                    SUM(CASE WHEN T.is_not_paid AND T.is_not_pa
                                  AND T.is_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sanc_sum_tariff_hosp, -- сумма снятая по стационару

                    SUM(CASE WHEN T.is_not_paid AND T.is_not_pa
                                  AND T.is_day_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sanc_sum_tariff_day_hosp, -- сумма снятая по дневному стационару

                    SUM(CASE WHEN T.is_not_paid AND T.is_not_pa AND T.is_policlinic
                                  AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sanc_sum_tariff_policlinic, -- сумма снятая по поликлинике

                    -- Услуги сняты сверх объёма
                    COUNT(CASE WHEN T.is_not_paid AND T.is_pa
                                 THEN T.event_id END
                          ) AS pa_count, -- количество санкций сверх объёма
                    SUM(CASE WHEN T.is_not_paid AND T.is_pa
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS pa_sum_tariff, -- сумма санкций сверх объёма

                    SUM(CASE WHEN T.is_not_paid AND T.is_pa
                                  AND T.is_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS pa_sum_tariff_hosp, -- сумма санкций сверх объёма по стациоанру

                    SUM(CASE WHEN T.is_not_paid AND T.is_pa
                                  AND T.is_day_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS pa_sum_tariff_day_hosp, -- сумма санкций сверх объёма по дневному стационару

                    SUM(CASE WHEN T.is_not_paid AND T.is_pa
                                  AND T.is_policlinic
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS pa_sum_tariff_policlinic, -- сумма санкций сверх объёма по поликлинике

                    -- Не подлежит к оплате (итоговая)
                    SUM(CASE WHEN T.is_not_paid AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sanc_sum_tariff_all
                FROM (
                    SELECT
                         pe.id_pk AS event_id,
                         ps.id_pk AS service_id,
                         mo.id_pk AS organization,
                         ps.payment_type_fk = 3 AS is_not_paid,
                         ps.payment_type_fk = 2 AS is_paid,
                         ps.tariff AS tariff,
                         ps.accepted_payment AS accepted_payment,
                         ps.provided_tariff AS provided_tariff,

                         ps.payment_kind_fk in (1, 3) AS is_tariff,

                         pe.term_fk = 1
                         AND (ms.group_fk != 31 OR ms.group_fk is null) AS is_hospital,
                         pe.term_fk = 2 AS is_day_hospital,
                         pe.term_fk = 3 OR pe.term_fk is NULL OR ms.group_fk = 31 AS is_policlinic,
                         pe.term_fk = 4 AS is_ambulance,

                        (ms.group_fk != 19 OR ms.group_fk is NULL) OR
                        (ms.group_fk = 19 AND ms.subgroup_fk is not NULL) AS is_event,
                        (ms.group_fk in (25, 26)) AS is_phase_exam,

                        ms.group_fk = 19 AND ms.subgroup_fk != 12 AS is_stomatology,

                        (
                           SELECT
                               MAX(ms1.subgroup_fk)
                           FROM provided_service ps1
                               JOIN medical_service ms1
                                  ON ps1.code_fk = ms1.id_pk
                           WHERE ps1.event_fk = ps.event_fk
                                 AND ms1.group_fk = 19
                        ) is NULL AND ms.group_fk = 19
                        OR (ms.group_fk = 7 AND ms.subgroup_fk = 5) AS is_not_count,

                        pss.error_fk != 75 AS is_not_pa,
                        pss.error_fk = 75 AS is_pa

                    FROM medical_register mr
                        JOIN medical_register_record mrr
                           ON mr.id_pk = mrr.register_fk
                        JOIN provided_event pe
                           ON mrr.id_pk = pe.record_fk
                        JOIN provided_service ps
                           ON ps.event_fk = pe.id_pk
                        JOIN medical_organization mo
                           ON mo.id_pk = ps.organization_fk
                        JOIN medical_service ms
                           ON ms.id_pk = ps.code_fk
                        LEFT JOIN provided_service_sanction pss
                           ON pss.service_fk = ps.id_pk and pss.error_fk = (
                                SELECT
                                    pss1.error_fk
                                FROM provided_service_sanction pss1
                                    JOIN medical_error me1 ON me1.id_pk = pss1.error_fk
                                WHERE pss1.is_active
                                      AND pss1.service_fk = ps.id_pk
                                ORDER BY me1.weight DESC LIMIT 1
                          )
                    WHERE mr.is_active
                          AND mr.year = %(year)s
                          AND mr.period = %(period)s
                          AND mr.organization_code = %(organization)s
                          AND ((pss.id_pk is not NULL AND pss.is_active) OR pss.id_pk is NULL)
                          AND (ms.group_fk != 27 OR ms.group_fk is NULL)
                     ) AS T
                     JOIN medical_organization mo
                         ON T.organization = mo.id_pk
                GROUP BY mo.id_pk
                '''
        return query

    @staticmethod
    def get_sanctions_query(term, is_include_pa=False):
        query = """
            SELECT
                ps.id_pk, pe.id_pk AS event_pk,
                dep.old_code AS dep_old_code,
                mrr.id AS record_id,
                mr.period AS period,
                pt.insurance_policy_number AS insurance_policy_number,
                pt.insurance_policy_series AS insurance_policy_series,
                ps.provided_tariff AS provided_tariff,
                pe.term_fk AS term,
                md.code  AS division_code,
                msp.code AS profile_code,
                me.id_pk AS error_id,
                (ps.payment_kind_fk = 2 OR (pe.term_fk = 4 and ps.payment_kind_fk = 2)) AS is_capitation
            FROM medical_register mr
                JOIN medical_register_record mrr
                   ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                   ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                   ON ps.event_fk=pe.id_pk
                JOIN patient pt
                   ON pt.id_pk = mrr.patient_fk
                JOIN medical_organization dep
                   ON dep.id_pk = ps.department_fk
                JOIN medical_service ms
                   ON ms.id_pk = ps.code_fk
                LEFT JOIN medical_division md
                   ON md.id_pk = ps.division_fk
                LEFT JOIN medical_service_profile msp
                   ON msp.id_pk = ps.profile_fk
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
                   ON me.id_pk = COALESCE((SELECT me1.parent_fk
                                          FROM medical_error me1
                                          WHERE me1.id_pk = pss.error_fk
                                               AND me1.parent_fk IS NOT NULL),
                                          pss.error_fk)
            WHERE mr.is_active
                  AND mr.year = %(year)s
                  AND mr.period = %(period)s
                  AND mr.organization_code = %(organization)s
                  AND pss.is_active
                  AND ps.payment_type_fk = 3
                  AND (ms.group_fk != 27 OR ms.group_fk is NULL)
            """
        term_criteria = {
            'hospital': 'AND (pe.term_fk = 1 AND (ms.group_fk != 31 OR ms.group_fk is NULL))',
            'day_hospital': 'AND pe.term_fk = 2',
            'policlinic': 'AND (pe.term_fk = 3 OR pe.term_fk is NULL OR ms.group_fk = 31)',
            'ambulance': 'AND pe.term_fk = 4',
            '': ''
        }

        return query + term_criteria[term] + (
            ' AND pss.error_fk = 75' if is_include_pa
            else ' AND pss.error_fk!=75'
        ) + ' order by mrr.id'

    def print_page(self, sheet, parameters):
        sheet.set_style({'bold': True})
        mo_info = get_mo_info(parameters.organization_code)
        sheet.write_cell(1, 4, mo_info['act_number'])
        sheet.write_cell(2, 1, u'за %s' % parameters.date_string)
        sheet.write_cell(9, 0, parameters.report_name)
        sheet.write_cell(10, 1, parameters.organization_code)
        sheet.set_style({})
        # Представлены реестры счетов (все поданные)
        sheet.write_cell(12, 2, self.data['inv_sum_tariff'])             # всего подано по тарифу
        sheet.write_cell(13, 4, self.data['inv_sum_tariff_other_mo'])    # заказано в другой мо
        sheet.write_cell(14, 4, self.data['inv_sum_tariff_mo'])          # заявлено к оплате
    
        sheet.write_cell(15, 4, self.data['inv_sum_tariff_all'])         # всего представлено на сумму
        sheet.write_cell(18, 1, self.data['inv_count_hosp'])             # всего подано по стационару
        sheet.write_cell(19, 1, self.data['inv_sum_tariff_hosp'])
        sheet.write_cell(21, 1, self.data['inv_count_day_hosp'])         # всего подано по дневному стационару
        sheet.write_cell(22, 1, self.data['inv_sum_tariff_day_hosp'])
    
        sheet.write_cell(24, 1, self.data['inv_count_policlinic'])       # всего подано по поликлинике
        sheet.write_cell(25, 1, self.data['inv_sum_tariff_policlinic'])
        sheet.write_cell(27, 1, self.data['inv_count_ambulance'])        # всего по скорой помощи
        sheet.write_cell(28, 1, self.data['inv_sum_tariff_ambulance'])
    
        # Принятые к оплате реестры счетов
        sheet.write_cell(30, 2, self.data['accept_sum_tariff'])             # принято по тарифу
        # Подушевое
        sheet.write_cell(31, 2, self.data['accept_sum_policlinic_tariff_capitation'])
        sheet.write_cell(32, 2, self.data['accept_sum_ambulance_tariff_capitation'])
        sheet.write_cell(33, 2, self.data['accept_sum_fluorography'])
    
        sheet.write_cell(34, 3, self.data['accept_sum_tariff_other_mo'])    # заказано в другой мо
        sheet.write_cell(35, 2, self.data['accept_sum_tariff_mo'])          # принято к оплате
        sheet.write_cell(36, 1, self.data['accept_count_all'])              # всего принято к оплате
        sheet.write_cell(36, 4, self.data['accept_sum_tariff_all'])
    
        sheet.write_cell(38, 5, self.data['accept_sum_tariff_hosp'])        # принято по стационару
        sheet.write_cell(38, 7, self.data['accept_count_hosp'])
        sheet.write_cell(39, 5, self.data['accept_sum_tariff_day_hosp'])    # принято по дневному стационару
        sheet.write_cell(39, 7, self.data['accept_count_day_hosp'])
        sheet.write_cell(40, 5, self.data['accept_sum_tariff_policlinic'])  # принято по поликлинике
        sheet.write_cell(40, 7, self.data['accept_count_policlinic'])
    
        sheet.write_cell(41, 5, self.data['accept_sum_tariff_ambulance'])  # принято по скорой помощи
        sheet.write_cell(41, 7, self.data['accept_count_ambulance'])

        sheet.write_cell(42, 5, self.data['accept_sum_fluorography'])
    
        # Не принятые к оплате реестры счетов
        sheet.write_cell(43, 5, self.data['sanc_sum_tariff'])             # не принято к оплате
        sheet.write_cell(44, 5, self.data['sanc_sum_tariff_hosp'])        # не принято по стационару
        sheet.write_cell(44, 7, self.data['sanc_count_hosp'])
        sheet.write_cell(45, 5, self.data['sanc_sum_tariff_day_hosp'])    # не принято по дневному стационару
        sheet.write_cell(45, 7, self.data['sanc_count_day_hosp'])
        sheet.write_cell(46, 5, self.data['sanc_sum_tariff_policlinic'])  # не принято по поликлинике
        sheet.write_cell(46, 7, self.data['sanc_count_policlinic'])
    
        sheet.write_cell(47, 5, self.data['sanc_sum_tariff_ambulance'])  # не принято по скорой помощи
        sheet.write_cell(47, 7, self.data['sanc_count_ambulance'])
    
        sheet.write_cell(48, 5, self.data['pa_sum_tariff'])          # не принято сверх объема
        sheet.write_cell(48, 7, self.data['pa_count'])
        sheet.write_cell(49, 3, self.data['sanc_count_all'])              # не подлежит оплате
        sheet.write_cell(49, 5, self.data['sanc_sum_tariff_all'])

        sheet.set_position(50, 0)
        self.print_sanctions(sheet, 'hospital')
        self.print_sanctions(sheet, 'day_hospital')
        self.print_sanctions(sheet, 'policlinic')
        self.print_sanctions(sheet, 'ambulance')

        sheet.set_style({})
        sheet.write(u'2.3. Не принято к оплате в связи с превышением '
                    u'согласованных объемов медицинских услуг на сумму:', 'c', 8)
        sheet.write(self.data['pa_sum_tariff'], 'c')
        sheet.write(u'руб.', 'r')
        sheet.write(u'В т.ч.:  за стационарную медицинскую помощь на сумму:', 'c', 4)
        sheet.write(self.data['pa_sum_tariff_hosp'], 'c')
        sheet.write(u'руб.', 'r')
        sheet.write(u'за медицинскую помощь в дневном стационаре на сумму:', 'c', 4)
        sheet.write(self.data['pa_sum_tariff_day_hosp'], 'c')
        sheet.write(u'руб.', 'r')
        sheet.write(u'за амбулаторно-поликлиническую мед.помощь на сумму :', 'c', 4)
        sheet.write(self.data['pa_sum_tariff_policlinic'], 'c')
        sheet.write(u'руб.', 'r')
    
        self.print_sanctions(sheet, 'pa')
    
        sheet.set_style({})
        sheet.write('', 'r')
        sheet.write(u'Дата предоставления счетов СМО (ТФ) медицинской организацией', 'r', 5)
        sheet.write(u'Дата проверки счетов (реестров)', 'r', 3)
        sheet.write(u'Специалист (Ф.И.О и подпись)', 'c', 3)
        sheet.set_style({'bottom': 1})
        sheet.write('', 'r')

    def print_sanctions(self, sheet, term):
        if term == 'policlinic':
            sanc_sum_key = 'sanc_sum_tariff_policlinic'
            sanc_count_key = 'sanc_count_policlinic'
            title = u'2.1.3. за амбулаторно-поликлиническую помощь  на сумму:'
            services = self.policlinic_services
        elif term == 'hospital':
            sanc_sum_key = 'sanc_sum_tariff_hosp'
            sanc_count_key = 'sanc_count_hosp'
            title = u'2.1.1. за стационарную медицинскую помощь на сумму:'
            services = self.hospital_services
        elif term == 'day_hospital':
            sanc_sum_key = 'sanc_sum_tariff_day_hosp'
            sanc_count_key = 'sanc_count_day_hosp'
            title = u'2.1.2. за мед. помощь в дневном стационаре  на сумму:'
            services = self.day_hospital_services
        elif term == 'ambulance':
            sanc_sum_key = 'sanc_sum_tariff_ambulance'
            sanc_count_key = 'sanc_count_ambulance'
            title = u'2.1.4. за скорую медицинскую помощь  на сумму:'
            services = self.ambulance_services
        elif term == 'pa':
            sanc_sum_key = 'pa_sum_tariff'
            sanc_count_key = 'pa_count'
            title = u''
            services = self.pa_services

        sheet.set_style({})
        sheet.write('', 'r')
        sheet.write(title, 'c', 4)
        sheet.write(self.data[sanc_sum_key], 'c')
        sheet.write(u'руб.', 'c')
        sheet.write(self.data[sanc_count_key], 'c')
        sheet.write(u'счетов', 'r')
        sheet.set_style({
            'border': 1, 'font_size': 9,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center'
        })

        sheet.write(u'Код структурного подразделения', 'c')
        sheet.write(u'Код отделения или профиля коек', 'c')
        sheet.write(u'№ индивидуального счета', 'c')
        sheet.write(u'Период (месяц)', 'c')
        sheet.write(u'№ документа ОМС', 'c')
        sheet.write(u'Код дефекта/нарушения', 'c')
        sheet.write(u'Код ошибки', 'c')
        sheet.write(u'Сумма, подлежащая отказу в оплате', 'c')
        sheet.write(u'Код финансовых санкций', 'c')
        sheet.write(u'Сумма финансовых санкций', 'c')
        sheet.write(u'Примечание', 'r')
        sheet.write(u'1', 'c')
        sheet.write(u'2', 'c')
        sheet.write(u'3', 'c')
        sheet.write(u'4', 'c')
        sheet.write(u'5', 'c')
        sheet.write(u'6', 'c')
        sheet.write(u'7', 'c')
        sheet.write(u'8', 'c')
        sheet.write(u'9', 'c')
        sheet.write(u'10', 'c')
        sheet.write(u'11', 'r')
        sheet.set_style({'border': 1})

        for service in services:
            error_id = service.error_id
            sheet.write(service.dep_old_code, 'c')
            sheet.write(str(service.profile_code or '' if service.term in [1, 2]
                            else service.division_code or ''), 'c')
            sheet.write(service.record_id, 'c')
            sheet.write(service.period, 'c')
            sheet.write(service.insurance_policy_series.replace('\n', '') + ' ' +
                        service.insurance_policy_number
                        if service.insurance_policy_series
                        else service.insurance_policy_number, 'c')
            sheet.write(func.FAILURE_CAUSES[func.ERRORS[error_id]['failure_cause']]['number'], 'c')
            sheet.write(func.ERRORS[error_id]['code'], 'c')
            sheet.write(
                u'Подуш.'
                if service.is_capitation
                else service.provided_tariff, 'c'
            )
            sheet.write(1, 'c')
            sheet.write('', 'c')
            sheet.write('', 'r')