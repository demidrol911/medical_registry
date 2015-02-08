#! -*- coding: utf-8 -*-

import time

from django.core.management.base import BaseCommand
from django.db import connection

from tfoms.models import MedicalOrganization
from medical_service_register.path import REESTR_MEC, BASE_DIR
from report_printer.excel_writer import ExcelWriter


class Command(BaseCommand):

    def handle(self, *args, **options):
        start = time.time()
        year = args[0]
        period = args[1]
        cursor_query = connection.cursor()
        query = """
                SELECT medical_organization.id_pk, idc.idc_code, idc.name,
                COUNT(DISTINCT provided_event.id_pk), SUM(provided_service.quantity),
                SUM(provided_service.accepted_payment)
                FROM provided_service
                JOIN medical_service
                    ON medical_service.id_pk = provided_service.code_fk
                JOIN idc
                    ON idc.id_pk = provided_service.basic_disease_fk
                JOIN provided_event
                    ON provided_service.event_fk = provided_event.id_pk
                JOIN medical_register_record
                    ON provided_event.record_fk = medical_register_record.id_pk
                JOIN medical_register
                    ON medical_register_record.register_fk = medical_register.id_pk
                JOIN medical_organization
                    ON medical_organization.id_pk = provided_service.organization_fk
                WHERE medical_register.is_active
                    AND medical_register.year = '{year}'
                    AND medical_register.period = '{period}'
                    AND provided_event.term_fk = 1
                    GROUP BY medical_organization.id_pk, idc.idc_code, idc.name
                    ORDER BY medical_organization.id_pk, idc.idc_code, idc.name
                """.format(year=year, period=period)
        cursor_query.execute(query)

        mo_dict = {}
        for row in cursor_query.fetchall():
            if row[0] not in mo_dict.keys():
                mo_dict[row[0]] = []
            mo_dict[row[0]].append((row[1], row[2], row[3], row[4], row[5]))
        cursor_query.close()

        value_style = {'border': 1}
        template = BASE_DIR + r'\templates\excel_pattern\hospital_diagnoses.xls'

        reestr_diag = REESTR_MEC % (year, period)

        for mo_code in mo_dict:
            mo_name = MedicalOrganization.objects.get(id_pk=mo_code).name
            mo_name = mo_name.replace('"', '').replace(' ', '_')
            with ExcelWriter(reestr_diag + r'\%s' % mo_name,
                             template=template) as act_book:
                act_book.set_style(value_style)
                act_book.set_sheet(0)
                act_book.set_cursor(2, 0)

                for idc_data in mo_dict[mo_code]:
                    act_book.write_cell(idc_data[0], 'c')
                    act_book.write_cell(idc_data[1], 'c')
                    act_book.write_cell(idc_data[2], 'c')
                    act_book.write_cell(idc_data[3], 'c')
                    act_book.write_cell(idc_data[4], 'r')

        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)
