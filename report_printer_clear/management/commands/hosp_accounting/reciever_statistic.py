#! -*- coding: utf-8 -*-

from report_printer_clear.utils.page import ReportPage
from main.models import MedicalOrganization
from report_printer_clear.utils.excel_style import VALUE_STYLE


class ReceiverStatisticPage(ReportPage):
    """
    Отчёт статистика получателя
    """
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                WITH all_hospitalization AS (
                    select receiver.id_pk AS received_id,
                        h.id_pk AS hosp_id, h.type, h.number AS napr_number,
                        exists (select 1 from hospitalization where "type" = 9 and "number" = h.number) AS has_utoch,
                        exists (select 1 from hospitalization where "type" = 1 and "number" = h.number) AS has_napr,

                        exists (select 1
                                 from hospitalization hi
                                 join hospitalization_patient hpi on hpi.id_pk = hi.patient_fk
                                 where hi.type = 1
                                   and upper(format('%%s%%s%%s%%s', hpi.last_name, hpi.first_name, hpi.middle_name, hpi.birthdate)) =
                                       upper(format('%%s%%s%%s%%s', hp.last_name, hp.first_name, hp.middle_name, hp.birthdate))
                        )  AS has_napr_na_pat,

                        exists (select 1
                                 from hospitalization hi
                                 join hospitalization_patient hpi on hpi.id_pk = hi.patient_fk
                                 where hi.type = 9
                                    and upper(format('%%s%%s%%s%%s', hpi.last_name, hpi.first_name, hpi.middle_name, hpi.birthdate)) =
                                        upper(format('%%s%%s%%s%%s', hp.last_name, hp.first_name, hp.middle_name, hp.birthdate))
                        ) AS has_utoch_na_pat,

                        h.start_date between %(hosp_start)s and %(hosp_end)s AS is_current_hosp
                    from hospitalization h
                           LEFT JOIN hospitalization_patient hp
                            on hp.id_pk = h.patient_fk
                           LEFT JOIN medical_organization receiver
                            on receiver.id_pk = h.organization_reciever_fk
                    where
                        h.received_date between %(start)s and %(end)s
                )
                select
                    mo.id_pk,
                    mo.name AS receiver_name,
                    mo.code AS receiver_code,
                    count(DISTINCT CASE WHEN "type" = 1
                                          THEN napr_number
                          END) AS count_napr, -- направлений
                    count(DISTINCT CASE WHEN "type" = 1 and has_utoch
                                          THEN napr_number
                          END) AS count_napr_s_utoch, -- направлений с уточнениями
                    count(DISTINCT CASE WHEN "type" = 1 and NOT has_utoch
                                          THEN napr_number
                          END) AS count_napr_bez_utoch, -- направлений без уточнений
                    count(DISTINCT CASE WHEN "type" = 9 and NOT has_napr
                                          THEN napr_number
                          END) AS count_utoch_bez_napr, -- уточнений без направлений
                    count(DISTINCT CASE WHEN "type" = 1 and is_current_hosp
                                          THEN napr_number
                          END) AS count_napr_at_current_date, -- направлений на отчётную дату

                    count(DISTINCT CASE WHEN "type" = 2
                                          THEN napr_number
                          END) AS count_hospit_vsego, -- план госпитализаций всего
                    count(DISTINCT CASE WHEN "type" = 2 and has_napr and has_utoch
                                          THEN napr_number
                          END) AS count_hospit_s_napr_i_utoch, -- план госпитализаций с направлениями и уточнениями
                    count(DISTINCT CASE WHEN "type" = 2 and has_napr and NOT has_utoch
                                          THEN napr_number
                          END) AS count_hospit_s_napr_bez_utoch, -- план госпитализаций с направленими без уточнений
                    count(DISTINCT CASE WHEN "type" = 2 and NOT has_napr and has_utoch
                                          THEN napr_number
                                   END) AS count_hospit_bez_napr_s_utoch, -- план госпитализаций без направлений с уточнениями
                    count(DISTINCT CASE WHEN "type" = 2 and NOT has_napr
                                          THEN napr_number
                                   END) AS count_hospit_bez_napr, -- план госпитализаций без направлений
                    count(DISTINCT CASE WHEN "type" = 2 and is_current_hosp
                                          THEN napr_number
                                   END) AS count_hospit_at_current_date, -- план госпитализаций на отчётную дату

                    count(DISTINCT CASE WHEN "type" = 3
                                          THEN hosp_id
                          END) AS count_eksr_vsego, -- экстренные госпитализации всего
                    count(DISTINCT CASE WHEN "type" = 3 and has_napr_na_pat and has_utoch_na_pat
                                          THEN hosp_id
                          END) AS count_ekstr_hospit_so_vsem, -- экстренные госпитализации комплект
                    count(DISTINCT CASE WHEN "type" = 3 and has_napr_na_pat and NOT has_utoch_na_pat
                                          THEN hosp_id
                          END) AS count_ekstr_hospit_s_napr_bez_utoch, -- экстренные госпитализации с направлениями без уточнения
                    count(DISTINCT CASE WHEN "type" = 3 and NOT has_napr_na_pat and has_utoch_na_pat
                                          THEN hosp_id
                          END) AS count_ekstr_hospit_bez_napr_s_utoch, -- экстренные госпитализации без направления с уточнением
                    count(DISTINCT CASE WHEN "type" = 3 AND NOT has_napr_na_pat and NOT has_utoch_na_pat
                                          THEN hosp_id
                          END) AS count_ekstr_hospit_bez_napr, -- экстренные госпитализации без направления
                    count(DISTINCT CASE WHEN "type" = 3 and is_current_hosp
                                          THEN hosp_id
                          END) AS count_ekstr_hospit_at_current_date -- экстренные госпитализации на отчётную дату

                from all_hospitalization
                join medical_organization mo
                   ON mo.id_pk = received_id
                /*
                WHERE receiver_code in ('280013', '280003', '280026', '280036', '280066', '280064', '280069',
                    '280043', '280018', '280005', '280038', '280085', '280083')
                */
                group by mo.id_pk, received_id, receiver_name
                order by receiver_name
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
                                                    hosp_start=parameters.hosp_start,
                                                    hosp_end=parameters.hosp_end,
                                                    start=parameters.start_date,
                                                    end=parameters.end_date))

    def print_page(self, sheet, parameters):
        sheet.set_position(0, 0)
        sheet.set_style(VALUE_STYLE)
        sheet.write('', 'c')
        sheet.write(u'МО', 'c')
        sheet.write(u'Поступило напр-й', 'c')
        sheet.write(u'Напр. С уточ.', 'c')
        sheet.write(u'Напр. Без уточ', 'c')
        sheet.write(u'Уточ. Без напр.', 'c')
        sheet.write(u'Напр. на тек. дату', 'c')
        sheet.write(u'Госп. План всего', 'c')
        sheet.write(u'Госп. План полный комплект', 'c'),
        sheet.write(u'Госп. План с напр., без уточ.', 'c'),
        sheet.write(u'Госп план без напр., с уточ', 'c'),
        sheet.write(u'Госп план без всего', 'c'),
        sheet.write(u'Госп план на тек. дату', 'c')
        sheet.write(u'Госп. Экстр всего', 'c'),
        sheet.write(u'Госп. Экстр полн. Комплект', 'c'),
        sheet.write(u'Госп экстр с напр, без уточ', 'c'),
        sheet.write(u'Госп экстр с без напр, с уточ', 'c'),
        sheet.write(u'Госп экстр без всего', 'с')
        sheet.write(u'Госп экстр на тек. дату', 'r')

        for item in self.data:
            sheet.write('', 'c')
            sheet.write(item.receiver_name, 'c')
            sheet.write(item.count_napr, 'c'),
            sheet.write(item.count_napr_s_utoch, 'c'),
            sheet.write(item.count_napr_bez_utoch, 'c'),
            sheet.write(item.count_utoch_bez_napr, 'c'),
            sheet.write(item.count_napr_at_current_date, 'c'),
            sheet.write(item.count_hospit_vsego, 'c'),
            sheet.write(item.count_hospit_s_napr_i_utoch, 'c'),
            sheet.write(item.count_hospit_s_napr_bez_utoch, 'c'),
            sheet.write(item.count_hospit_bez_napr_s_utoch, 'c'),
            sheet.write(item.count_hospit_bez_napr, 'c'),
            sheet.write(item.count_hospit_at_current_date, 'c'),
            sheet.write(item.count_eksr_vsego, 'c'),
            sheet.write(item.count_ekstr_hospit_so_vsem, 'c'),
            sheet.write(item.count_ekstr_hospit_s_napr_bez_utoch, 'c'),
            sheet.write(item.count_ekstr_hospit_bez_napr_s_utoch, 'c'),
            sheet.write(item.count_ekstr_hospit_bez_napr, 'c'),
            sheet.write(item.count_ekstr_hospit_at_current_date, 'r')

        sheet.write('', 'c')
        sheet.write(u'Всего', 'c')


