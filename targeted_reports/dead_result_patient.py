# -*- coding: utf-8 -*-

import psycopg2
import os
import datetime

from xlsxwriter.workbook import Workbook

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()

current_date = datetime.datetime.now().date()

report_save_path = u'T:/Куракса/Отчёты по просроченным госпитализациям/'

overdue_query = u"""
select mo.name "МО",
    --row_number() OVER () as "№ п/п",
    mr.period, p.last_name "Фамилия", p.first_name "Имя", p.middle_name "Отчество",
    to_char(p.birthdate, 'YYYY-MM-DD') "ДР",
    trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) "Полис",
    to_char(ps.start_date, 'YYYY-MM-DD') as "Начало",
    to_char(ps.end_date, 'YYYY-MM-DD') as "Конец",
    md.name as "Отделение",
    ms.code "Услуга",
    pe.anamnesis_number "Номер карты",
    idc.idc_code "Код диагноза",
    idc.name "Диагноз",
    ps.quantity "Кол-во",
    (case ps.payment_type_fk when 2 then ps.accepted_payment else 0 end) "Оплачено",
    ps.tariff "Тариф",
    (case ps.payment_type_fk WHEN 2 THEN '' ELSE array_to_string(ARRAY(
        select DISTINCT me.old_code
        from provided_service_sanction pss
            join medical_error me
                on me.id_pk = pss.error_fk
        WHERE
            pss.service_fk = ps.id_pk and pss.is_active
            and pss.type_fk = 1
    ), ' ') END ) "Ошибки",
    case ms.group_fk when 19 then ms.uet else 0 end as "УЕТ",
    dep.old_code "Подразделение",
    tr.name,
    e.act_number, e.underpayment, e.penalty, e.sanction_date
from provided_service ps
    JOIN provided_event pe
        on ps.event_fk = pe.id_pk
    JOIN medical_register_record mrr
        on mrr.id_pk = pe.record_fk
    JOIN medical_register mr
        on mr.id_pk = mrr.register_fk
    JOIN medical_organization dep
        on dep.id_pk = ps.department_fk
    JOIN medical_register_status mrs
        on mrs.id_pk = mr.status_fk
    JOIN patient p
        on p.id_pk = mrr.patient_fk
    LEFT JOIN medical_division md
        on md.id_pk = ps.division_fk
    LEFT JOIN medical_service_profile msp
        on msp.id_pk = ps.profile_fk
    JOIN medical_service ms
        on ms.id_pk = ps.code_fk
    LEFT JOIN idc
        on idc.id_pk = ps.basic_disease_fk
    left join medical_service_term mst
        on mst.id_pk = pe.term_fk
    LEFT join treatment_result tr
        on tr.id_pk = pe.treatment_result_fk
    LEFT join provided_service_sanction pss
        on pss.service_fk = ps.id_pk and pss.is_active and pss.type_fk = 1
    LEFT JOIN medical_error me
        on me.id_pk = pss.error_fk

    JOIN medical_organization mo
        on mo.code = mr.organization_code and mo.parent_fk is null

    LEFT JOIN idc idc1
        on idc1.id_pk = pe.initial_disease_fk
    LEFT JOIN idc idc2
        on idc2.id_pk = pe.basic_disease_fk

    /*
    left join expertiza e
        on e.policy = trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number))
            and ms.code = e.service_code and ps.end_date = e.end_date and idc.idc_code = e.disease
            and mr.organization_code = e.organization and (kinda = '2' or kindp = '2')
            and e.act_number like 'КЦ%%'
    */

where mr.is_active
    and mr.year = '2015'
    and mr.period = '12'
    and pe.term_fk IN (1, 2)
    and pe.treatment_result_fk in (5, 6, 15, 16)
    and ps.payment_type_fk = 2
    --and mr.organization_code = '280026'
    and ms.code not like 'A%%'
    --AND (e.act_number like 'КЦ%%' or e.act_number is NULL)
ORDER BY mo.name, mr.period, dep.old_code, p.last_name, p.first_name, p.middle_name

    """

year = '2015'
period = '12'

cursor_pg.execute(overdue_query, dict(year=year, period=period))
result = cursor_pg.fetchall()

current_mo = None

columns = [u'', u'Период', #u'№ п/п',
           u'Фамилия', u'Имя',
           u'Отчество', u'ДР',
           u'Полис',
           u'Начало',
           u'Окончание',
           u'Отделение',
           u'Услуга',
           u'Номер карты',
           u'Код диагноза',
           u'Диагноз',
           u'Кол-во',
           u'Оплачено',
           u'Тариф',
           u'Ошибки',
           u'УЕТ',
           u'Подразделение', u'Результат', u'Номер акта', u'Недоплата', u'Штраф', u'Дата', u'']

widths = [1, 6, 14, 14, 17, 10, 18, 10, 10, 29,
          10, 12, 12, 46, 10, 12, 12, 12, 10, 14, 18, 18, 18, 18, 18]

workbook = None

row_number = 1

recieved_date = None
save_dir = u'c:/work/dead_result/'

for rec in result:
    if current_mo != rec[0]:

        if workbook:
            workbook.close()
            row_number = 1

        current_mo = rec[0]
        mo_name = rec[0].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, u'%s%s' % (mo_name, u'.xlsx'))

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