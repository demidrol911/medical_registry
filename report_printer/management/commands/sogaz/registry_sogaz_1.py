#! -*- coding: utf-8 -*-
from copy import deepcopy
from decimal import Decimal
from django.core.management.base import BaseCommand
from tfoms import func
from medical_service_register.path import REESTR_DIR, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.excel_style import VALUE_STYLE
from tfoms.func import get_services, get_patients, get_sanctions
from helpers.correct import date_correct


# Рассчёт итоговой суммы
def calculate_total_sum(total_sum, intermediate_sum):
    for key in total_sum:
        total_sum[key] += intermediate_sum[key]
    return total_sum


### Распечатка итоговой суммы по ошибкам (для акта ошибки МЭК)
def print_total_sum_error(act_book, title, total_sum):
    act_book.set_style(VALUE_STYLE)
    act_book.write_cell(title, 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell(total_sum['sum_day'], 'c')
    act_book.write_cell(total_sum['sum_uet'], 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell('', 'c')
    act_book.write_cell(total_sum['sum_tariff'], 'c')
    act_book.write_cell(total_sum['sum_calculated_payment'], 'c')
    act_book.write_cell(total_sum['sum_discontinued_payment'], 'r')
    act_book.set_style()
    act_book.row_inc()


def print_registry_sogaz_2(act_book, mo):
    handbooks = {
        'errors': func.ERRORS,
        'failure_cause': func.FAILURE_CAUSES
    }

    mo_name = func.get_mo_info(mo)['name']
    data = {
        'patients': func.get_patients(mo),
        'sanctions': func.get_sanctions(mo),
        'discontinued_services': func.get_services(mo, payment_type=[3, 4])
    }
    capitation_events = func.get_capitation_events(mo_code=mo)
    init_sum = {
        'sum_day': 0,                      # Сумма дней
        'sum_uet': 0,                      # Сумма УЕТ
        'sum_tariff': 0,                   # Сумма основного тарифа
        'sum_calculated_payment': 0,       # Рассчётная сумма
        'sum_discontinued_payment': 0      # Сумма снятая с оплаты
    }

    act_book.set_sheet(1)
    act_book.set_style()
    act_book.write_cella(3, 3, mo_name)
    services_mek = data['discontinued_services']
    sanctions_mek = data['sanctions']
    patients = data['patients']
    errors_code = handbooks['errors']

    # Разбивка снятых с оплаты услуг на группы по коду ошибки и причине отказа
    failure_causes_group = {}
    for index, service in enumerate(services_mek):
        active_error = sanctions_mek[service['id']][0]['error']
        failure_cause_id = errors_code[active_error]['failure_cause']

        if failure_cause_id not in failure_causes_group:
            failure_causes_group[failure_cause_id] = {}

        if active_error not in failure_causes_group[failure_cause_id]:
            failure_causes_group[failure_cause_id][active_error] = []

        failure_causes_group[failure_cause_id][active_error].\
            append((index, service['event_id'] in capitation_events or service['term'] == 4))

    act_book.set_cursor(9, 0)
    title_table = [
        u'№ n/n в реестре счетов', u'№ документа ОМС',
        u'ФИО', u'Дата рождения', u'Номер карты', u'Дата лечения', u'Кол-во дней лечения',
        u'УЕТ', u'Код услуги', u'Код по МКБ-10', u'Отд.', u'Профиль отделения', u'№ случая',
        u'ID_SERV', u'ID_PAC', u'Представлено к оплате', u'Расчетная сумма',
        u'Отказано в оплате'
    ]
    total_sum = deepcopy(init_sum)

    for failure_cause_id in failure_causes_group:
        act_book.set_style({'bold': True, 'font_color': 'red', 'font_size': 11})
        act_book.write_cell(func.FAILURE_CAUSES[failure_cause_id]['number'] + ' ' +
                            func.FAILURE_CAUSES[failure_cause_id]['name'], 'r')
        for error_id in failure_causes_group[failure_cause_id]:
            # Распечатка наименования ошибки
            act_book.set_style({'bold': True, 'font_color': 'blue', 'font_size': 11})
            act_book.write_cell(func.ERRORS[error_id]['code'] + ' ' +
                                func.ERRORS[error_id]['name'], 'r')
            act_book.set_style({'bold': True, 'border': 1, 'align': 'center', 'font_size': 11, 'text_wrap': True})

            # Распечатка загловков таблицы с информацией о снятых услугах
            for title in title_table:
                act_book.write_cell(title, 'c')
            act_book.row_inc()
            total_sum_error = deepcopy(init_sum)               # Итоговая сумма по ошибке
            act_book.set_style(VALUE_STYLE)
            for index, is_capitation in failure_causes_group[failure_cause_id][error_id]:
                service = services_mek[index]
                patient = patients[service['patient_id']]
                act_book.write_cell(service['xml_id'], 'c')                           # Ид услуги в xml
                act_book.write_cell(patient['policy_series'].replace('\n', '') + ' ' +
                                    patient['policy_number']
                                    if patient['policy_series']
                                    else patient['policy_number'], 'c')               # Печать номера полиса

                act_book.write_cell(('%s %s %s' %
                                     (patient['last_name'] or '',
                                      patient['first_name'] or '',
                                      patient['middle_name'] or '')).upper(), 'c')    # Печать ФИО

                act_book.write_cell(date_correct(patient['birthdate']).
                                    strftime('%d.%m.%Y'), 'c')                        # Печать даты рождения

                act_book.write_cell(service['anamnesis_number'], 'c')                 # Номер карты

                act_book.write_cell(date_correct(service['end_date']).
                                    strftime('%d.%m.%Y'), 'c')                        # Дата окончания услуги

                act_book.write_cell(service['quantity'], 'c')                         # Количество дней

                act_book.write_cell(service['uet'], 'c')                              # Количество УЕТ

                act_book.write_cell(service['code'], 'c')                             # Код услуги

                act_book.write_cell(service['basic_disease'], 'c')                    # Код основного диагноза

                act_book.write_cell(service['name'], 'c')                             # Название услуги)

                act_book.write_cell(
                    str(service['profile'] or ''
                        if service['term'] in [1, 2]                                  #Профиль или код спец.
                        else service['worker_speciality'] or ''), 'c')

                act_book.write_cell(service['event_id'], 'c')                         # Ид случая

                act_book.write_cell(service['xml_id'], 'c')                           # Ид услуги в xml

                act_book.write_cell(patient['xml_id'], 'c')                           # Ид патиента в xml

                act_book.write_cell(service['tariff'], 'c')                           # Основной тариф

                act_book.write_cell(service['calculated_payment'], 'c')               # Рассчётная сумма

                act_book.write_cell(u'Подуш.'
                                    if is_capitation
                                    else service['provided_tariff'], 'r')             # Снятая сумма
                # Рассчёт итоговой суммы по ошибке
                total_sum_error['sum_day'] += service['quantity']
                total_sum_error['sum_uet'] += service['uet']
                total_sum_error['sum_tariff'] += service['tariff']
                total_sum_error['sum_calculated_payment'] += service['calculated_payment']
                total_sum_error['sum_discontinued_payment'] += 0 \
                    if is_capitation else service['provided_tariff']
            # Рассчёт итоговой суммы по всем ошибкам в MO
            total_sum = calculate_total_sum(total_sum, total_sum_error)

            # Печать итоговой суммы по ошибке
            print_total_sum_error(act_book, u'Итого по ошибке', total_sum_error)

    # Печать итоговой суммы по всем ошибкам
    print_total_sum_error(act_book, u'Итого по всем ошибкам', total_sum)

    act_book.hide_column('M:O')
    act_book.set_style({'bold': True})
    act_book.write_cell(' ', 'r')

    # Печать места для подписей
    signature_dict = [
        {'title': u'Исполнитель',
         'column': 0,
         'name': u'()',
         'row_space': 2,
         'newline': False},
        {'title': u'Исполнитель',
         'column': 0,
         'name': u'()',
         'row_space': 1,
         'newline': False},
        {'title': u'Руководитель страховой медицинской организации',
         'column': 6,
         'name': u'(Е.Л.Дьячкова)',
         'row_space': 1,
         'newline': True}
    ]
    for signature in signature_dict:
        act_book.set_style()
        act_book.write_cell(signature['title'], 'c', signature['column'])
        act_book.write_cell('', 'c')
        act_book.write_cell('', 'c')
        if signature['newline']:
            act_book.row_inc()
            act_book.row_inc()
            act_book.write_cell('', 'c')
            act_book.write_cell('', 'c')
            act_book.write_cell('', 'c')
        act_book.set_style({'bottom': 1})
        act_book.write_cell('', 'c', 1)
        act_book.set_style()
        act_book.write_cell(u'подпись', 'c')
        act_book.write_cell(signature['name'], 'r', 1)
        for index in xrange(signature['row_space']):
            act_book.row_inc()

    act_book.write_cell(u'М. П.', 'r')
    act_book.write_cell('', 'r')
    act_book.write_cell(u'Должность, подпись руководителя медицинской организации, '
                        u'ознакомившегося с Актом', 'r', 8)
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'r', 5)
    act_book.set_style()
    act_book.write_cell(u'Дата'+'_'*30, size=8)

