#! -*- coding: utf-8 -*-

from report_printer_clear.utils.page import ReportPage
from main.funcs import dictfetchall
from report_printer_clear.utils.excel_style import VALUE_STYLE
from django.db import connection
from main.funcs import howlong


class InfoByMoPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = """
                select row_number() over () AS num,
                       sender_name,
                       last_name,
                       first_name,
                       middle_name,
                       birthdate,
                       number,
                       reciever_name,
                       napr_division,
                       fact_division,
                       napr_date,
                       napr_plan_date,
                       napr_plan_date-napr_date AS difference,
                       napr_hosp_date,
                       napr_cancel_date,
                       napr_urgent_date,
                       files
                FROM (
                    select sender.name as sender_name,
                        T.last_name, T.first_name, T.middle_name, T.birthdate,
                        h.number,
                        receiver.name as reciever_name,
                        (
                            select md.name
                            from hospitalization hi

                                LEFT join medical_division md
                                    on md.id_pk = hi.division_fk
                            WHERE hi.number = h.number and hi.type = 1
                            ORDER BY md.name ASC nulls last
                            limit 1
                        ) napr_division,
                        (
                            select md.name
                            from hospitalization hi

                                LEFT join medical_division md
                                    on md.id_pk = hi.division_fk
                            WHERE hi.number = h.number and hi.type in (2, 3, 4)
                            ORDER BY md.name ASC nulls last
                            limit 1
                        ) fact_division,
                        coalesce((select max("date") from hospitalization where "number" = h.number and "type" = 1),
                        (select max("date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and "type" = 1

                        )) as napr_date,

                        GREATEST(
                        coalesce( (select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
                        (select max("start_date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and "type" = 1
                        and received_date >= h.received_date
                        )),

                        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 9),
                        (select max("start_date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and received_date >= h.received_date
                        and "type" = 9))) as napr_plan_date,

                        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 2),(select max("start_date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and "type" = 2
                        and received_date >= h.received_date
                        )) as napr_hosp_date,

                        coalesce((select max("end_date") from hospitalization where "number" = h.number and "type" = 4),
                        (select max("end_date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and received_date >= h.received_date
                        and "type" = 4)) as napr_cancel_date,

                        coalesce((select max("start_date") from hospitalization where "number" = h.number and "type" = 3),
                        (select max("start_date")
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate
                        and received_date >= h.received_date
                        and "type" = 3)) as napr_urgent_date,

                        (select string_agg(casT("type" as VARCHAR), ', ')
                        from hospitalization
                            join hospitalization_patient
                                on hospitalization_patient.id_pk = hospitalization.patient_fk
                        where (last_name = T.last_name and first_name = T.first_name and middle_name = T.middle_name and hospitalization_patient.birthdate = T.birthdate)
                            or (h.number = "number")
                        and received_date >= h.received_date
                         ) as files


                /*
                        (select max("date") from hospitalization where "number" = h.number and "type" = 1) as napr_date,

                        GREATEST((select max("start_date") from hospitalization where "number" = h.number and "type" = 1),
                        (select max("start_date") from hospitalization where "number" = h.number and "type" = 9)) as napr_plan_date,

                        (select max("start_date") from hospitalization where "number" = h.number and "type" = 2) as napr_hosp_date,
                        (select max("end_date") from hospitalization where "number" = h.number and "type" = 4) as napr_cancel_date,
                        (select max("start_date") from hospitalization where "number" = h.number and "type" = 3) as napr_urgent_date,
                        (select string_agg(casT("type" as VARCHAR), ', ') from hospitalization where "number" = h.number) as files
                */


                    from
                        hospitalization h

                        LEFT JOIN hospitalization_type ht
                            on ht.id_pk = h.type
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

                        LEFT JOIN idc
                            on idc.id_pk = h.disease_fk

                    where
                        h.received_date between %(start)s and %(end)s
                        and sender.code in ('280066', '280036', '280085', '280038', '280003', '280026', '280043', '280064',
                        '280013', '280069', '280018', '280005') -- , '280017', '280026'
                    GROUP BY sender.name, h.number, receiver.name, T.last_name, T.first_name, T.middle_name, T.birthdate, h.received_date
                    --ORDER BY number
                ) as Z
                ORDER BY 3,4,5,6
                """
        cursor = connection.cursor()
        cursor.execute(query, dict(start=parameters.start_date, end=parameters.end_date))
        self.data = dictfetchall(cursor)

    def print_page(self, sheet, parameters):
        # СВЕДЕНИЯ ОБ ИНФОРМАЦИОННОМ ОБМЕНЕ ПО МО г.БЛАГОВЕЩЕНСКА за период с 12.11.2015 по 17.11.2015
        sheet.set_position(0, 0)
        sheet.set_style(VALUE_STYLE)
        sheet.write(u'Номер', 'c')
        sheet.write(u'Отправитель', 'c')
        sheet.write(u'Фамилия', 'c')
        sheet.write(u'Имя', 'c')
        sheet.write(u'Отчество', 'c')
        sheet.write(u'ДР', 'c')
        sheet.write(u'Номер напр.', 'c')
        sheet.write(u'Получатель', 'c')
        sheet.write(u'Отделение в направлении', 'c')
        sheet.write(u'Отделение в госпит.', 'c')
        sheet.write(u'Дата напр.', 'c')
        sheet.write(u'Плановая дата госп.', 'c')
        sheet.write(u'Разница (дн.)', 'c')
        sheet.write(u'Плановая госп.', 'c')
        sheet.write(u'Аннулирование', 'c')
        sheet.write(u'Экстренная госп.', 'c')
        sheet.write(u'Файлы', 'r')

        for item in self.data:
            sheet.write(item['num'], 'c')
            sheet.write(item['sender_name'], 'c')
            sheet.write(item['last_name'], 'c')
            sheet.write(item['first_name'], 'c')
            sheet.write(item['middle_name'], 'c')
            sheet.write(item['birthdate'], 'c')
            sheet.write(item['number'], 'c')
            sheet.write(item['reciever_name'], 'c')
            sheet.write(item['napr_division'], 'c')
            sheet.write(item['fact_division'], 'c')
            sheet.write(item['napr_date'], 'c')
            sheet.write(item['napr_plan_date'], 'c')
            sheet.write(item['difference'], 'c')
            sheet.write(item['napr_hosp_date'], 'c')
            sheet.write(item['napr_cancel_date'], 'c')
            sheet.write(item['napr_urgent_date'], 'c')
            sheet.write(item['files'], 'r')
