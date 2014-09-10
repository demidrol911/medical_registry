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

    rb = open_workbook('d:/work/01_adult_disp.xls', formatting_info=True)
    tl = easyxf('border: left thin, top thin, bottom thin, right thin; font: name Times New Roman, height 200;')
    r_sheet = rb.sheet_by_index(0)
    wb = copy(rb)
    w_sheet = wb.get_sheet(0)

    total_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code__in=('019021', '019022', '019023', '019024'))

    male_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code__in=('019021', '019023'))

    female_services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True,
        code__code__in=('019022', '019024'))

    total_services_students = total_services.filter(event__comment__startswith='F1')
    male_services_students = male_services.filter(event__comment__startswith='F1')
    female_services_students = female_services.filter(event__comment__startswith='F1')

    comment_round_one = Q(event__comment__startswith='F00') | Q(event__comment__startswith='F10') | Q(event__comment='') | Q(event__comment=None)
    comment_round_two = Q(event__comment__startswith='F01') | Q(event__comment__startswith='F11')

    for row, services in enumerate([total_services, male_services,
                                    female_services]):

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
        group_one = Q(event__comment='F001') | Q(event__comment='F011') | Q(event__comment='F101') | Q(event__comment='F111')
        group_two = Q(event__comment='F002') | Q(event__comment='F012') | Q(event__comment='F102') | Q(event__comment='F112')
        group_three = Q(event__comment='F003') | Q(event__comment='F013') | Q(event__comment='F103') | Q(event__comment='F113')
        group_none = Q(event__comment='') | Q(event__comment=None) |  Q(event__comment='F000') | Q(event__comment='F100') | Q(event__comment='F110') | Q(event__comment='F010')

        patient_health_group_one = services.filter(group_one).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_two = services.filter(group_two).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_three = services.filter(group_three).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_none = services.filter(group_none).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        #print patient_health_group_none
        w_sheet.write(2, 0,
                      u'по состоянию на %s' % (datetime.datetime.now().strftime('%d.%m.%Y')),
                      style=tl)
        w_sheet.write(8+row, 2, total_invoiced, style=tl)
        w_sheet.write(8+row, 3, invoiced_round_one_events, style=tl)
        w_sheet.write(8+row, 4, invoiced_round_one_sum, style=tl)
        w_sheet.write(8+row, 5, invoiced_round_two_events, style=tl)
        w_sheet.write(8+row, 6, invoiced_round_tow_sum, style=tl)
        w_sheet.write(8+row, 7, total_accepted, style=tl)
        w_sheet.write(8+row, 8, accepted_round_one_events, style=tl)
        w_sheet.write(8+row, 9, accepted_round_one_sum, style=tl)
        w_sheet.write(8+row, 10, accepted_round_two_events, style=tl)
        w_sheet.write(8+row, 11, accepted_round_two_sum, style=tl)
        w_sheet.write(8+row, 12, invoiced_round_two_events, style=tl)
        w_sheet.write(8+row, 13, patient_health_group_one, style=tl)
        w_sheet.write(8+row, 14, patient_health_group_two, style=tl)
        w_sheet.write(8+row, 15, patient_health_group_three, style=tl)
        w_sheet.write(8+row, 16, patient_health_group_none, style=tl)

    for row, services in enumerate([total_services_students, male_services_students, female_services_students]):
        print row
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

        group_one = Q(event__comment='F001') | Q(event__comment='F011') | Q(event__comment='F101') | Q(event__comment='F111')
        group_two = Q(event__comment='F002') | Q(event__comment='F012') | Q(event__comment='F102') | Q(event__comment='F112')
        group_three = Q(event__comment='F003') | Q(event__comment='F013') | Q(event__comment='F103') | Q(event__comment='F113') | Q(event__comment='') | Q(event__comment=None) |  Q(event__comment='F000') | Q(event__comment='F100') | Q(event__comment='F110') | Q(event__comment='F010')

        patient_health_group_one = services.filter(group_one).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_two = services.filter(group_two).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_three = services.filter(group_three).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        patient_health_group_none = services.filter(group_none).values('event__record__patient__pk').distinct('event__record__patient__pk').count()
        print patient_health_group_none

        w_sheet.write(17+row, 2, total_invoiced, style=tl)
        w_sheet.write(17+row, 3, invoiced_round_one_events, style=tl)
        w_sheet.write(17+row, 4, invoiced_round_one_sum, style=tl)
        w_sheet.write(17+row, 5, invoiced_round_two_events, style=tl)
        w_sheet.write(17+row, 6, invoiced_round_tow_sum, style=tl)
        w_sheet.write(17+row, 7, total_accepted, style=tl)
        w_sheet.write(17+row, 8, accepted_round_one_events, style=tl)
        w_sheet.write(17+row, 9, accepted_round_one_sum, style=tl)
        w_sheet.write(17+row, 10, accepted_round_two_events, style=tl)
        w_sheet.write(17+row, 11, accepted_round_two_sum, style=tl)
        w_sheet.write(17+row, 12, invoiced_round_two_events, style=tl)
        w_sheet.write(17+row, 13, patient_health_group_one, style=tl)
        w_sheet.write(17+row, 14, patient_health_group_two, style=tl)
        w_sheet.write(17+row, 15, patient_health_group_three, style=tl)
        w_sheet.write(17+row, 16, patient_health_group_none, style=tl)

    wb.save('d:/work/01_adult_disp_05_10_%s.xls' % ( YEAR, ))


class Command(BaseCommand):
    help = 'export reports'

    def handle(self, *args, **options):
        main()
