#! -*- coding: utf-8 -*-

from django.db.models import Q
from tfoms import func
from func_sogaz import (
    calculated_money, calculated_capitation,
    get_services, calculated_services,
    get_service_pa,

    ACCEPTED_CRITERIA, SANCTION_CRITERIA,
    CAPITATION_CRITERIA,
    HOSPITAL_CRITERIA,
    DAY_HOSPITAL_CRITERIA,
    POLICLINIC_CRITERIA,
    AMBULANCE_CRITERIA
)
from tfoms.models import Sanction


### Предъявленные реестры счетов
def calculated_sum_invoiced(services):
    sum_dict = dict()

    # Сумма предъявленная по основному тарифу
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=Q(),
        field='tariff'
    )
    sum_dict['sum_tariff_other_mo'] = 0

    # Сумма предъявленная рассчётная
    sum_dict['sum_tariff_mo'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment',
        is_calculate_capitation=True
    ) + calculated_money(
        services,
        condition=SANCTION_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )

    sum_dict['sum_tariff_all'] = sum_dict['sum_tariff_mo']

    # Предъявленные реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_services(
        services,
        condition=HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=HOSPITAL_CRITERIA,
        field='tariff'
    )

    # Предъяыленные реестры счетов за дневной стационар
    sum_dict['count_day_hosp'] = calculated_services(
        services,
        condition=DAY_HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=DAY_HOSPITAL_CRITERIA,
        field='tariff'
    )

    # Предъявленные реестры счетов за поликлинику
    sum_dict['count_policlinic'] = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & POLICLINIC_CRITERIA & ~((Q(code__group=19) & Q(code__subgroup__isnull=True))
           | (Q(code__group=7) & Q(code__subgroup=5)))
    ) + calculated_services(
        services,
        condition=SANCTION_CRITERIA & POLICLINIC_CRITERIA
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=POLICLINIC_CRITERIA,
        field='tariff'
    )

    # Предъявленные реестры счетов по скорой помощи
    sum_dict['count_ambulance'] = calculated_services(
        services,
        condition=AMBULANCE_CRITERIA
    )
    sum_dict['sum_tariff_ambulance'] = calculated_money(
        services,
        condition=AMBULANCE_CRITERIA,
        field='tariff'
    )
    return sum_dict


### Принятые реестры счетов
def calculated_sum_accepted(services):
    sum_dict = dict()

    # Сумма принятая к оплате (без подушевого)
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment'
    )

    # Подушевое по поликлинике
    sum_dict['sum_policlinic_tariff_capitation'] = calculated_capitation(services, 3)

    # Подушевое по скорой
    sum_dict['sum_ambulance_tariff_capitation'] = calculated_capitation(services, 4)

    sum_dict['sum_tariff_other_mo'] = 0

    # Сумма принятая к оплате (с подушевым)
    sum_dict['sum_tariff_mo'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment',
        is_calculate_capitation=True
    )

    # Количество принятых услуг (в акте)
    sum_dict['count_all'] = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & ~(
            (Q(code__group=19) & Q(code__subgroup__isnull=True))
            | (Q(code__group=7) & Q(code__subgroup=5))
        )
    )
    sum_dict['sum_tariff_all'] = sum_dict['sum_tariff_mo']

    # Принятые реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & HOSPITAL_CRITERIA,
        field='accepted_payment'
    )

    # Принятые реестры отчётов за дневной стационар
    sum_dict['count_day_hosp'] = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & DAY_HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & DAY_HOSPITAL_CRITERIA,
        field='accepted_payment'
    )

    # Принятые реестры отчётов за поликлинику
    sum_dict['count_policlinic'] = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & POLICLINIC_CRITERIA & ~((Q(code__group=19) & Q(code__subgroup__isnull=True))
           | (Q(code__group=7) & Q(code__subgroup=5)))
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & POLICLINIC_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment'
    ) + calculated_capitation(services, 3)

    return sum_dict


 ### Не принятые к оплате
