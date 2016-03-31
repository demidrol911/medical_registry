# -*- coding: utf-8 -*-

import psycopg2
import os
import datetime

from xlsxwriter.workbook import Workbook

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()

current_date = datetime.datetime.now().date()

overdue_query = u"""
    with all_data as (
        select DISTINCT pe.id_pk event_1, min(T.event_id) event_2
        FROM provided_service ps
            join provided_event pe
                on pe.id_pk = ps.event_fk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN insurance_policy ip
                on ip.version_id_pk = p.insurance_policy_fk
            JOIN (
                select pe1.id_pk as event_id, mr1.organization_code,
                    ip1.id, pe1.term_fk, ps1.basic_disease_fk, ps1.code_fk,
                    pe1.start_date as event_start_date,
                    pe1.end_date as event_end_date, ps1.id_pk as service_id,
                    ps1.department_fk AS department_id,
                    format('%%s-%%s-01', mr1.year, mr1.period)::DATE AS checking_period
                FROM provided_service ps1
                    join provided_event pe1
                        on pe1.id_pk = ps1.event_fk
                    JOIN medical_register_record mrr1
                        on mrr1.id_pk = pe1.record_fk
                    JOIN medical_register mr1
                        on mr1.id_pk = mrr1.register_fk
                    JOIN patient p1
                        on p1.id_pk = mrr1.patient_fk
                    JOIN insurance_policy ip1
                        on ip1.version_id_pk = p1.insurance_policy_fk
                WHERE mr1.is_active
                    and format('%%s-%%s-01', mr1.year, mr1.period)::DATE <= format('%%s-%%s-01', %(year)s, %(period)s)::DATE
                    and format('%%s-%%s-01', mr1.year, mr1.period)::DATE >= format('%%s-%%s-01', %(year)s, %(period)s)::DATE - interval '9 months'
                    and (pe1.term_fk in (1,2,4)
                        or (
                            (pe1.term_fk = 3 and
                                (select count(ps2.id_pk)
                                FROM provided_service ps2
                                    join medical_service ms2 on ms2.id_pk = ps2.code_fk
                                WHERE ps2.event_fk = ps1.event_fk
                                    and (ms2.group_fk is NULL or ms2.group_fk = 24)
                                    and ms2.reason_fk = 1
                                ) > 1
                            )
                        )
                    )
                    and ps1.payment_type_fk in (2)
                    and ps1.tariff > 0

                ) as T on T.id = ip.id and mr.organization_code = T.organization_code and T.term_fk = pe.term_fk
                    and ps.basic_disease_fk = T.basic_disease_fk and T.event_id <> pe.id_pk
                    and ps.id_pk <> T.service_id
                    and (CASE WHEN checking_period = format('%%s-%%s-01', mr.year, mr.period)::DATE THEN T.event_id < pe.id_pk ELSE True END)
        WHERE mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = '280017'
            AND ps.payment_type_fk = 2
            and (( pe.term_fk in (1, 2) and ps.code_fk = T.code_fk
                and (pe.end_date - event_start_date between 0 and 89 or pe.end_date - T.event_end_date between 0 and 89 or pe.start_date - T.event_start_date between 0 and 89 or pe.start_date - T.event_end_date  between 0 and 89))
                or (pe.term_fk = 4 and ps.code_fk = T.code_fk and age(pe.end_date, T.event_end_date) = '0 days')
                or (pe.term_fk = 4 and T.term_fk = 4 and (age(pe.end_date, T.event_end_date) BETWEEN '0 days' AND '1 days' OR age(T.event_end_date, pe.end_date) BETWEEN '0 days' AND '1 days'))
                or (pe.term_fk = 3 and ps.code_fk = T.code_fk and (age(pe.end_date, T.event_start_date) between '1 days' and '29 days' or age(pe.start_date, T.event_end_date) between '1 days' and '29 days'))
            )
            and ps.tariff > 0
            and (pe.term_fk in (1, 2, 4)
                or (
                    (pe.term_fk = 3 and
                        (select count(ps2.id_pk)
                        FROM provided_service ps2
                            join medical_service ms2 on ms2.id_pk = ps2.code_fk
                        WHERE ps2.event_fk = ps.event_fk
                            and (ms2.group_fk is NULL or ms2.group_fk = 24)
                            and ms2.reason_fk = 1
                        ) > 1
                    )


                )
            )

        group by 1
    )

    select mo.name AS mo_name,
        dep.old_code as department,
        case when pe.term_fk in (1, 2) then 'Стационар, днев. стационар' when pe.term_fk = 3 Then 'Поликлиника' when pe.term_fk = 4 Then 'Скорая помощь' END as term_name,
        p.last_name,
        p.first_name,
        p.middle_name,
        p.birthdate,
        ms.code as service_code,
        idc.idc_code as disease,
        ps.accepted_payment,
        ps.start_date,
        ps.end_date,
        pe.start_date,
        pe.end_date,
        1 as sort,
        mr.period
    from all_data
        join provided_event pe
            on pe.id_pk = all_data.event_1
        JOIN provided_service ps
            on ps.event_fk = pe.id_pk
        LEFT JOIN medical_service ms
            on ms.id_pk = ps.code_fk
        JOIN medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
        JOIN patient p
            on p.id_pk = mrr.patient_fk
        LEFT JOIN idc
            on idc.id_pk = ps.basic_disease_fk
        JOIN medical_organization dep
            on dep.id_pk = ps.department_fk
        JOIN medical_organization mo
            on mo.code = mr.organization_code and mo.parent_fk is null
    WHERE ms.code not like 'A%%'

    union

    select mo.name AS mo_name,
        dep.old_code as department,
        case when pe.term_fk in (1, 2) then 'Стационар, днев. стационар' when pe.term_fk = 3 Then 'Поликлиника' when pe.term_fk = 4 Then 'Скорая помощь' END as term_name,
        p.last_name,
        p.first_name,
        p.middle_name,
        p.birthdate,
        ms.code as service_code,
        idc.idc_code as disease,
        ps.accepted_payment,
        ps.start_date,
        ps.end_date,
        pe.start_date,
        pe.end_date,
        0 as sort,
        mr.period
    from all_data
        join provided_event pe
            on pe.id_pk = all_data.event_2 and pe.id_pk NOT IN (SELECT DISTINCT event_1 from all_data)
        JOIN provided_service ps
            on ps.event_fk = pe.id_pk
        LEFT JOIN medical_service ms
            on ms.id_pk = ps.code_fk
        JOIN medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
        JOIN patient p
            on p.id_pk = mrr.patient_fk
        LEFT JOIN idc
            on idc.id_pk = ps.basic_disease_fk
        JOIN medical_organization dep
            on dep.id_pk = ps.department_fk
        JOIN medical_organization mo
            on mo.code = mr.organization_code and mo.parent_fk is null
    WHERE ms.code not like 'A%%'
    order by mo_name, term_name, last_name, first_name, middle_name, birthdate, sort
    """

