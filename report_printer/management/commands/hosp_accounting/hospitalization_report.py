# -*- coding: utf-8 -*-

import psycopg2
import os
import datetime

from xlsxwriter.workbook import Workbook

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()
cursor_pg_2 = connect_pg.cursor()

current_date = datetime.datetime.now().date()

query = u"""
select row_number() over (), sender_name, last_name,
    first_name, middle_name, birthdate, number,
    reciever_name, napr_division, fact_division,
    napr_date, napr_plan_date, napr_plan_date-napr_date,
    napr_hosp_date, napr_cancel_date, napr_urgent_date, files
FROM (
    select sender.name as sender_name,
        T.last_name, T.first_name, T.middle_name, T.birthdate,
        h.number,
        receiver.name as reciever_name,
        (
            select md.name
            from hospitalization hi

                LEFT join medical_division md
                    on md.id_pk = hi.division_fk
            WHERE hi.number = h.number and hi.type = 1
            ORDER BY md.name ASC nulls last
            limit 1
        ) napr_division,
        (
            select md.name
            from hospitalization hi

                LEFT join medical_division md
                    on md.id_pk = hi.division_fk
            WHERE hi.number = h.number and hi.type in (2, 3, 4)
            ORDER BY md.name ASC nulls last
            limit 1
        ) fact_division,
        coalesce((select max("date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 1

        )) as napr_date,

        GREATEST(
        coalesce( (select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 1
        and received_date >= h.received_date
        )),
        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 9),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 9))) as napr_plan_date,

        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 2),(select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 2
        and received_date >= h.received_date
        )) as napr_hosp_date,

        coalesce((select max("end_date") from hospitalization where "number" = h.number and "type" = 4),
        (select max("end_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 4)) as napr_cancel_date,

        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 3),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 3)) as napr_urgent_date,

        (select string_agg(casT("type" as VARCHAR), ', ')
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where (last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate)
            or (h.number = "number")
        and received_date >= h.received_date
         ) as files


/*
        (select max("date") from hospitalization where "number" = h.number and "type" = 1) as napr_date,

        GREATEST((select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("start_date") from hospitalization where "number" = h.number and "type" = 9)) as napr_plan_date,

        (select max("start_date") from hospitalization where "number" = h.number and "type" = 2) as napr_hosp_date,
        (select max("end_date") from hospitalization where "number" = h.number and "type" = 4) as napr_cancel_date,
        (select max("start_date") from hospitalization where "number" = h.number and "type" = 3) as napr_urgent_date,
        (select string_agg(casT("type" as VARCHAR), ', ') from hospitalization where "number" = h.number) as files
*/


    from
        hospitalization h

        LEFT JOIN hospitalization_type ht
            on ht.id_pk = h.type
        LEFT join LATERAL
             (
                select hpi.id_pk, hpi.last_name, hpi.first_name, hpi.middle_name, hpi.birthdate
                from hospitalization hi
                    join hospitalization_patient hpi
                        on hpi.id_pk = hi.patient_fk
                WHERE h.number = hi.number
                ORDER BY hi.patient_fk DESC NULLS LAST
            ) T on true
        LEFT JOIN medical_organization sender
            on sender.id_pk = h.organization_sender_fk
        LEFT JOIN medical_organization receiver
            on receiver.id_pk = h.organization_reciever_fk

        LEFT JOIN idc
            on idc.id_pk = h.disease_fk

    where
        h.received_date between %(start_date)s and %(end_date)s
        and sender.code = %(mo_code)s -- , '280017', '280026'
    GROUP BY sender.name, h.number, receiver.name, T.last_name, T.first_name, T.middle_name, T.birthdate, h.received_date
    ORDER BY number
) as Z
"""

