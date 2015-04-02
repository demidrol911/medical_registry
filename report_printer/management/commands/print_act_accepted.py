#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection
from medical_service_register.path import (
    REESTR_DIR,
    REESTR_EXP,
    BASE_DIR
)
from report_printer.excel_writer import ExcelWriter
from report_printer.const import MONTH_NAME
from report_printer.excel_style import (
    VALUE_STYLE,
    TITLE_STYLE,
    TOTAL_STYLE,
    WARNING_STYLE
)
from report_printer.management.commands.sogaz import (
    registry_sogaz,
    registry_sogaz_1,
    registry_sogaz_2
)
from helpers.correct import date_correct
from main.models import MedicalService
from tfoms import func
from pse_exporter import Command as PseExporter
from copy import deepcopy
from decimal import Decimal
import time

ACT_WIDTH = 27


### Вспомогательные функции
def run(query):
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def print_division(act_book, title, values):
    act_book.write_cell(title, 'c')
    for value in values[:-1]:
        act_book.write_cell(value, 'c')
    act_book.write_cell(values[-1], 'r')


def calc_sum(total_sum, cur_sum, pres=0):
    if total_sum:
        for i, value in enumerate(cur_sum):
            if pres:
                total_sum[i] = total_sum[i] + value
            else:
                total_sum[i] = total_sum[i] + value
        return total_sum
    else:
        return list(cur_sum)


# Распечатка суммы (по отделению, причинам отказа, виду помощи и т. д
def print_sum(act_book, title, total_sum, sum_keys, prec=2, style=VALUE_STYLE):
    act_book.set_style(style)
    if title:
        act_book.write_cell(title, 'c')
    act_book.set_number_precision(prec)
    for title_key, column_keys in sum_keys:
        for column_key in column_keys:
            act_book.write_cell(total_sum[title_key][column_key], 'c')
    act_book.row_inc()


def calculate_total_sum_adv(total_sum, intermediate_sum, sum_keys, round_point=None):
    for title_key, column_keys in sum_keys:
        for column_key in column_keys:
            if round_point:
                total_sum[title_key][column_key] += Decimal(round(intermediate_sum[title_key][column_key], round_point))
            else:
                total_sum[title_key][column_key] += Decimal(intermediate_sum[title_key][column_key])
    return total_sum


# Рассчёт итоговой суммы
def calculate_total_sum(total_sum, intermediate_sum):
    for key in total_sum:
        total_sum[key] += intermediate_sum[key]
    return total_sum


def get_title(dict_src, key):
    if key and key in dict_src:
        return dict_src[key]['name']
    else:
        return u'Неизвестно'


### Распечатка первого листа в акте (для приянытх и поданных услуг)
def print_first_page(act_book, mo, data, data_coefficient,
                     sum_capitation_policlinic,
                     sum_capitation_amb):
    last_title_term = None
    last_title_division = None
    last_capitation = 0
    is_print_capit = True
    is_print_unit = True
    last_division_id = 0
    act_book.set_sheet(0)
    act_book.set_cursor(2, 0)
    act_book.write_cell(func.get_mo_info(mo)['code']+' '+func.get_mo_info(mo)['name'])
    act_book.set_cursor(2, 9)
    act_book.write_cell(u'за %s %s г.' % (
        MONTH_NAME[func.PERIOD],
        func.YEAR)
    )
    act_book.set_cursor(3, 0)
    act_book.write_cell(u'Частичный реестр: %s' %
                        ','.join(func.get_partial_register(mo)))
    act_book.set_cursor(7, 0)
    sum_term = None
    total_sum = None
    for row in data:
        term = row[0]
        capitation = row[1]
        reason = row[2]
        group = row[3]
        subgroup = row[4]
        division = row[5]
        gender = row[6]
        values = list(row[7:])

        # Прибавляем коэффициенты
        key = row[:6]
        for key_coef in data_coefficient:
            if key == key_coef[:6]:
                print key
                values = calc_sum(values, key_coef[7:])
                break

        if group:
            if group == 23:
                term_title = get_title(func.MEDICAL_SUBGROUPS, reason)
            elif group == 19:
                term_title = u'Стоматология'
            else:
                term_title = get_title(func.MEDICAL_GROUPS, group)
            if subgroup:
                if division == 999:
                    division_title = u'Стоматология'
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

        # Печатаем заголовок
        if term_title != last_title_term or last_capitation != capitation:
            if sum_term:
                act_book.set_style(TOTAL_STYLE)
                print_division(act_book, u'Итого', sum_term)
                act_book.cursor['row'] += 1
                total_sum = calc_sum(total_sum, sum_term)
                last_title_division = None
                last_division_id = 0
                sum_term = None

            if term == 3:
                if capitation == 0 and is_print_capit:
                    act_book.set_style(TITLE_STYLE)
                    act_book.write_cell(u'Поликлиника (подушевое)', 'r', ACT_WIDTH+1)
                    print u'Поликлиника (подушевое)'
                    last_title_division = None
                    last_division_id = 0
                    is_print_capit = False
                elif capitation == 1 and is_print_unit:
                    act_book.set_style(TITLE_STYLE)
                    act_book.write_cell(u'Поликлиника (за единицу объёма)', 'r', ACT_WIDTH+1)
                    print u'Поликлиника (за единицу объёма)'
                    last_title_division = None
                    last_division_id = 0
                    is_print_unit = False

            print term_title
            act_book.set_style(TITLE_STYLE)
            act_book.write_cell(term_title, 'r', ACT_WIDTH+1)
            act_book.set_style(VALUE_STYLE)
            last_title_term = term_title
            last_capitation = capitation

        # Печатаем отделение
        if division_title != last_title_division or last_division_id != division:
            last_title_division = division_title
            last_division_id = division
            act_book.set_style(VALUE_STYLE)
            if division_title == u'Неизвестно':
                act_book.set_style(WARNING_STYLE)
            print_division(act_book, division_title, values)
        sum_term = calc_sum(sum_term, values)
    if data:
        act_book.set_style(TOTAL_STYLE)
        print_division(act_book, u'Итого', sum_term)
        total_sum = calc_sum(total_sum, sum_term)
        act_book.row_inc()

    if data:
        print_division(act_book, u'Итого по МО', total_sum)

    label_list = [
        u'0 - 1 год мужчина',
        u'0 - 1 год женщина',
        u'1 - 4 год мужчина',
        u'1 - 4 год женщина',
        u'5 - 17 год мужчина',
        u'5 - 17 год женщина',
        u'18 - 59 год мужчина',
        u'18 - 54 год женщина',
        u'60 лет и старше мужчина',
        u'60 лет и старше год женщина',
    ]

    act_book.row_inc()
    if sum_capitation_policlinic[0]:
        act_book.set_style(TITLE_STYLE)
        act_book.write_cell(u'Подушевой норматив по амбул. мед. помощи', 'r', ACT_WIDTH+1)
        total_policlinic = None
        act_book.set_style(VALUE_STYLE)
        for idx, age_group in enumerate(sum_capitation_policlinic[1]):
            print_division(act_book, label_list[idx], age_group)
            total_policlinic = calc_sum(total_policlinic, age_group)
        if total_policlinic:
            act_book.set_style(TOTAL_STYLE)
            print_division(act_book, u'Итого по подушевому нормативу', total_policlinic)
            total_sum = calc_sum(total_sum, total_policlinic)
        act_book.row_inc()

    if sum_capitation_amb[0]:
        act_book.set_style(TITLE_STYLE)
        act_book.write_cell(u'Подушевой норматив по скорой мед. помощи', 'r', ACT_WIDTH+1)
        total_amb = None
        act_book.set_style(VALUE_STYLE)
        for idx, age_group in enumerate(sum_capitation_amb[1]):
            print_division(act_book, label_list[idx], age_group)
            total_amb = calc_sum(total_amb, age_group)
        if total_amb:
            act_book.set_style(TOTAL_STYLE)
            print_division(act_book, u'Итого по подушевому нормативу', total_amb)
            total_sum = calc_sum(total_sum, total_amb)
        act_book.row_inc()

    if sum_capitation_policlinic[0] or sum_capitation_amb[0]:
        print_division(act_book, u'Итого по МО c подушевым', total_sum)


