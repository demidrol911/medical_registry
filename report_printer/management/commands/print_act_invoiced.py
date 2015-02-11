#! -*- coding: utf-8 -*-

from copy import deepcopy
from decimal import Decimal
from django.db import connection

from django.core.management.base import BaseCommand

from medical_service_register.path import REESTR_DIR, REESTR_EXP, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.const import MONTH_NAME
import tfoms.func as register_function
from report_printer.excel_style import VALUE_STYLE, TITLE_STYLE, TOTAL_STYLE


DEBUG = True


def run(query):
    cursor = connection.cursor()
    cursor.execute(query)
    return cursor.fetchall()


def print_accepted_services(act_book, year, period, mo, sum_capitation_policlinic, sum_capitation_amb, handbooks):
    query = """
            --- Все нормальные услуги ---
            select
            -- Вид помощи
            case when pe.term_fk is null then 6
                 ELSE pe.term_fk
                 end as term,

            -- Подушевое
            case when pe.term_fk = 3 THEN (
                 CASE WHEN ps.payment_kind_fk = 2 THEN 0
                      WHEN ps.payment_kind_fk = 1 THEN 1
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
                           where ps1.event_fk = ps.event_fk and (ms1.group_fk != 27 or ms.group_fk is null)
                           ) = 1 then 99
                           else ms.reason_fk END
                      )
                      when pe.term_fk = 2 then msd.term_fk
                      ELSE 0
                      END
                 )
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

            sum(CASE WHEN ms.code ilike '0%' and ps.payment_kind_fk != 2
                     THEN (
                         CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                              WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                              WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                         END
                     )
                     ELSE 0 END) AS accepted_payment_adult,
            sum(CASE WHEN ms.code ilike '1%' and ps.payment_kind_fk != 2
                     THEN (
                         CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                              WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                              WHEN ps.payment_type_fk = 4 THEN ps.accepted_payment + ps.provided_tariff
                         END
                     )
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
                6 as term,

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
                7 as "group",

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

                sum(CASE WHEN ms.code ilike '0%' and ps.payment_kind_fk != 2
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
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.quantity*ms1.uet)
                          from provided_service ps1
                               join medical_service ms1 on ms1.id_pk = ps1.code_fk
                               where ps1.event_fk = ps.event_fk
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS quantity_child,

                sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS tariff_adult,
                sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(ps1.tariff)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
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

                 sum(CASE WHEN ms.code ilike '0%'
                          THEN (SELECT sum(CASE WHEN ps1.payment_type_fk = 2 THEN ps1.accepted_payment
                                                WHEN ps1.payment_type_fk = 3 THEN ps1.provided_tariff
                                                END)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
                                     and ps1.start_date = ps.start_date
                                     and ps1.end_date = ps.end_date)
                          ELSE 0 END) AS accepted_payment_adult,
                 sum(CASE WHEN ms.code ilike '1%'
                          THEN (SELECT sum(CASE WHEN ps1.payment_type_fk = 2 THEN ps1.accepted_payment
                                                WHEN ps1.payment_type_fk = 3 THEN ps1.provided_tariff
                                                END)
                          from provided_service ps1
                               where ps1.event_fk = ps.event_fk
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
                 JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                 where mr.is_active and mr.year='{year}' and mr.period='{period}'
                      and mo.code = '{mo}'
                 AND ms.group_fk = 19 and ms.subgroup_fk is not null

                 group by term, capitation,  sub_term, "group", subgroup, division, gender

            order by term, capitation, sub_term, "group", subgroup, division, gender
            """

    query_coef = """
                select
                -- Вид помощи
                case when pe.term_fk is null then 6
                     ELSE pe.term_fk
                     end as term,

                -- Подушевое
                case when pe.term_fk = 3 THEN (
                     CASE WHEN ps.payment_kind_fk = 2 THEN 0
                          WHEN ps.payment_kind_fk = 1 THEN 1
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
                           where ps1.event_fk = ps.event_fk and (ms1.group_fk != 27 or ms.group_fk is null)
                           ) = 1 then 99
                           else ms.reason_fk END
                      )
                      when pe.term_fk = 2 then msd.term_fk
                      ELSE 0
                      END
                 )
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

                sum(CASE WHEN ms.code like '0%' and tc.id_pk = 7 THEN tc.value*ps.tariff ELSE 0 END),
                sum(CASE WHEN ms.code like '1%' and tc.id_pk = 7 THEN tc.value*ps.tariff ELSE 0 END),

                sum(CASE WHEN ms.code like '0%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),
                sum(CASE WHEN ms.code like '1%' and tc.id_pk = 4 THEN (tc.value-1)*ps.tariff ELSE 0 END),

                sum(CASE WHEN ms.code like '0%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),
                sum(CASE WHEN ms.code like '1%' and tc.id_pk = 5 THEN (tc.value-1)*ps.tariff ELSE 0 END),


                0,
                0,

                sum(CASE WHEN ms.code like '0%' and tc.id_pk = 6 THEN (tc.value-1)*ps.tariff ELSE 0 END),
                sum(CASE WHEN ms.code like '1%' and tc.id_pk = 6 THEN (tc.value-1)*ps.tariff ELSE 0 END),

                sum(CASE WHEN ms.code like '0%' and tc.id_pk in (8, 9, 10, 11, 12) THEN tc.value*ps.tariff ELSE 0 END),
                sum(CASE WHEN ms.code like '1%' and tc.id_pk in (8, 9, 10, 11, 12) THEN tc.value*ps.tariff ELSE 0 END),

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
    data = run(query.format(year=year, period=period, mo=mo))
    print u'='*10, u'Рассчёт коэффициентов', u'='*10
    data_coef = run(query_coef.format(year=year, period=period, mo=mo))
    last_title_term = None
    last_title_division = None
    last_capitation = 0
    is_print_capit = True
    is_print_unit = True

    act_book.set_sheet(0)
    act_book.set_cursor(2, 0)
    act_book.write_cell(mo+' '+handbooks['mo_info']['name'])
    act_book.set_cursor(2, 9)
    act_book.write_cell(u'за %s %s г.' % (MONTH_NAME[period], year))
    act_book.set_cursor(3, 0)
    act_book.write_cell(u'Частичный реестр: %s' % ','.join(handbooks['partial_register']))
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
        for key_coef in data_coef:
            if key == key_coef[:6]:
                print key
                values = calc_sum(values, key_coef[7:])
                break

        if group:
            if group == 7:
                #last_title_division = None
                term_title = handbooks['medical_subgroups'][reason]['name']
            elif group == 19:
                term_title = u'Стоматология'
                #last_title_division = None
            else:
                term_title = handbooks['medical_groups'][group]['name']
            if subgroup:
                division_title = handbooks['medical_subgroups'][division]['name']
            else:
                division_title = handbooks['medical_code'][division]['name']
        else:
            division_title = ''
            if term == 1:
                term_title = u'Стационар'
                division_title = handbooks['tariff_profile'][division]['name']
            elif term == 2:
                if reason == 10:
                    term_title = u'Дневной стационар (Дневной стационар в стационаре)'
                elif reason == 11:
                    term_title = u'Дневной стационар (Дневной стационар при поликлинике)'
                elif reason == 12:
                    term_title = u'Дневной стационар (Дневной стационар на дому)'
                division_title = handbooks['tariff_profile'][division]['name']
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
                division_title = handbooks['medical_division'][division]['name']
            elif term == 4:
                term_title = u'Скорая помощь'
                division_title = handbooks['medical_division'][division]['name']
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
                sum_term = None

            if term == 3:
                if capitation == 0 and is_print_capit:
                    act_book.set_style(TITLE_STYLE)
                    act_book.write_cell(u'Поликлиника (подушевое)', 'r', 24)
                    print u'Поликлиника (подушевое)'
                    last_title_division = None
                    is_print_capit = False
                elif capitation == 1 and is_print_unit:
                    act_book.set_style(TITLE_STYLE)
                    act_book.write_cell(u'Поликлиника (за единицу объёма)', 'r', 24)
                    print u'Поликлиника (за единицу объёма)'
                    last_title_division = None
                    is_print_unit = False

            print term_title
            act_book.set_style(TITLE_STYLE)
            act_book.write_cell(term_title, 'r', 24)
            act_book.set_style(VALUE_STYLE)
            last_title_term = term_title
            last_capitation = capitation

        # Печатаем отделение
        if division_title != last_title_division:
            last_title_division = division_title
            print_division(act_book, division_title, values)
        sum_term = calc_sum(sum_term, values)
    if data:
        act_book.set_style(TOTAL_STYLE)
        print_division(act_book, u'Итого', sum_term)
        total_sum = calc_sum(total_sum, sum_term)
        act_book.row_inc()

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
        act_book.write_cell(u'Подушевой норматив по амбул. мед. помощи', 'r', 24)
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
        act_book.write_cell(u'Подушевой норматив по скорой мед. помощи', 'r', 24)
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


def print_division(act_book, title, values):
    act_book.write_cell(title, 'c')
    for value in values[:-1]:
        act_book.write_cell(value, 'c')
    act_book.write_cell(values[-1], 'r')


def calc_sum(total_sum, cur_sum):
    if total_sum:
        for i, value in enumerate(cur_sum):
            total_sum[i] = total_sum[i] + value
        return total_sum
    else:
        return list(cur_sum)

'''
### Рвспечатка сводного реестра принятых услуг
def print_accepted_service(act_book, year, period, mo,
                           capitation_events, treatment_events,
                           sum_capitation_policlinic,
                           sum_capitation_ambulance,
                           data, handbooks):
    value_keys = (
        'adult',                                # Взрослые
        'children'                              # Дети
    )

    column_keys = (
        ('population', value_keys),             # Численность
        ('treatment', value_keys),              # Количество обращений
        ('services', value_keys),               # Количество услуг
        ('days', value_keys),                   # Количество дней (УЕТ)
        ('basic_tariff', value_keys),           # Основной тариф
        ('index015', value_keys),               # Индекс. кафедры АГМА
        ('index_6', value_keys),                # Индекс. разовые посещения
        ('index2', value_keys),                 # Индекс. неотложка
        ('index07', value_keys),                # Индекс. мобил. бригады
        ('indexFAP', value_keys),               # Индекс. ФАП
        ('index_7', value_keys),                # Индекс. сверх объёма
        ('accepted_payment', value_keys))       # Принятая сумма (с подуш.)

    # Отображение кода коэффициента на имя поля
    coef_to_field = {
        2: 'index015',
        3: 'index_6',
        4: 'index2',
        5: 'index07',
        1: 'indexFAP',
        6: 'index_7'
    }

    # Виды медицинской помощи
    term_keys = (
        'hospital',                             # Стационар
        'day_hospital',                         # Дневной стационар
        'policlinic_capitation',                # Поликлиника подушевое
        'policlinic',                           # Поликлиника
        'examination_adult',                    # Диспансеризация взрослых
        'examination',                          # Диспансеризация и профосмотры
        'stomatology',                          # Стоматология
        'ambulance',                            # Скорая помощь
        'unidentified',                         # Неопознанные
    )

    init_sum = {column_key: {value_key: 0
                             for value_key in value_keys}
                for column_key, _ in column_keys}          # Инициализация суммы по отделению

    sum_division_nogroup = {}                              # Сводные суммы для услуг без группы
    sum_division_group = {}                                # Сводные суммы для услуг с группами

    # Словарь, в котором описывается по каким полям группировать услуги,
    # какие названия соответствуют разделам, видам помощи и отделениям
    # используется для услуг не имеющих групп или услуг с группами-исключениями
    division_by_dict = {
        'hospital': {                                                   # Круглосуточный стационар
            'title_term': handbooks['medical_terms'][1]['name'],
            'section': None,
            'title_section': None,
            'division': 'tariff_profile_id',
            'name': 'tariff_profile'
        },

        'day_hospital': {                                               # Дневной стационар
            'title_term': handbooks['medical_terms'][2]['name'],
            'section': 'division_term',
            'title_section': 'medical_terms',
            'division': 'tariff_profile_id',
            'name': 'tariff_profile'
        },

        'policlinic_capitation': {                                      # Поликлиника подушевое
            'title_term': u'Поликлиника (подушевое)',
            'section': None,
            'title_section': None,
            'division': 'division_id',
            'name': 'medical_division'
        },

        'policlinic': {                                                 # Поликлиника
            'title_term': handbooks['medical_terms'][3]['name'],
            'section': 'reason',
            'title_section': 'medical_reasons',
            'division': 'division_id',
            'name': 'medical_division'
        },

        'examination_adult': {                                          # Диспансеризация взрослых
            'title_term': u'Диспансеризация взрослых',
            'section': 'subgroup',
            'title_section': 'medical_subgroups',
            'division': 'code_id',
            'name': 'medical_code'
        },

        'examination': {                                                # Диспансеризация и профосмотры
            'title_term': u'Диспансеризация',
            'section': None,
            'title_section': None,
            'division': 'code_id',
            'name': 'medical_code'
        },

        'stomatology': {                                                # Стоматология
            'title_term': u'Стоматология',
            'section': None,
            'title_section': None,
            'division': 'subgroup',
            'name': 'medical_subgroups'
        },

        'ambulance': {                                                  # Скорая помощь
            'title_term': handbooks['medical_terms'][4]['name'],
            'section': None,
            'title_section': None,
            'division': 'division_id',
            'name': 'medical_division'
        },

        'unidentified': {                                               # Неопознанные услуги
            'title_term': u'Неопознанные',
            'section': None,
            'title_section': None,
            'division': 'code_id',
            'name': 'medical_code'
        }
    }

    # Группы - исключения (при рассчёте суммы по ним считаются не как для обычных групп,
    # а особым способом, зависящим от кода группы)

    exception_group = [24, 19, 7]

    accepted_services = data['invoiced_services']                       # Поданные услуги
    coefficients = data['coefficients']                                # Тарифные коэффициенты
    patients = data['patients']

    total_sum_mo = deepcopy(init_sum)                                  # Итоговая сумма по МО

    viewed_event = []                                                  # Просмотренные случаи
    viewed_patient = {term_key: [] for term_key in term_keys}          # Просмотренные пациенты

    # Отображение случая на подгруппу, определяющую приём по стоматологии
    # (используется для рассчёта стоматологии)
    stomatology_event = {}
    for service in accepted_services:
        if service['group'] == 19 and service['subgroup']:
            event_data = (service['event_id'], service['start_date'], service['end_date'])
            if event_data not in stomatology_event:
                stomatology_event[event_data] = service['subgroup']

    # Отображение случая на подгруппу по взрослой диспансеризации
    # (спользуется для рассчёта первого этапа по взрослой диспансеризации)
    adult_examination_event = {}
    for service in accepted_services:
        if service['group'] == 7 and service['subgroup'] in (19, 20, 21, 22):
            event_data = service['event_id']
            if event_data not in adult_examination_event:
                adult_examination_event[event_data] = service['subgroup']

    if DEBUG:
        file_viewed_service = file('log.csv', 'w')

    # Рассчёт сводных сумм
    for service in accepted_services:
        gender = 'male' if patients[service['patient_id']]['gender_code'] == 1 else 'female'
        # Список коэффициентов для текущей услуги
        coefficient_service = coefficients.get(service['id'], [])

        # Признак того что такой случай уже был просмотрен
        # (используется для подсчёта количества обращений)
        is_viewed_event = service['event_id'] in viewed_event

        # Признак возраста пациента
        age = 'children' if service['code'][0] == '1' else 'adult'

        # Список словарей, определяющих условие, по которому услуга относится
        # к тому или иному виду помощи, правила рассчёта сумм и
        # кортеж уникальности пациента
        rules_list = [
            # Круглосуточный стационар
            {'condition': service['term'] == 1,
             'term': 'hospital',
             'unique_patient': (service['patient_id'], service['tariff_profile_id'], service['group'], age),
             'column_condition': {}},

            # Дневной стационар
            {'condition': service['term'] == 2,
             'term': 'day_hospital',
             'unique_patient': (service['patient_id'], service['division_term'],
                                service['tariff_profile_id'], service['group'], age),
             'column_condition': {}},

            # Поликлиника (подушевое)
            {'condition': service['term'] == 3
             and service['event_id'] in capitation_events,
             'term': 'policlinic_capitation',
             'unique_patient': (service['patient_id'], service['reason'],
                                service['division_id'], age),
             'column_condition': {
                 'treatment': {
                     'condition': service['event_id'] in treatment_events
                     and not is_viewed_event,
                     'value': 1
                 },
                 'accepted_payment': {
                     'condition': service['event_id'] in capitation_events,
                     'value': 0
                 }}},

            # Поликлиника
            {'condition': service['term'] == 3 and service['event_id'] not in capitation_events
             and service['group'] != 19,
             'term': 'policlinic',
             'unique_patient': (service['patient_id'], service['reason'], service['division_id'], age),
             'column_condition': {
                 'treatment': {
                     'condition': service['event_id'] in treatment_events
                     and not is_viewed_event,
                     'value': 1
                 }}},

            # Диспансеризация взрослых
            {'condition': not service['term'] and service['group'] in (7, 25, 26),
             'term': 'examination_adult',
             'unique_patient': (service['patient_id'], service['code_id'], age),
             'column_condition': {}},

            # Диспансеризация
            {'condition': not service['term'] and service['group'] not in (7, 25, 26),
             'term': 'examination',
             'unique_patient': (service['patient_id'], service['subgroup'], None, age) if service['subgroup']
             else (service['patient_id'], None, service['code_id'], age),
             'column_condition': {}},

            # Стоматология
            {'condition': service['term'] == 3 and service['group'] == 19,
             'term': 'stomatology',
             'unique_patient': (service['patient_id'],
                                service['subgroup'], age),
             'column_condition': {
                 'population': {
                     'condition': not service['subgroup'],
                     'value': 0
                 },
                 'treatment': {
                     'condition': service['subgroup'] == 12
                     and service['event_id'] in treatment_events
                     and not is_viewed_event,
                     'value': 1
                 },
                 'services': {
                     'condition': not service['subgroup'],
                     'value': 0
                 },
                 'days': {
                     'condition': True,
                     'value': service['uet']
                 }
             }},

            # Скорая помощь
            {'condition': service['term'] == 4,
             'term': 'ambulance',
             'unique_patient': (service['patient_id'], service['division_id'], age),
             'column_condition': {
                 'accepted_payment': {
                     'condition': service['event_id'] in capitation_events,
                     'value': 0
                 }
             }}
        ]

        # Поиск к какому виду помощи относится услуга
        term = None
        column_condition = None
        patient = None
        for rule in rules_list:
            if rule['condition']:
                term = rule['term']
                column_condition = rule['column_condition']
                patient = rule['unique_patient']
        if not term:
            term = 'unidentified'
            patient = (service['patient_id'], service['code'])
            column_condition = {}

        # Признак того что такой пациент уже был просмотрен
        # (используется для подсчёта численности)
        is_viewed_patient = patient in viewed_patient[term]

        # Значения используемые для рассчёта сумм по умолчанию
        value_default = {
            'population': 1 if not is_viewed_patient else 0,
            'treatment': 0,
            'services': 1,
            'days': service['quantity'],
            'basic_tariff': service['tariff'],
            'accepted_payment': service['provided_tariff'] if service['payment_type'] in [3] else
            (service['provided_tariff'] + service['accepted_payment'] if service['payment_type'] in [4] else service['accepted_payment'])
        }

        sum_tariff_coefficient = float(service['tariff'])

        for code in sorted(coef_to_field):
            field = coef_to_field[code]
            prec = 3 if code == 2 or \
                (code == 6 and handbooks['mo_info']['is_agma_cathedra'])else 2
            if code in coefficient_service:
                if code == 6:
                    value = 0
                else:
                    value = round((handbooks['coefficient_type'][code]['value']-1)*service['tariff'], prec)
                    sum_tariff_coefficient += value
            else:
                value = 0
            value_default[field] = value

        if term not in sum_division_nogroup:
            sum_division_nogroup[term] = {}
            sum_division_group[term] = {}

        # Расчёт сумм для услуг не имеющих групп, неопознанных или имеющих группы-исключения
        if not service['group'] or (service['group'] and service['group'] in exception_group) \
                or term == 'unidentified':
            # Получение информации о способе группировки
            division_by = division_by_dict[term]
            # Получение идентификатора раздела
            section = service[division_by['section']] if division_by['section'] else 0
            if service['group'] == 7:
                section = adult_examination_event.get(service['event_id'], 0)

            if section not in sum_division_nogroup[term]:
                sum_division_nogroup[term][section] = {}

            # Вычисления для групп - исключений
            # для стоматологии
            if service['group'] == 19:
                event_data = (service['event_id'], service['start_date'], service['end_date'])
                division = stomatology_event.get(event_data, None)
            elif service['group'] == 7:
                if not service['subgroup'] or service['subgroup'] in (20, 22, 19, 21):
                    division = service['code_id']
                else:
                    division = 0
            else:
                # Вычисления для обычных услуг
                division = service[division_by['division']] or 0

            if division:
                if division not in sum_division_nogroup[term][section]:
                    sum_division_nogroup[term][section][division] = deepcopy(init_sum)

                # Расчёт сумм
                for sum_key in sum_division_nogroup[term][section][division]:
                    if sum_key in column_condition:
                        if column_condition[sum_key]['condition']:
                            value = column_condition[sum_key]['value']
                        else:
                            value = value_default[sum_key]
                    else:
                        value = value_default[sum_key]
                    sum_division_nogroup[term][section][division][sum_key][age] += value
                if DEBUG:
                    file_viewed_service.write(str(service['id'])+'\n')
        # Рассчёт сумм для услуг, имеющих обычные группы
        elif service['group'] and service['group'] not in exception_group \
                and not term == 'unidentified':

            # Получение идентификатора раздела
            section = service['group']
            if section not in sum_division_group[term]:
                sum_division_group[term][section] = {'code': {}, 'subgroup': {}}
            # Группмровка по подгруппам для услуг, имеющих подгруппы
            if service['subgroup']:
                division = service['subgroup']
                if division not in sum_division_group[term][section]['subgroup']:
                    sum_division_group[term][section]['subgroup'][division] = {'male': deepcopy(init_sum),
                                                                               'female':  deepcopy(init_sum)}

                # Рассчёт сумм
                if service['group'] in [11, 12, 13]:
                    for sum_key in sum_division_group[term][section]['subgroup'][division][gender]:
                        sum_division_group[term][section]['subgroup'][division][gender][sum_key][age] += \
                            value_default[sum_key]
                else:
                    for sum_key in sum_division_group[term][section]['subgroup'][division]['male']:
                        sum_division_group[term][section]['subgroup'][division]['male'][sum_key][age] += value_default[sum_key]
                if DEBUG:
                    file_viewed_service.write(str(service['id'])+'\n')
            # Группировка по кодам для всех остальных
            else:
                division = service['code_id']
                if division not in sum_division_group[term][section]['code']:
                    sum_division_group[term][section]['code'][division] = deepcopy(init_sum)
                # Рассчёт сумм
                for sum_key in sum_division_group[term][section]['code'][division]:
                    sum_division_group[term][section]['code'][division][sum_key][age] += value_default[sum_key]
                if DEBUG:
                    file_viewed_service.write(str(service['id'])+'\n')

        if not is_viewed_event:
            viewed_event.append(service['event_id'])

        if not is_viewed_patient:
            viewed_patient[term].append(patient)

    if DEBUG:
        file_viewed_service.close()

    # Рассчёт подушевого по поликлинике
    capitation_policlinic = {'male': deepcopy(init_sum), 'female': deepcopy(init_sum)}
    for gender in capitation_policlinic:
        capitation_policlinic[gender]['population']['adult'] = \
            sum_capitation_policlinic[gender]['population']['adult']
        capitation_policlinic[gender]['population']['children'] =\
            sum_capitation_policlinic[gender]['population']['children']
        capitation_policlinic[gender]['services']['adult'] = \
            sum_capitation_policlinic[gender]['tariff']['adult']
        capitation_policlinic[gender]['services']['children'] = \
            sum_capitation_policlinic[gender]['tariff']['children']
        capitation_policlinic[gender]['basic_tariff']['adult'] = \
            sum_capitation_policlinic[gender]['population_tariff']['adult']
        capitation_policlinic[gender]['basic_tariff']['children'] = \
            sum_capitation_policlinic[gender]['population_tariff']['children']
        capitation_policlinic[gender]['indexFAP']['adult'] = \
            sum_capitation_policlinic[gender]['coefficient']['adult']
        capitation_policlinic[gender]['indexFAP']['children'] = \
            sum_capitation_policlinic[gender]['coefficient']['children']
        capitation_policlinic[gender]['accepted_payment']['adult'] = \
            sum_capitation_policlinic[gender]['accepted_payment']['adult']
        capitation_policlinic[gender]['accepted_payment']['children'] = \
            sum_capitation_policlinic[gender]['accepted_payment']['children']

    # Рассчёт подушевого по скорой помощи
    capitation_ambulance = {'male': deepcopy(init_sum), 'female': deepcopy(init_sum)}
    for gender in capitation_ambulance:
        capitation_ambulance[gender]['population']['adult'] = \
            sum_capitation_ambulance[gender]['population']['adult']
        capitation_ambulance[gender]['population']['children'] = \
            sum_capitation_ambulance[gender]['population']['children']
        capitation_ambulance[gender]['services']['adult'] = \
            sum_capitation_ambulance[gender]['tariff']['adult']
        capitation_ambulance[gender]['services']['children'] = \
            sum_capitation_ambulance[gender]['tariff']['children']
        capitation_ambulance[gender]['basic_tariff']['adult'] = \
            sum_capitation_ambulance[gender]['population_tariff']['adult']
        capitation_ambulance[gender]['basic_tariff']['children'] = \
            sum_capitation_ambulance[gender]['population_tariff']['children']
        capitation_ambulance[gender]['indexFAP']['adult'] = \
            sum_capitation_ambulance[gender]['coefficient']['adult']
        capitation_ambulance[gender]['indexFAP']['children'] = \
            sum_capitation_ambulance[gender]['coefficient']['children']
        capitation_ambulance[gender]['accepted_payment']['adult'] = \
            sum_capitation_ambulance[gender]['accepted_payment']['adult']
        capitation_ambulance[gender]['accepted_payment']['children'] = \
            sum_capitation_ambulance[gender]['accepted_payment']['children']

    capitation_total = deepcopy(init_sum)
    capitation_total = calculate_total_sum_adv(capitation_total, capitation_policlinic['male'], column_keys, round_point=2)
    capitation_total = calculate_total_sum_adv(capitation_total, capitation_policlinic['female'], column_keys, round_point=2)
    capitation_total = calculate_total_sum_adv(capitation_total, capitation_ambulance['male'], column_keys, round_point=2)
    capitation_total = calculate_total_sum_adv(capitation_total, capitation_ambulance['female'], column_keys, round_point=2)

    # Распечатка сводного акта
    act_book.set_sheet(0)
    act_book.set_cursor(2, 0)
    act_book.write_cell(mo+' '+handbooks['mo_info']['name'])
    act_book.set_cursor(2, 9)
    act_book.write_cell(u'за %s %s г.' % (MONTH_NAME[period], year))
    act_book.set_cursor(3, 0)
    act_book.write_cell(u'Частичный реестр: %s' % ','.join(handbooks['partial_register']))

    act_book.set_cursor(7, 0)
    for term in term_keys:
        if sum_division_nogroup.get(term, None):
            # Cправочник наименований отделений
            division_name_handbook = handbooks[division_by_dict[term]['name']]
            # Распечатка сводных сумм услуг без групп
            for section in sum_division_nogroup[term]:
                # Распечатка заголовка раздела
                act_book.set_style(TITLE_STYLE)
                if section:
                    title_handbook = handbooks[division_by_dict[term]['title_section']]
                    title = u'%s (%s)' % (division_by_dict[term]['title_term'],
                                          title_handbook[section]['name'])
                else:
                    title = division_by_dict[term]['title_term']
                print title
                act_book.write_cell(title, 'r', 24)

                total_sum_section = deepcopy(init_sum)                    # Итоговая сумма по разделу

                # Распечатка сводных сумм по отделениям
                act_book.set_style(VALUE_STYLE)
                for division in sorted(sum_division_nogroup[term][section]):
                    sum_value = sum_division_nogroup[term][section][division]
                    total_sum_section = calculate_total_sum_adv(total_sum_section, sum_value, column_keys)
                    division_name = division_name_handbook[division]['name'] \
                        if division_name_handbook.get(division, None) else u' '
                    if term == 'hospital' and handbooks['mo_info']['is_agma_cathedra']:
                        print_sum(act_book, division_name, sum_value, column_keys, prec=3)
                    else:
                        print_sum(act_book, division_name, sum_value, column_keys)

                total_sum_mo = calculate_total_sum_adv(total_sum_mo, total_sum_section, column_keys)

                # Распечатка итоговой сумы по разделу
                print_sum(act_book, u'Итого', total_sum_section, column_keys, style=TOTAL_STYLE)
                act_book.row_inc()

        if sum_division_group.get(term, None):
            # Распечатка сводных услуг с группами
            for section in sorted(sum_division_group[term]):
                # Распечатка заголовка раздела
                act_book.set_style(TITLE_STYLE)
                title = handbooks['medical_groups'][section]['name']
                print title
                act_book.write_cell(title, 'r', 24)

                total_sum_section = deepcopy(init_sum)                    # Итоговая сумма по разделу

                # Распечатка сводных сумм
                act_book.set_style(VALUE_STYLE)

                # Распечатка услуг, разделённых по кодам
                for division in sorted(sum_division_group[term][section]['code']):
                    sum_value = sum_division_group[term][section]['code'][division]
                    total_sum_section = calculate_total_sum_adv(total_sum_section, sum_value, column_keys)
                    print_sum(act_book, handbooks['medical_code'][division]['name'], sum_value, column_keys)

                # Распечатка услуг, разделённых по подгруппам
                if term == 'examination' and section in [11, 12, 13]:
                    for division in sorted(sum_division_group[term][section]['subgroup']):
                        sum_value = sum_division_group[term][section]['subgroup'][division]['female']
                        total_sum_section = calculate_total_sum_adv(total_sum_section, sum_value, column_keys)
                        print_sum(act_book, handbooks['medical_subgroups'][division]['name']+u', девочки', sum_value, column_keys)
                        sum_value = sum_division_group[term][section]['subgroup'][division]['male']
                        total_sum_section = calculate_total_sum_adv(total_sum_section, sum_value, column_keys)
                        print_sum(act_book, handbooks['medical_subgroups'][division]['name']+u', мальчики', sum_value, column_keys)

                else:
                    for division in sorted(sum_division_group[term][section]['subgroup']):
                        sum_value = sum_division_group[term][section]['subgroup'][division]['male']
                        total_sum_section = calculate_total_sum_adv(total_sum_section, sum_value, column_keys)
                        print_sum(act_book, handbooks['medical_subgroups'][division]['name'], sum_value, column_keys)

                total_sum_mo = calculate_total_sum_adv(total_sum_mo, total_sum_section, column_keys)

                # Распечатка итоговой суммы по разделу
                print_sum(act_book, u'Итого', total_sum_section, column_keys, style=TOTAL_STYLE)
                act_book.row_inc()

    # Распечатка итоговой суммы по МО
    print_sum(act_book, u'Итого по МО', total_sum_mo, column_keys, style=TOTAL_STYLE)

    # Распечатка итоговой суммы и подушевого
    if capitation_ambulance['male'] != init_sum \
            or capitation_ambulance['female'] != init_sum \
            or capitation_policlinic['male'] != init_sum \
            or capitation_policlinic['female'] != init_sum:
        act_book.row_inc()
        act_book.set_style(TITLE_STYLE)
        act_book.write_cell(u'Подушевой норматив', 'c', 4)
        act_book.write_cell(u'ТАРИФ', 'c', 1)
        act_book.write_cell(u' ', 'r', 17)
        print_sum(act_book, u'Подушевой норматив по амбул. мед. помощи муж.',
                  capitation_policlinic['male'], column_keys, style=VALUE_STYLE)
        print_sum(act_book, u'Подушевой норматив по амбул. мед. помощи жен.',
                  capitation_policlinic['female'], column_keys, style=VALUE_STYLE)
        print_sum(act_book, u'Подушевой норматив по скорой мед. помощи муж.',
                  capitation_ambulance['male'], column_keys, style=VALUE_STYLE)
        print_sum(act_book, u'Подушевой норматив по скорой мед. помощи жен.',
                  capitation_ambulance['female'], column_keys, style=VALUE_STYLE)
        print_sum(act_book, u'Итого по подушевому нормативу',
                  capitation_total, column_keys, style=TOTAL_STYLE)

        total_sum_mo = calculate_total_sum_adv(total_sum_mo, capitation_total, column_keys)
        act_book.row_inc()
        print_sum(act_book, u'ИТОГО по МО с подушевым нормативом',
                  total_sum_mo, column_keys, style=TOTAL_STYLE)


### Распечатка суммы (по отделению, причинам отказа, виду помощи и т. д
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


### Рассчёт итоговой суммы
def calculate_total_sum(total_sum, intermediate_sum):
    for key in total_sum:
        total_sum[key] += intermediate_sum[key]
    return total_sum
'''


### Печатает сводный реестр для экономистов
### Формат вызова print_act_econom год период статус_реестра признак_печати_для_прикреплённых_больниц(1 если надо)
class Command(BaseCommand):
    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        status = int(args[2])
        is_partial_register = args[3] if len(args) == 4 else 0
        printed_act = []
        template = BASE_DIR + r'\templates\excel_pattern\reestr_201408_test.xls'
        target_dir = REESTR_DIR if status in (8, 6) else REESTR_EXP
        handbooks = {'failure_causes': register_function.get_failure_causes(),
                     'errors_code': register_function.get_errors(),
                     'workers_speciality': register_function.get_medical_worker_speciality(),
                     'tariff_profile': register_function.get_tariff_profile(),
                     'medical_terms': register_function.get_medical_term(),
                     'medical_reasons': register_function.get_medical_reason(),
                     'medical_division': register_function.get_medical_division(),
                     'medical_code': register_function.get_medical_code(),
                     'medical_groups': register_function.get_medical_group(),
                     'medical_subgroups': register_function.get_medical_subgroup(),
                     'medical_profile': register_function.get_medical_profile(),
                     'coefficient_type': register_function.get_coefficient_type()}
        organizations = register_function.get_mo_register(year, period, status=status)
        for mo in organizations:
            partial_register = register_function.get_partial_register(year, period, mo)
            handbooks['partial_register'] = partial_register
            handbooks['mo_info'] = register_function.get_mo_info(mo)
            print u'Сборка сводного реестра для', mo
            print u'Загрузка данных...'
            data = {
                'patients': register_function.get_patients(year, period, mo),
                'sanctions': register_function.get_sanctions(year, period, mo),
                'coefficients': register_function.get_coefficients(year, period, mo),
                'invoiced_services': register_function.get_services(year, period, mo),
                'accepted_services': register_function.get_services(year, period, mo, payment_type=[2, 4]),
                'discontinued_services': register_function.get_services(year, period, mo,
                                                                        payment_type=[3, 4],
                                                                        is_include_operation=True)
            }

            print u'Поиск случаев с обращениями...'
            treatment_events = register_function.get_treatment_events(year, period, mo)
            print u'Поиск случаев с подушевым...'
            capitation_events = register_function.get_capitation_events(year, period, mo)

            sum_capitation_policlinic = register_function.calculate_capitation_tariff(3, year, period, mo)
            sum_capitation_ambulance = register_function.calculate_capitation_tariff(4, year, period, mo)

            target = target_dir % (year, period) + ur'\поданные\%s_поданные' % \
                handbooks['mo_info']['name'].replace('"', '').strip()
            print u'Печать акта: %s ...' % target

            with ExcelWriter(target, template=template) as act_book:
                act_book.set_overall_style({'font_size': 11})
                print_accepted_services(
                    act_book=act_book, year=year, period=period,
                    mo=mo,
                    sum_capitation_policlinic=sum_capitation_policlinic,
                    sum_capitation_amb=sum_capitation_ambulance,
                    handbooks=handbooks
                )

                if status == 8:
                    register_function.pse_export(year, period, mo, 6, data, handbooks)
                if status == 3:
                    register_function.change_register_status(year, period, mo, 9)
                printed_act.append(act_book.name)
            print u'Выгружен', mo

        print u'-'*50
        print u'Напечатанные акты:'
        if status == 3:
            print u'  Предварительные акты:'
        elif status == 8:
            print u'  Акты после проверки экспертов:'
        for act in printed_act:
            print act