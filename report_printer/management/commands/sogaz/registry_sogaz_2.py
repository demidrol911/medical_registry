#! -*- coding: utf-8 -*-
from report_printer.const import MONTH_NAME
from tfoms import func
from tfoms.models import Sanction
from django.db.models import Q
from func_sogaz import (
    calculated_money, get_services, calculated_services,

    SANCTION_CRITERIA,
    ACCEPTED_CRITERIA,
    CAPITATION_CRITERIA
)


def get_sanctions_error(services):
    services_pk = services.filter(SANCTION_CRITERIA).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(service__in=services_pk).order_by('-service__pk', '-error__weight')
    sanctions_data = dict()
    sanctions_error = []
    for sanction in sanctions:
        if sanction.service.pk not in sanctions_data:
            sanctions_data[sanction.service.pk] = sanction.error_id
            if sanction.error_id not in sanctions_error:
                sanctions_error.append(sanction.error_id)
    return sanctions_error


### Проверяет наличие указанных ошибок в реестре
def has_error(services, error_list, handbooks):
    sanction_error = get_sanctions_error(services)
    for error in sanction_error:
        if handbooks['errors'][error]['code'].upper() in error_list:
            return True
    return False


def print_registry_sogaz_3(act_book, mo):
    handbooks = {
        'errors': func.ERRORS,
        'failure_cause': func.FAILURE_CAUSES
    }
    mo_name = func.get_mo_info(mo)['name']

    services = get_services(func.YEAR, func.PERIOD, mo)

    # Количество поданных услуг
    count_invoiced = calculated_services(
        services,
        condition=ACCEPTED_CRITERIA & ~((Q(code__group=19) & Q(code__subgroup__isnull=True))
           | (Q(code__group=7) & Q(code__subgroup=5)))
    ) + calculated_services(
        services,
        condition=SANCTION_CRITERIA
    )

    # Cумма поданная к оплате (расчётная)
    sum_invoiced = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment',
        is_calculate_capitation=True
    ) + calculated_money(
        services,
        condition=SANCTION_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )

    has_su = has_error(services, ['SU'], handbooks)
    has_nl = has_error(services, ['NL', 'TP', 'L1', 'L2'], handbooks)

    # Количество услуг снятых с оплаты
    count_sanction = calculated_services(
        services,
        condition=SANCTION_CRITERIA
    )

    # Сумма снятая с оплаты
    sum_sanction = calculated_money(
        services,
        condition=SANCTION_CRITERIA & CAPITATION_CRITERIA,
        field='provided_tariff'
    )
    sum_sanction_total = sum_sanction
    sum_sanction_other_mo = 0
    sum_sanction_repeat_mek = 0

    # Сумма принятая к оплате
    sum_accepted = calculated_money(
        services,
        condition=ACCEPTED_CRITERIA & CAPITATION_CRITERIA,
        field='accepted_payment',
        is_calculate_capitation=True
    )
    act_book.set_sheet(8)
    act_book.set_style()
    act_book.set_style({'align': 'center'})
    act_book.write_cella(3, 2, u'за %s %s г.' % (MONTH_NAME[func.PERIOD], func.YEAR))
    act_book.write_cella(5, 0, mo_name)
    act_book.set_style({})
    act_book.write_cella(5, 5, mo)
    act_book.write_cella(10, 5, count_invoiced)
    act_book.write_cella(11, 5, sum_invoiced)
    if not has_su:
        act_book.write_cella(14, 0, u'Тарифы, указанные в реестре оказанной '
                                    u'медицинской помощи, соответствуют '
                                    u'утвержденным тарифам,')
    if not has_nl:
        act_book.write_cella(15, 0, u'Виды и профили оказанной '
                                    u'медицинской помощи соответствуют '
                                    u'лицензии медицинского учреждения')
    act_book.write_cella(19, 5, count_sanction)
    act_book.write_cella(20, 5, sum_sanction)
    act_book.write_cella(24, 2, sum_sanction_total)
    act_book.write_cella(26, 2, sum_sanction_other_mo)
    act_book.write_cella(29, 2, sum_sanction_repeat_mek)
    act_book.write_cella(31, 5, sum_accepted)


