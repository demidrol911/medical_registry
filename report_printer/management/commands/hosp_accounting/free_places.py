#! -*- coding: utf-8 -*-
from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization
from report_printer.libs.excel_style import VALUE_STYLE


class FreePlacesCountPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                select mo.id_pk, mo.name AS mo_name,
                       sum(males_amount) AS total_males_amount,
                       sum(females_amount) AS total_females_amount,
                       sum(children_amount) AS total_children_amount,

                       sum(males_free_amount) AS total_males_free_amount,
                       sum(females_free_amount) AS total_females_free_amount,
                       sum(children_free_amount) AS total_children_free_amount,

                       sum(patients_amount) AS total_patients_amount,
                       sum(patients_recieved) AS total_patients_recieved,
                       sum(patients_retired) AS total_patients_retired,
                       sum(planned) AS total_planned
                FROM hospitalizations_room hr
                    JOIN medical_organization mo
                        on mo.id_pk = hr.organization_fk

                where received_date = %(end)s
                GROUP BY mo.id_pk, mo_name
                ORDER BY mo_name
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            start=parameters.start_date,
            end=parameters.end_date
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(4, 0)
        sheet.set_style(VALUE_STYLE)
        for item in self.data:
            sheet.write('', 'c')
            sheet.write(item.mo_name, 'c')
            sheet.write(item.total_males_amount, 'c')
            sheet.write(item.total_males_free_amount, 'c')
            sheet.write(item.total_females_amount, 'c')
            sheet.write(item.total_females_free_amount, 'c')
            sheet.write(item.total_children_amount, 'c')
            sheet.write(item.total_children_free_amount, 'c')
            sheet.write(item.total_patients_amount, 'c')
            sheet.write(item.total_patients_recieved, 'c')
            sheet.write(item.total_patients_retired, 'c')
            sheet.write(item.total_planned, 'r')
        sheet.write('', 'c')
        sheet.write(u'ИТОГО')