class AllInfoStatisticPage(ReceiverStatisticPage):
    """
    Отчёт статистка всей информации
    """
    def __init__(self):
        super(AllInfoStatisticPage, self).__init__()

    def print_page(self, sheet, parameters):
        sheet.set_position(2, 0)
        sheet.set_style(VALUE_STYLE)
        for item in self.data:
            sheet.write(item.receiver_name, 'c')
            sheet.write(item.count_napr, 'c'),
            sheet.write(item.count_napr_s_utoch, 'c'),
            sheet.write(item.count_napr_bez_utoch, 'c'),
            sheet.write(item.count_utoch_bez_napr, 'c'),
            sheet.write(item.count_hospit_vsego, 'c'),
            sheet.write(item.count_hospit_s_napr_i_utoch, 'c'),
            sheet.write(item.count_hospit_s_napr_bez_utoch, 'c'),
            sheet.write(item.count_hospit_bez_napr_s_utoch, 'c'),
            sheet.write(item.count_hospit_bez_napr, 'c'),
            sheet.write(item.count_hospit_at_current_date, 'c'),
            sheet.write(item.count_eksr_vsego, 'c'),
            sheet.write(item.count_ekstr_hospit_so_vsem, 'c'),
            sheet.write(item.count_ekstr_hospit_s_napr_bez_utoch, 'c'),
            sheet.write(item.count_ekstr_hospit_bez_napr_s_utoch, 'c'),
            sheet.write(item.count_ekstr_hospit_bez_napr, 'c'),
            sheet.write(item.count_ekstr_hospit_at_current_date, 'r')
        sheet.write(u'Всего', 'c')
