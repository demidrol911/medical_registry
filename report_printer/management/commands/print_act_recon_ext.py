#! -*- coding: utf-8 -*-

import time
import datetime

from django.core.management.base import BaseCommand
from django.db.models import Sum

from report_printer.excel_style import VALUE_STYLE
from medical_service_register.path import REESTR_EXP, BASE_DIR
from helpers.excel_writer import ExcelWriter
from report_printer.const import ACT_CELL_POSITION_EXT, MONTH_NAME
from tfoms.models import ProvidedService, Sanction




### Печатает сводный акт принятых услуг за месяц
### c доплатой и подушевым
### Формат вызова print_act_recon_ext год период
class Command(BaseCommand):

    def handle(self, *args, **options):
        start = time.time()
        year = args[0]
        period = args[1]
        reestr_path = REESTR_EXP % (year, period)

        # Рассчёт сумм
        invoiced_payment = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True).\
            values('organization__code').\
            annotate(sum_invoiced=Sum('invoiced_payment'))

        accepted_payment = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            payment_type__in=[2, 4]).\
            values('organization__code').\
            annotate(sum_accepted=Sum('accepted_payment'))

        policlinic_capitation = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            payment_type__in=[2, 4],
            payment_kind__in=[2, 3],
            event__term=3).\
            values('organization__code').\
            annotate(sum_capitation=Sum('accepted_payment'))

        acute_care = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            payment_type__in=[2, 4],
            payment_kind__in=[2, 3],
            event__term=4).\
            values('organization__code').\
            annotate(sum_capitation=Sum('accepted_payment'))

        surcharge = Sanction.objects.filter(
            type=4,
            date=datetime.date(year=int(year), month=int(period)-1, day=30)).\
            values('service__organization__code').\
            annotate(sum_surcharge=Sum('underpayment'))

        def print_sum(act_book, sum_data, sum_key, mo_key, column):
            for data in sum_data:
                act_book.set_cursor(ACT_CELL_POSITION_EXT[data[mo_key]], column)
                act_book.write_cell(data[sum_key])

        # Распечатка акта
        with ExcelWriter(u'%s/сверка_%s_%s' % (reestr_path, year, MONTH_NAME[period]),
                         template=ur'%s/templates/excel_pattern/recon_ext.xls' % BASE_DIR) as act_book:
            act_book.set_cursor(2, 0)
            act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
            act_book.set_style(VALUE_STYLE)
            print_sum(act_book, invoiced_payment, 'sum_invoiced', 'organization__code', 3)
            print_sum(act_book, accepted_payment, 'sum_accepted', 'organization__code', 4)
            print_sum(act_book, policlinic_capitation, 'sum_capitation', 'organization__code', 5)
            print_sum(act_book, acute_care, 'sum_capitation', 'organization__code', 6)
            print_sum(act_book, surcharge, 'sum_surcharge', 'service__organization__code', 11)

        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)


