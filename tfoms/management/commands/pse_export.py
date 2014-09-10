#! -*- coding: utf-8 -*-

from os import path
import time

from django.core.management.base import BaseCommand
from django.db.models import (Min, Max)

from medical_register.settings import (BASE_DIR, MONTH_NAME,
                                       REESTR_EXP)
from tfoms.management.commands.utils import excel_writer
from tfoms.models import (MedicalOrganization, ProvidedService, ProvidedServiceSanction, PaymentFailureCause)
from pse_export_func import pse_export


def print_summary(min_id, max_id, mo_code, year, period):
    print u'Печать акта для экспертов...'
    template_act_path = BASE_DIR+'/templates/summary.xls'
    reestr_path = REESTR_EXP % (year, period)
    mo_name = MedicalOrganization.objects.get(code=mo_code, parent=None).name
    act_path = u'%s/_%s.xlsx' % (reestr_path, mo_code.replace(' ', '_'))
    number = 1
    while path.exists(act_path):
        act_path = u'%s/_%s_%s.xlsx' % (reestr_path, mo_code.replace(' ', '_'), number)
        number += 1
    act_book = excel_writer.ExcelWriter(template_act_path, act_path)
    act_book.write_cell_ic(mo_name)
    act_book.write_cell_ic(u'%s %s года' % (MONTH_NAME[period], year))

    mo_sum = {'patients': 0, 'services': 0,
              'hospital': 0, 'day_hospital': 0,
              'policlinic': 0, 'policlinic_disease': 0,
              'policlinic_emergency': 0, 'examination_1_stage': 0,
              'examination_2_stage': 0, 'baseline_examination_adult': 0,
              'baseline_examination_children': 0, 'examination_children': 0,
              'ambulance': 0,
              'physical_children': 0, 'stomatology': 0,
              'invoiced_payment': 0, 'uet': 0.0}
    mo_services = ProvidedService.objects.filter(id_pk__range=(min_id, max_id))
    mo_service_list = mo_services.values('id_pk', 'tariff',
                                         'quantity',
                                         'code__uet', 'event__term__id_pk',
                                         'code__reason__ID', 'code__group__id_pk')
    mo_sum['patients'] = mo_services.values('event__record__patient__id_pk').distinct().count()
    for service in mo_service_list:
        mo_sum['services'] += 1
        mo_sum['invoiced_payment'] += service['tariff']
        uet = float(service['code__uet'] or 0)*float(service['quantity'] or 0)
        mo_sum['uet'] += uet
        term = service['event__term__id_pk']
        reason = service['code__reason__ID']
        group = service['code__group__id_pk']
        if term == 1:
            mo_sum['hospital'] += 1
        else:
            if term == 2:
                mo_sum['day_hospital'] += 1
            else:
                if term == 3 and reason != 5 and group != 19:
                    mo_sum['policlinic'] += 1
                else:
                    if term == 4:
                        mo_sum['ambulance'] += 1

        if term == 3 and reason == 1 and not group:
            mo_sum['policlinic_disease'] += 1
        else:
            if term == 3 and reason == 5:
                mo_sum['policlinic_emergency'] += 1

        if group == 7:
            mo_sum['examination_1_stage'] += 1
        else:
            if group == 8:
                mo_sum['examination_2_stage'] += 1
            else:
                if group == 9:
                    mo_sum['baseline_examination_adult'] += 1
                else:
                    if group == 11:
                        mo_sum['baseline_examination_children'] += 1
                    else:
                        if group in [12, 13]:
                            mo_sum['examination_children'] += 1
                        else:
                            if group in [15, 16]:
                                mo_sum['physical_children'] += 1
                            else:
                                if group == 19:
                                    mo_sum['stomatology'] += 1

    act_book.set_style({'border': 1})
    act_book.write_cell(2, 0, u'Патиентов')
    act_book.write_cell(2, 1, mo_sum['patients'])
    act_book.write_cell(3, 0, u'Услуг')
    act_book.write_cell(3, 1, mo_sum['services'])

    act_book.write_cell(5, 0, u'Госпитализаций')
    act_book.write_cell(5, 1, mo_sum['hospital'])

    act_book.write_cell(7, 0, u'Поликлиника')
    act_book.write_cell(7, 1, mo_sum['policlinic'])

    act_book.write_cell(8, 0, u'в т. ч. заболевания')
    act_book.write_cell(8, 1, mo_sum['policlinic_disease'])

    act_book.write_cell(9, 0, u'по диспансеризации взр. I этап')
    act_book.write_cell(9, 1, mo_sum['examination_1_stage'])

    act_book.write_cell(10, 0, u'по диспансеризации взр. II этап')
    act_book.write_cell(10, 1, mo_sum['examination_2_stage'])

    act_book.write_cell(11, 0, u'по профосмотру взр.')
    act_book.write_cell(11, 1, mo_sum['baseline_examination_adult'])

    act_book.write_cell(12, 0, u'по профосмотру дет.')
    act_book.write_cell(12, 1, mo_sum['baseline_examination_children'])

    act_book.write_cell(13, 0, u'по диспансеризации дет.')
    act_book.write_cell(13, 1, mo_sum['examination_children'])

    act_book.write_cell(14, 0, u'по медосмотру дет.')
    act_book.write_cell(14, 1, mo_sum['physical_children'])

    act_book.write_cell(16, 0, u'Неотложная помощь')
    act_book.write_cell(16, 1, mo_sum['policlinic_emergency'])

    act_book.write_cell(18, 0, u'Дневной стационар')
    act_book.write_cell(18, 1, mo_sum['day_hospital'])

    act_book.write_cell(20, 0, u'Скорая помощь')
    act_book.write_cell(20, 1, mo_sum['ambulance'])

    act_book.write_cell(21, 0, u'Стоматология')
    act_book.write_cell(21, 1, mo_sum['stomatology'])
    act_book.append_style({'num_format': '0.00'})
    act_book.write_cell(22, 0, u'УЕТ')
    act_book.write_cell(22, 1, mo_sum['uet'])
    act_book.write_cell(24, 0, u'Предъявленная сумма')
    act_book.write_cell(24, 1, mo_sum['invoiced_payment'])

    act_book.sheets[0].set_column(0, 0, 40)
    services_mek = ProvidedService.objects.filter(id_pk__range=(min_id, max_id), payment_type__id_pk=3)
    service_mek_group = {}
    for service in services_mek:
        sanction = ProvidedServiceSanction.objects.filter(service__pk=service.id_pk).\
            order_by('-pk')
        if sanction:
            failure_cause = sanction[0].error.failure_cause_id
            failure_cause = 53 if failure_cause == 115 else failure_cause
            if failure_cause not in service_mek_group.keys():
                service_mek_group[failure_cause] = 0
            service_mek_group[failure_cause] += 1

    act_book.current_sheet = 1
    act_book.current_row = 0
    act_book.current_col = 0
    act_book.set_style({})
    act_book.write_cell_ic(mo_name)
    act_book.write_cell_ic(u'%s %s года' % (MONTH_NAME[period], year))
    act_book.set_style({'border': 1})
    act_book.current_row = 4
    act_book.current_col = 0
    act_book.write_cell_ic(u'Код')
    act_book.write_cell_ic(u'Наименование')
    act_book.write_cell_ir(u'Количество')
    for failure_cause in service_mek_group:
        failure_cause_info = PaymentFailureCause.objects.get(id_pk=failure_cause)
        act_book.current_col = 0
        act_book.write_cell_ic(failure_cause_info.number)
        act_book.write_cell_ic(failure_cause_info.name)
        act_book.write_cell_ir(service_mek_group[failure_cause])
    act_book.sheets[1].set_column(1, 1, 50)
    act_book.close()


class Command(BaseCommand):

    def handle(self, *args, **options):
        start = time.time()
        year = args[0]
        period = args[1]
        mo_code = args[2]
        print u'Поиск услуг...'
        min_or_max = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            organization__code=mo_code).aggregate(min_id=Min('id_pk'), max_id=Max('id_pk'))
        min_id = min_or_max['min_id']
        max_id = min_or_max['max_id']
        print_summary(min_id, max_id, mo_code, year, period)
        pse_export(min_id, max_id, mo_code, year, period, 4)
        finish = time.time()
        print u'Время выполнения: {:.3f} минут'.format((finish - start)/60)