### Распечатка сводного реестра поданных услуг
def print_invoiced_services(act_book, mo, sum_capitation_policlinic,
                            sum_capitation_amb):
    query = """
            --- Все нормальные услуги ---
            select
            -- Вид помощи
            case when pe.term_fk is null then 4
                 WHEN pe.term_fk = 4 then 5
                 ELSE pe.term_fk
                 end as term,

            -- Подушевое
            case when pe.term_fk = 3 THEN (
                 CASE WHEN ps.payment_kind_fk = 2 THEN 0
                      WHEN ps.payment_kind_fk in (1, 3) THEN 1
                 END
                 )
                 WHEN pe.term_fk = 4 THEN 0
                 ELSE 1
                 END AS capitation,

            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 CASE when pe.term_fk = 3 THEN (
                           CASE WHEN ms.reason_fk = 1 and
                                   (ms.group_fk = 24 or ms.group_fk is NULL) and
                                   (select count(ps1.id_pk) from provided_service ps1
                                   join medical_service ms1 on ms1.id_pk = ps1.code_fk
                                   where ps1.event_fk = ps.event_fk
                                         and (ms1.group_fk = 24 or ms1.group_fk is null)
                                         and ms1.reason_fk = 1
                                         ) = 1 then 99
                           else ms.reason_fk END
                      )
                      when pe.term_fk = 2 then msd.term_fk
                      ELSE 0
                      END
                 )
                 WHEN ms.group_fk in (25, 26) THEN 23
                 ELSE 0
                 END AS sub_term,

            -- Группы услуг
            case when ms.group_fk is NULL THEN 0
                 WHEN ms.group_fk = 24 THEN 0
                 ELSE ms.group_fk
                 END as "group",

            -- Подгруппы
            CASE when ms.subgroup_fk IS NULL THEN 0
                 ELSE 1
                 END AS subgroup,

            -- Отделения
            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 case WHEn pe.term_fk = 3 THEN ms.division_fk
                      when pe.term_fk = 4 then ms.division_fk
                      when pe.term_fk = 2 then ms.tariff_profile_fk
                      when pe.term_fk = 1 then ms.tariff_profile_fk
                      end
                )
                ELSE (
                   case when ms.subgroup_fk is null THEN ms.id_pk
                        else ms.subgroup_fk
                        END
                )
                END AS division,

            -- Пол
            CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
                 ELSE 0
                 END AS gender,


            -- Рассчёт --
            count(distinct CASE WHEN ms.code ilike '0%' THEN pt.id_pk END) AS patient_adult,
            count(distinct CASE WHEN ms.code ilike '1%' THEN pt.id_pk END) AS patient_child,

            count(distinct CASE WHEN ms.code ilike '0%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_adult,
            count(distinct CASE WHEN ms.code ilike '1%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_child,

            count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
            count(CASE WHEN ms.code ilike '1%' THEN ps.id_pk END) AS service_child,

            sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN ps.quantity ELSE 0 END) AS quantity_child,

            sum(CASE WHEN ms.code ilike '0%' THEN ps.tariff ELSE 0 END) AS tariff_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN ps.tariff ELSE 0 END) AS tariff_child,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            sum(round(CASE WHEN ms.code ilike '0%'
                     THEN (CASE when ps.payment_kind_fk = 2 or pe.term_fk = 4 THEN 0
                           ELSE (
                                 CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                                      WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                                      WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                                 END)
                           END
                     )
                     ELSE 0 END, 2)) AS accepted_payment_adult,
            sum(round(CASE WHEN ms.code ilike '1%'
                     THEN (CASE when ps.payment_kind_fk = 2 or pe.term_fk = 4 THEN 0
                           ELSE (
                                 CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                                      WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                                      WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                                 END)
                           END
                     )
                     ELSE 0 END, 2)) AS accepted_payment_children

            from medical_register mr
            JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            JOIN patient pt
                ON pt.id_pk = mrr.patient_fk
            left join medical_division msd
                on msd.id_pk = pe.division_fk
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  and (ms.group_fk not in (7, 19, 27) or ms.group_fk is null)
            group by term, capitation,  sub_term, "group", subgroup, division, gender

            --- Диспансеризация взрослых ---
            union
             select
                -- Вид помощи
                4 as term,

                -- Подушевое
                1 AS capitation,

                -- Место или причина
                (select ms1.subgroup_fk from
                       provided_service ps1
                       JOIN medical_service ms1 on ps1.code_fk = ms1.id_pk
                       WHERE ps1.event_fk = ps.event_fk
                             and ps1.payment_type_fk = 2
                             and ms1.code in ('019021',
                                              '019023',
                                              '019022',
                                              '019024'))
                       as sub_term,

                -- Группы услуг
                23 as "group",

                -- Подгруппы
                0 AS subgroup,

                -- Отделения
                ms.id_pk AS division,

                -- Пол
                0 AS gender,


                 -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                0,

                0,
                0,

                count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.tariff ELSE 0 END) AS tariff_adult,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code like '0%' and psc.coefficient_fk = 5 THEN 0.07*ps.tariff ELSE 0 END),
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%'
                     THEN (
                         CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                              WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                              WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                         END
                     )
                     ELSE 0 END) AS accepted_payment_adult,
                0

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 left join provided_service_coefficient psc
                    on psc.service_fk = ps.id_pk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                 AND ms.group_fk = 7 and ms.code in (
                        '019021', '019023', '019022', '019024',
                        '019001', '019020'
                 )

            group by term, capitation,  sub_term, "group", subgroup, division, gender
            union

            --- Стоматология ---
            select
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
                999 AS division,

                -- Пол
                0 AS gender,

                -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                count(distinct CASE WHEN ms.code ilike '1%' THEN mrr.patient_fk END) AS patinet_child,

                count(distinct CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_adult,
                count(distinct CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_child,

                count(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_adult,
                count(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_child,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity*ms.uet
                    ELSE 0 END) as quantity_adult,
                sum(CASE WHEN ms.code ilike '1%' THEN ps.quantity*ms.uet
                    ELSE 0 END) as quantity_children,

                sum(round(CASE WHEN ms.code ilike '0%' THEN ps.tariff ELSE 0 END, 2)) as tariff_adult,
                sum(round(CASE WHEN ms.code ilike '1%' THEN ps.tariff ELSE 0 END, 2)) as tariff_children,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),
                sum(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                sum(round(CASE WHEN ms.code ilike '0%' THEN ps.provided_tariff
                          ELSE 0 END, 2)) as accepted_payment_adult,
                sum(round(CASE WHEN ms.code ilike '1%' THEN ps.provided_tariff
                          ELSE 0 END, 2)) as accepted_payment_children

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                 AND ms.group_fk = 19

                 group by term, capitation,  sub_term, "group", subgroup, division, gender

            order by term, capitation, sub_term, "group", subgroup, division, gender
            """

    query_coefficient = """
            select
            -- Вид помощи
            case when pe.term_fk is null then 4
                 WHEN pe.term_fk = 4 then 5
                 ELSE pe.term_fk
                 end as term,

            -- Подушевое
            case when pe.term_fk = 3 THEN (
                 CASE WHEN ps.payment_kind_fk = 2 THEN 0
                      WHEN ps.payment_kind_fk in (1, 3) THEN 1
                 END
                 )
                 WHEN pe.term_fk = 4 THEN 0
                 ELSE 1
                 END AS capitation,

            -- Место или причина
            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
             CASE when pe.term_fk = 3 THEN (
                       CASE WHEN ms.reason_fk = 1 and
                                   (ms.group_fk = 24 or ms.group_fk is NULL) and
                                   (select count(ps1.id_pk) from provided_service ps1
                                   join medical_service ms1 on ms1.id_pk = ps1.code_fk
                                   where ps1.event_fk = ps.event_fk
                                         and (ms1.group_fk = 24 or ms1.group_fk is null)
                                         and ms1.reason_fk = 1
                                         ) = 1 then 99
                       else ms.reason_fk END
                  )
                  when pe.term_fk = 2 then msd.term_fk
                  ELSE 0
                  END
             )
             WHEN ms.group_fk in (25, 26) THEN 23
             ELSE 0
             END AS sub_term,

            -- Группы услуг
            case when ms.group_fk is NULL THEN 0
                 WHEN ms.group_fk = 24 THEN 0
                 ELSE ms.group_fk
                 END as "group",

            -- Подгруппы
            CASE when ms.subgroup_fk IS NULL THEN 0
                 ELSE 1
                 END AS subgroup,

            -- Отделения
            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 case WHEn pe.term_fk = 3 THEN ms.division_fk
                      when pe.term_fk = 4 then ms.division_fk
                      when pe.term_fk = 2 then ms.tariff_profile_fk
                      when pe.term_fk = 1 then ms.tariff_profile_fk
                      end
                )
                ELSE (
                   case when ms.subgroup_fk is null THEN ms.id_pk
                        else ms.subgroup_fk
                        END
                )
                END AS division,

            -- Пол
            CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
                 ELSE 0
                 END AS gender,


            -- Рассчёт --
            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,
            ---

            sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7
                     AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                                JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                                where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                                THEN round(0.25*ps.tariff, 2) * (
                    select   tc1.value from provided_service_coefficient psc1
                                JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                                where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                     ) ELSE 0 END, 2)) +

            sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7

                                THEN  round(0.25*ps.tariff, 2)
                     ELSE 0  END, 2)),

             sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7
                     AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                                JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                                where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                                THEN  round(0.25*ps.tariff, 2) * (
                    select   tc1.value from provided_service_coefficient psc1
                                JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                                where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                     ) ELSE 0 END, 2)) +

            sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7

                                THEN  round(0.25*ps.tariff, 2)
                     ELSE 0  END, 2)),

            sum(CASE WHEN ms.code like '0%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),

            sum(CASE WHEN ms.code like '0%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),


            0,
            0,

            sum(CASE WHEN ms.code like '0%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),

            sum(CASE WHEN ms.code like '0%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),

            sum(CASE WHEN ms.code like '0%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),

            sum(CASE WHEN ms.code like '0%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),
            sum(CASE WHEN ms.code like '1%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),

            ---
            0,
            0

            from medical_register mr
            JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            JOIN medical_organization dep ON ps.department_fk = dep.id_pk
            join patient pt on pt.id_pk = mrr.patient_fk
            left join medical_division msd
                on msd.id_pk = pe.division_fk
            join provided_service_coefficient psc
                ON psc.service_fk = ps.id_pk
            join tariff_coefficient tc
                on tc.id_pk = psc.coefficient_fk
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  and (ms.group_fk not in (27, 19, 7) or ms.group_fk is null)
            group by term, capitation,  sub_term, "group", subgroup, division, gender
            order by term, capitation, sub_term, "group", subgroup, division, gender
            """

    print u'='*10, u'Рассчёт сумм по отделениям', u'='*10
    data = run(query.format(
        year=func.YEAR,
        period=func.PERIOD,
        mo=mo)
    )
    print u'='*10, u'Рассчёт коэффициентов', u'='*10
    data_coefficient = run(query_coefficient.format(
        year=func.YEAR,
        period=func.PERIOD,
        mo=mo)
    )

    print_first_page(
        act_book, mo, data, data_coefficient,
        sum_capitation_policlinic, sum_capitation_amb
    )


