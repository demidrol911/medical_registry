#! -*- coding: utf-8 -*-

import time
from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_EXP
from helpers.excel_writer import ExcelWriter
from helpers.const import MONTH_NAME
from django.db import connection


class Command(BaseCommand):

    def handle(self, *args, **options):
        start = time.time()
        year = args[0]
        period = args[1]
        reestr_path = REESTR_EXP % (year, period)

        query = """
        SELECT
        medical_division.id_pk, medical_division.code, medical_division.name,
        COUNT(DISTINCT CASE WHEN medical_register.period = '{period}' THEN provided_event.id_pk END),
        COUNT(DISTINCT provided_event.id_pk)
        FROM provided_service
        JOIN provided_event
             ON provided_event.id_pk = provided_service.event_fk
        JOIN medical_register_record
             ON medical_register_record.id_pk = provided_event.record_fk
        JOIN medical_register
             ON medical_register.id_pk = medical_register_record.register_fk
        JOIN medical_division
             ON medical_division.id_pk = provided_event.division_fk
        WHERE medical_register.year='{year}'
              AND medical_register.is_active
              AND provided_service.payment_type_fk in (2, 4)
              AND provided_event.term_fk = 1
        GROUP BY medical_division.id_pk, medical_division.code, medical_division.name
        ORDER BY medical_division.code
        """

        cursor = connection.cursor()
        cursor.execute(query.format(year=year, period=period))

        # Распечатка акта
        with ExcelWriter(u'%s/кругстац_%s_%s' % (reestr_path, year, MONTH_NAME[period])) as act_book:
            act_book.set_style()
            act_book.write_cell(u'Код', 'c')
            act_book.write_cell(u'Наименование', 'c')
            act_book.write_cell(u'за %s' % MONTH_NAME[period], 'c')
            act_book.write_cell(u'за %d месяцев' % int(period), 'r')
            for mo_data in cursor.fetchall():
                for value in mo_data[1:]:
                    act_book.write_cell(value, 'c')
                act_book.write_cell('', 'r')
        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)
