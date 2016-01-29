#! -*- coding: utf-8 -*-

from report_printer_clear.utils.page import ReportPage
from main.models import MedicalOrganization
from report_printer_clear.utils.excel_style import VALUE_STYLE


class SenderStatisticPage(ReportPage):
    """
    Отчёт статистика отправителя
    """
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                select sender.id_pk, sender.name as sender_name,
                    count(DISTINCT case when "type" = 1 then h.number END) AS count_napr, -- направления
                    count(
                        DISTINCT CASE WHEN "type" = 1 and exists (
                            select 1 from hospitalization
                            where "type" = 9 and "number" = h.number
                        ) THEN h.number END
                    ) AS count_napr_s_utoch,   -- направление с уточнениями

                    count(
                        DISTINCT CASE WHEN "type" = 9 and NOT exists (
                            select 1 from hospitalization
                            where "type" = 1 and "number" = h.number
                        ) THEN h.number END
                    ) AS count_utoch_bez_napr, -- уточнения без направлений

                    count(
                        DISTINCT CASE WHEN "type" = 1 and NOT exists (
                            select 1 from hospitalization
                            where "type" = 9 and "number" = h.number
                        ) THEN h.number END
                    ) AS count_napr_bez_utoch -- направления без уточнений
                from
                    hospitalization h
                    LEFT JOIN medical_organization sender
                        on sender.id_pk = h.organization_sender_fk
                where
                    h.received_date between %(start)s and %(end)s
                GROUP BY sender.id_pk, sender_name
                ORDER BY sender_name
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            start=parameters.start_date,
            end=parameters.end_date
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(0, 0)
        sheet.set_style(VALUE_STYLE)
        sheet.write(u'МО', 'c')
        sheet.write(u'Направления', 'c')
        sheet.write(u'Напр с уточ', 'c')
        sheet.write(u'Уточ без напр', 'c')
        sheet.write(u'Напр без уточ', 'r')

        for item in self.data:
            sheet.write(item.sender_name, 'c')
            sheet.write(item.count_napr, 'c')
            sheet.write(item.count_napr_s_utoch, 'c')
            sheet.write(item.count_utoch_bez_napr, 'c')
            sheet.write(item.count_napr_bez_utoch, 'r')
        sheet.write(u'ИТОГО', 'c')

