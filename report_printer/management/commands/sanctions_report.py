#! -*- coding: utf-8 -*-

from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization
from django.core.management.base import BaseCommand
from report_printer.libs.report import Report, ReportParameters


class SanctionsPage(ReportPage):
    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = """
            select
                org.id_pk,
                org.name AS organization_name,--pss.act,
                sum(case when pss.type_fk = 2 then pss.underpayment else 0 end) AS mee,
                sum(case when pss.type_fk = 3 then pss.underpayment else 0 end) AS ekmp,
                sum(case when pss.type_fk = 2 then pss.penalty else 0 end) AS mee_penalty,
                sum(case when pss.type_fk = 3 then pss.penalty else 0 end) AS ekmp_penalty,
                --sum(case when pss.type_fk = 4 then pss.underpayment else 0 end),
                mr.organization_code
            from provided_service ps
                JOIN medical_service ms
                    on ms.id_pk = ps.code_fk
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                JOIN provided_service_sanction pss
                    on pss.service_fk = ps.id_pk and pss.type_fk in (2, 3, 4)
                LEFT JOIN medical_organization org
                    on (org.code = mr.organization_code and org.parent_fk is null) or
                    (org.id_pk = (select parent_fk from medical_organization where code = mr.organization_code order by id_pk DESC limit 1))
            where mr.is_active
                and pss.date between '2016-05-01' and '2016-05-31'
            GROUP BY org.id_pk, org.name, mr.organization_code, org.id_pk, org.id_pk
            ORDER BY org.name--, pss.act
        """
        self.data = MedicalOrganization.objects.raw(query)

    def print_page(self, sheet, parameters):
        sheet.set_position(0, 0)
        sheet.write(u'Организация', 'c')
        sheet.write(u'МЭЭ', 'c')
        sheet.write(u'ЭКМП', 'c')
        sheet.write(u'МЭЭ штрафы', 'c')
        sheet.write(u'ЭКМП штрафы', 'c')
        sheet.set_position(1, 0)
        for item in self.data:
            sheet.write(item.organization_name, 'c')
            sheet.write(item.mee, 'c')
            sheet.write(item.ekmp, 'c')
            sheet.write(item.mee_penalty, 'c')
            sheet.write(item.ekmp_penalty, 'r')


class Command(BaseCommand):

    def handle(self, *args, **options):
        parameters = ReportParameters()
        parameters.path_to_dir = u'T:\Паршин А.А\сверка санкций'
        parameters.report_name = u'Сверка санкций за июнь 2016'

        report = Report()
        report.add_page(SanctionsPage())
        report.print_pages(parameters)
