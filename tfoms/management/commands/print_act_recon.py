#! -*- coding: utf-8 -*-

import time

from django.core.management.base import BaseCommand
from django.db.models import Sum

from medical_service_register.path import REESTR_EXP, BASE_DIR, MONTH_NAME
from tfoms.management.commands.utils import excel_writer_1
from tfoms.management.commands.utils.excel_style import (VALUE_STYLE,
                                                         TITLE_STYLE,
                                                         TOTAL_STYLE)
from tfoms.models import ProvidedService, AdministrativeArea


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
                   'organization__name',
                   'organization__region__ID').\
            annotate(sum_tariff=Sum('tariff'),
                     sum_invoiced=Sum('invoiced_payment'),
                     sum_accepted=Sum('accepted_payment')).\
            order_by('organization__region__name', 'organization__name')
        total_sum = {'sum_tariff': 0, 'sum_invoiced': 0, 'sum_accepted': 0}

        # Распечатка акта
        with excel_writer_1.ExcelWriter(u'%s/сверка_%s_%s' % (reestr_path,
                                                              year,
                                                              MONTH_NAME[period]),
                                        template=ur'%s/templates/recon.xls' % BASE_DIR) as act_book:
            act_book.set_overall_style({'font_size': 11})
            act_book.set_style(VALUE_STYLE)
            current_region = 0
            act_book.set_cursor(1, 0)
            for mo_data in reconciliation_data:
                # Печать названия региона в заголовке
                if current_region != mo_data['organization__region__ID']:
                    current_region = mo_data['organization__region__ID']
                    admin_area = AdministrativeArea.objects.filter(ID=current_region)
                    name = admin_area[0].name if admin_area else ''
                    act_book.set_style(TITLE_STYLE)
                    act_book.set_style_property('align', 'center')
                    act_book.write_cell(name, 'r', 4)
                    act_book.set_style(VALUE_STYLE)

                # Распечатка сумм
                act_book.write_cell(mo_data['organization__code'], 'c')
                act_book.write_cell(mo_data['organization__name'], 'c')
                act_book.write_cell(mo_data['sum_tariff'], 'c')
                act_book.write_cell(mo_data['sum_invoiced'], 'c')
                act_book.write_cell(mo_data['sum_accepted'], 'r')

                # Рассчёт итоговой суммы
                total_sum['sum_tariff'] += mo_data['sum_tariff']
                total_sum['sum_invoiced'] += mo_data['sum_invoiced']
                total_sum['sum_accepted'] += mo_data['sum_accepted']

            # Распечатка итоговой суммы
            act_book.set_style(TOTAL_STYLE)
            act_book.write_cell(u'Итого', 'c')
            act_book.write_cell(u' ', 'c')
            act_book.write_cell(total_sum['sum_tariff'], 'c')
            act_book.write_cell(total_sum['sum_invoiced'], 'c')
            act_book.write_cell(total_sum['sum_accepted'], 'r')
        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)


