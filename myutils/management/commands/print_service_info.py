#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from report_printer.excel_style import VALUE_STYLE
from tfoms.func import get_patients
from main.models import ProvidedService
from report_printer.excel_writer import ExcelWriter
from medical_service_register.path import REESTR_EXP
from helpers.correct import date_correct


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        mo_code = args[2]
        services_pk_list = [

        ]

        services = ProvidedService.objects.filter(
            pk__in=services_pk_list
        )

        services_values = services.values(
            'id_pk',                                            # Ид услуги
            'id',                                               # Ид из xml
            'event__anamnesis_number',                          # Амбулаторная карта
            'event__term__pk',                                  # Условие оказания МП
            'worker_code',                                      # Код мед. работника
            'quantity',                                         # Количество дней (услуг)
            'comment',                                          # Комментарий
            'code__pk',                                         # Ид кода услуги
            'code__code',                                       # Код услуги
            'code__name',                                       # Название услуги
            'start_date',                                       # Дата начала услуги
            'end_date',                                         # Дата конца услуги
            'basic_disease__idc_code',                          # Основной диагноз
            'event__concomitant_disease__idc_code',             # Сопутствующий диагноз
            'code__group__id_pk',                               # Группа
            'code__subgroup__id_pk',                            # Подгруппа услуги
            'code__reason__ID',                                 # Причина
            'division__code',                                   # Код отделения
            'division__term__pk',                               # Вид отделения
            'code__division__pk',                               # Ид отделения (для поликлиники)
            'code__tariff_profile__pk',                         # Тарифный профиль (для стационара и дн. стационара)
            'profile__pk',                                      # Профиль услуги
            'is_children_profile',                              # Возрастной профиль
            'worker_speciality__pk',                            # Специалист
            'payment_type__pk',                                 # Тип оплаты
            'payment_kind__pk',                                 # Вид оплаты
            'tariff',                                           # Основной тариф
            'invoiced_payment',                                 # Поданная сумма
            'accepted_payment',                                 # Принятая сумма
            'calculated_payment',                               # Рассчётная сумма
            'provided_tariff',                                  # Снятая сумма
            'code__uet',                                        # УЕТ
            'event__pk',                                        # Ид случая
            'department__old_code',                             # Код филиала
            'event__record__patient__pk'                        # Ид патиента
        ).order_by('event__record__patient__last_name',
                   'event__record__patient__first_name',
                   'event__pk', 'code__code')

        services_list = [
            {'id': service['id_pk'],
             'xml_id': service['id'],
             'anamnesis_number': service['event__anamnesis_number'],
             'term': service['event__term__pk'],
             'worker_code': service['worker_code'],
             'quantity': float(service['quantity'] or 1),
             'comment': service['comment'],
             'code_id': service['code__pk'],
             'code': service['code__code'],
             'name': service['code__name'],
             'start_date': service['start_date'],
             'end_date': service['end_date'],
             'basic_disease': service['basic_disease__idc_code'],
             'concomitant_disease': service['event__concomitant_disease__idc_code'],
             'group': service['code__group__id_pk'],
             'subgroup': service['code__subgroup__id_pk'],
             'reason': service['code__reason__ID'],
             'division_code': service['division__code'],
             'division_term': service['division__term__pk'],
             'division_id': service['code__division__pk'],
             'tariff_profile_id': service['code__tariff_profile__pk'],
             'profile': service['profile__pk'],
             'worker_speciality': service['worker_speciality__pk'],
             'payment_type': service['payment_type__pk'],
             'payment_kind': service['payment_kind__pk'],
             'tariff': service['tariff'],
             'invoiced_payment': service['invoiced_payment'],
             'accepted_payment': service['accepted_payment'],
             'calculated_payment': service['calculated_payment'] or 0,
             'provided_tariff': service['provided_tariff'] or service['tariff'],
             'uet': float(service['code__uet'] or 0) * float(service['quantity'] or 1),
             'event_id': service['event__pk'],
             'department': service['department__old_code'],
             'patient_id': service['event__record__patient__pk']}
            for service in services_values]

        patients = get_patients(mo_code)

        title_table = [
            u'Полис', u'ФИО', u'Дата рожд', u'Номер карты',
            u'Дата усл', u'Пос\госп', u'Кол дн', u'УЕТ', u'Код',
            u'Диагн', u'Отд.', u'ЛПУ', u'ID_SERV', u'ID_PAC',
            u'Предъявл', u'Расч.\Сумма', u'Снят.\Сумма'
        ]
        reestr_path = REESTR_EXP % (year, period)
        with ExcelWriter(u'%s/%s' % (reestr_path, mo_code)) as act_book:
            # Распечатка наименования ошибки
            act_book.set_style({'bold': True, 'border': 1, 'align': 'center', 'font_size': 11})
            # Распечатка загловков таблицы с информацией о снятых услугах
            for title in title_table:
                act_book.write_cell(title, 'c')
            act_book.row_inc()
            act_book.set_style(VALUE_STYLE)
            for service in services_list:
                patient = patients[service['patient_id']]

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

                act_book.write_cell(0 if service['group'] == 27 else 1, 'c')          # Посещения (госпитализация)

                act_book.write_cell(service['quantity'], 'c')                         # Количество дней

                act_book.write_cell(service['uet'], 'c')                              # Количество УЕТ

                act_book.write_cell(service['code'], 'c')                             # Код услуги

                act_book.write_cell(service['basic_disease'], 'c')                    # Код основного диагноза

                act_book.write_cell(service['name'], 'c')                             # Название услуги

                act_book.write_cell(service['department'], 'c')                         # Ид случая

                act_book.write_cell(service['xml_id'], 'c')                           # Ид услуги в xml

                act_book.write_cell(patient['xml_id'], 'c')                           # Ид патиента в xml

                act_book.write_cell(service['tariff'], 'c')                           # Основной тариф

                act_book.write_cell(service['calculated_payment'], 'c')               # Рассчётная сумма

                act_book.write_cell(service['provided_tariff'], 'r')             # Снятая сумма




