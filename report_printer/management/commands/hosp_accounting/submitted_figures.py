#! -*- coding: utf-8 -*-

from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization
from report_printer.libs.excel_style import VALUE_STYLE


class SubmittedFiguresPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
                select mo.id_pk, mo.name AS mo_name,
                    (
                        SELECT COUNT(distinct hr.id_pk)
                        from hospitalizations_room hr
                        where
                            hr.organization_fk = mo.id_pk
                            and hr.received_date between %(start)s and %(end)s
                    )
                    as count_free_places, --"свободные места"

                    (
                        SELECT COUNT(distinct ha.id_pk)
                        from hospitalizations_amount ha
                        where
                            ha.organization_fk = mo.id_pk
                            and ha.received_date between %(start)s and %(end)s
                    )
                    as count_volumes, --"объёмы"

                    (
                        SELECT COUNT(distinct h.id_pk)
                        from hospitalization h
                        where
                            (h.organization_sender_fk = mo.id_pk)
                            and h.received_date between %(start)s and %(end)s
                            and h.type = 1
                    )
                    as count_referral, --"направления"

                    (
                        SELECT COUNT(distinct h.id_pk)
                        from hospitalization h
                        where
                            (h.organization_reciever_fk = mo.id_pk or h.organization_sender_fk = mo.id_pk)
                            and h.received_date between %(start)s and %(end)s
                            and h.type = 2
                    )
                    as count_hosp_referral, --"госпитализированные по направлению"

                    (
                        SELECT COUNT(distinct h.id_pk)
                        from hospitalization h
                        where
                            (h.organization_reciever_fk = mo.id_pk or h.organization_sender_fk = mo.id_pk)
                            and h.received_date between %(start)s and %(end)s
                            and h.type = 3
                    )
                    as count_hosp_urgently, --"госпитализированные экстренно"

                    (
                        SELECT COUNT(distinct h.id_pk)
                        from hospitalization h
                        where
                            (h.organization_reciever_fk = mo.id_pk or h.organization_sender_fk = mo.id_pk)
                            and h.received_date between %(start)s and %(end)s
                            and h.type = 4
                    )
                    as count_annulment, --"аннулирование"

                    (
                        SELECT COUNT(distinct h.id_pk)
                        from hospitalization h
                        where
                            (h.organization_reciever_fk = mo.id_pk or h.organization_sender_fk = mo.id_pk)
                            and h.received_date between %(start)s and %(end)s
                            and h.type = 5
                    )
                    as count_disposal --"выбытие"

                from
                    medical_organization mo
                where
                    mo.parent_fk is null --and mo.attach_class_fk <> 4
                GROUP BY mo.id_pk,  mo_name, mo.id_pk
                ORDER BY mo_name
                """
        self.data = MedicalOrganization.objects.raw(query, dict(
            start=parameters.start_date,
            end=parameters.end_date
        ))

    def print_page(self, sheet, parameters):
        sheet.set_position(0, 0)
        sheet.write(u'Сведения о количестве записей по информационному обмену по сопровождению застрахованных за ' +
                    parameters.start_date)

        sheet.set_position(2, 0)
        sheet.set_style(VALUE_STYLE)

        sheet.write(u'МО', 'c')
        sheet.write(u'Свободные места', 'c')
        sheet.write(u'Объёмы', 'c')
        sheet.write(u'Направления', 'c')
        sheet.write(u'Госпитализированные по направлен', 'c')
        sheet.write(u'Госпитализированные экстренно', 'c')
        sheet.write(u'Аннулирование', 'c')
        sheet.write(u'Выбытие', 'r')

        for item in self.data:
            sheet.write(item.mo_name, 'c')
            sheet.write(item.count_free_places, 'c')
            sheet.write(item.count_volumes, 'c')
            sheet.write(item.count_referral, 'c')
            sheet.write(item.count_hosp_referral, 'c')
            sheet.write(item.count_hosp_urgently, 'c')
            sheet.write(item.count_annulment, 'c')
            sheet.write(item.count_disposal, 'r')
        sheet.write(u'ИТОГО', 'c')
