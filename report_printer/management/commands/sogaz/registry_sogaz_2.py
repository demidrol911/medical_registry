#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.const import MONTH_NAME
from tfoms import func
from medical_service_register.path import REESTR_DIR, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from tfoms.models import ProvidedService, Sanction
from django.db.models import Sum, Count, Q


def get_services(year, period, mo_code):
    return ProvidedService.objects.filter(
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code
    )


def calculated_money(services, condition, field, is_calculate_capitation=False):
    if is_calculate_capitation:
        mo_code = services[0].event.record.register.organization_code
        capitation_policlinic = func.calculate_capitation_tariff(3, mo_code=mo_code)
        capitation_ambulance = func.calculate_capitation_tariff(4, mo_code=mo_code)
        sum_capitation = 0
        for group in capitation_policlinic[1]:
            sum_capitation += group[27] + group[26]
        for group in capitation_ambulance[1]:
            sum_capitation += group[27] + group[26]
        print sum_capitation
        return services.filter(condition).aggregate(sum_value=Sum(field))['sum_value'] or 0 + sum_capitation
    else:
        return services.filter(condition).aggregate(sum_value=Sum(field))['sum_value'] or 0


def calculated_services(services, condition):
    return services.filter(condition).aggregate(
        count_value=Count('id_pk')
    )['count_value']


def get_sanctions_error(services):
    services_pk = services.filter(payment_type__in=[3, 4]).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(service__in=services_pk).order_by('-service__pk', '-error__weight')
    sanctions_data = dict()
    sanctions_error = []
    for sanction in sanctions:
        if sanction.service.pk not in sanctions_data:
            sanctions_data[sanction.service.pk] = sanction.error_id
            if sanction.error_id not in sanctions_error:
                sanctions_error.append(sanction.error_id)
    return sanctions_error


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
    count_invoiced = calculated_services(
        services,
        condition=Q()
    )
    sum_invoiced = calculated_money(
        services,
        condition=Q(payment_type=2) & Q(payment_kind=1) & ~Q(event__term=4),
        field='accepted_payment',
        is_calculate_capitation=True
    ) + calculated_money(
        services,
        condition=Q(payment_type__in=[3, 4]) & Q(payment_kind=1) & ~Q(event__term=4),
        field='provided_tariff'
    )

    has_su = has_error(services, ['SU'], handbooks)
    has_nl = has_error(services, ['NL', 'TP', 'L1', 'L2'], handbooks)

    count_sanction = calculated_services(
        services,
        condition=Q(payment_type__in=[3, 4])
    )
    sum_sanction = calculated_money(
        services,
        condition=Q(payment_type__in=[3, 4]) & Q(payment_kind=1) & ~Q(event__term__pk=4),
        field='provided_tariff'
    )
    sum_sanction_total = calculated_money(
        services,
        condition=Q(payment_type__in=[3, 4]) & Q(payment_kind=1) & ~Q(event__term__pk=4),
        field='provided_tariff'
    )
    sum_sanction_other_mo = 0
    sum_sanction_repeat_mek = 0
    sum_accepted = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]) & Q(payment_kind=1) & ~Q(event__term__pk=4),
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