query_2 = u"""
select row_number() over (), sender_name, last_name,
    first_name, middle_name, birthdate, number,
    reciever_name, napr_division, fact_division,
    napr_date, napr_plan_date, napr_plan_date-napr_date,
    napr_hosp_date, napr_cancel_date, napr_urgent_date, files
FROM (
    select sender.name as sender_name,
        T.last_name, T.first_name, T.middle_name, T.birthdate,
        h.number,
        receiver.name as reciever_name,
        (
            select md.name
            from hospitalization hi

                LEFT join medical_division md
                    on md.id_pk = hi.division_fk
            WHERE hi.number = h.number and hi.type = 1
            ORDER BY md.name ASC nulls last
            limit 1
        ) napr_division,
        (
            select md.name
            from hospitalization hi

                LEFT join medical_division md
                    on md.id_pk = hi.division_fk
            WHERE hi.number = h.number and hi.type in (2, 3, 4)
            ORDER BY md.name ASC nulls last
            limit 1
        ) fact_division,
        coalesce((select max("date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 1

        )) as napr_date,

        GREATEST(
        coalesce( (select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 1
        and received_date >= h.received_date
        )),
        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 9),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 9))) as napr_plan_date,

        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 2),(select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and "type" = 2
        and received_date >= h.received_date
        )) as napr_hosp_date,

        coalesce((select max("end_date") from hospitalization where "number" = h.number and "type" = 4),
        (select max("end_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 4)) as napr_cancel_date,

        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 3),
        (select max("start_date")
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
        and received_date >= h.received_date
        and "type" = 3)) as napr_urgent_date,

        (select string_agg(casT("type" as VARCHAR), ', ')
        from hospitalization
            join hospitalization_patient
                on hospitalization_patient.id_pk = hospitalization.patient_fk
        where (last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate)
            or (h.number = "number")
        and received_date >= h.received_date
         ) as files


/*
        (select max("date") from hospitalization where "number" = h.number and "type" = 1) as napr_date,

        GREATEST((select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
        (select max("start_date") from hospitalization where "number" = h.number and "type" = 9)) as napr_plan_date,

        (select max("start_date") from hospitalization where "number" = h.number and "type" = 2) as napr_hosp_date,
        (select max("end_date") from hospitalization where "number" = h.number and "type" = 4) as napr_cancel_date,
        (select max("start_date") from hospitalization where "number" = h.number and "type" = 3) as napr_urgent_date,
        (select string_agg(casT("type" as VARCHAR), ', ') from hospitalization where "number" = h.number) as files
*/


    from
        hospitalization h

        LEFT JOIN hospitalization_type ht
            on ht.id_pk = h.type
        LEFT join LATERAL
             (
                select hpi.id_pk, hpi.last_name, hpi.first_name, hpi.middle_name, hpi.birthdate
                from hospitalization hi
                    join hospitalization_patient hpi
                        on hpi.id_pk = hi.patient_fk
                WHERE h.number = hi.number
                ORDER BY hi.patient_fk DESC NULLS LAST
            ) T on true
        LEFT JOIN medical_organization sender
            on sender.id_pk = h.organization_sender_fk
        LEFT JOIN medical_organization receiver
            on receiver.id_pk = h.organization_reciever_fk

        LEFT JOIN idc
            on idc.id_pk = h.disease_fk

    where
        h.received_date between %(start_date)s and %(end_date)s
        and receiver.code = %(mo_code)s -- , '280017', '280026'
    GROUP BY sender.name, h.number, receiver.name, T.last_name, T.first_name, T.middle_name, T.birthdate, h.received_date
    ORDER BY number
) as Z
"""
#cursor_pg.execute(query, dict(year=year, period=period))
#result = cursor_pg.fetchall()

current_mo = None

columns = [u'№', u'Отправитель', u'', u'ФИО', u'', u'ДР', u'Номер напр.',
           u'Получатель', u'Отделение в направлении', u'Отделение в госпит.',
           u'Дата напр.', u'Плановая дата госп.', u'Разница (дн.)',
           u'Плановая госп.', u'Аннулирование', u'Экстренная госп.', u'Файлы']

widths = [10, 42, 15, 15, 20, 10, 16, 42, 40, 40, 10, 10, 10, 10, 10, 10, 12]

workbook = None

row_number = 1

recieved_date = None
save_dir = u'c:/work/hospitalization_reports/'
start_date = '2015-11-12'
end_date = '2015-11-17'

cursor_pg.execute('select code, name from medical_organization where parent_fk is null')
mos = cursor_pg.fetchall()

for mo in mos:
    cursor_pg.execute(query, dict(mo_code=mo[0], start_date=start_date, end_date=end_date))
    result = cursor_pg.fetchall()

    cursor_pg_2.execute(query_2, dict(mo_code=mo[0], start_date=start_date, end_date=end_date))
    result_2 = cursor_pg_2.fetchall()

    if not result and not result_2:
        continue

    mo_name = mo

    path = u'%s/%s.xlsx' % (save_dir, mo[1].replace('"', '').decode('utf-8'))

    workbook = Workbook(path)
    worksheet = workbook.add_worksheet(u'Отправитель')

    bold = workbook.add_format({'bold': True})

    for i, column in enumerate(columns):
        worksheet.set_column(i, i, widths[i])
        worksheet.write(0, i, columns[i], bold)

    row_number = 1

    for j, rec in enumerate(result):
        for i, column in enumerate(rec):

            if type(column) == str:
                value = column.decode('utf-8')
            elif type(column) == type(current_date):
                value = str(column)
            else:
                value = column

            worksheet.write(row_number, i, value)

        row_number += 1

    row_number = 1

    worksheet2 = workbook.add_worksheet(u'Получатель')

    for i, column in enumerate(columns):
        worksheet2.set_column(i, i, widths[i])
        worksheet2.write(0, i, columns[i], bold)

    for j, rec in enumerate(result_2):
        for i, column in enumerate(rec):

            if type(column) == str:
                value = column.decode('utf-8')
            elif type(column) == type(current_date):
                value = str(column)
            else:
                value = column

            worksheet2.write(row_number, i, value)

        row_number += 1

    workbook.close()

connect_pg.close()