# -*- coding: utf-8 -*-

import psycopg2
import os

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()

year = '2016'
period = '02'

cursor_pg.execute('select DISTINCT organization_code from medical_register '
                  'where is_active and year = %s and period = %s ', [year, period])

active_mo = set([rec[0] for rec in cursor_pg.fetchall()])

cursor_pg.execute('select code from medical_organization where parent_fk is null')

all_mo = set([rec[0] for rec in cursor_pg.fetchall()])

xml_archive = set([rec[4:10] for rec in os.listdir('c:/work/checking/')])

flc_archive = set([rec[2:8] for rec in os.listdir('c:/work/xml_archive/')])

not_passed_flc = flc_archive - active_mo

no_files = all_mo - xml_archive - flc_archive
print xml_archive

print u'Не прошли ФЛК:'
for rec in not_passed_flc:
    cursor_pg.execute('select name from medical_organization where code = %s and parent_fk is null',
                      [rec])
    print cursor_pg.fetchone()[0].decode('utf-8')

print

print u'Нет файлов:'
for rec in no_files:
    cursor_pg.execute('select name from medical_organization where code = %s and parent_fk is null',
                      [rec])
    print cursor_pg.fetchone()[0].decode('utf-8')

connect_pg.close()

