#! -*- coding: utf-8 -*-

from time import clock

from django.core.management.base import BaseCommand

from tfoms import func
from medical_service_register.path import REESTR_EXP, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.const import MONTH_NAME
from pse_exporter import Command as PseExporter


### Печать сокращённого сводного акта для экспертов
### (для сверки суммы поданной больницей)
def print_summary(mo_code, data):
    print u'Печать акта для экспертов'
    target_dir = REESTR_EXP % (func.YEAR, func.PERIOD)

    services = data['invoiced_services']
    patients = data['patients']
    sanctions = data['sanctions']

    mo_sum = {'patients': {'value': len(patients), 'pos': 2},            # Численность пациентов
              'services': {'value': len(services), 'pos': 3},            # Количество услуг
              'hospital': {'value': 0, 'pos': 5},                        # Госпитализации по круг. стац.
              'day_hospital': {'value': 0, 'pos': 18},                   # Госпитализации дн. стац.
              'policlinic': {'value': 0, 'pos': 7},                      # Поликлиника
              'policlinic_disease': {'value': 0, 'pos': 8},              # Поликлиника (по заболеванию)
              'policlinic_emergency': {'value': 0, 'pos': 16},           # Поликлиника (неотложка)
              'examination_1_stage': {'value': 0, 'pos': 9},             # Диспанс. взр. I этап
              'examination_2_stage': {'value': 0, 'pos': 10},            # Диспанс. взр. II этап
              'baseline_examination_adult': {'value': 0, 'pos': 11},     # Профосмотры взр.
              'baseline_examination_children': {'value': 0, 'pos': 12},  # Профосмотры дет.
              'examination_children': {'value': 0, 'pos': 13},           # Диспанс дет. сирот
              'ambulance': {'value': 0, 'pos': 20},                      # Скорая помощь
              'physical_children': {'value': 0, 'pos': 14},              # Медосмотр дет.
              'stomatology': {'value': 0, 'pos': 21},                    # Стоматология
              'invoiced_payment': {'value': 0, 'pos': 24},               # Предъявленная сумма
              'uet': {'value': 0.0, 'pos': 22}}                          # УЕТ по стоматологии

    # Рассчёт сумм
    for service in services:
        # Итоговые суммы
        mo_sum['invoiced_payment']['value'] += service['tariff']
        mo_sum['uet']['value'] += service['uet']

        # Суммы по группам услуг
        rules_dict = [
            (service['term'] == 1 and not service['group'] == 27, 'hospital'),
            (service['term'] == 2 and service['group'] not in (27, 28), 'day_hospital'),
            (service['term'] == 3 and not service['group'] == 19, 'policlinic'),
            (service['term'] == 4, 'ambulance'),
            (service['term'] == 3 and service['reason'] == 1
             and not service['group'] == 19, 'policlinic_disease'),
            (service['term'] == 3 and service['reason'] == 5, 'policlinic_emergency'),
            (service['group'] == 7, 'examination_1_stage'),
            (service['group'] in [25, 26], 'examination_2_stage'),
            (service['group'] == 9, 'baseline_examination_adult'),
            (service['group'] == 11, 'baseline_examination_children'),
            (service['group'] in [12, 13], 'examination_children'),
            (service['group'] in [15, 16], 'physical_children'),
            (service['group'] == 19, 'stomatology')
        ]
        for rule in rules_dict:
            if rule[0]:
                mo_sum[rule[1]]['value'] += 1

    # Расчёт по ошибкам
    failure_cause_dict = {}
    for service_id, sanction in sanctions.iteritems():
        active_sanction = sanction[0]
        failure_cause_id = func.ERRORS[active_sanction['error']]['failure_cause']
        if failure_cause_id not in failure_cause_dict:
            failure_cause_dict[failure_cause_id] = 0
        failure_cause_dict[failure_cause_id] += 1

    # Печать акта
    with ExcelWriter(ur'%s/__%s' % (target_dir, mo_code),
                     template=ur'%s/templates/excel_pattern/summary_1.xls' % BASE_DIR) as act_book:
        act_book.set_sheet(0)
        act_book.set_cursor(0, 0)
        act_book.write_cell(func.get_mo_info(mo_code)['name'], 'c', 1)
        act_book.write_cell(u'{month} {year} года'.format(month=MONTH_NAME[func.PERIOD], year=func.YEAR), 'c', 1)

        for value in mo_sum.itervalues():
            act_book.set_cursor(value['pos'], 1)
            act_book.write_cell(value['value'], 'c', 2)

        act_book.set_sheet(1)
        act_book.set_cursor(0, 0)
        act_book.write_cell(func.get_mo_info(mo_code)['name'], 'c', 1)
        act_book.write_cell(u'{month} {year} года'.format(month=MONTH_NAME[func.PERIOD], year=func.YEAR), 'c', 1)

        act_book.set_sheet(1)
        act_book.set_cursor(5, 0)
        for key, value in failure_cause_dict.iteritems():
            act_book.write_cell(func.FAILURE_CAUSES[key]['number'], 'c')
            act_book.write_cell(func.FAILURE_CAUSES[key]['name'], 'c')
            act_book.write_cell(value, 'r')
        act_name = act_book.name
    return act_name


### Печатает краткий сводный акт для сверки суммы поданной больницей
### Форма запуска print_summary код_больницы_1 код_больницы_2 ...
class Command(BaseCommand):

    def handle(self, *args, **options):
        mo_register = [mo for mo in args]

        printed_act = []
        for mo_code in mo_register:
            start = clock()
            print u'Выгружается...', mo_code
            data = {
                'invoiced_services': func.get_services(mo_code, is_include_operation=True),
                'patients': func.get_patients(mo_code),
                'sanctions': func.get_sanctions(mo_code)
            }
            act_name = print_summary(mo_code, data)
            PseExporter().handle(*[mo_code, 8])
            elapsed = clock() - start
            print u'Выгружен', mo_code
            print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed//60), int(elapsed % 60))
            print
            printed_act.append((act_name, func.get_mo_info(mo_code)['name']))

        print u'-'*50
        print u'Напечатанные акты:'
        for act in printed_act:
            print act[0], act[1]