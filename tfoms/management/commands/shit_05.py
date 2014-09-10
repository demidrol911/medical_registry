#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models import Q
import datetime
from tfoms.models import (ProvidedService, )
from xlutils.copy import copy
from xlrd import open_workbook
from xlwt import easyxf


def main():
    YEAR = '2013'
    PERIOD = ('05', '06', '07', '08', '09', '10')

    rb = open_workbook('d:/work/05_medosm_neshoversh.xls', formatting_info=True)
    tl = easyxf('border: left thin, top thin, bottom thin, right thin; font: name Times New Roman, height 200;')
    r_sheet = rb.sheet_by_index(0)
    wb = copy(rb)
    w_sheet = wb.get_sheet(0)

    preventive_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code__in=(
            '119051', '119052', '119053', '119054', '119055', '119056'))

    preliminary_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code__in=('119101', '119119', '119120'))

    periodic_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code='119151')

    comment_round_one = Q(event__comment__startswith='F0') | Q(event__comment='')
    comment_round_two = Q(event__comment__startswith='F1')

    for row, services in enumerate([preventive_services, preliminary_services,
                                    periodic_services]):

        total_invoiced = services.aggregate(sum=Sum('invoiced_payment'))['sum']
        invoiced_round_one_events = services.filter(
            comment_round_one).values('event__pk').distinct('event__pk').count()
        invoiced_round_one_sum = services.filter(
            comment_round_one).aggregate(sum=Sum('invoiced_payment'))['sum']
        invoiced_round_two_events = services.filter(
            comment_round_two).values('event__pk').distinct('event__pk').count()
        invoiced_round_tow_sum = services.filter(
            comment_round_two).aggregate(sum=Sum('invoiced_payment'))['sum']

        total_accepted = services.aggregate(sum=Sum('accepted_payment'))['sum']
        accepted_round_one_events = services.filter(
            comment_round_one &
            Q(payment_type_id=2)).values('event__pk').distinct('event__pk').count()
        accepted_round_one_sum = services.filter(
            comment_round_one &
            Q(payment_type_id=2)).aggregate(sum=Sum('accepted_payment'))['sum']
        accepted_round_two_events = services.filter(
            comment_round_two &
            Q(payment_type__in=(2, 4))).values('event__pk').distinct('event__pk').count()
        accepted_round_two_sum = services.filter(
            comment_round_two &
            Q(payment_type_id__in=(2, 4))).aggregate(sum=Sum('accepted_payment'))['sum']

        group_one = Q(event__comment__startswith='F01') | Q(event__comment__startswith='F11')
        group_two = Q(event__comment__startswith='F02') | Q(event__comment__startswith='F12')
        group_three = Q(event__comment__startswith='F03') | Q(event__comment__startswith='F13')
        group_four = Q(event__comment__startswith='F04') | Q(event__comment__startswith='F14')
        group_five = Q(event__comment__startswith='F05') | Q(event__comment__startswith='F15')
        group_none = Q(event__comment='') | Q(event__comment=None)
        patient_health_group_one = services.filter(group_one).values('event__record__patient__pk').count()
        patient_health_group_two = services.filter(group_two).values('event__record__patient__pk').count()
        patient_health_group_three = services.filter(group_three).values('event__record__patient__pk').count()
        patient_health_group_four = services.filter(group_four).values('event__record__patient__pk').count()
        patient_health_group_five = services.filter(group_five).values('event__record__patient__pk').count()
        patient_health_group_none = services.filter(group_none).values('event__record__patient__pk').count()
        print patient_health_group_none

        w_sheet.write(2, 0,
                      u'по состоянию на %s' % (datetime.datetime.now().strftime('%d.%m.%Y')),
                      style=tl)
        w_sheet.write(7+row, 1, total_invoiced, style=tl)
        w_sheet.write(7+row, 2, invoiced_round_one_events, style=tl)
        w_sheet.write(7+row, 3, invoiced_round_one_sum, style=tl)
        w_sheet.write(7+row, 4, invoiced_round_two_events, style=tl)
        w_sheet.write(7+row, 5, invoiced_round_tow_sum, style=tl)
        w_sheet.write(7+row, 6, total_accepted, style=tl)
        w_sheet.write(7+row, 7, accepted_round_one_events, style=tl)
        w_sheet.write(7+row, 8, accepted_round_one_sum, style=tl)
        w_sheet.write(7+row, 9, accepted_round_two_events, style=tl)
        w_sheet.write(7+row, 10, accepted_round_two_sum, style=tl)
        w_sheet.write(7+row, 11, patient_health_group_one, style=tl)
        w_sheet.write(7+row, 12, patient_health_group_two, style=tl)
        w_sheet.write(7+row, 13, patient_health_group_three, style=tl)
        w_sheet.write(7+row, 14, patient_health_group_four, style=tl)
        w_sheet.write(7+row, 15, patient_health_group_five, style=tl)

    wb.save('d:/work/05_medosm_neshoversh_%s_%s.xls' % (PERIOD, YEAR))


class Command(BaseCommand):
    help = 'export reports'

    def handle(self, *args, **options):
        main()
