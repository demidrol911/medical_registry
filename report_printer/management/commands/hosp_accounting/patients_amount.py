#! -*- coding: utf-8 -*-

from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization
from report_printer.libs.excel_style import VALUE_STYLE


class ReceiverHospPatientsAmountPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                with dates as (select cast(%(hosp_start)s as DATE) as "start", cast(%(hosp_end)s as DATE) as "end")
                select receiver.id_pk, receiver.name org,
                    count(distinct case when h.type = 1
                                             and h.date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_napr,
                    count(distinct case when h.type = 2
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_plan,
                    count(distinct case when h.type = 3
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_ekstr

                from
                    hospitalization h
                    LEFT JOIN hospitalization_patient hp
                        on hp.id_pk = h.patient_fk
                    LEFT JOIN medical_organization receiver
                        on receiver.id_pk = h.organization_reciever_fk
                where
                    (h.date between (select dates.start from dates) and (select dates.end from dates)
                    or h.start_date between (select dates.start from dates) and (select dates.end from dates))
                    and h.type in (1,2,3)
                GROUP BY receiver.id_pk, org
                ORDER BY org
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            hosp_start=parameters.hosp_start,
            hosp_end=parameters.hosp_end
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(1, 0)
        sheet.set_style(VALUE_STYLE)

        for item in self.data:
            sheet.write(item.org, 'c')
            sheet.write(item.count_napr, 'c')
            sheet.write(item.count_plan, 'c')
            sheet.write(item.count_ekstr, 'r')
        sheet.write(u'ИТОГО', 'c')


class SenderHospPatientsAmountPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 1

    def calculate(self, parameters):
        self.data = None
        query = """
                with dates as (select cast(%(hosp_start)s as DATE) as "start", cast(%(hosp_end)s as DATE) as "end")
                select
                    sender.id_pk, sender.name org,
                    count(distinct case when h.type = 1
                                             and h.date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_napr,
                    count(distinct case when h.type = 2
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_plan,
                    count(distinct case when h.type = 3
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_ekstr

                from
                    hospitalization h
                    LEFT JOIN hospitalization_patient hp
                        on hp.id_pk = h.patient_fk
                    LEFT JOIN medical_organization sender
                        on sender.id_pk = h.organization_sender_fk
                where
                    (h.date between (select dates.start from dates) and (select dates.end from dates)
                    or h.start_date between (select dates.start from dates) and (select dates.end from dates))
                    and h.type in (1,2,3)
                GROUP BY sender.id_pk, org
                ORDER BY org
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            hosp_start=parameters.hosp_start,
            hosp_end=parameters.hosp_end
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(1, 0)
        sheet.set_style(VALUE_STYLE)

        for item in self.data:
            sheet.write(item.org, 'c')
            sheet.write(item.count_napr, 'c')
            sheet.write(item.count_plan, 'c')
            sheet.write(item.count_ekstr, 'r')
        sheet.write(u'ИТОГО', 'c')


class HospPatientsAmountPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                with dates as (select cast(%(hosp_start)s as DATE) as "start", cast(%(hosp_end)s as DATE) as "end")
                select mo.id_pk, mo.name org,
                    count(distinct case when mo.id_pk = h.organization_sender_fk
                                             AND h.type = 1 and h.date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_send_napr,
                    count(distinct case when mo.id_pk = h.organization_sender_fk AND h.type = 2
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_send_plan,
                    count(distinct case when mo.id_pk = h.organization_sender_fk AND h.type = 3
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_send_ekstr,

                    count(distinct case when mo.id_pk = h.organization_reciever_fk AND h.type = 1
                                             and h.date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_reciever_napr,
                    count(distinct case when mo.id_pk = h.organization_reciever_fk AND h.type = 2
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_reciever_plan,
                    count(distinct case when mo.id_pk = h.organization_reciever_fk AND h.type = 3
                                             and h.start_date between (select dates.start from dates) and (select dates.end from dates)
                                          then concat(hp.last_name, hp.first_name, hp.middle_name, hp.birthdate)
                          END) AS count_reciever_ekstr

                from
                    hospitalization h
                    LEFT JOIN hospitalization_patient hp
                        on hp.id_pk = h.patient_fk
                    LEFT JOIN medical_organization mo
                        on (mo.id_pk = h.organization_sender_fk or mo.id_pk = h.organization_reciever_fk)
                where
                    (h.date between (select dates.start from dates) and (select dates.end from dates)
                    or h.start_date between (select dates.start from dates) and (select dates.end from dates))
                    and h.type in (1,2,3)
                GROUP BY mo.id_pk, org
                ORDER BY org
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            hosp_start=parameters.hosp_start,
            hosp_end=parameters.hosp_end
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(0, 0)
        sheet.set_style(VALUE_STYLE)

        sheet.write(u'МО', 'c')
        sheet.write(u'Направлений отправлено', 'c')
        sheet.write(u'Направлений получено', 'c')
        sheet.write(u'Планово', 'c')
        sheet.write(u'Экстренно', 'r')

        for item in self.data:
            sheet.write(item.org, 'c')
            sheet.write(item.count_send_napr, 'c')
            sheet.write(item.count_reciever_napr, 'c')
            sheet.write(item.count_reciever_plan, 'c')
            sheet.write(item.count_reciever_ekstr, 'r')
        sheet.write(u'ИТОГО', 'c')

