#! -*- coding: utf-8 -*-

import time

from django.core.management.base import BaseCommand
from django.db.models import Sum

from medical_service_register.path import REESTR_EXP, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.const import ACT_CELL_POSITION, MONTH_NAME
from tfoms.models import ProvidedService


### Печатает сводный акт принятых услуг за месяц
### Формат вызова print_act_recon год период
class Command(BaseCommand):

    def handle(self, *args, **options):
        start = time.time()
        year = args[0]
        period = args[1]
        reestr_path = REESTR_EXP % (year, period)

        # Рассчёт сумм
        reconciliation_data = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            payment_type_id__in=[2, 4]).\
            values('organization__code',
                   'organization__name').\
            annotate(sum_tariff=Sum('tariff'),
                     sum_invoiced=Sum('invoiced_payment'),
                     sum_accepted=Sum('accepted_payment'))
        total_sum = {'sum_tariff': 0, 'sum_invoiced': 0, 'sum_accepted': 0}

        # Распечатка акта
        with ExcelWriter(u'%s/сверка_%s_%s' % (reestr_path, year, MONTH_NAME[period]),
                         template=ur'%s/templates/excel_pattern/recon.xls' % BASE_DIR) as act_book:
            act_book.set_style({'align': 'center'})
            act_book.set_cursor(5, 1)
            act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
            act_book.set_style()
            for mo_data in reconciliation_data:
                act_book.set_cursor(ACT_CELL_POSITION[mo_data['organization__code']], 2)
                # Распечатка сумм
                act_book.write_cell(mo_data['sum_tariff'], 'c')
                act_book.write_cell(mo_data['sum_invoiced'], 'c')
                act_book.write_cell(mo_data['sum_accepted'])

                # Рассчёт итоговой суммы
                total_sum['sum_tariff'] += mo_data['sum_tariff']
                total_sum['sum_invoiced'] += mo_data['sum_invoiced']
                total_sum['sum_accepted'] += mo_data['sum_accepted']

            # Распечатка итоговой суммы
            act_book.set_cursor(101, 2)
            act_book.write_cell(total_sum['sum_tariff'], 'c')
            act_book.write_cell(total_sum['sum_invoiced'], 'c')
            act_book.write_cell(total_sum['sum_accepted'])
        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)