### Рвспечатка сводного реестра принятых услуг
def print_accepted_services(act_book, mo, sum_capitation_policlinic,
                            sum_capitation_amb, department=None):
    query = """
            --- Все нормальные услуги ---
            select
            -- Вид помощи
            case when pe.term_fk is null then 4
                 WHEN pe.term_fk = 4 then 5
                 ELSE pe.term_fk
                 end as term,

            -- Подушевое
            case when pe.term_fk = 3 THEN (
                 CASE WHEN ps.payment_kind_fk = 2 THEN 0
                      WHEN ps.payment_kind_fk in (1, 3) THEN 1
                 END
                 )
                 WHEN pe.term_fk = 4 THEN 0
                 ELSE 1
                 END AS capitation,

            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 CASE when pe.term_fk = 3 THEN (
                           CASE WHEN ms.reason_fk = 1 and
                                   (ms.group_fk = 24 or ms.group_fk is NULL) and
                                   (select count(ps1.id_pk) from provided_service ps1
                                   join medical_service ms1 on ms1.id_pk = ps1.code_fk
                                   where ps1.event_fk = ps.event_fk
                                         and (ms1.group_fk = 24 or ms1.group_fk is null)
                                         and ms1.reason_fk = 1
                                         ) = 1 then 99
                           else ms.reason_fk END
                      )
                      when pe.term_fk = 2 then msd.term_fk
                      ELSE 0
                      END
                 )
                 WHEN ms.group_fk in (25, 26) THEN 23
                 ELSE 0
                 END AS sub_term,

            -- Группы услуг
            case when ms.group_fk is NULL THEN 0
                 WHEN ms.group_fk = 24 THEN 0
                 ELSE ms.group_fk
                 END as "group",

            -- Подгруппы
            CASE when ms.subgroup_fk IS NULL THEN 0
                 ELSE 1
                 END AS subgroup,

            -- Отделения
            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 case WHEn pe.term_fk = 3 THEN ms.division_fk
                      when pe.term_fk = 4 then ms.division_fk
                      when pe.term_fk = 2 then ms.tariff_profile_fk
                      when pe.term_fk = 1 then ms.tariff_profile_fk
                      end
                )
                ELSE (
                   case when ms.subgroup_fk is null THEN ms.id_pk
                        else ms.subgroup_fk
                        END
                )
                END AS division,

            -- Пол
            CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
                 ELSE 0
                 END AS gender,


            -- Рассчёт --
            count(distinct CASE WHEN ms.code ilike '0%' THEN pt.id_pk END) AS patient_adult,
            count(distinct CASE WHEN ms.code ilike '1%' THEN pt.id_pk END) AS patient_child,

            count(distinct CASE WHEN ms.code ilike '0%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_adult,
            count(distinct CASE WHEN ms.code ilike '1%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_child,

            count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
            count(CASE WHEN ms.code ilike '1%' THEN ps.id_pk END) AS service_child,

            sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN ps.quantity ELSE 0 END) AS quantity_child,

            sum(CASE WHEN ms.code ilike '0%' THEN round(ps.tariff, 2) ELSE 0 END) AS tariff_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN round(ps.tariff, 2) ELSE 0 END) AS tariff_child,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            sum(round(CASE WHEN ms.code ilike '0%' THEN (
                    CASE WHEN ps.payment_kind_fk = 2 THEN 0
                    ELSE ps.accepted_payment END
                    )
                    ELSE 0 END, 2)) AS accepted_payment_adult,
            sum(round(CASE WHEN ms.code ilike '1%' THEN (
                    CASE WHEN ps.payment_kind_fk = 2 THEN 0
                    ELSE ps.accepted_payment END
                    )
                    ELSE 0 END, 2)) AS accepted_payment_child

            from medical_register mr
            JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            JOIN patient pt
                ON pt.id_pk = mrr.patient_fk
            JOIN medical_organization dep ON ps.department_fk = dep.id_pk
            left join medical_division msd
                on msd.id_pk = pe.division_fk
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  and ps.payment_type_fk = 2
                  and (ms.group_fk not in (7, 19, 27) or ms.group_fk is null)
                  {department}
            group by term, capitation,  sub_term, "group", subgroup, division, gender

            --- Диспансеризация взрослых ---
            union
             select
                -- Вид помощи
                4 as term,

                -- Подушевое
                1 AS capitation,

                -- Место или причина
                (select ms1.subgroup_fk from
                       provided_service ps1
                       JOIN medical_service ms1 on ps1.code_fk = ms1.id_pk
                       WHERE ps1.event_fk = ps.event_fk
                             and ps1.payment_type_fk = 2
                             and ms1.code in ('019021',
                                              '019023',
                                              '019022',
                                              '019024'))
                       as sub_term,

                -- Группы услуг
                23 as "group",

                -- Подгруппы
                0 AS subgroup,

                -- Отделения
                ms.id_pk AS division,

                -- Пол
                0 AS gender,


                 -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                0,

                0,
                0,

                count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.tariff ELSE 0 END) AS tariff_adult,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code like '0%' and psc.coefficient_fk = 5 THEN 0.07*ps.tariff ELSE 0 END),
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%'
                         THEN ps.accepted_payment ELSE 0 END) AS accepted_payment_adult,
                0

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 JOIN medical_organization dep ON ps.department_fk = dep.id_pk
                 left join provided_service_coefficient psc
                    on psc.service_fk = ps.id_pk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                      and ps.payment_type_fk = 2
                      {department}
                 AND ms.group_fk = 7 and ms.code in (
                        '019021', '019023', '019022', '019024',
                        '019001', '019020'
                 )

            group by term, capitation,  sub_term, "group", subgroup, division, gender
            union

            --- Стоматология ---
            select
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
                ms.subgroup_fk AS division,

                -- Пол
                0 AS gender,


                -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                count(distinct CASE WHEN ms.code ilike '1%' THEN mrr.patient_fk END) AS patinet_child,

                count(distinct CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_adult,
                count(distinct CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_child,

                count(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_adult,
                count(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_child,

                sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.quantity*ms1.uet)
                          from provided_service ps1
                               join medical_service ms1 on ms1.id_pk = ps1.code_fk
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.quantity*ms1.uet)
                          from provided_service ps1
                               join medical_service ms1 on ms1.id_pk = ps1.code_fk
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_child,

                sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS tariff_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS tariff_child,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),
                sum(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),


                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                 sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.accepted_payment)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS accepted_payment_adult,
                 sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.accepted_payment)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 2
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS accepted_payment_child

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_organization dep ON ps.department_fk = dep.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                      and ps.payment_type_fk = 2
                      {department}
                 AND ms.group_fk = 19 and ms.subgroup_fk is not null

                 group by term, capitation,  sub_term, "group", subgroup, division, gender

            order by term, capitation, sub_term, "group", subgroup, division, gender
            """

    query_coefficient = """
        select
        -- Вид помощи
        case when pe.term_fk is null then 4
             WHEN pe.term_fk = 4 then 5
             ELSE pe.term_fk
             end as term,

        -- Подушевое
        case when pe.term_fk = 3 THEN (
             CASE WHEN ps.payment_kind_fk = 2 THEN 0
                  WHEN ps.payment_kind_fk in (1, 3) THEN 1
             END
             )
             WHEN pe.term_fk = 4 THEN 0
             ELSE 1
             END AS capitation,

        -- Место или причина
        case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
         CASE when pe.term_fk = 3 THEN (
                   CASE WHEN ms.reason_fk = 1 and
                           (ms.group_fk = 24 or ms.group_fk is NULL) and
                           (select count(ps1.id_pk) from provided_service ps1
                           join medical_service ms1 on ms1.id_pk = ps1.code_fk
                           where ps1.event_fk = ps.event_fk
                                 and (ms1.group_fk = 24 or ms1.group_fk is null)
                                 and ms1.reason_fk = 1
                                 ) = 1 then 99
                   else ms.reason_fk END
              )
              when pe.term_fk = 2 then msd.term_fk
              ELSE 0
              END
         )
         WHEN ms.group_fk in (25, 26) THEN 23
         ELSE 0
         END AS sub_term,

        -- Группы услуг
        case when ms.group_fk is NULL THEN 0
             WHEN ms.group_fk = 24 THEN 0
             ELSE ms.group_fk
             END as "group",

        -- Подгруппы
        CASE when ms.subgroup_fk IS NULL THEN 0
             ELSE 1
             END AS subgroup,

        -- Отделения
        case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
             case WHEn pe.term_fk = 3 THEN ms.division_fk
                  when pe.term_fk = 4 then ms.division_fk
                  when pe.term_fk = 2 then ms.tariff_profile_fk
                  when pe.term_fk = 1 then ms.tariff_profile_fk
                  end
            )
            ELSE (
               case when ms.subgroup_fk is null THEN ms.id_pk
                    else ms.subgroup_fk
                    END
            )
            END AS division,

        -- Пол
        CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
             ELSE 0
             END AS gender,


        -- Рассчёт --
        0,
        0,

        0,
        0,

        0,
        0,

        0,
        0,

        0,
        0,
        ---

        sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7
                 AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                            THEN round(0.25*ps.tariff, 2) * (
                select   tc1.value from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                 ) ELSE 0 END, 2)) +

        sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7

                            THEN  round(0.25*ps.tariff, 2)
                 ELSE 0  END, 2)),

         sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7
                 AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                            THEN  round(0.25*ps.tariff, 2) * (
                select   tc1.value from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                 ) ELSE 0 END, 2)) +

        sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7

                            THEN  round(0.25*ps.tariff, 2)
                 ELSE 0  END, 2)),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),


        0,
        0,

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),

        ---
        0,
        0

        from medical_register mr
        JOIN medical_register_record mrr
            ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
            ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
            ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
            ON ps.organization_fk=mo.id_pk
        JOIN medical_service ms
            ON ms.id_pk = ps.code_fk
        JOIN medical_organization dep ON ps.department_fk = dep.id_pk
        join patient pt on pt.id_pk = mrr.patient_fk
        left join medical_division msd
            on msd.id_pk = pe.division_fk
        join provided_service_coefficient psc
            ON psc.service_fk = ps.id_pk
        join tariff_coefficient tc
            on tc.id_pk = psc.coefficient_fk
        where mr.is_active and mr.year='{year}' and mr.period='{period}'
              and mo.code = '{mo}'
              and ps.payment_type_fk = 2
              {department}
              and (ms.group_fk not in (27, 19, 7) or ms.group_fk is null)
        group by term, capitation,  sub_term, "group", subgroup, division, gender
        order by term, capitation, sub_term, "group", subgroup, division, gender
        """

    department_query = "AND dep.old_code = '%s'" % department if department else ''

    print u'='*10, u'Рассчёт сумм по отделениям', u'='*10
    data = run(query.format(
        year=func.YEAR, period=func.PERIOD,
        mo=mo, department=department_query
    ))
    print u'='*10, u'Рассчёт коэффициентов', u'='*10
    data_coefficient = run(query_coefficient.format(
        year=func.YEAR, period=func.PERIOD,
        mo=mo, department=department_query
    ))
    print_first_page(
        act_book, mo, data, data_coefficient,
        sum_capitation_policlinic, sum_capitation_amb
    )


