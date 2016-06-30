# -*- coding: utf-8 -*-

import psycopg2
import os
import datetime

from xlsxwriter.workbook import Workbook

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()

current_date = datetime.datetime(year=2016, month=6, day=27) #datetime.datetime.now().date()  # datetime.datetime(year=2016, month=4, day=1)

report_save_path = u'T:/Куракса/Отчёты по просроченным госпитализациям/'

overdue_query = """
    select DISTINCT ht.name, sender.code, sender.name, hp.last_name, hp.first_name, hp.middle_name, hp.birthdate, h.number, h.start_date, idc.idc_code, hp.contact, h.received_date, receiver.name, %(current_date)s :: DATE
        --, h_i.received_date, h_i.start_date, h_i.number
    from hospitalization h
        JOIN hospitalization_type ht
            on ht.id_pk = h.type
        left join hospitalization_patient hp
            on hp.id_pk = h.patient_fk
        JOIN medical_organization sender
            on sender.id_pk = h.organization_sender_fk
        LEFT JOIN medical_organization receiver
            on receiver.id_pk = h.organization_reciever_fk

        JOIN idc
            on idc.id_pk = h.disease_fk
        left join hospitalization h_i
            on h_i.number = h.number and h_i.type in (2, 4) and h_i.start_date >= h.start_date
    where
        h.type = 1

        and %(current_date)s :: DATE - h.start_date > 30
        and h_i.id_pk is null
        and h.received_date between '2016-05-13' and '2016-06-24'
    order by --h.received_date,
    sender.code
    """

print current_date
cursor_pg.execute(overdue_query, {'current_date': current_date})
result = cursor_pg.fetchall()

current_mo = None

columns = [u'Тип',
           u'Код МО',
           u'Наименование МО',
           u'Фамилия', u'Имя',
           u'Отчество', u'ДР',
           u'Направление №',
           u'Плановая дата',
           u'Диагноз',
           u'Контакт',
           u'Дата получения',
           u'Получатель',
           u'Дата проверки'
          ]

workbook = None

row_number = 1

recieved_date = None

for rec in result:
    current_date = rec[13]
    if recieved_date != current_date:
        recieved_date = current_date

        save_dir = os.path.join(report_save_path, str(recieved_date))
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)

        current_mo = None

    if current_mo != rec[1]:

        if workbook:
            workbook.close()
            row_number = 1

        current_mo = rec[1]
        mo_name = rec[2].replace('"', '').decode('utf8')
        path = os.path.join(save_dir, '%s%s' % (mo_name, u'.xlsx'))

        workbook = Workbook(path)
        worksheet = workbook.add_worksheet('1')

        bold = workbook.add_format({'bold': True})

        for i, column in enumerate(rec):
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