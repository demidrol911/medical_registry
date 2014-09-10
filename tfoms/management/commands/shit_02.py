#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Sum
import datetime
from tfoms.models import (ProvidedService, )

from xlutils.copy import copy
from xlrd import open_workbook
from xlwt import easyxf


def main():
    YEAR = '2013'
    PERIOD = ('05', '06', '07', '08', '09', '10')

    row = 8
    rb = open_workbook('d:/work/02_adult_profosmotr.xls', formatting_info=True)
    tl = easyxf('border: left thin, top thin, bottom thin, right thin; font: name Times New Roman, height 200;')
    r_sheet = rb.sheet_by_index(0)
    wb = copy(rb)
    w_sheet = wb.get_sheet(0)

    services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period__in=PERIOD,
        event__record__register__is_active=True)

    prof_med_osm = services.filter(code__code='019212')

    total_invoiced = prof_med_osm.aggregate(sum=Sum('invoiced_payment'))
    total_patients = prof_med_osm.distinct('event__record__patient__pk').values('event__record__patient__pk').count()
    total_accepted = prof_med_osm.filter(
        payment_type_id__in=(2, 4)).aggregate(sum=Sum('accepted_payment'))

    prof_med_osm_man = prof_med_osm.filter(
        event__record__patient__gender_id=1)

    total_invoiced_man = prof_med_osm_man.aggregate(sum=Sum('invoiced_payment'))
    total_patients_man = prof_med_osm_man.distinct('event__record__patient__pk').values('event__record__patient__pk').count()
    total_accepted_man = prof_med_osm_man.filter(
        payment_type_id__in=(2, 4)).aggregate(sum=Sum('accepted_payment'))

    prof_med_osm_woman = prof_med_osm.filter(
        event__record__patient__gender_id=2)

    total_invoiced_woman = prof_med_osm_woman.aggregate(sum=Sum('invoiced_payment'))
    total_patients_woman = prof_med_osm_woman.distinct('event__record__patient__pk').values('event__record__patient__pk').count()
    total_accepted_woman = prof_med_osm_woman.filter(
        payment_type_id__in=(2, 4)).aggregate(sum=Sum('accepted_payment'))

    print total_invoiced['sum'], total_patients, total_accepted['sum']
    print total_invoiced_man['sum'], total_patients_man, total_accepted_man['sum']
    print total_invoiced_woman['sum'], total_patients_woman, total_accepted_woman['sum']

    w_sheet.write(2, 0,
                  u'по состоянию на %s' % (datetime.datetime.now().strftime('%d.%m.%Y')),
                  style=tl)
    w_sheet.write(7, 2, total_invoiced['sum'], style=tl)
    w_sheet.write(7, 3, total_patients, style=tl)
    w_sheet.write(7, 4, total_accepted['sum'], style=tl)
    w_sheet.write(8, 2, total_invoiced_man['sum'], style=tl)
    w_sheet.write(8, 3, total_patients_man, style=tl)
    w_sheet.write(8, 4, total_accepted_man['sum'], style=tl)
    w_sheet.write(9, 2, total_invoiced_woman['sum'], style=tl)
    w_sheet.write(9, 3, total_patients_woman, style=tl)
    w_sheet.write(9, 4, total_accepted_woman['sum'], style=tl)

    wb.save('d:/work/02_adult_profosmotr_05_10_%s.xls' % (YEAR, ))


class Command(BaseCommand):
    help = 'export reports'

    def handle(self, *args, **options):
        main()