def print_sanction_services(act_book, mo, sum_capitation_policlinic,
                            sum_capitation_amb, department=None):
    print '****'
    query = """
            --- Все нормальные услуги ---
            select
            -- Вид помощи
            case when pe.term_fk is null then 4
                 WHEN pe.term_fk = 4 then 5
                 ELSE pe.term_fk
                 end as term,

            -- Подушевое
            case when pe.term_fk = 3 THEN (
                 CASE WHEN ps.payment_kind_fk = 2 THEN 0
                      WHEN ps.payment_kind_fk in (1, 3) THEN 1
                 END
                 )
                 WHEN pe.term_fk = 4 THEN 0
                 ELSE 1
                 END AS capitation,

            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 CASE when pe.term_fk = 3 THEN (
                           CASE WHEN ms.reason_fk = 1 and
                                   (ms.group_fk = 24 or ms.group_fk is NULL) and
                                   (select count(ps1.id_pk) from provided_service ps1
                                   join medical_service ms1 on ms1.id_pk = ps1.code_fk
                                   where ps1.event_fk = ps.event_fk
                                         and (ms1.group_fk = 24 or ms1.group_fk is null)
                                         and ms1.reason_fk = 1
                                         ) = 1 then 99
                           else ms.reason_fk END
                      )
                      when pe.term_fk = 2 then msd.term_fk
                      ELSE 0
                      END
                 )
                 WHEN ms.group_fk in (25, 26) THEN 23
                 ELSE 0
                 END AS sub_term,

            -- Группы услуг
            case when ms.group_fk is NULL THEN 0
                 WHEN ms.group_fk = 24 THEN 0
                 ELSE ms.group_fk
                 END as "group",

            -- Подгруппы
            CASE when ms.subgroup_fk IS NULL THEN 0
                 ELSE 1
                 END AS subgroup,

            -- Отделения
            case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
                 case WHEn pe.term_fk = 3 THEN ms.division_fk
                      when pe.term_fk = 4 then ms.division_fk
                      when pe.term_fk = 2 then ms.tariff_profile_fk
                      when pe.term_fk = 1 then ms.tariff_profile_fk
                      end
                )
                ELSE (
                   case when ms.subgroup_fk is null THEN ms.id_pk
                        else ms.subgroup_fk
                        END
                )
                END AS division,

            -- Пол
            CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
                 ELSE 0
                 END AS gender,


            -- Рассчёт --
            count(distinct CASE WHEN ms.code ilike '0%' THEN pt.id_pk END) AS patient_adult,
            count(distinct CASE WHEN ms.code ilike '1%' THEN pt.id_pk END) AS patient_child,

            count(distinct CASE WHEN ms.code ilike '0%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_adult,
            count(distinct CASE WHEN ms.code ilike '1%' and ms.reason_fk = 1 THEN pe.id_pk END) AS treatment_child,

            count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
            count(CASE WHEN ms.code ilike '1%' THEN ps.id_pk END) AS service_child,

            sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN ps.quantity ELSE 0 END) AS quantity_child,

            sum(CASE WHEN ms.code ilike '0%' THEN round(ps.tariff, 2) ELSE 0 END) AS tariff_adult,
            sum(CASE WHEN ms.code ilike '1%' THEN round(ps.tariff, 2) ELSE 0 END) AS tariff_child,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            0,
            0,

            sum(round(CASE WHEN ms.code ilike '0%' THEN (
                    CASE WHEN ps.payment_kind_fk = 2 THEN 0
                    ELSE ps.accepted_payment END
                    )
                    ELSE 0 END, 2)) AS accepted_payment_adult,
            sum(round(CASE WHEN ms.code ilike '1%' THEN (
                    CASE WHEN ps.payment_kind_fk = 2 THEN 0
                    ELSE ps.accepted_payment END
                    )
                    ELSE 0 END, 2)) AS accepted_payment_child

            from medical_register mr
            JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            JOIN patient pt
                ON pt.id_pk = mrr.patient_fk
            JOIN medical_organization dep ON ps.department_fk = dep.id_pk
            left join medical_division msd
                on msd.id_pk = pe.division_fk
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  and ps.payment_type_fk = 3
                  and (ms.group_fk not in (7, 19, 27) or ms.group_fk is null)
                  {department}
            group by term, capitation,  sub_term, "group", subgroup, division, gender

            --- Диспансеризация взрослых ---
            union
             select
                -- Вид помощи
                4 as term,

                -- Подушевое
                1 AS capitation,

                -- Место или причина
                (select ms1.subgroup_fk from
                       provided_service ps1
                       JOIN medical_service ms1 on ps1.code_fk = ms1.id_pk
                       WHERE ps1.event_fk = ps.event_fk
                             and ps1.payment_type_fk = 3
                             and ms1.code in ('019021',
                                              '019023',
                                              '019022',
                                              '019024'))
                       as sub_term,

                -- Группы услуг
                23 as "group",

                -- Подгруппы
                0 AS subgroup,

                -- Отделения
                ms.id_pk AS division,

                -- Пол
                0 AS gender,


                 -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                0,

                0,
                0,

                count(CASE WHEN ms.code ilike '0%' THEN ps.id_pk END) AS service_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.quantity ELSE 0 END) AS quantity_adult,
                0,

                sum(CASE WHEN ms.code ilike '0%' THEN ps.tariff ELSE 0 END) AS tariff_adult,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code like '0%' and psc.coefficient_fk = 5 THEN 0.07*ps.tariff ELSE 0 END),
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%'
                         THEN ps.accepted_payment ELSE 0 END) AS accepted_payment_adult,
                0

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 JOIN medical_organization dep ON ps.department_fk = dep.id_pk
                 left join provided_service_coefficient psc
                    on psc.service_fk = ps.id_pk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                      and ps.payment_type_fk = 3
                      {department}
                 AND ms.group_fk = 7 and ms.code in (
                        '019021', '019023', '019022', '019024',
                        '019001', '019020'
                 )

            group by term, capitation,  sub_term, "group", subgroup, division, gender
            union

            --- Стоматология ---
            select
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
                ms.subgroup_fk AS division,

                -- Пол
                0 AS gender,


                -- Рассчёт --
                count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
                count(distinct CASE WHEN ms.code ilike '1%' THEN mrr.patient_fk END) AS patinet_child,

                count(distinct CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_adult,
                count(distinct CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_child,

                count(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_adult,
                count(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_child,

                sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.quantity*ms1.uet)
                          from provided_service ps1
                               join medical_service ms1 on ms1.id_pk = ps1.code_fk
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.quantity*ms1.uet)
                          from provided_service ps1
                               join medical_service ms1 on ms1.id_pk = ps1.code_fk
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_child,

                sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS tariff_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS tariff_child,

                0,
                0,

                sum(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),
                sum(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 17
                          THEN (SELECT sum(ps1.tariff*0.2)
                          from provided_service ps1
                               join provided_service_coefficient psc
                                   on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END),


                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                0,
                0,

                 sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.accepted_payment)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS accepted_payment_adult,
                 sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.accepted_payment)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.payment_type_fk = 3
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS accepted_payment_child

                 from medical_register mr
                 JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                 JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                 JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                 JOIN medical_organization mo
                    ON ps.organization_fk=mo.id_pk
                 JOIN medical_organization dep ON ps.department_fk = dep.id_pk
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                      and ps.payment_type_fk = 3
                      {department}
                 AND ms.group_fk = 19 and ms.subgroup_fk is not null

                 group by term, capitation,  sub_term, "group", subgroup, division, gender

            order by term, capitation, sub_term, "group", subgroup, division, gender
            """

    query_coefficient = """
        select
        -- Вид помощи
        case when pe.term_fk is null then 4
             WHEN pe.term_fk = 4 then 5
             ELSE pe.term_fk
             end as term,

        -- Подушевое
        case when pe.term_fk = 3 THEN (
             CASE WHEN ps.payment_kind_fk = 2 THEN 0
                  WHEN ps.payment_kind_fk in (1, 3) THEN 1
             END
             )
             WHEN pe.term_fk = 4 THEN 0
             ELSE 1
             END AS capitation,

        -- Место или причина
        case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
         CASE when pe.term_fk = 3 THEN (
                   CASE WHEN ms.reason_fk = 1 and
                           (ms.group_fk = 24 or ms.group_fk is NULL) and
                           (select count(ps1.id_pk) from provided_service ps1
                           join medical_service ms1 on ms1.id_pk = ps1.code_fk
                           where ps1.event_fk = ps.event_fk
                                 and (ms1.group_fk = 24 or ms1.group_fk is null)
                                 and ms1.reason_fk = 1
                                 ) = 1 then 99
                   else ms.reason_fk END
              )
              when pe.term_fk = 2 then msd.term_fk
              ELSE 0
              END
         )
         WHEN ms.group_fk in (25, 26) THEN 23
         ELSE 0
         END AS sub_term,

        -- Группы услуг
        case when ms.group_fk is NULL THEN 0
             WHEN ms.group_fk = 24 THEN 0
             ELSE ms.group_fk
             END as "group",

        -- Подгруппы
        CASE when ms.subgroup_fk IS NULL THEN 0
             ELSE 1
             END AS subgroup,

        -- Отделения
        case when ms.group_fk is NULL or ms.group_fk = 24 THEN (
             case WHEn pe.term_fk = 3 THEN ms.division_fk
                  when pe.term_fk = 4 then ms.division_fk
                  when pe.term_fk = 2 then ms.tariff_profile_fk
                  when pe.term_fk = 1 then ms.tariff_profile_fk
                  end
            )
            ELSE (
               case when ms.subgroup_fk is null THEN ms.id_pk
                    else ms.subgroup_fk
                    END
            )
            END AS division,

        -- Пол
        CASE WHEN ms.subgroup_fk in (8, 16, 9, 10, 24, 25) THEN pt.gender_fk
             ELSE 0
             END AS gender,


        -- Рассчёт --
        0,
        0,

        0,
        0,

        0,
        0,

        0,
        0,

        0,
        0,
        ---

        sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7
                 AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                            THEN round(0.25*ps.tariff, 2) * (
                select   tc1.value from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                 ) ELSE 0 END, 2)) +

        sum(round(CASE WHEN  ms.code like '0%' and psc.coefficient_fk = 7

                            THEN  round(0.25*ps.tariff, 2)
                 ELSE 0  END, 2)),

         sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7
                 AND ((select count(distinct psc1.id_pk) from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)) >= 1)
                            THEN  round(0.25*ps.tariff, 2) * (
                select   tc1.value from provided_service_coefficient psc1
                            JOIN tariff_coefficient tc1 ON tc1.id_pk = psc1.coefficient_fk
                            where psc1.service_fk = ps.id_pk AND tc1.id_pk in (8, 9, 10, 11, 12)
                 ) ELSE 0 END, 2)) +

        sum(round(CASE WHEN  ms.code like '1%' and psc.coefficient_fk = 7

                            THEN  round(0.25*ps.tariff, 2)
                 ELSE 0  END, 2)),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),


        0,
        0,

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 13 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 14 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk = 15 THEN (tc.value-1)*ps.tariff ELSE 0 END),

        sum(CASE WHEN ms.code like '0%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),
        sum(CASE WHEN ms.code like '1%' and tc.id_pk in (8, 9, 10, 11, 12) THEN round(tc.value*ps.tariff, 2) ELSE 0 END),

        ---
        0,
        0

        from medical_register mr
        JOIN medical_register_record mrr
            ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
            ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
            ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
            ON ps.organization_fk=mo.id_pk
        JOIN medical_service ms
            ON ms.id_pk = ps.code_fk
        JOIN medical_organization dep ON ps.department_fk = dep.id_pk
        join patient pt on pt.id_pk = mrr.patient_fk
        left join medical_division msd
            on msd.id_pk = pe.division_fk
        join provided_service_coefficient psc
            ON psc.service_fk = ps.id_pk
        join tariff_coefficient tc
            on tc.id_pk = psc.coefficient_fk
        where mr.is_active and mr.year='{year}' and mr.period='{period}'
              and mo.code = '{mo}'
              and ps.payment_type_fk = 3
              {department}
              and (ms.group_fk not in (27, 19, 7) or ms.group_fk is null)
        group by term, capitation,  sub_term, "group", subgroup, division, gender
        order by term, capitation, sub_term, "group", subgroup, division, gender
        """

    department_query = "AND dep.old_code = '%s'" % department if department else ''

    print u'='*10, u'Рассчёт сумм по отделениям', u'='*10
    data = run(query.format(
        year=func.YEAR, period=func.PERIOD,
        mo=mo, department=department_query
    ))
    print u'='*10, u'Рассчёт коэффициентов', u'='*10
    data_coefficient = run(query_coefficient.format(
        year=func.YEAR, period=func.PERIOD,
        mo=mo, department=department_query
    ))
    print_first_page(
        act_book, mo, data, data_coefficient,
        sum_capitation_policlinic, sum_capitation_amb
    )


