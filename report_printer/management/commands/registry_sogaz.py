#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Sum, Count, Q
from medical_service_register.path import REESTR_DIR, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from tfoms.func import get_mo_info, get_mo_register, get_errors, get_failure_causes
from tfoms.models import ProvidedService, Sanction


def get_services(year, period, mo_code):
    return ProvidedService.objects.filter(
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code
    )


def calculated_money(services, condition, field):
    return services.filter(condition).aggregate(sum_value=Sum(field))['sum_value']


def calculated_invoice(services, condition):
    return services.filter(condition).aggregate(
        count_value=Count('event__record__pk')
    )['count_value']


def calculated_sum_invoiced(services):
    ### Предъявленные реестры счетов
    sum_dict = dict()
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=Q(),
        field='tariff'
    )
    sum_dict['sum_tariff_other_mo'] = 0
    sum_dict['sum_tariff_mo'] = calculated_money(
        services,
        condition=Q(),
        field='tariff'
    )
    sum_dict['sum_tariff_all'] = calculated_money(
        services,
        condition=Q(),
        field='tariff'
    )

    # Предъявленные реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_invoice(
        services,
        condition=Q(event__term=1)
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=Q(event__term=1),
        field='tariff'
    )

    # Предъяыленные реестры счетов за дневной стационар
    sum_dict['count_day_hosp'] = calculated_invoice(
        services,
        condition=Q(event__term=2)
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=Q(event__term=2),
        field='tariff'
    )

    # Предъявленные реестры счетов за поликлинику
    sum_dict['count_policlinic'] = calculated_invoice(
        services,
        condition=Q(event__term=3) | Q(event__term__isnull=True)
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=Q(event__term=3) | Q(event__term__isnull=True),
        field='tariff'
    )

    # Предъявленные реестры счетов по скорой помощи
    sum_dict['count_ambulance'] = calculated_invoice(
        services,
        condition=Q(event__term=4)
    )
    sum_dict['sum_tariff_ambulance'] = calculated_money(
        services,
        condition=Q(event__term=4),
        field='tariff'
    )
    return sum_dict


def calculated_sum_accepted(services):
    sum_dict = dict()
    ### Принятые реестры счетов
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]),
        field='tariff'
    )
    sum_dict['sum_tariff_other_mo'] = 0
    sum_dict['sum_tariff_mo'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]),
        field='accepted_payment'
    )
    sum_dict['count_all'] = calculated_invoice(
        services,
        condition=Q(payment_type__in=[2, 4])
    )
    sum_dict['sum_tariff_all'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]),
        field='accepted_payment'
    )

    # Принятые реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_invoice(
        services,
        condition=Q(payment_type__in=[2, 4]) & Q(event__term=1)
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]) & Q(event__term=1),
        field='accepted_payment'
    )

    # Принятые реестры отчётов за дневной стационар
    sum_dict['count_day_hosp'] = calculated_invoice(
        services,
        condition=Q(payment_type__in=[2, 4]) & Q(event__term=2)
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]) & Q(event__term=2),
        field='accepted_payment'
    )

    # Принятые реестры отчётов за поликлинику
    sum_dict['count_policlinic'] = calculated_invoice(
        services,
        condition=Q(payment_type__in=[2, 4]) & (Q(event__term=3) | Q(event__term__isnull=True))
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=Q(payment_type__in=[2, 4]) & (Q(event__term=3) | Q(event__term__isnull=True)),
        field='accepted_payment'
    )

    return sum_dict


