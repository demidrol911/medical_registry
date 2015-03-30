#! -*- coding: utf-8 -*-

from django.db.models import Q
from tfoms import func
from tfoms.models import (
    Sanction,
    MedicalOrganization,
    ProvidedService
)
from report_printer.const import MONTH_NAME


def get_services(year, period, mo_code):
    return ProvidedService.objects.filter(
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code
    ).exclude(code__group=27)


def calculated_capitation(mo, term):
    sum_capitation = 0
    if term == 3:
        capitation_policlinic = func.calculate_capitation_tariff(3, mo_code=mo)
        for group in capitation_policlinic[1]:
            sum_capitation += group[27] + group[26]
    if term == 4:
        capitation_ambulance = func.calculate_capitation_tariff(4, mo_code=mo)
        for group in capitation_ambulance[1]:
            sum_capitation += group[27] + group[26]
    return sum_capitation


def get_statistics(mo):
    query = """
            select
            mo.id_pk,
            -- Поданные услуги --
            count(distinct CASE WHEN T.is_paid THEn T.event_id END) as count_invoiced,

            sum(CASE WHEN T.is_paid and T.is_tariff THEn T.accepted_payment ELSE 0 END) +
            sum(CASE WHEN T.is_not_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as sum_invoiced, -- сумма предъявленная рассчётная

            count(distinct CASE WHEN T.is_not_paid THEn T.event_id END) as count_sanction,
            sum(CASE WHEN T.is_not_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as sum_sanction, -- сумма снятая рассчётная

            sum(CASE WHEN T.is_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as sum_accepted -- сумма принятая рассчётная

            from (
            select pe.id_pk as event_id,
                 mo.id_pk as organization,
                 ps.payment_type_fk = 3 as is_not_paid,
                 ps.payment_type_fk = 2 AS is_paid,
                 ps.tariff as tariff,
                 ps.accepted_payment as accepted_payment,
                 ps.provided_tariff as provided_tariff,
                 ps.payment_kind_fk = 1 and (pe.term_fk !=4 or pe.term_fk is NULL) as is_tariff,

                 pe.term_fk = 1 as is_hospital,
                 pe.term_fk = 2 as is_day_hospital,
                 pe.term_fk = 3 or pe.term_fk is null as is_policlinic,
                 pe.term_fk = 4 As is_ambulance,

                (select max(ms1.subgroup_fk)
                 from provided_service ps1
                 join medical_service ms1 on ps1.code_fk = ms1.id_pk
                 where ps1.event_fk = ps.event_fk and ms1.group_fk = 19) is NULL  and ms.group_fk = 19
                or (ms.group_fk=7 and ms.subgroup_fk=5) as is_not_count,
                pss.error_fk != 75 as is_not_pa,
                pss.error_fk = 75 as is_pa

            from medical_register mr JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                  ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                  ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                  ON mo.id_pk = ps.organization_fk
            JOIN medical_service ms
                  ON ms.id_pk = ps.code_fk
            left join provided_service_sanction pss
                  ON pss.service_fk = ps.id_pk and pss.error_fk = (
                        select pss1.error_fk
                        from provided_service_sanction pss1
                        JOIN medical_error me1 ON me1.id_pk = pss1.error_fk
                        where pss1.is_active
                              and pss1.service_fk = ps.id_pk
                        order by me1.weight desc LIMIT 1
                  )
            where mr.is_active and mr.year = %(year)s
                  and mr.period = %(period)s
                  and mr.organization_code = %(organization)s
                  and ((pss.id_pk is not null and pss.is_active) or pss.id_pk is null)
                  AND (ms.group_fk != 27 or ms.group_fk is NULL)
             ) as T
             join medical_organization mo
                 on T.organization = mo.id_pk
            group by mo.id_pk
            """

    stat_obj = MedicalOrganization.objects.raw(query, dict(year=func.YEAR, period=func.PERIOD, organization=mo))[0]
    capitation_policlinic = calculated_capitation(mo, 3)
    capitation_ambulance = calculated_capitation(mo, 4)

    stat_dict = dict()
    stat_dict['count_invoiced'] = stat_obj.count_invoiced
    stat_dict['sum_invoiced'] = stat_obj.sum_invoiced + capitation_policlinic + capitation_ambulance
    stat_dict['count_sanction'] = stat_obj.count_sanction
    stat_dict['sum_sanction'] = stat_obj.sum_sanction
    stat_dict['sum_sanction_total'] = stat_dict['sum_sanction']
    stat_dict['sum_sanction_other_mo'] = 0
    stat_dict['sum_sanction_repeat_mek'] = 0
    stat_dict['sum_accepted'] = stat_obj.sum_accepted + capitation_policlinic + capitation_ambulance
    return stat_dict


def get_sanctions_error(services):
    services_pk = services.filter(Q(payment_type=3)).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(
        service__in=services_pk,
        is_active=True
    ).order_by('-service__pk', '-error__weight')
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
    has_su = has_error(services, ['SU'], handbooks)
    has_nl = has_error(services, ['NL', 'TP', 'L1', 'L2'], handbooks)
    stat_dict = get_statistics(mo)

    act_book.set_sheet(8)
    act_book.set_style()
    act_book.set_style({'align': 'center'})
    act_book.write_cella(3, 2, u'за %s %s г.' % (MONTH_NAME[func.PERIOD], func.YEAR))
    act_book.write_cella(5, 0, mo_name)
    act_book.set_style({})
    act_book.write_cella(5, 5, mo)
    act_book.write_cella(10, 5, stat_dict['count_invoiced'])
    act_book.write_cella(11, 5, stat_dict['sum_invoiced'])
    if not has_su:
        act_book.write_cella(14, 0, u'Тарифы, указанные в реестре оказанной '
                                    u'медицинской помощи, соответствуют '
                                    u'утвержденным тарифам,')
    if not has_nl:
        act_book.write_cella(15, 0, u'Виды и профили оказанной '
                                    u'медицинской помощи соответствуют '
                                    u'лицензии медицинского учреждения')
    act_book.write_cella(19, 5, stat_dict['count_sanction'])
    act_book.write_cella(20, 5, stat_dict['sum_sanction'])
    act_book.write_cella(24, 2, stat_dict['sum_sanction_total'])
    act_book.write_cella(26, 2, stat_dict['sum_sanction_other_mo'])
    act_book.write_cella(29, 2, stat_dict['sum_sanction_repeat_mek'])
    act_book.write_cella(31, 5, stat_dict['sum_accepted'])