### Распечатка ошибок МЭК (в форме удобной для проверки)
def print_errors_page(act_book, mo, capitation_events, treatment_events, data):
    print u'Список ошибок...'
    services_mek = data['discontinued_services']
    sanctions_mek = data['sanctions']

    # Разбивка снятых с оплаты услуг на группы по коду ошибки и причине отказа
    failure_causes_group = {}
    for index, service in enumerate(services_mek):
        active_error = sanctions_mek[service['id']][0]['error']
        failure_cause_id = func.ERRORS[active_error]['failure_cause']

        if failure_cause_id not in failure_causes_group:
            failure_causes_group[failure_cause_id] = {}

        if active_error not in failure_causes_group[failure_cause_id]:
            failure_causes_group[failure_cause_id][active_error] = []

        failure_causes_group[failure_cause_id][active_error].\
            append((index, service['event_id'] in capitation_events or service['term'] == 4))


    # Сводная информация по причинам отказа
    value_keys = (
        'visited',                                       # Количество посещений
        'treatment',                                     # Количество обращений
        'invoiced_payment',                              # Поданая сумма
        'discontinued_payment'                           # Снятая с оплаты сумма
    )
    stomatology_value_keys = (
        'visited',                                       # Количество посещений
        'treatment',                                     # Количество обращений
        'uet',                                           # Количество YET
        'invoiced_payment',                              # Подданная сумма
        'discontinued_payment'                           # Снятая с оплаты сумма
    )
    service_term_keys = (
        ('hospital', value_keys),                        # Стационар
        ('day_hospital', value_keys),                    # Дневной стационар
        ('policlinic', value_keys),                      # Поликлиника + Диспасеризация + Профосмотры
        ('ambulance', value_keys),                       # Скорая помощь
        ('stomatology', stomatology_value_keys),         # Стоматология
        ('total', value_keys)                            # Итоговая сумма
    )

    init_sum = {term_key: {
        column_key: 0 for column_key in column_keys}
        for term_key, column_keys in service_term_keys}  # Инициализация суммы по причине отказа

    act_book.set_sheet(2)
    act_book.set_cursor(2, 0)
    act_book.set_style()
    act_book.write_cell(func.get_mo_info(mo)['name'])
    act_book.set_cursor(2, 5)
    act_book.write_cell(u'%s %s года' % (MONTH_NAME[func.PERIOD], func.YEAR))
    act_book.set_cursor(3, 0)
    partial_register = ','.join(func.get_partial_register(mo))
    act_book.write_cell(u'Частичный реестр: %s' % partial_register)

    act_book.set_cursor(6, 0)
    act_book.set_style(VALUE_STYLE)

    # Рассчёт сумм по причинам отказов
    for failure_cause_id in failure_causes_group:
        total_sum_failure = deepcopy(init_sum)          # Сумма по причине отказа
        unique_event = []                               # Просмотренные случаи (нужно для рассчёта обращений)
        for error_id in failure_causes_group[failure_cause_id]:

            for index, is_capitation in failure_causes_group[failure_cause_id][error_id]:
                service = services_mek[index]
                if failure_cause_id == 127:
                    print service['id'], service['code'], service['name'], service['event_id']
                    print unique_event
                # Словарь, в котором описываются условия разбивки услуг (по стационару, поликлинике и т. д.)
                # и переопределяются значения рассчёта по умолчанию
                rules_dict = [
                    # Круглосуточный стационар
                    {'condition': service['term'] == 1,
                     'term': 'hospital',
                     'column_condition': {
                         'visited': {'condition': service['group'] == 27, 'value': 0}
                     }},

                    # Дневной стационар
                    {'condition': service['term'] == 2,
                     'term': 'day_hospital',
                     'column_condition': {
                         'visited': {'condition': service['group'] == 27, 'value': 0}
                     }},

                    # Поликлиника
                    {'condition': (service['term'] == 3 and not service['group'] == 19)
                    or not service['term'],
                     'term': 'policlinic',
                     'column_condition': {
                         'discontinued_payment': {'condition': is_capitation, 'value': 0},
                         'treatment': {'condition': service['event_id'] in treatment_events
                         and service['event_id'] not in unique_event, 'value': 1}
                     }},

                    # Стоматология
                    {'condition': service['term'] == 3 and service['group'] == 19,
                     'term': 'stomatology',
                     'column_condition': {
                         'treatment': {'condition': service['event_id'] in treatment_events
                         and service['event_id'] not in unique_event and service['subgroup'] == 12, 'value': 1}
                     }},

                    # Скорая помощь
                    {'condition': service['term'] == 4,
                     'term': 'ambulance',
                     'column_condition': {
                         'discontinued_payment': {'condition': is_capitation, 'value': 0}
                     }}
                ]

                # Значения для рассчёта по умолчанию
                value_default = {
                    'visited': 1,
                    'treatment': 0,
                    'invoiced_payment': service['tariff'],
                    'uet': service['uet'],
                    'discontinued_payment': service['provided_tariff']
                }

                # Поиск к какому виду помощи относится услуга
                term = None
                column_conditions = None
                for rule in rules_dict:
                    if rule['condition']:
                        term = rule['term']
                        column_conditions = rule['column_condition']

                if term:
                    for column_key in total_sum_failure[term]:
                        if column_key in column_conditions:
                            column_condition = column_conditions[column_key]

                            if column_condition['condition']:
                                value = column_condition['value']
                            else:
                                value = value_default[column_key]

                        else:
                            value = value_default[column_key]
                        total_sum_failure[term][column_key] += value

                if service['event_id'] in treatment_events and service['subgroup'] == 12 and service['term'] == 3 and service['group'] == 19:
                    if service['event_id'] not in unique_event:
                        unique_event.append(service['event_id'])
                elif service['event_id'] in treatment_events and (service['term'] == 3 and not service['group'] == 19):
                    if service['event_id'] not in unique_event:
                        unique_event.append(service['event_id'])

        # Рассчёт колонки с итоговой суммой
        for term in total_sum_failure:
            if not term == 'total':
                total_sum_failure['total'] = calculate_total_sum(total_sum_failure['total'],
                                                                 total_sum_failure[term])
        # Печать наименования причины отказа
        act_book.write_cell(func.FAILURE_CAUSES[failure_cause_id]['number'], 'c')

        # Печать суммы по причине отказа
        print_sum(act_book, func.FAILURE_CAUSES[failure_cause_id]['name'],
                  total_sum_failure, service_term_keys)


