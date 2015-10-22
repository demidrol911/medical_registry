#! -*- coding: utf-8 -*-
from django.db import connection
from main.funcs import dictfetchall
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage


class AmbulanceCareALLPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = self.get_query()
        cursor = connection.cursor()
        cursor.execute(query, dict(year=parameters.registry_year,
                                   period=parameters.registry_period))
        self.data = dictfetchall(cursor)[0]
        cursor.close()

    def get_query(self):
        return AmbulanceCareALLPage.get_general_query()

    @staticmethod
    def get_general_query():
        query = '''
                SELECT
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (27, 33, 39, 45)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_emergency,
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (28, 34, 40, 46)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_urgent,
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (29, 35, 41, 47)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_transport,
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (30, 36, 42, 48)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_ineffective,
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (31, 37, 43, 49)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_unreasonable,
                     COUNT(DISTINCT CASE WHEN ms.subgroup_fk in (32, 38, 44, 50)
                                           THEN ps.id_pk
                                         ELSE NULL
                                    END) AS count_thrombolysis,
                     COUNT(DISTINCT (mr.organization_code, pt.id_pk, ms.subgroup_fk, ms.code ILIKE '0%%')) AS count_patients,
                     SUM(ps.tariff) AS total_tariff

                FROM medical_register mr
                    JOIN medical_register_record mrr
                       ON mr.id_pk = mrr.register_fk
                    JOIN provided_event pe
                       ON mrr.id_pk = pe.record_fk
                    JOIN provided_service ps
                       ON ps.event_fk = pe.id_pk
                    JOIN medical_organization mo
                       ON ps.organization_fk = mo.id_pk
                    JOIN medical_service ms
                       ON ms.id_pk = ps.code_fk
                    JOIN patient pt
                       ON pt.id_pk = mrr.patient_fk
                WHERE mr.is_active
                    AND mr.period = %(period)s
                    AND mr.year = %(year)s
                    AND ps.payment_type_fk = 2
                    AND pe.term_fk = 4
                    AND ms.group_fk in (33, 34, 35, 36)
                '''
        return query

    def print_page(self, sheet, parameters):
        sheet.write_cell(4, 1, parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        sheet.write_cell(9, 4, self.data['count_emergency'])
        sheet.write_cell(10, 4, self.data['count_urgent'])
        sheet.write_cell(11, 4, self.data['count_transport'])
        sheet.write_cell(12, 4, self.data['count_ineffective'])
        sheet.write_cell(13, 4, self.data['count_unreasonable'])
        sheet.write_cell(14, 4, self.data['count_patients'])
        sheet.write_cell(15, 4, self.data['total_tariff'])
        sheet.write_cell(16, 4, self.data['count_thrombolysis'])


class AmbulanceSpecializedPage(AmbulanceCareALLPage):

    def __init__(self):
        AmbulanceCareALLPage.__init__(self)

    def get_query(self):
        return AmbulanceCareALLPage.get_general_query() + ' AND ms.group_fk in (33, 34)'


class AmbulanceMedicalPage(AmbulanceCareALLPage):

    def __init__(self):
        AmbulanceCareALLPage.__init__(self)

    def get_query(self):
        return AmbulanceCareALLPage.get_general_query() + ' AND ms.group_fk = 35'


class AmbulanceParamedicPage(AmbulanceCareALLPage):

    def __init__(self):
        AmbulanceCareALLPage.__init__(self)

    def get_query(self):
        return AmbulanceCareALLPage.get_general_query() + ' AND ms.group_fk = 36'