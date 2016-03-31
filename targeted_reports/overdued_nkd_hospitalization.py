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
select *,
    case when nkd <= 1 then 100
    else round(T.quantity / T.nkd * 100, 0)
    END
from (
    select DISTINCT medical_organization.name as organization_name,
        mst.name as term_name,
        department.old_code as department_code,
        format('%%s %%s %%s', patient.last_name, patient.first_name, patient.middle_name) as fio,
        patient.birthdate, idc.idc_code, medical_service.code,
        tp.name as profile_name,
        provided_service.accepted_payment, provided_service.start_date, provided_service.end_date,
        COALESCE(
                (
                    select tariff_nkd.value
                    from tariff_nkd
                    where start_date = (
                        select max(start_date)
                        from tariff_nkd
                        where start_date <= greatest('2016-01-01'::DATE, provided_service.end_date) and start_date >= '2016-01-01'::DATE
                            and profile_fk = medical_service.tariff_profile_fk
                            and is_children_profile = provided_service.is_children_profile
                            and "level" = department.level
                    ) and profile_fk = medical_service.tariff_profile_fk
                        and is_children_profile = provided_service.is_children_profile
                        and (( provided_event.term_fk = 1 and "level" = department.level)
                            or (provided_event.term_fk = 2)
                        )
                    order by start_date DESC
                    limit 1
                ), 1
        ) as nkd,
        provided_service.quantity as quantity
    from
        provided_service
        join provided_event
            on provided_event.id_pk = provided_service.event_fk
        join medical_register_record
            on medical_register_record.id_pk = provided_event.record_fk
        join medical_register
            on medical_register_record.register_fk = medical_register.id_pk
        JOIN medical_service
            on medical_service.id_pk = provided_service.code_fk
        JOIN medical_organization department
            on department.id_pk = provided_service.department_fk
        join medical_organization
            on medical_organization.code = medical_register.organization_code
                and medical_organization.parent_fk is null
        join patient
            on patient.id_pk = medical_register_record.patient_fk
        JOIN idc
            on idc.id_pk = provided_service.basic_disease_fk
        JOIN medical_service_term mst
            on mst.id_pk = provided_event.term_fk
        LEFT JOIN tariff_profile tp
            on tp.id_pk = medical_service.tariff_profile_fk
    where medical_register.is_active
        and medical_register.year = %(year)s
        and medical_register.period = %(period)s
        and medical_register.organization_code = '280069'
        and provided_event.term_fk in (1, 2)
        and provided_service.tariff > 0
        and provided_service.payment_type_fk = 2

) as T
where
    case when nkd <= 1 then 100
    else round(T.quantity / T.nkd * 100, 0)
    END >= 150
    or
    case when nkd <= 1 then 100
    else round(T.quantity / T.nkd * 100, 0)
    END <= 50
ORDER BY organization_name, term_name, fio

    """

year = '2016'
period = '02'
cursor_pg.execute(overdue_query, dict(year=year, period=period))
result = cursor_pg.fetchall()

current_mo = None

columns = [u'', u'Условия', u'Подразделение',
           u'ФИО',
           u'ДР',
           u'Код диагноза',
           u'Услуга',
           u'Профиль',
           u'Оплачено',
           u'Начало услуги',
           u'Окончание услуги',
           u'Средняя прод-сть',
           u'Факт. прод-сть',
           u'Процент', u'', ]

widths = [1, 1, 15, 22, 12, 10, 12, 26, 10, 12, 12, 12, 12, 12]

workbook = None

row_number = 1

recieved_date = None
save_dir = u'c:/work/OVERDUED_NKD/'

for rec in result:
    if current_mo != rec[0]:
        current_term = rec[1]

        if workbook:
            workbook.close()
            row_number = 1

        current_mo = rec[0]
        mo_name = rec[0].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, u'%s %s%s' % (mo_name, current_term.decode('utf-8'), u'.xlsx'))

        workbook = Workbook(path)
        worksheet = workbook.add_worksheet('1')

        bold = workbook.add_format({'bold': True})
        print len(columns)

        for i, column in enumerate(rec):
            worksheet.set_column(i, i, widths[i])
            worksheet.write(0, i, columns[i], bold)

    if current_term != rec[1]:
        if workbook:
            workbook.close()
            row_number = 1

        current_term = rec[1]

        mo_name = rec[0].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, u'%s %s%s' % (mo_name, current_term.decode('utf-8'), u'.xlsx'))

        workbook = Workbook(path)
        worksheet = workbook.add_worksheet('1')

        bold = workbook.add_format({'bold': True})
        print len(columns)

        for i, column in enumerate(rec):
            worksheet.set_column(i, i, widths[i])
            worksheet.write(0, i, columns[i], bold)

    for i, column in enumerate(rec):

        if type(column) == str:
            value = column.decode('utf-8')
        elif type(column) == type(current_date):
            value = str(column)
        else:
            value = column

        worksheet.write(row_number, i, value)


    row_number += 1

workbook.close()

connect_pg.close()