### Распечатка итоговой суммы по ошибкам (для акта ошибки МЭК)
def print_total_sum_error(act_book, title, total_sum):
    act_book.set_style(VALUE_STYLE)
    act_book.write_cell(title, 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell(total_sum['sum_visited'], 'c')
    act_book.write_cell(total_sum['sum_day'], 'c')
    act_book.write_cell(total_sum['sum_uet'], 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell(total_sum['sum_tariff'], 'c')
    act_book.write_cell(total_sum['sum_calculated_payment'], 'c')
    act_book.write_cell(total_sum['sum_discontinued_payment'], 'r')
    act_book.set_style()
    act_book.row_inc()


### Распечатка акта по 146-му приказу
def print_order_146(act_book, mo, sum_capitation_policlinic,
                    sum_capitation_ambulance, department=None):
    print u'Приказ 146...'
    query = """
             --- Все нормальные услуги ---
            select
            -- Вид помощи
            case  WHEN pe.term_fk = 3 and ms.reason_fk = 1                 -- по поводу заболевания (первич. )
                     and ms.division_fk in (
                                  443,
                                  399,
                                  401,
                                  403,
                                  444
                     )   THEN 2

                 WHEN (pe.term_fk = 3 AND ms.reason_fk in (2, 3, 8)        -- Профилактика (первич. )
                       and ms.division_fk in (443, 399, 401, 403, 444))
                       or  ms.group_fk = 4
                       --Новые коды по профосмотру взрослых
                       or  ms.code in ('019214', '019215', '019216', '019217')
                       or  ms.code in ('019001', '019021', '019023', '019022', '019024')
                       or  ms.code  = '019107'
                       --Новые коды по диспансеризации детей сирот в стац. учреждениях
                       or ms.code in ('119020', '119021', '119022', '119023',
                             '119024', '119025', '119026', '119027',
                             '119028', '119029', '119030', '119031')
                       --Новые коды по диспансеризации детей сирот без попечения родителей
                       or  ms.code in ('119220', '119221', '119222', '119223',
                             '119224', '119225', '119226', '119227',
                             '119228', '119229', '119230', '119231')
                       --Новые коды по профосмотрам несовершеннолетних
                       or ms.code in ('119080', '119081', '119082', '119083',
                             '119084', '119085', '119086', '119087',
                             '119088', '119089', '119090', '119091')
                       or  ms.code in ('119101', '119119', '119120')
                       or  ms.code =  '119151'
                       THEN 3


                 WHEN pe.term_fk = 3 and ms.reason_fk = 5                  -- Неотложка (первич.)
                 and ms.group_fk is null
                 and ms.division_fk in (
                              443, 399,
                              401, 403,
                              444
                 )   THEN 4

                 when ms.group_fk = 19  then 5                             -- Стоматология

                 WHEN pe.term_fk = 2                                       -- Дневной стационар (на дому)
                           and ms.group_fk is null
                           and msd.term_fk = 12      THEN 6

                 WHEN pe.term_fk = 3 and ms.reason_fk = 1                  -- по поводу заболевания (спец.)
                 AND (ms.group_fk != 19 or ms.group_fk is null)
                 and ms.division_fk not in (
                              443,
                              399,
                              401,
                              403,
                              444
                 )   THEN 9

                 when (pe.term_fk = 3                                      -- профилактика (спец. )
                          and (ms.group_fk is NULL or ms.group_fk =24)
                          AND ms.reason_fk in (2, 3, 8)
                          AND ms.division_fk not in (443, 399, 401, 403, 444))
                          or   ms.code = '019020'
                          or  ms.code in ('019108', '019106', '019105', '019104', '019103', '019102')
                          or  ms.code in ('019114', '019113', '019112', '019111', '019110', '019109')
                          or  ms.subgroup_fk in (9, 10, 8, 11)
                  THEN 10


                 WHEN pe.term_fk = 3 and ms.reason_fk = 5                   -- Неотложка (спец.)
                 and ms.group_fk is null
                 and ms.division_fk not in (
                              443, 399,
                              401, 403,
                              444
                 )   THEN 11

                 when ms.code in ('049021', '149021') then 12               -- Гемодиализ в поликлинике

                 when ms.code in ('049022', '149022') THEN 13               -- Перитонеальный диализ в поликлинике

                 WHEN (pe.term_fk = 2                                       -- Дневной стационар (при стационаре  и поликлинике)
                           and ms.group_fk is null
                           and msd.term_fk in (10, 11) )
                              or ms.group_fk = 28    THEN 14

                 WHEN ms.group_fk = 17 THEN 15                              -- ЭКО

                 WHEN pe.term_fk = 1                                        -- Стационар
                            and (ms.group_fk not in (17, 3, 5)
                                     or ms.group_fk is null) THEN 17

                 when ms.code in ('049023', '149023')  THEN  18             -- Гемодиализ в стационаре

                 WHEN ms.code in ('049024', '149024')  THEN 19              -- Перитонеальный диализ в стационаре

                 WHEN pe.term_fk = 4 THEN 20                                -- Скорая медицинская помощь

                 ELSE 0
                 end as term,

            -- Количество пациентов
            count(distinct  CASE when
                      ms.code in ('019201', '019214', '019215',  '019001', '019020' )
                      or ms.subgroup_fk not in  (12, 13, 14, 17)
                      or ms.subgroup_fk in (9, 10, 8, 11)
                            THEN NULL

                      ELSE (
                          CASE when (ms.group_fk is null or ms.group_fk = 24) and pe.term_fk = 3 THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk is null and pe.term_fk = 4 THEN (2, 0, 0, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk is null AND pe.term_fk = 1 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk is null AND pe.term_fk = 2 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk = 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk != 19 and subgroup_fk is NULL THEN  (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk,  ms.code ilike '0%')
                                   WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                           END
                      )
                      END) AS patient,

            count(distinct CASE WHEN  ms.code ilike '0%'  THEN (
                        CASE when
                              ms.code in ('019201', '019214', '019215',  '019001', '019020' )
                              or ms.subgroup_fk not in  (12, 13, 14, 17)
                              or ms.subgroup_fk in (9, 10, 8, 11)
                                    THEN NULL

                              ELSE (
                                  CASE when (ms.group_fk is null or ms.group_fk = 24) and pe.term_fk = 3 THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null and pe.term_fk = 4 THEN (2, 0, 0, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null AND pe.term_fk = 1 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null AND pe.term_fk = 2 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                            WHEN ms.group_fk = 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk != 19 and subgroup_fk is NULL THEN  (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                                   END
                              )
                              END

            )
            ELSE NULL END) AS patient_adult,

            count(distinct CASE WHEN  ms.code ilike '1%'  THEN (
                        CASE when
                              ms.code in ('019201', '019214', '019215',  '019001', '019020' )
                              or ms.subgroup_fk not in  (12, 13, 14, 17)
                              or ms.subgroup_fk in (9, 10, 8, 11)
                                    THEN NULL

                              ELSE (
                                  CASE when (ms.group_fk is null or ms.group_fk = 24) and pe.term_fk = 3 THEN (1, ps.payment_kind_fk, ms.reason_fk, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null and pe.term_fk = 4 THEN (2, 0, 0, ms.division_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null AND pe.term_fk = 1 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk is null AND pe.term_fk = 2 THEN (3, 0, 0, ms.tariff_profile_fk,  pt.id_pk,  ms.code ilike '0%')
                                            WHEN ms.group_fk = 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk != 19 and subgroup_fk is NULL THEN  (ms.group_fk, 0, 0, ms.id_pk,  pt.id_pk,  ms.code ilike '0%')
                                           WHEN ms.group_fk != 19 and subgroup_fk is NOT NULL THEN  (ms.group_fk, 0, 0, ms.subgroup_fk,  pt.id_pk,  ms.code ilike '0%')
                                   END
                              )
                              END

            )
            ELSE NULL END) AS patient_children,

            -- Количество обращений
            count(distinct CASE when ms.subgroup_fk=12
                  or (
                        (select count(ps1.id_pk) from provided_service ps1
                        join medical_service ms1 on ms1.id_pk = ps1.code_fk
                        where ps1.event_fk = ps.event_fk and (ms1.group_fk != 27 or ms1.group_fk is null))>1
                        and ms.reason_fk = 1 AND pe.term_fk = 3 and (ms.group_fk is null or ms.group_fk = 24)
                  ) THEN pe.id_pk END) AS treatments,
            count(distinct CASE WHEN  ms.code ilike '0%'  THEN (
                        CASE when ms.subgroup_fk=12
                        or (
                        (select count(ps1.id_pk) from provided_service ps1
                         join medical_service ms1 on ms1.id_pk = ps1.code_fk
                         where ps1.event_fk = ps.event_fk and (ms1.group_fk != 27 or ms1.group_fk is null))>1
                        and ms.reason_fk = 1 AND pe.term_fk = 3 and (ms.group_fk is null or ms.group_fk = 24)
                        ) THEN pe.id_pk END
                       )
                END) AS treatments_adult,
            count(distinct CASE WHEN  ms.code ilike '1%'  THEN (
                        CASE when ms.subgroup_fk=12
                        or (
                        (select count(ps1.id_pk) from provided_service ps1
                         join medical_service ms1 on ms1.id_pk = ps1.code_fk
                         where ps1.event_fk = ps.event_fk and (ms1.group_fk != 27 or ms1.group_fk is null))>1
                        and ms.reason_fk = 1 AND pe.term_fk = 3 and (ms.group_fk is null or ms.group_fk = 24)
                        ) THEN pe.id_pk END
                       )
                END)  AS treatments_children,

            -- Количество услуг
            count(distinct CASE when ms.group_fk = 19 and ms.subgroup_fk is NULL then NULL
                      ELSE ps.id_pk
                      END) AS services,
            count(distinct CASE WHEN  ms.code ilike '0%' THEN (
                     CASE when ms.group_fk = 19 and ms.subgroup_fk is NULL then NULL
                          ELSE ps.id_pk
                          END
                  )
                  END) AS services_adult,
            count(distinct CASE WHEN  ms.code ilike '1%' THEN (
                     CASE when ms.group_fk = 19 and ms.subgroup_fk is NULL then NULL
                          ELSE ps.id_pk
                          END
                  )
                  END) AS services_children,

            -- Количество дней
            sum(CASE when ms.group_fk = 19 THEN ps.quantity*ms.uet
                  WHEN ps.quantity is NULL THEN 1
                  else ps.quantity
                  END) as quantity,
            sum(CASE WHEN ms.code ilike '0%' THEN (
                    CASE when ms.group_fk = 19 THEN ps.quantity*ms.uet
                             WHEN ps.quantity is NULL THEN 1
                             else ps.quantity
                             END
                    ) ELSE 0 END
                ) AS quantity_adult,

            sum(CASE WHEN ms.code ilike '1%' THEN (
                   CASE when ms.group_fk = 19 THEN ps.quantity*ms.uet
                             WHEN ps.quantity is NULL THEN 1
                             else ps.quantity
                             END
                    ) ELSE 0 END
                ) AS quantity_children,


            -- Принятая сумма
            sum(CASE WHEN ps.payment_kind_fk=2  then 0 ELSE ps.accepted_payment END) as accepted_payment,
            sum(CASE WHEN ms.code ilike '0%' THEN (
                            CASE when ps.payment_kind_fk=2 THEN 0 else ps.accepted_payment  END
                            ) ELSE 0 END
                   ) AS accepted_payment_adult,

            sum(CASE WHEN ms.code ilike '1%' THEN (
                            CASE when ps.payment_kind_fk=2 THEN 0 else ps.accepted_payment  END
                            ) ELSE 0 END
                   ) AS accepted_payment_children


            from medical_register mr
            JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
            JOIN medical_organization dep
                ON ps.department_fk=dep.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            JOIN patient pt
                ON pt.id_pk = mrr.patient_fk
            left join medical_division msd
                on msd.id_pk = pe.division_fk
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  and ps.payment_type_fk = 2
                  and (ms.group_fk != 27 or ms.group_fk is null)
                  {department}
            group by term
            order by term
            """

    if not department:
        data = run(query.format(
            year=func.YEAR,
            period=func.PERIOD,
            mo=mo, department='')
        )
    else:
        data = run(query.format(
            year=func.YEAR,
            period=func.PERIOD, mo=mo,
            department="AND dep.old_code = '"+department+"'")
        )

    act_book.set_sheet(4)
    act_book.set_style()
    act_book.set_cursor(2, 0)
    act_book.write_cell(func.get_mo_info(mo)['name'])
    act_book.set_cursor(3, 10)
    act_book.write_cell(u'за %s %s г.' % (MONTH_NAME[func.PERIOD], func.YEAR))
    act_book.set_style(VALUE_STYLE)
    total = [Decimal(0)]*15
    for row in data:
        if row[0]:
            act_book.set_cursor(8 + int(row[0]), 3)
            for idx, value in enumerate(row[1:]):
                act_book.write_cell(value, 'c')
                total[idx] += Decimal(value)
    if sum_capitation_policlinic[0]:
        act_book.set_cursor(31, 15)
        for value in sum_capitation_policlinic[1]:
            total[13] += value[ACT_WIDTH-1]
            total[14] += value[ACT_WIDTH]
            total[12] += value[ACT_WIDTH-1] + value[ACT_WIDTH]
            act_book.write_cell(value[ACT_WIDTH-1], 'c')
            act_book.write_cell(value[ACT_WIDTH], 'c')
            act_book.write_cell(value[ACT_WIDTH-1] + value[ACT_WIDTH], 'c')
            act_book.cursor['row'] += 1
            act_book.cursor['column'] = 15
    if sum_capitation_ambulance[0]:
        act_book.set_cursor(42, 15)
        for value in sum_capitation_ambulance[1]:
            total[13] += value[ACT_WIDTH-1]
            total[14] += value[ACT_WIDTH]
            total[12] += value[ACT_WIDTH-1] + value[ACT_WIDTH]
            act_book.write_cell(value[ACT_WIDTH-1], 'c')
            act_book.write_cell(value[ACT_WIDTH], 'c')
            act_book.write_cell(value[ACT_WIDTH-1] + value[ACT_WIDTH], 'c')
            act_book.cursor['row'] += 1
            act_book.cursor['column'] = 15
    act_book.set_cursor(52, 3)
    for value in total:
        act_book.write_cell(value, 'c')


def print_error_pk(act_book, mo, capitation_events, treatment_events, data):
    print u'Распечатка справки по ошибке PK'
    services_mek = data['discontinued_services']
    sanctions_mek = data['sanctions']
    patients = data['patients']

    services_pk = []

    # Поиск услуг снятых по ошибке PK
    for index, service in enumerate(services_mek):
        active_error = sanctions_mek[service['id']][0]['error']
        if active_error == 54:
            services_pk.append(index)

    service_term_keys = (
        'hospital',                        # Стационар
        'day_hospital',                    # Дневной стационар
        'policlinic',                      # Поликлиника + Диспасеризация + Профосмотры
        'ambulance',                       # Скорая помощь
        'stomatology',                     # Стоматология
        'total'                            # Итоговая сумма
    )

    sum_error_pk = {term_key: {'count_service': 0, 'sum_sanctions': 0}
                    for term_key in service_term_keys}

    sum_error_pk['population'] = 0
    unique_patient = []

    # Рассчёт сумм по ошибкe PK
    for index in services_pk:
        service = services_mek[index]
        is_capitation = service['event_id'] in capitation_events or service['term'] == 4
        # Словарь, в котором описываются условия разбивки услуг (по стационару, поликлинике и т. д.)
        # и переопределяются значения рассчёта по умолчанию
        rules_dict = [
            # Круглосуточный стационар
            {'condition': service['term'] == 1,
             'term': 'hospital',
             'column_condition': {
                 'count_service': {'condition': service['group'] == 27, 'value': 0}
             }},

            # Дневной стационар
            {'condition': service['term'] == 2,
            'term': 'day_hospital',
            'column_condition': {
                'count_service': {'condition': service['group'] == 27, 'value': 0}
            }},

            # Поликлиника
            {'condition': (service['term'] == 3 and not service['group'] == 19)
                or not service['term'],
            'term': 'policlinic',
            'column_condition': {
                'sum_sanctions': {'condition': is_capitation, 'value': 0}
            }},

            # Стоматология
            {'condition': service['term'] == 3 and service['group'] == 19,
             'term': 'stomatology',
             'column_condition': {}},

            # Скорая помощь
            {'condition': service['term'] == 4,
             'term': 'ambulance',
             'column_condition': {
                 'sum_sanctions': {'condition': is_capitation, 'value': 0}
             }}
        ]

        # Значения для рассчёта по умолчанию
        value_default = {
            'count_service': 1,
            'sum_sanctions': service['provided_tariff']
        }

        if service['patient_id'] not in unique_patient:
            unique_patient.append(service['patient_id'])

        # Поиск к какому виду помощи относится услуга
        term = None
        column_conditions = None
        for rule in rules_dict:
            if rule['condition']:
                term = rule['term']
                column_conditions = rule['column_condition']

        if term:
            for column_key in sum_error_pk[term]:
                if column_key in column_conditions:
                    column_condition = column_conditions[column_key]
                    if column_condition['condition']:
                        value = column_condition['value']
                    else:
                        value = value_default[column_key]

                else:
                    value = value_default[column_key]
                sum_error_pk[term][column_key] += value

    for term_key in service_term_keys[:-1]:
        sum_error_pk['total']['count_service'] += sum_error_pk[term_key]['count_service']
        sum_error_pk['total']['sum_sanctions'] += sum_error_pk[term_key]['sum_sanctions']

    sum_error_pk['population'] = len(unique_patient)

    # Распечатка сумм в акт
    act_book.set_sheet(3)
    act_book.set_cursor(2, 0)
    act_book.set_style()
    act_book.write_cell(func.get_mo_info(mo)['name'])
    act_book.set_cursor(2, 5)
    act_book.write_cell(u'%s %s года' % (MONTH_NAME[func.PERIOD], func.YEAR))
    act_book.set_cursor(3, 0)
    partial_register = ','.join(func.get_partial_register(mo))
    act_book.write_cell(u'Частичный реестр: %s' % partial_register)
    act_book.set_style(VALUE_STYLE)
    act_book.set_cursor(6, 0)

    act_book.write_cell(sum_error_pk['population'], 'c')
    for term_key in service_term_keys:
        act_book.write_cell(sum_error_pk[term_key]['count_service'], 'c')
        act_book.write_cell(sum_error_pk[term_key]['sum_sanctions'], 'c')


### Распечатка ошибок МЭК (в табличной форме)
def print_error_fund(act_book, mo, data, handbooks):
    services_mek = data['discontinued_services']
    patients = data['patients']
    sanctions_mek = data['sanctions']
    service_all = data['invoiced_services']

    # Группировка услуг по ошибкам и рассчёт итоговой суммы снятой с оплаты
    sanctions_group = {}
    total_sum_sanction = 0
    for index, service in enumerate(services_mek):
        active_error = sanctions_mek[service['id']][0]['error']
        if active_error not in sanctions_group:
            sanctions_group[active_error] = []
        sanctions_group[active_error].append(index)
        total_sum_sanction += service['provided_tariff']

    value_keys = (
        'count',                                      # Количество услуг
        'sum'                                         # Сумма
    )
    column_keys = (
        ('invoiced_payment', value_keys),             # Поданные услуги
        ('discontinued_payment', value_keys),         # Снятые с оплаты услуги
        ('accepted_payment', value_keys)              # Принятые услуги
    )

    # Словарь, в котором описаны виды помощи, способы разбивки
    # и суммы по поданным, снятым и принятым услугам
    division_group = {
        'hospital_all': {                             # Стационар и дневной стационар
            'division': 'profile',                    # Разбивка по медицинским профилям
            'division_info': 'medical_profile',
            'data': {}},
        'examination_all': {                          # Диспансеризация и профосмотр
            'division': None,                         # Разбивки нет, считается одной строкой
            'division_info': None,
            'data': {}
        },
        'other_all': {                                # Поликлиника и скорая помощь
            'division': 'worker_speciality',          # Разбивка по коду специальности мед. работника
            'division_info': 'workers_speciality',
            'data': {}
        }
    }

    for service in service_all:
        # Выбор вида помощи
        if service['term'] in (1, 2):
            term = 'hospital_all'
        elif service['term'] in (3, 4):
            term = 'other_all'
        else:
            term = 'examination_all'

        # Инициализация суммы по соответсвующему разбиению
        division = service[division_group[term]['division']] if division_group[term]['division'] else 0
        if division not in division_group[term]['data']:
            division_group[term]['data'][division] = {column_key: {value: 0 for value in values}
                                                      for column_key, values in column_keys}

        # Рассчёт сумм для принятых и частично оплаченных услуг
        if service['payment_type'] in (2, 4):
            division_group[term]['data'][division]['accepted_payment']['count'] += 1
            division_group[term]['data'][division]['accepted_payment']['sum'] += service['accepted_payment']

        # Рассчёт сумм для снятых с оплаты и частично оплаченных услуг
        if service['payment_type'] in (3, 4):
            division_group[term]['data'][division]['discontinued_payment']['count'] += 1
            division_group[term]['data'][division]['discontinued_payment']['sum'] += service['provided_tariff']

        # Рассчёт сумм для всех поданных услуг
        division_group[term]['data'][division]['invoiced_payment']['count'] += 1
        division_group[term]['data'][division]['invoiced_payment']['sum'] += service['invoiced_payment']

    act_book.set_sheet(6)
    act_book.set_style({'align': 'center'})
    act_book.set_cursor(3, 0)
    act_book.write_cell(u'в медицинской организации: %s' % func.get_mo_info(mo)['name'])
    act_book.set_cursor(11, 0)

    # Распечатка услуг снятых с оплаты или частично оплаченных
    act_book.set_style(VALUE_STYLE)
    for error_id in sorted(sanctions_group):
        for index in sanctions_group[error_id]:
            service = services_mek[index]
            patient = patients[service['patient_id']]

            act_book.write_cell(service['xml_id'], 'c')              # Ид услуги, поставленный больницей

            act_book.write_cell(patient['policy_series'] + ' '
                                + patient['policy_number']
                                if patient['policy_series']
                                else patient['policy_number'], 'c')  # Полис (серия и номер)

            act_book.write_cell(service['basic_disease'], 'c')       # Основной диагноз
            act_book.write_cell(date_correct(
                service['start_date']).strftime('%d.%m.%Y'), 'c')    # Дата начала услуги

            act_book.write_cell(date_correct(
                service['end_date']).strftime('%d.%m.%Y'), 'c')      # Дата окончания услуги

            act_book.write_cell(func.ERRORS[error_id]['code'], 'c')  # Код ошибки

            act_book.write_cell(func.ERRORS[error_id]['name'], 'c')  # Наименование ошибки

            act_book.write_cell(service['provided_tariff'], 'r')     # Сумма снятая с оплаты (без подушевого)

    # Распечатка итоговой снятой суммы)
    act_book.write_cell(u'Итого по акту на сумму', 'c', 6)
    act_book.write_cell(total_sum_sanction, 'r')

    # Распечатка сумм с разбивкой
    act_book.write_cell(u'в т. ч. по коду:', 'r', 7)
    act_book.row_inc()

    act_book.write_cell(u'Профиль отделения (койки) или специалиста', 'c', 1)
    act_book.write_cell(u'Предоставлено к оплате', 'c', 1)
    act_book.write_cell(u'Отказано в оплате', 'c', 1)
    act_book.write_cell(u'Оплатить', 'r', 1)
    act_book.write_cell('', 'c', 1)
    act_book.write_cell(u'кол-во', 'c')
    act_book.write_cell(u'сумма', 'c')
    act_book.write_cell(u'кол-во', 'c')
    act_book.write_cell(u'сумма', 'c')
    act_book.write_cell(u'кол-во', 'c')
    act_book.write_cell(u'сумма', 'r')

    for term in division_group:
        division_info = division_group[term]['division_info']
        for division in division_group[term]['data']:
            code = u' '
            name = u' '
            if division_info:
                code = handbooks[division_info][division]['code']
                name = handbooks[division_info][division]['name']
            act_book.write_cell(str(code), 'c')
            print_sum(act_book, name, division_group[term]['data'][division], column_keys)

    # Распечатка места для подписи
    act_book.set_style({})
    act_book.write_cell(u'Итого по счёту:', 'c', 1)
    act_book.row_inc()
    act_book.write_cell(u'Исполнитель', 'c')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'c', 1)
    act_book.set_style({})
    act_book.write_cell(u'подпись', 'c')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'c', 2)
    act_book.set_style({})
    act_book.write_cell(u'расшифровка подписи', 'r')
    act_book.write_cell(u'Руководитель страховой медицинской организации/директор'
                        u' территориального фонда обязательного медицинского страхования', 'r', 4)
    act_book.write_cell('', 'c')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'c', 1)
    act_book.set_style({})
    act_book.write_cell(u'подпись', 'c')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'c', 2)
    act_book.set_style({})
    act_book.write_cell(u'расшифровка подписи', 'r')
    act_book.write_cell(u'М.П.', 'r')
    act_book.write_cell(u'Должность, подпись руководителя медицинской организации, '
                        u'ознакомившегося с Актом', 'r')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'r', 3)
    act_book.set_style({})
    act_book.write_cell(u'Дата', 'c')
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'c', 1)