year = '2016'
period = '02'
cursor_pg.execute(overdue_query, dict(year=year, period=period))
result = cursor_pg.fetchall()

current_mo = None

columns = [u'МО',
           u'Подразделение',
           u'Условия',
           u'ФИО',
           u'',
           u'',
           u'ДР',
           u'Код диагноза',
           u'Услуга',
           u'Оплачено',
           u'Начало услуги',
           u'Окончание услуги',
           u'Начало случая',
           u'Окончание случая',
           u'Повтор', u'Период']

widths = [1, 4, 4, 12, 12, 15, 15, 19, 12, 10, 10, 10, 12, 12, 12, 12, 1, 1, 4,
          4, 22, 12, 12, 12, 12, 12, 12, 12, 12, 12]

workbook = None

row_number = 1

recieved_date = None
save_dir = u'c:/work/REPEATED/'

count_services = 0
count_all = 490/30

for rec in result:
    print rec[4], rec[5], rec[6]
    if current_mo != rec[0]:
        current_term = rec[2]

        if workbook:
            workbook.close()
            row_number = 1
            count_services = 0

        current_mo = rec[0]
        mo_name = rec[0].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, u'%s %s%s' % (mo_name, current_term.decode('utf-8'), u'.xlsx'))

        workbook = Workbook(path)
        worksheet = workbook.add_worksheet('1')

        bold = workbook.add_format({'bold': True})
        print len(columns)

        print len(rec), len(widths), len(columns)

        for i, column in enumerate(rec):
            worksheet.set_column(i, i, widths[i])
            worksheet.write(0, i, columns[i], bold)

    if current_term != rec[2]:
        if workbook:
            workbook.close()
            row_number = 1
            count_services = 0

        current_term = rec[2]

        mo_name = rec[0].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, u'%s %s%s' % (mo_name, current_term.decode('utf-8'), u'.xlsx'))

        workbook = Workbook(path)
        worksheet = workbook.add_worksheet('1')

        bold = workbook.add_format({'bold': True})
        print len(columns)

        for i, column in enumerate(rec):
            if i == 0:
                continue
            worksheet.set_column(i, i, widths[i])
            worksheet.write(0, i, columns[i], bold)

    if count_services < count_all:
        for i, column in enumerate(rec):

            if type(column) == str:
                value = column.decode('utf-8')
            elif type(column) == type(current_date):
                value = str(column)
            else:
                value = column

            worksheet.write(row_number, i, value)

    if rec[14] == 1 and current_term == u'Поликлиника':
        count_services += 1

    row_number += 1

workbook.close()

connect_pg.close()