def calculated_sum_sanction(services):
    ### Не принятые к оплате
    sum_dict = dict()
    sum_dict['sum_tariff'] = calculated_money(
        services,
        condition=Q(payment_type__in=[3, 4]),
        field='provided_tariff'
    )

    # Не принятые реестры счетов за стационар
    sum_dict['count_hosp'] = calculated_invoice(
        services,
        condition=Q(payment_type=3) & Q(event__term=1)
    )
    sum_dict['sum_tariff_hosp'] = calculated_money(
        services,
        condition=Q(payment_type=3) & Q(event__term=1),
        field='provided_tariff'
    )

    # Не принятые реестры за дневной стационар
    sum_dict['count_day_hosp'] = calculated_invoice(
        services,
        condition=Q(payment_type=3) & Q(event__term=2)
    )
    sum_dict['sum_tariff_day_hosp'] = calculated_money(
        services,
        condition=Q(payment_type=3) & Q(event__term=2),
        field='provided_tariff'
    )

    # Не принятые реестры за поликлинику
    sum_dict['count_policlinic'] = calculated_invoice(
        services,
        condition=Q(payment_type=3) & (Q(event__term=3) | Q(event__term__isnull=True))
    )
    sum_dict['sum_tariff_policlinic'] = calculated_money(
        services,
        condition=Q(payment_type=3) & (Q(event__term=3) | Q(event__term__isnull=True)),
        field='provided_tariff'
    )

    # Не принятые услуги сверх объема
    sum_dict['sum_tariff_pa'] = calculated_money(
        services,
        condition=Q(payment_type=4),
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за стационар
    sum_dict['sum_tariff_hosp_pa'] = calculated_money(
        services,
        condition=Q(payment_type=4) & Q(event__term=1),
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за дневной стационар
    sum_dict['sum_tariff_day_hosp_pa'] = calculated_money(
        services,
        condition=Q(payment_type=4) & Q(event__term=2),
        field='provided_tariff'
    )

    # Не принятые услуги сверх объёма за поликлинику
    sum_dict['sum_tariff_policlinic_pa'] = calculated_money(
        services,
        condition=Q(payment_type=4) & (Q(event__term=3) | Q(event__term__isnull=True)),
        field='provided_tariff'
    )

    # Не подлежит оплате
    sum_dict['count_all'] = calculated_invoice(
        services,
        condition=Q(payment_type=3)
    )
    sum_dict['sum_tariff_all'] = calculated_money(
        services,
        condition=Q(payment_type=3),
        field='provided_tariff'
    )

    return sum_dict


def get_sanction_info(services, condition):
    services_data = services.filter(condition).values(
        'pk',
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
    services_pk = services.filter(condition).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(service__in=services_pk).order_by('-service__pk', '-error__weight')
    sanctions_data = dict()
    for sanction in sanctions:
        if sanction.service.pk not in sanctions_data:
            sanctions_data[sanction.service.pk] = sanction.error_id

    sum_tariff = calculated_money(
        services,
        condition=condition,
        field='provided_tariff'
    )
    count = calculated_invoice(
        services,
        condition=condition,
    )
    return {
        'services': services_data,
        'sanctions': sanctions_data,
        'sum_tariff': sum_tariff,
        'count': count
    }


def print_sanction(act_book, data, title, handbooks):
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
        error_id = sanctions_data[service['pk']]
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
        act_book.write_cell(service['provided_tariff'], 'c')
        act_book.write_cell(1, 'c')
        act_book.write_cell('', 'c')
        act_book.write_cell('', 'r')


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        status = args[2]
        handbooks = {
            'errors': get_errors(),
            'failure_cause': get_failure_causes()
        }
        organizations = get_mo_register(year, period, status=status)
        for mo in organizations:
            mo_name = get_mo_info(mo)['name']
            template = BASE_DIR + r'\templates\excel_pattern\registry_sogaz.xls'
            target = REESTR_DIR % (year, period) + r'\%s' % \
                mo_name.replace('"', '').strip()
            services = get_services(year, period, mo)
            invoiced = calculated_sum_invoiced(services)
            accepted = calculated_sum_accepted(services)
            sanction = calculated_sum_sanction(services)
            hospital_sanction_info = get_sanction_info(
                services,
                condition=Q(payment_type=3) & Q(event__term=1)
            )
            day_hospital_sanction_info = get_sanction_info(
                services,
                condition=Q(payment_type=3) & Q(event__term=2)
            )
            policlinic_sanction_info = get_sanction_info(
                services,
                condition=Q(payment_type=3) & (Q(event__term=3) | Q(event__term__isnull=True))
            )
            ambulance_sanction_info = get_sanction_info(
                services,
                condition=Q(payment_type=3) & Q(event__term=4)
            )
            pa_sanction_info = get_sanction_info(
                services,
                condition=Q(payment_type=4)
            )

            with ExcelWriter(template=template, target=target) as act_book:
                act_book.write_cella(9, 0, mo_name)
                act_book.write_cella(10, 1, mo)
                # Представлены реестры счетов (все поданные)
                act_book.write_cella(12, 2, invoiced['sum_tariff'])             # всего подано по тарифу
                act_book.write_cella(13, 4, invoiced['sum_tariff_other_mo'])    # заказано в другой мо
                act_book.write_cella(14, 4, invoiced['sum_tariff_mo'])          # заявлено к оплате
                act_book.write_cella(15, 4, invoiced['sum_tariff_all'])         # всего представлено на сумму
                act_book.write_cella(18, 4, invoiced['count_hosp'])             # всего подано по стационару
                act_book.write_cella(19, 1, invoiced['sum_tariff_hosp'])
                act_book.write_cella(21, 0, invoiced['count_day_hosp'])         # всего подано по дневному стационару
                act_book.write_cella(22, 4, invoiced['sum_tariff_day_hosp'])
                act_book.write_cella(24, 4, invoiced['count_policlinic'])       # всего подано по поликлинике
                act_book.write_cella(24, 6, invoiced['sum_tariff_policlinic'])
                act_book.write_cella(26, 4, invoiced['count_ambulance'])        # всего по скорой помощи
                act_book.write_cella(27, 1, invoiced['sum_tariff_ambulance'])

                # Принятые к оплате реестры счетов
                act_book.write_cella(29, 2, accepted['sum_tariff'])             # принято по тарифу
                act_book.write_cella(30, 3, accepted['sum_tariff_other_mo'])    # заказано в другой мо
                act_book.write_cella(31, 2, accepted['sum_tariff_mo'])          # принято к оплате
                act_book.write_cella(32, 1, accepted['count_all'])              # всего принято к оплате
                act_book.write_cella(32, 4, accepted['sum_tariff_all'])
                act_book.write_cella(34, 5, accepted['sum_tariff_hosp'])        # принято по стационару
                act_book.write_cella(34, 7, accepted['count_hosp'])
                act_book.write_cella(35, 5, accepted['sum_tariff_day_hosp'])    # принято по дневному стационару
                act_book.write_cella(35, 7, accepted['count_day_hosp'])
                act_book.write_cella(36, 5, accepted['sum_tariff_policlinic'])  # принято по поликлинике
                act_book.write_cella(36, 7, accepted['count_policlinic'])

                # Не принятые к оплате реестры счетов
                act_book.write_cella(37, 5, sanction['sum_tariff'])             # не принято к оплате
                act_book.write_cella(38, 5, sanction['sum_tariff_hosp'])        # не принято по стационару
                act_book.write_cella(38, 7, sanction['count_hosp'])
                act_book.write_cella(39, 5, sanction['sum_tariff_day_hosp'])    # не принято по дневному стационару
                act_book.write_cella(39, 7, sanction['count_day_hosp'])
                act_book.write_cella(40, 5, sanction['sum_tariff_policlinic'])  # не принято по поликлинике
                act_book.write_cella(40, 7, sanction['count_policlinic'])
                act_book.write_cella(41, 5, sanction['sum_tariff_pa'])          # не принято сверх объема
                act_book.write_cella(42, 3, sanction['count_all'])              # не подлежит оплате
                act_book.write_cella(42, 5, sanction['sum_tariff_all'])

                # Снятая с оплаты в стационаре
                act_book.set_cursor(43, 0)
                print_sanction(
                    act_book,
                    data=hospital_sanction_info,
                    title=u'2.1.1. за стационарную медицинскую помощь на сумму:',
                    handbooks=handbooks
                )
                print_sanction(
                    act_book,
                    data=day_hospital_sanction_info,
                    title=u'2.1.2. за мед. помощь в дневном стационаре  на сумму:',
                    handbooks=handbooks
                )
                print_sanction(
                    act_book,
                    data=policlinic_sanction_info,
                    title=u'2.1.3. за амбулаторно-поликлиническую помощь  на сумму:',
                    handbooks=handbooks
                )
                print_sanction(
                    act_book,
                    data=ambulance_sanction_info,
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