### Печатает сводный реестр для экономистов
### Формат вызова print_act_econom статус_реестра признак_печати_для_прикреплённых_больниц(1 если надо)
class Command(BaseCommand):
    def handle(self, *args, **options):
        status = int(args[0])
        is_partial_register = args[1] if len(args) == 2 else 0
        template = BASE_DIR + r'\templates\excel_pattern\reestr_201501.xls'
        target_dir = REESTR_DIR if status in (8, 6, 600) else REESTR_EXP
        handbooks = {
            'year': func.YEAR,
            'period': func.PERIOD,
            'failure_causes': func.FAILURE_CAUSES,
            'errors_code': func.ERRORS,
            'workers_speciality': func.WORKER_SPECIALITIES,
            'tariff_profile': func.TARIFF_PROFILES,
            'medical_terms': func.MEDICAL_TERMS,
            'medical_reasons': func.MEDICAL_REASONS,
            'medical_division': func.MEDICAL_DIVISIONS,
            'medical_code': func.MEDICAL_SERVICES,
            'medical_groups': func.MEDICAL_GROUPS,
            'medical_subgroups': func.MEDICAL_SUBGROUPS,
            'medical_profile': func.MEDICAL_PROFILES,
            'coefficient_type': func.COEFFICIENT_TYPES
        }
        organizations = func.get_mo_register(status=status)
        printed_act = []
        for mo in organizations:
            start = time.clock()
            partial_register = func.get_partial_register(mo)
            handbooks['partial_register'] = partial_register
            handbooks['mo_info'] = func.get_mo_info(mo)
            print u'Сборка сводного реестра для', mo
            print u'Загрузка данных...'
            data = {
                'patients': func.get_patients(mo),
                'sanctions': func.get_sanctions(mo),
                'coefficients': func.get_coefficients(mo),
                'invoiced_services': func.get_services(
                    mo,
                    is_include_operation=True
                ),
                'accepted_services': func.get_services(
                    mo, payment_type=[2, 4],
                    payment_kind=[1, 2, 3]),
                'discontinued_services': func.get_services(
                    mo,
                    payment_type=[3, 4])
            }

            print u'Поиск случаев с обращениями...'
            treatment_events = func.get_treatment_events(mo)
            print u'Поиск случаев с подушевым...'
            capitation_events = func.get_capitation_events(mo)

            sum_capitation_policlinic = func.calculate_capitation_tariff(3, mo)
            sum_capitation_ambulance = func.calculate_capitation_tariff(4, mo)

            target = target_dir % (handbooks['year'], handbooks['period']) + ur'\согаз3\%s' % \
                handbooks['mo_info']['name'].replace('"', '').strip()
            print u'Печать акта: %s ...' % target

            with ExcelWriter(target, template=template) as act_book:
                act_book.set_overall_style({'font_size': 11})
                '''
                print_sanction_services(
                    act_book=act_book,
                    mo=mo,
                    sum_capitation_policlinic=sum_capitation_policlinic,
                    sum_capitation_amb=sum_capitation_ambulance
                )
                '''

                print_accepted_services(
                    act_book=act_book,
                    mo=mo,
                    sum_capitation_policlinic=sum_capitation_policlinic,
                    sum_capitation_amb=sum_capitation_ambulance
                )

                print_errors_page(act_book, mo, capitation_events,
                                  treatment_events, data)

                print_error_pk(
                    act_book, mo,
                    capitation_events, treatment_events,
                    data
                )
                print_order_146(
                    act_book, mo,
                    sum_capitation_policlinic,
                    sum_capitation_ambulance
                )

                print_error_fund(act_book, mo, data, handbooks)

                ### Согазовские отчёты
                registry_sogaz_1.print_registry_sogaz_2(act_book=act_book, mo=mo)
                registry_sogaz.print_registry_sogaz_1(act_book=act_book, mo=mo)
                registry_sogaz_2.print_registry_sogaz_3(act_book=act_book, mo=mo)

                if status == 8:
                    PseExporter().handle(*[mo, 6])
                if status == 3:
                    func.change_register_status(mo, 9)
                printed_act.append(act_book.name)
            print u'Выгружен', mo

            if status == 8:
                target = target_dir % (handbooks['year'], handbooks['period']) + \
                    ur'\поданные\%s_поданные' % handbooks['mo_info']['name'].replace('"', '').strip()
                print u'Печать акта поданных услуг: %s ...' % target

                with ExcelWriter(target, template=template) as act_book:
                    act_book.set_overall_style({'font_size': 11})
                    print_invoiced_services(
                        act_book=act_book,
                        mo=mo,
                        sum_capitation_policlinic=sum_capitation_policlinic,
                        sum_capitation_amb=sum_capitation_ambulance
                    )

            if is_partial_register:
                print u'Сборка сводного реестра по прикреплённым больницам...'
                for department in partial_register:
                    print u'Загрузка данных...'
                    handbooks['mo_info'] = func.get_mo_info(mo, department)
                    print handbooks['mo_info'], department
                    handbooks['partial_register'] = [department, ]

                    data['invoiced_services'] = func.get_services(
                        mo,
                        department_code=department,
                        is_include_operation=True
                    )
                    data['accepted_services'] = func.get_services(
                        mo,
                        payment_type=[2, 4],
                        payment_kind=[1, 2, 3],
                        department_code=department
                    )
                    data['discontinued_services'] = func.get_services(
                        mo,
                        payment_type=[3, 4],
                        department_code=department
                    )
                    target = target_dir % (handbooks['year'], handbooks['period']) + r'\%s' % handbooks['mo_info']['name'].\
                        replace('"', '').strip()
                    print u'Печать акта: %s ...' % target

                    with ExcelWriter(target, template=template) as act_book:
                        act_book.set_overall_style({'font_size': 11})
                        print_accepted_services(
                            act_book=act_book,
                            mo=mo,
                            sum_capitation_policlinic=sum_capitation_policlinic,
                            sum_capitation_amb=sum_capitation_ambulance,
                            department=department
                        )

                        registry_sogaz_1.print_registry_sogaz_2(act_book=act_book, mo=mo, department=department)

                        print_errors_page(
                            act_book, mo,
                            capitation_events, treatment_events,
                            data
                        )

                        print_error_pk(
                            act_book, mo,
                            capitation_events, treatment_events,
                            data
                        )
                        print_order_146(
                            act_book, mo,
                            sum_capitation_policlinic,
                            sum_capitation_ambulance,
                            department=department
                        )
                        print_error_fund(act_book, mo, data, handbooks)
                    print u'Выгружен', department
            elapsed = time.clock() - start
            print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed//60), int(elapsed % 60))

        print u'-'*50
        print u'Напечатанные акты:'
        if status == 3:
            print u'  Предварительные акты:'
        elif status == 8:
            print u'  Акты после проверки экспертов:'
        for act in printed_act:
            print act
