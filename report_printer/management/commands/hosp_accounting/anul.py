#! -*- coding: utf-8 -*-

from report_printer.libs.page import ReportPage
from main.funcs import dictfetchall
from report_printer.libs.excel_style import VALUE_STYLE
from django.db import connection
from main.funcs import howlong


class AnulPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = """
                select
                     distinct
                     h.id_pk,
                     h.number AS napr_number,
                     h.reason AS reason,
                     T.last_name AS last_name,
                     T.first_name AS first_name,
                     T.middle_name AS middle_name,
                     T.birthdate AS birthdate,
                     sender.name AS sender_name,
                     receiver.name AS receiver_name,
                     (select max("date") from hospitalization where "number" = h.number and "type" = 1) AS napr_date,
                     GREATEST(
                       (select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
                       (select max("start_date") from hospitalization where "number" = h.number and "type" = 9)) AS napr_plan_date,
                     h.end_date AS anul_date,
                     h.received_date AS received_date
                from hospitalization  h
                LEFT join LATERAL
                     (
                    select hpi.id_pk, hpi.last_name, hpi.first_name, hpi.middle_name, hpi.birthdate
                    from hospitalization hi
                        join hospitalization_patient hpi
                        on hpi.id_pk = hi.patient_fk
                    WHERE h.number = hi.number
                    ORDER BY hi.patient_fk DESC NULLS LAST
                    ) T on true
                LEFT JOIN medical_organization sender
                         on sender.id_pk = h.organization_sender_fk
                LEFT JOIN medical_organization receiver
                         on receiver.id_pk = h.organization_reciever_fk
                where
                h.type = 4
                and
                h.received_date = %(start)s
                order by receiver.name, last_name, first_name, middle_name
                """
        cursor = connection.cursor()
        cursor.execute(query, dict(start=parameters.start_date))
        self.data = dictfetchall(cursor)

    def print_page(self, sheet, parameters):
        REASONS = {
            0: u'Не указана',
            1: u'Неявка',
            2: u'Отказ МО',
            3: u'Отказ пациента',
            4: u'Смерть',
            5: u'Прочие'
        }

        sheet.set_position(0, 0)
        sheet.set_style(VALUE_STYLE)
        sheet.write(u'Номер напр.', 'c')
        sheet.write(u'Причина', 'c')
        sheet.write(u'Фамилия', 'c')
        sheet.write(u'Имя', 'c')
        sheet.write(u'Отчество', 'c')
        sheet.write(u'ДР', 'c')
        sheet.write(u'Отправитель', 'c')
        sheet.write(u'Получатель', 'c')
        sheet.write(u'Дата напр.', 'c')
        sheet.write(u'Плановая дата госп.', 'c')
        sheet.write(u'Аннулирование', 'c')
        sheet.write(u'Дата получения', 'r')

        for item in self.data:
            sheet.write(item['napr_number'], 'c')
            sheet.write(REASONS[item['reason']], 'c')
            sheet.write(item['last_name'], 'c')
            sheet.write(item['first_name'], 'c')
            sheet.write(item['middle_name'], 'c')
            sheet.write(item['birthdate'].strftime('%d.%m.%Y') if item['birthdate'] else '', 'c')
            sheet.write(item['sender_name'], 'c')
            sheet.write(item['receiver_name'], 'c')
            sheet.write(item['napr_date'].strftime('%d.%m.%Y') if item['napr_date'] else '', 'c')
            sheet.write(item['napr_plan_date'].strftime('%d.%m.%Y') if item['napr_plan_date'] else '', 'c')
            sheet.write(item['anul_date'].strftime('%d.%m.%Y') if item['anul_date'] else '', 'c')
            sheet.write(item['received_date'].strftime('%d.%m.%Y') if item['received_date'] else '', 'r')
