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

# Острый коронарный синдромом (ОКС) и острое нарушение мозгового кровообращения (ОНМК)

overdue_query = """
select mo.name "МО",
    row_number() OVER (PARTITION BY mo.name order by dep.old_code, p.last_name, p.first_name, p.middle_name) as "№ п/п",
    p.last_name "Фамилия", p.first_name "Имя", p.middle_name "Отчество",
    to_char(p.birthdate, 'YYYY-MM-DD') "ДР",
    trim(BOTH ' ' from format('%s %s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) "Полис",
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
    dep.old_code "Подразделение"
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

where mr.is_active
    and mr.year = '2016'
    and mr.period = '02'
    and mr.organization_code NOT IN ('280075', '280001', '280026', '280003', '280027',  '280084') --'280038', '280085', '280083', '280036', '280066', '280001', '280052'
    and (idc.idc_code IN (
        'I20.0', 'I21.9', 'I22.0', 'I22.1', 'I22.8', 'I22.9', 'I23.8', 'I26.0', 'I26.9',
        'G45.8', 'G45.9',
        'I61.8', 'I61.9', 'I62.0', 'I62.1', 'I62.9',
        'I63.8', 'I63.9', 'I64.0'
) or idc.idc_code between 'I21.0' and 'I21.4' or idc.idc_code between 'I23.0' and 'I23.6' or idc.idc_code between 'G46.0' and 'G46.8' or idc.idc_code between 'I60.0' and 'I60.9'
or idc.idc_code between 'I61.0' and 'I61.6' or idc.idc_code between 'I63.0' and 'I63.6' or idc.idc_code between 'G45.0' and 'G45.4')
    and (ms.group_fk not in (1, 2) or ms.group_fk is null)
    and pe.term_fk in (1)
    and (md.name not ilike '%%РСЦ%%' and md.name not ilike '%%ПСО%%')
    --and mo.code = '280017'
    and ps.payment_type_fk = 2
    and ms.code LIKE '_98%%'
ORDER BY mo.name, dep.old_code, p.last_name, p.first_name, p.middle_name

    """

cursor_pg.execute(overdue_query)
result = cursor_pg.fetchall()

current_mo = None

columns = [u'', u'№ п/п',
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
           u'Подразделение', u'']

widths = [1, 6, 14, 14, 17, 10, 18, 10, 10, 29,
          10, 12, 12, 46, 10, 12, 12, 12, 10, 14]

workbook = None

row_number = 1

recieved_date = None
save_dir = u'c:/work/OKS_ONMK/'


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