def calculated_sum_sanction(services):
    sum_dict = dict()
    pa_list = get_service_pa(services)
    PA_CRITERIA = Q(pk__in=pa_list)

    # Непринятые к оплате (без подушевого)
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=SANCTION_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_services(
        services,
        condition=SANCTION_CRITERIA & ~PA_CRITERIA & HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=SANCTION_CRITERIA & ~PA_CRITERIA & HOSPITAL_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые реестры за дневной стационар
    sum_dict['count_day_hosp'] = calculated_services(
        services,
        condition=SANCTION_CRITERIA & ~PA_CRITERIA & DAY_HOSPITAL_CRITERIA
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=SANCTION_CRITERIA & ~PA_CRITERIA & DAY_HOSPITAL_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые реестры за поликлинику
    sum_dict['count_policlinic'] = calculated_services(
        services,
        condition=SANCTION_CRITERIA & POLICLINIC_CRITERIA
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=SANCTION_CRITERIA & POLICLINIC_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые услуги сверх объема
    sum_dict['sum_tariff_pa'] = calculated_money(
        services,
        condition=PA_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за стационар
    sum_dict['sum_tariff_hosp_pa'] = calculated_money(
        services,
        condition=PA_CRITERIA & HOSPITAL_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за дневной стационар
    sum_dict['sum_tariff_day_hosp_pa'] = calculated_money(
        services,
        condition=PA_CRITERIA & DAY_HOSPITAL_CRITERIA,
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за поликлинику
    sum_dict['sum_tariff_policlinic_pa'] = calculated_money(
        services,
        condition=PA_CRITERIA & POLICLINIC_CRITERIA,
        field='provided_tariff'
    )

    # Не подлежит оплате
    sum_dict['count_all'] = calculated_services(
        services,
        condition=SANCTION_CRITERIA
    )
    sum_dict['sum_tariff_all'] = calculated_money(
        services,
        condition=SANCTION_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )

    return sum_dict


### Услуги снятые с оплаты
def get_sanction_info(services, condition):
    services_data = services.filter(condition).values(
        'pk',
        'event__pk',
        'organization__old_code',
        'event__record__id',
        'event__record__register__period',
        'event__record__patient__insurance_policy_number',
        'event__record__patient__insurance_policy_series',
        'provided_tariff',
        'event__term__id_pk',
        'division__code',
        'profile__code'
    ).order_by('event__record__id')
    services_pk = services.filter(SANCTION_CRITERIA & condition).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(service__in=services_pk).order_by('-service__pk', '-error__weight')
    sanctions_data = dict()
    for sanction in sanctions:
        if sanction.service.pk not in sanctions_data:
            sanctions_data[sanction.service.pk] = sanction.error_id

    sum_tariff = calculated_money(
        services,
        condition=Q(payment_type=3) & condition & CAPITATION_CRITERIA,
        field='provided_tariff'
    )
    count = calculated_services(
        services,
        condition=Q(payment_type=3) & condition,
    )
    return {
        'services': services_data,
        'sanctions': sanctions_data,
        'sum_tariff': sum_tariff,
        'count': count
    }


### Распечатка услуг снятых с оплаты
def print_sanction(act_book, data, capitation_events, title, handbooks):
    act_book.set_style()
    act_book.write_cell('', 'r')
    if title:
        act_book.write_cell(title, 'c', 4)
        act_book.write_cell(data['sum_tariff'], 'c')
        act_book.write_cell(u'руб.', 'c')
        act_book.write_cell(data['count'], 'c')
        act_book.write_cell(u'счетов', 'r')
    act_book.set_style({
        'border': 1, 'font_size': 9,
        'text_wrap': True,
        'valign': 'vcenter',
        'align': 'center'
    })
    act_book.set_row_height(60)
    act_book.write_cell(u'Код структурного подразделения', 'c')
    act_book.write_cell(u'Код отделения или профиля коек', 'c')
    act_book.write_cell(u'№ индивидуального счета', 'c')
    act_book.write_cell(u'Период (месяц)', 'c')
    act_book.write_cell(u'№ документа ОМС', 'c')
    act_book.write_cell(u'Код дефекта/нарушения', 'c')
    act_book.write_cell(u'Код ошибки', 'c')
    act_book.write_cell(u'Сумма, подлежащая отказу в оплате', 'c')
    act_book.write_cell(u'Код финансовых санкций', 'c')
    act_book.write_cell(u'Сумма финансовых санкций', 'c')
    act_book.write_cell(u'Примечание', 'r')
    act_book.write_cell(u'1', 'c')
    act_book.write_cell(u'2', 'c')
    act_book.write_cell(u'3', 'c')
    act_book.write_cell(u'4', 'c')
    act_book.write_cell(u'5', 'c')
    act_book.write_cell(u'6', 'c')
    act_book.write_cell(u'7', 'c')
    act_book.write_cell(u'8', 'c')
    act_book.write_cell(u'9', 'c')
    act_book.write_cell(u'10', 'c')
    act_book.write_cell(u'11', 'r')
    services_data = data['services']
    sanctions_data = data['sanctions']
    act_book.set_style({'border': 1})
    for service in services_data:
        error_id = sanctions_data.get(service['pk'], 0)
        if error_id:
            act_book.write_cell(service['organization__old_code'], 'c')
            act_book.write_cell(str(service['profile__code'] or '' if service['event__term__id_pk'] in [1, 2]
                                    else service['division__code'] or ''), 'c')
            act_book.write_cell(service['event__record__id'], 'c')
            act_book.write_cell(service['event__record__register__period'], 'c')
            act_book.write_cell(service['event__record__patient__insurance_policy_series'].replace('\n', '') + ' ' +
                                service['event__record__patient__insurance_policy_number']
                                if service['event__record__patient__insurance_policy_series']
                                else service['event__record__patient__insurance_policy_number'], 'c')
            act_book.write_cell(handbooks['failure_cause'][handbooks['errors'][error_id]['failure_cause']]['number'], 'c')
            act_book.write_cell(handbooks['errors'][error_id]['code'], 'c')
            act_book.write_cell(u'Подуш.' if service['event__pk'] in capitation_events or service['event__term__id_pk'] == 4
                                else service['provided_tariff'], 'c')
            act_book.write_cell(1, 'c')
            act_book.write_cell('', 'c')
            act_book.write_cell('', 'r')


def print_registry_sogaz_1(act_book, mo):
    handbooks = {
        'errors': func.ERRORS,
        'failure_cause': func.FAILURE_CAUSES
    }

    mo_name = func.get_mo_info(mo)['name']
    services = get_services(func.YEAR, func.PERIOD, mo)
    pa_list = get_service_pa(services)
    PA_CRITERIA = Q(pk__in=pa_list)
    invoiced = calculated_sum_invoiced(services)
    accepted = calculated_sum_accepted(services)
    sanction = calculated_sum_sanction(services)
    hospital_sanction_info = get_sanction_info(
        services,
        condition=HOSPITAL_CRITERIA & ~PA_CRITERIA
    )
    day_hospital_sanction_info = get_sanction_info(
        services,
        condition=DAY_HOSPITAL_CRITERIA & ~PA_CRITERIA
    )
    policlinic_sanction_info = get_sanction_info(
        services,
        condition=POLICLINIC_CRITERIA & ~PA_CRITERIA
    )
    ambulance_sanction_info = get_sanction_info(
        services,
        condition=AMBULANCE_CRITERIA & ~PA_CRITERIA
    )

    pa_sanction_info = get_sanction_info(
        services,
        condition=PA_CRITERIA
    )

    capitation_events = func.get_capitation_events(mo_code=mo)

    act_book.set_sheet(7)
    act_book.set_style()
    act_book.write_cella(9, 0, mo_name)
    act_book.write_cella(10, 1, mo)
    # Представлены реестры счетов (все поданные)
    act_book.write_cella(12, 2, invoiced['sum_tariff'])             # всего подано по тарифу
    act_book.write_cella(13, 4, invoiced['sum_tariff_other_mo'])    # заказано в другой мо
    act_book.write_cella(14, 4, invoiced['sum_tariff_mo'])          # заявлено к оплате
    act_book.write_cella(15, 4, invoiced['sum_tariff_all'])         # всего представлено на сумму
    act_book.write_cella(18, 1, invoiced['count_hosp'])             # всего подано по стационару
    act_book.write_cella(19, 1, invoiced['sum_tariff_hosp'])
    act_book.write_cella(21, 1, invoiced['count_day_hosp'])         # всего подано по дневному стационару
    act_book.write_cella(22, 1, invoiced['sum_tariff_day_hosp'])
    act_book.write_cella(24, 1, invoiced['count_policlinic'])       # всего подано по поликлинике
    act_book.write_cella(24, 6, invoiced['sum_tariff_policlinic'])
    act_book.write_cella(26, 1, invoiced['count_ambulance'])        # всего по скорой помощи
    act_book.write_cella(27, 1, invoiced['sum_tariff_ambulance'])

    # Принятые к оплате реестры счетов
    act_book.write_cella(29, 2, accepted['sum_tariff'])             # принято по тарифу
    # Подушевое
    act_book.write_cella(30, 2, accepted['sum_policlinic_tariff_capitation'])
    act_book.write_cella(31, 2, accepted['sum_ambulance_tariff_capitation'])

    act_book.write_cella(32, 3, accepted['sum_tariff_other_mo'])    # заказано в другой мо
    act_book.write_cella(33, 2, accepted['sum_tariff_mo'])          # принято к оплате
    act_book.write_cella(34, 1, accepted['count_all'])              # всего принято к оплате
    act_book.write_cella(34, 4, accepted['sum_tariff_all'])
    act_book.write_cella(36, 5, accepted['sum_tariff_hosp'])        # принято по стационару
    act_book.write_cella(36, 7, accepted['count_hosp'])
    act_book.write_cella(37, 5, accepted['sum_tariff_day_hosp'])    # принято по дневному стационару
    act_book.write_cella(37, 7, accepted['count_day_hosp'])
    act_book.write_cella(38, 5, accepted['sum_tariff_policlinic'])  # принято по поликлинике
    act_book.write_cella(38, 7, accepted['count_policlinic'])

    # Не принятые к оплате реестры счетов
    act_book.write_cella(39, 5, sanction['sum_tariff'])             # не принято к оплате
    act_book.write_cella(40, 5, sanction['sum_tariff_hosp'])        # не принято по стационару
    act_book.write_cella(40, 7, sanction['count_hosp'])
    act_book.write_cella(41, 5, sanction['sum_tariff_day_hosp'])    # не принято по дневному стационару
    act_book.write_cella(41, 7, sanction['count_day_hosp'])
    act_book.write_cella(42, 5, sanction['sum_tariff_policlinic'])  # не принято по поликлинике
    act_book.write_cella(42, 7, sanction['count_policlinic'])
    act_book.write_cella(43, 5, sanction['sum_tariff_pa'])          # не принято сверх объема
    act_book.write_cella(44, 3, sanction['count_all'])              # не подлежит оплате
    act_book.write_cella(44, 5, sanction['sum_tariff_all'])

    # Снятая с оплаты в стационаре
    act_book.set_cursor(45, 0)
    print_sanction(
        act_book,
        data=hospital_sanction_info,
        capitation_events=capitation_events,
        title=u'2.1.1. за стационарную медицинскую помощь на сумму:',
        handbooks=handbooks
    )
    print_sanction(
        act_book,
        data=day_hospital_sanction_info,
        capitation_events=capitation_events,
        title=u'2.1.2. за мед. помощь в дневном стационаре  на сумму:',
        handbooks=handbooks
    )
    print_sanction(
        act_book,
        data=policlinic_sanction_info,
        capitation_events=capitation_events,
        title=u'2.1.3. за амбулаторно-поликлиническую помощь  на сумму:',
        handbooks=handbooks
    )
    print_sanction(
        act_book,
        data=ambulance_sanction_info,
        capitation_events=capitation_events,
        title=u'2.1.4. за скорую медицинскую помощь  на сумму:',
        handbooks=handbooks
    )
    act_book.set_style()
    act_book.write_cell(u'2.3. Не принято к оплате в связи с превышением '
                        u'согласованных объемов медицинских услуг на сумму:', 'c', 8)
    act_book.write_cell(sanction['sum_tariff_pa'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'В т.ч.:  за стационарную медицинскую помощь на сумму:', 'c', 4)
    act_book.write_cell(sanction['sum_tariff_hosp_pa'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'за медицинскую помощь в дневном стационаре на сумму:', 'c', 4)
    act_book.write_cell(sanction['sum_tariff_day_hosp_pa'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'за амбулаторно-поликлиническую мед.помощь на сумму :', 'c', 4)
    act_book.write_cell(sanction['sum_tariff_policlinic_pa'], 'c')
    act_book.write_cell(u'руб.', 'r')
    print_sanction(
        act_book,
        data=pa_sanction_info,
        capitation_events=capitation_events,
        title='',
        handbooks=handbooks
    )
    act_book.set_style()
    act_book.write_cell('', 'r')
    act_book.write_cell(u'Дата предоставления счетов СМО (ТФ) медицинской организацией', 'r', 5)
    act_book.write_cell(u'Дата проверки счетов (реестров)', 'r', 3)
    act_book.write_cell(u'Специалист (Ф.И.О и подпись)', 'c', 3)
    act_book.set_style({'bottom': 1})
    act_book.write_cell('', 'r')









