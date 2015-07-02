#! -*- coding: utf-8 -*-
from abc import abstractmethod
from copy import deepcopy
from report_printer_clear.utils.page import ReportPage
from django.db import connection
from tfoms import func
from main.funcs import howlong
from main.models import MedicalService
from report_printer.excel_style import (
    VALUE_STYLE,
    TITLE_STYLE,
    TOTAL_STYLE,
    WARNING_STYLE
)


class GeneralServicesPage(ReportPage):
    ACT_WIDTH = 27

    def __init__(self):
        self.data = None
        self.policlinic_capitation = None
        self.ambulance_capitation = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = None
        self.policlinic_capitation = None
        self.ambulance_capitation = None
        query = self.get_query(parameters)
        data_services = self.__run_query(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))
        query_coeff = self.get_coeff_query(parameters)
        data_coeff = self.__run_query(query_coeff, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

        self.data = []
        for row in data_services:
            values = list(row[7:])
            key = list(row[:7])
            for key_coef in data_coeff:
                if key == list(key_coef[:7]):
                    values = self.__calc_sum(values, list(key_coef[7:]))
                    break
            key.extend(values)
            self.data.append(key)

        def capitation_to_arrays(term_capitation):
            result = [[0, ] * 28 for _ in range(0, 10)]
            map_data = (
                ('population', 0),
                ('basic_tariff', 4),
                ('tariff', 8),
                ('coeff', 16),
                ('accepted', 26)
            )
            for data_key, pos_in_arr in map_data:
                result[0][pos_in_arr + 1] = term_capitation['men1'][data_key]
                result[1][pos_in_arr + 1] = term_capitation['fem1'][data_key]

                result[2][pos_in_arr + 1] = term_capitation['men2'][data_key]
                result[3][pos_in_arr + 1] = term_capitation['fem2'][data_key]

                result[4][pos_in_arr + 1] = term_capitation['men3'][data_key]
                result[5][pos_in_arr + 1] = term_capitation['fem3'][data_key]

                result[6][pos_in_arr] = term_capitation['men4'][data_key]
                result[7][pos_in_arr] = term_capitation['fem4'][data_key]

                result[8][pos_in_arr] = term_capitation['men5'][data_key]
                result[9][pos_in_arr] = term_capitation['fem5'][data_key]
            return result

        if parameters.policlinic_capitation[0]:
            self.policlinic_capitation = capitation_to_arrays(parameters.policlinic_capitation[1])
        if parameters.ambulance_capitation[0]:
            self.ambulance_capitation = capitation_to_arrays(parameters.ambulance_capitation[1])

    @abstractmethod
    def get_query(self, parameters):
        pass

    @abstractmethod
    def get_coeff_query(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        def print_division(act_book, title, row):
            act_book.write(title, 'c')
            for value in row[:-1]:
                act_book.write(value, 'c')
            act_book.write(row[-1], 'r')

        def get_title(dict_src, key):
            if key and key in dict_src:
                return dict_src[key]['name']
            else:
                return u'Неизвестно'

        signs_title = {
            'can_print_policlinic_capitation': True,
            'can_print_policlinic_unit': True,
            'can_print_exam_till_1_04_2015': True,
            'can_print_exam_since_1_04_2015': True,
            'can_print_ambulance': True
        }

        signs_term = {
            'is_policlinic': False,
            'is_ambulance': False,
            'is_exam_till_1_04_2015': False,
            'is_exam_since_1_04_2015': False,
            'is_exam_all_1_04_2015': False
        }

        zero_key = {
            'term': 0, 'capitation': 0,
            'reason': 0, 'group': 0,
            'subgroup': 0, 'division': 0,
            'gender': 0
        }

        latest_key = deepcopy(zero_key)

        sum_by_term = None
        subtotal = None
        total = None
        sum_adult_exam = None

        sheet.write_cell(0, 3, u'Сводная справка  по  дефектам за ' + parameters.date_string)
        sheet.write_cell(3, 0, parameters.organization_code+' '+parameters.report_name)

        sheet.write_cell(2, 0, parameters.organization_code+' '+parameters.report_name)
        sheet.write_cell(2, 9, u'за ' + parameters.date_string)
        sheet.write_cell(3, 0, u'Частичный реестр: %s' % ','.join(parameters.partial_register))
        sheet.set_position(7, 0)

        for row in self.data:
            term = row[0]
            capitation = row[1]
            reason = row[2]
            group = row[3]
            subgroup = row[4]
            division = row[5]
            gender = row[6]

            values = row[7:]

            # Вычисляем заголовоки разделов и отделений
            if group:
                if group == 23:
                    term_title = get_title(func.MEDICAL_SUBGROUPS, reason)
                elif group == 19:
                    term_title = u'Стоматология'
                else:
                    term_title = get_title(func.MEDICAL_GROUPS, group)
                if subgroup:
                    if division == 999:
                        division_title = u'Стоматология (снятые)'
                    else:
                        division_title = get_title(func.MEDICAL_SUBGROUPS, division)
                else:
                    division_title = get_title(func.MEDICAL_SERVICES, division)
                    if group == 20:
                        tariff_profile = MedicalService.objects.get(pk=division).tariff_profile.name
                        group_code = MedicalService.objects.get(pk=division).vmp_group
                        division_title = str(group_code) + ' (' + tariff_profile + ')' + division_title
            else:
                division_title = ''
                if term == 1:
                    term_title = u'Стационар'
                    division_title = get_title(func.TARIFF_PROFILES, division)
                elif term == 2:
                    if reason:
                        if reason == 10:
                            term_title = u'Дневной стационар (Дневной стационар в стационаре)'
                        elif reason == 11:
                            term_title = u'Дневной стационар (Дневной стационар при поликлинике)'
                        elif reason == 12:
                            term_title = u'Дневной стационар (Дневной стационар на дому)'
                        division_title = get_title(func.TARIFF_PROFILES, division)
                    else:
                        division_title = u'Дневной стационар'
                elif term == 3:
                    if reason == 1:
                        term_title = u'Поликлиника (заболевание)'
                    elif reason == 2:
                        term_title = u'Поликлиника (профосмотр)'
                    elif reason == 3:
                        term_title = u'Поликлиника (прививка)'
                    elif reason == 5:
                        term_title = u'Поликлиника (неотложка)'
                    elif reason == 8:
                        term_title = u'Поликлиника (с иными целями)'
                    elif reason == 99:
                        term_title = u'Поликлиника (разовые)'
                        values[2] = 0
                        values[3] = 0
                    division_title = get_title(func.MEDICAL_DIVISIONS, division)
                elif term == 5:
                    term_title = u'Скорая помощь'
                    division_title = get_title(func.MEDICAL_DIVISIONS, division)
                elif term == 7:
                    pass
            if gender == 1:
                division_title += u', мальчики'
            elif gender == 2:
                division_title += u', девочки'
            ###

            if term != latest_key['term'] \
                    or capitation != latest_key['capitation'] \
                    or reason != latest_key['reason'] \
                    or group != latest_key['group']:
                # Печать итоговой суммы по отделениям
                if sum_by_term:
                    total = self.__calc_sum(total, sum_by_term)
                    latest_key['division'] = 0
                    latest_key['gender'] = 0
                    sheet.set_style(TOTAL_STYLE)
                    print_division(sheet, u'Итого', sum_by_term)
                    sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())

                # Рассчет промежуточных итоговых сумм
                if signs_term['is_policlinic'] \
                        or signs_term['is_ambulance'] \
                        or signs_term['is_exam_till_1_04_2015'] \
                        or signs_term['is_exam_since_1_04_2015']:
                    subtotal = self.__calc_sum(subtotal, sum_by_term)

                if signs_term['is_exam_all_1_04_2015']:
                    sum_adult_exam = self.__calc_sum(sum_adult_exam, sum_by_term)

                sum_by_term = None

                # Печать промежуточных итоговых сумм
                signs_term_name = ''
                title_subtotal = ''
                if signs_term['is_policlinic'] \
                        and not(term == 3 and latest_key['capitation'] == capitation):
                    signs_term_name = 'is_policlinic'
                    title_subtotal = u'Итого по поликлинике'

                if signs_term['is_ambulance'] and (term != 5):
                    signs_term_name = 'is_ambulance'
                    title_subtotal = u'Итого по скорой помощи'

                if signs_term['is_exam_till_1_04_2015'] \
                        and not(term == 4 and capitation == 23):
                    signs_term_name = 'is_exam_till_1_04_2015'
                    title_subtotal = u'Итого по взр. диспансер. до 1 апреля'

                if signs_term['is_exam_since_1_04_2015'] \
                        and not(term == 4 and capitation == 24):
                    signs_term_name = 'is_exam_since_1_04_2015'
                    title_subtotal = u'Итого по взр. диспансер. после 1 апреля'

                if signs_term_name:
                    sheet.set_style(TOTAL_STYLE)
                    print_division(sheet, title_subtotal, subtotal)
                    sheet.set_position(sheet.get_row_index() + 1, 0)
                    signs_term[signs_term_name] = False

                if signs_term['is_exam_all_1_04_2015'] \
                        and not(term == 4 and capitation in [23, 24]):
                    sheet.set_style(TOTAL_STYLE)
                    print_division(sheet, u'Итого по взр. диспансер.', sum_adult_exam)
                    sheet.set_position(sheet.get_row_index() + 1, 0)
                    signs_term['is_exam_all_1_04_2015'] = False
                ###

                # Печать разделов, в которых будут рассчитываться промежуточные суммы
                signs_term_name = ''
                sings_can_print = ''
                title_subtotal = ''
                if term == 3 and capitation == 0 \
                        and signs_title['can_print_policlinic_capitation']:
                    signs_term_name = 'is_policlinic'
                    sings_can_print = 'can_print_policlinic_capitation'
                    title_subtotal = u'Поликлиника (подушевое)'

                elif term == 3 and capitation == 1 \
                        and signs_title['can_print_policlinic_unit']:
                    signs_term_name = 'is_policlinic'
                    sings_can_print = 'can_print_policlinic_unit'
                    title_subtotal = u'Поликлиника (за единицу объёма)'

                elif term == 4 and capitation == 23 \
                        and signs_title['can_print_exam_till_1_04_2015']:
                    signs_term_name = 'is_exam_till_1_04_2015'
                    sings_can_print = 'can_print_exam_till_1_04_2015'
                    title_subtotal = u'Диспансеризация взрослых до 1.04.2015'
                    signs_term['is_exam_all_1_04_2015'] = True

                elif term == 4 and capitation == 24 \
                        and signs_title['can_print_exam_since_1_04_2015']:
                    signs_term_name = 'is_exam_since_1_04_2015'
                    sings_can_print = 'can_print_exam_since_1_04_2015'
                    title_subtotal = u'Диспансеризация взрослых после 1.04.2015'
                    signs_term['is_exam_all_1_04_2015'] = True

                elif term == 5 \
                        and signs_title['can_print_ambulance']:
                    signs_term_name = 'is_ambulance'
                    sings_can_print = 'can_print_ambulance'
                    title_subtotal = u'Скорая помощь'

                if signs_term_name:
                    sheet.set_style(TITLE_STYLE)
                    sheet.write(title_subtotal, 'r', GeneralServicesPage.ACT_WIDTH+1)
                    signs_term[signs_term_name] = True
                    signs_title[sings_can_print] = False
                    subtotal = None
                    latest_key['division'] = 0
                    latest_key['gender'] = 0
                ###

                print term_title
                sheet.set_style(TITLE_STYLE)
                sheet.write(term_title, 'r', GeneralServicesPage.ACT_WIDTH+1)
                sheet.set_style(VALUE_STYLE)
                latest_key['term'] = term
                latest_key['capitation'] = capitation
                latest_key['reason'] = reason
                latest_key['group'] = group

            # Печатаем отделение
            if division != latest_key['division'] or gender != latest_key['gender']:
                sheet.set_style(VALUE_STYLE)
                if division_title == u'Неизвестно':
                    sheet.set_style(WARNING_STYLE)
                latest_key['division'] = division
                latest_key['gender'] = gender
                print_division(sheet, division_title, values)
            sum_by_term = self.__calc_sum(sum_by_term, values)
        if self.data:
            sheet.set_style(TOTAL_STYLE)
            print_division(sheet, u'Итого', sum_by_term)
            sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())
            total = self.__calc_sum(total, sum_by_term)

        if self.data:
            print_division(sheet, u'Итого по МО', total)

        def print_tariff_capitation(title, term_capitation):
            labels = [
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
            ]

            sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())
            if term_capitation:
                sheet.set_style(TITLE_STYLE)
                sheet.write(title, 'r', GeneralServicesPage.ACT_WIDTH+1)
                sheet.set_style(VALUE_STYLE)
                for idx, age_group in enumerate(term_capitation):
                    print_division(sheet, labels[idx], age_group)

        def sum_tariff_capitation(term_capitation):
            total_capitation = None
            for idx, age_group in enumerate(term_capitation):
                total_capitation = self.__calc_sum(total_capitation, age_group)
            return total_capitation

        if self.policlinic_capitation:
            total_policlinic = sum_tariff_capitation(self.policlinic_capitation)
            total = self.__calc_sum(total, total_policlinic)
            print_tariff_capitation(u'Подушевой норматив по амбул. мед. помощи', self.policlinic_capitation)
            sheet.set_style(TOTAL_STYLE)
            print_division(sheet, u'Итого по подушевому нормативу', total_policlinic)
            sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())

        if self.ambulance_capitation:
            total_ambulance = sum_tariff_capitation(self.ambulance_capitation)
            total = self.__calc_sum(total, total_ambulance)
            print_tariff_capitation(u'Подушевой норматив по скорой мед. помощи', self.ambulance_capitation)
            sheet.set_style(TOTAL_STYLE)
            print_division(sheet, u'Итого по подушевому нормативу', total_ambulance)
            sheet.set_position(sheet.get_row_index() + 1, sheet.get_column_index())

        if self.policlinic_capitation or self.ambulance_capitation:
            print_division(sheet, u'Итого по МО c подушевым', total)

    @staticmethod
    def get_general_query():
        query = '''
                -- Акт принятых услуг --
                WITH services_mo AS (
                     SELECT
                         ps.id_pk AS service_id,
                         pe.id_pk AS event_id,
                         pe.term_fk AS event_term,

                         CASE WHEN ms.group_fk = 19
                                THEN ps.quantity*ms.uet
                              ELSE ps.quantity
                         END AS service_quantity,

                         ROUND(ps.tariff, 2) AS service_tariff,
                         ROUND(ps.accepted_payment, 2) AS service_accepted_payment,
                         ROUND(ps.provided_tariff, 2) AS service_provided_tariff,


                         ps.payment_type_fk AS payment_type,
                         ps.start_date AS start_date,
                         ps.end_date AS end_date,
                         dep.old_code AS department,
                         ms.group_fk As service_group,
                         ms.subgroup_fk AS service_subgroup,
                         ms.division_fk AS service_division,
                         ms.tariff_profile_fk AS service_tariff_profile,
                         ms.id_pk AS service_code_id,
                         ms.code AS service_code,
                         ms.code ILIKE '0%%' AS is_adult,
                         ms.code ILIKE '1%%' AS is_child,
                         ms.reason_fk AS service_reason,
                         msd.term_fk AS division_term,
                         pt.id_pk AS patient_id,
                         pt.gender_fk AS patient_gender,

                         mr.organization_code AS organization,

                         CASE WHEN pe.term_fk = 3
                                THEN (
                                   CASE WHEN ps.payment_kind_fk = 2
                                          THEN 0
                                        WHEN ps.payment_kind_fk in (1, 3)
                                          THEN 1
                                   END
                                 )
                              WHEN pe.term_fk = 4 THEN 0
                              ELSE 1
                         END AS service_capitation,

                        (pe.term_fk = 3 AND ms.reason_fk = 1
                         AND (ms.group_fk = 24 OR ms.group_fk is null)
                         ) OR (ms.group_fk = 19 AND ms.subgroup_fk = 12) AS is_treatment

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
                         JOIN medical_organization dep
                           ON ps.department_fk = dep.id_pk
                         LEFT JOIN medical_division msd
                           ON msd.id_pk = pe.division_fk
                     WHERE
                          mr.is_active
                          AND mr.year=%(year)s
                          AND mr.period=%(period)s
                          AND mo.code = %(organization)s
                          AND (ms.group_fk != 27 OR ms.group_fk is NULL)
                )
                SELECT T.term, T.capitation, T.sub_term, T."group", T.subgroup, T.division, T.gender,

                -- Рассчёт --
                {inner_query}

                FROM (
                    (SELECT
                         service_id,

                         -- Вид помощи
                         CASE WHEN event_term is NULL
                                THEN 4
                              WHEN event_term = 4
                                THEN 5
                              ELSE event_term
                         END AS term,

                         -- Подушевое
                         service_capitation AS capitation,

                         -- Подраздел
                         CASE WHEN service_group is NULL
                                   OR service_group = 24
                                THEN (
                                    CASE WHEN event_term = 3 THEN (
                                           CASE WHEN service_reason = 1
                                                     AND (service_group = 24 OR service_group is NULL)
                                                     AND (
                                                        SELECT
                                                            COUNT(ps1.id_pk)
                                                        FROM provided_service ps1
                                                            JOIN medical_service ms1
                                                               ON ms1.id_pk = ps1.code_fk
                                                        WHERE
                                                             ps1.event_fk = event_id
                                                             AND (ms1.group_fk = 24 OR ms1.group_fk is NULL)
                                                             AND ms1.reason_fk = 1
                                                       ) = 1
                                                  THEN 99
                                                ELSE service_reason
                                           END
                                         )
                                         WHEN event_term = 2
                                           THEN division_term
                                         ELSE 0
                                    END
                                )
                              WHEN service_group in (25, 26)
                                THEN 23
                              ELSE 0
                         END AS sub_term,

                        -- Группы услуг
                        CASE WHEN service_group is NULL
                               THEN 0
                             WHEN service_group = 24
                               THEN 0
                             ELSE service_group
                        END as "group",

                        -- Подгруппы
                        CASE WHEN service_subgroup IS NULL
                               THEN 0
                             ELSE 1
                        END AS subgroup,

                        -- Отделения
                        CASE WHEN service_group is NULL OR service_group = 24
                               THEN (
                                   CASE WHEN event_term = 3
                                          THEN service_division
                                        WHEN event_term = 4
                                          THEN service_division
                                        WHEN event_term = 2
                                          THEN service_tariff_profile
                                        WHEN event_term = 1
                                          THEN service_tariff_profile
                                   END
                               )
                             ELSE (
                                  CASE WHEN service_subgroup is NULL
                                         THEN service_code_id
                                       ELSE service_subgroup
                                  END
                               )
                        END AS division,

                        -- Пол
                        CASE WHEN service_subgroup in (8, 16, 9, 10, 24, 25)
                               THEN patient_gender
                             ELSE 0
                        END AS gender
                    FROM  services_mo
                    WHERE
                         service_group not in (7, 19)
                         OR service_group is NULL
                    )
                    UNION
                    (
                        -- Диспансеризация взрослых
                        SELECT
                            service_id,
                            -- Вид помощи
                            4 as term,

                            -- Подушевое
                            CASE WHEN (
                                     SELECT
                                         ps1.start_date
                                     FROM provided_service ps1
                                         JOIN medical_service ms1
                                            ON ps1.code_fk = ms1.id_pk
                                     WHERE ps1.event_fk = event_id
                                           AND ps1.payment_type_fk = 2
                                           AND ms1.code = '019001') >= '2015-04-01'
                                   THEN 24
                                 ELSE 23
                            END AS capitation,

                            -- Место или причина
                            (SELECT
                                 ms1.subgroup_fk
                             FROM provided_service ps1
                                 JOIN medical_service ms1
                                    ON ps1.code_fk = ms1.id_pk
                             WHERE ps1.event_fk = event_id
                                   AND ps1.payment_type_fk = 2
                                   AND ms1.code in (
                                                '019021',
                                                '019023',
                                                '019022',
                                                '019024'
                                            )
                            ) AS sub_term,

                            -- Группы услуг
                            23 AS "group",

                            -- Подгруппы
                            0 AS subgroup,

                            -- Отделения
                            service_code_id AS division,

                            -- Пол
                            0 AS gender
                        FROM services_mo
                        WHERE service_group = 7
                              AND service_code in (
                                               '019021', '019023',
                                               '019022', '019024',
                                               '019001', '019020'
                                         )
                    )
                    UNION
                    (
                        -- Стоматология
                        SELECT
                            service_id,
                            -- Вид помощи
                            7 as term,

                            -- Подушевое
                            1 AS capitation,

                            -- Место или причина
                            0 as sub_term,

                            -- Группы услуг
                            19 as "group",

                            -- Подгруппы
                            1 AS subgroup,

                            -- Отделения
                            CASE WHEN payment_type=3
                                   THEN 999
                                 ELSE
                                    (
                                     SELECT
                                         MAX(ms1.subgroup_fk)
                                     FROM provided_service ps1
                                         JOIN medical_service ms1
                                            ON ms1.id_pk = ps1.code_fk
                                     WHERE ps1.event_fk = event_id
                                           AND ps1.payment_type_fk = payment_type
                                           AND ps1.start_date = start_date
                                           AND ps1.end_date = end_date
                                 )
                            END AS division,

                            -- Пол
                            0 AS gender
                        FROM services_mo
                        WHERE service_group = 19
                      )
                    ) AS T
                    JOIN services_mo S
                       ON S.service_id = T.service_id
                    {joins}
                WHERE {where}
                GROUP BY T.term, T.capitation, T.sub_term, T."group", T.subgroup, T.division, T.gender
                ORDER BY T.term, T.capitation, T.sub_term, T."group", T.subgroup, T.division, T.gender
                '''
        return query

    def __calc_sum(self, total_sum, cur_sum, pres=0):
        if total_sum:
            for i, value in enumerate(cur_sum):
                if pres:
                    total_sum[i] = total_sum[i] + value
                else:
                    total_sum[i] = total_sum[i] + value
            return total_sum
        else:
            return list(cur_sum)

    def __run_query(self, query, parameters):
        cursor = connection.cursor()
        cursor.execute(query, parameters)
        return [row for row in cursor.fetchall()]
