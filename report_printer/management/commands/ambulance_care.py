#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from main.models import MedicalOrganization
from report_printer.excel_style import VALUE_STYLE
from tfoms import func
from medical_service_register.path import REESTR_EXP, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.const import ACT_CELL_POSITION, MONTH_NAME

AMBULANCE_COLUMN_POSITION = {
    27: 2,
    28: 4,
    29: 6,
    30: 8,
    31: 10,
    32: 12,
    33: 14,
    34: 16,
    35: 18,
    36: 20,
    37: 22,
    38: 24,
    39: 26,
    40: 28,
    41: 30,
    42: 32,
    43: 34,
    44: 36,
    45: 38,
    46: 40,
    47: 42,
    48: 44,
    49: 46,
    50: 48
}


def calculate_ambulance_sum():
    query = """
            select
            mo.id_pk,
            mr.organization_code as organization_code,
            ms.subgroup_fk as ambulance_kind,
            count(distinct CASE WHEN ms.code like '0%%' THEN ps.id_pk END) as adult_count,
            count(distinct CASE WHEN ms.code like '1%%' THEN ps.id_pk END) as child_count
            from medical_register mr
                JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
                JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
                JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
                where
                  mr.is_active and mr.year = %(year)s
                  and mr.period = %(period)s
                  and pe.term_fk = 4
                  and ps.payment_type_fk = 2
            group by mo.id_pk, organization_code, ms.subgroup_fk
            """
    count_services_by_mo = MedicalOrganization.objects.raw(
        query,
        dict(year=func.YEAR, period=func.PERIOD)
    )
    return count_services_by_mo


def print_act_ambulance(count_services):
    reestr_path = REESTR_EXP % (func.YEAR, func.PERIOD)
    with ExcelWriter(u'%s/скорая_помощь_%s_%s' % (reestr_path, func.YEAR, MONTH_NAME[func.PERIOD]),
                     template=ur'%s/templates/excel_pattern/ambulance_care.xls' % BASE_DIR) as act_book:
        act_book.set_style(VALUE_STYLE)
        for count_in_mo in count_services:
            row_index = ACT_CELL_POSITION[count_in_mo.organization_code]
            column_index = AMBULANCE_COLUMN_POSITION[count_in_mo.ambulance_kind]
            act_book.write_cella(row_index, column_index, count_in_mo.adult_count)
            act_book.write_cella(row_index, column_index+1, count_in_mo.child_count)


class Command(BaseCommand):

    def handle(self, *args, **options):
        count_services_by_mo = calculate_ambulance_sum()
        print_act_ambulance(count_services_by_mo)




