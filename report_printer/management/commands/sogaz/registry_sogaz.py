#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from main.models import MedicalOrganization, ProvidedService
from tfoms import func


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
            sum(T.tariff) as inv_sum_tariff,     -- сумма предъявленная по основному тарифу

            sum(CASE WHEN T.is_paid and T.is_tariff THEn T.accepted_payment ELSE 0 END) +
            sum(CASE WHEN T.is_not_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as inv_sum_tariff_mo, -- сумма предъявленная рассчётная


            count(DISTINCT CASE WHEN T.is_hospital THEN T.event_id END) AS inv_count_hosp, --  кол-во услуг в стационаре

            sum(CASE WHEN T.is_hospital THEN T.tariff ELSE 0 END) AS inv_sum_tariff_hosp,  -- сумма по тарифу в стационаре


            count(DISTINCT CASE WHEN T.is_day_hospital THEN T.event_id END) AS inv_count_day_hosp, --  кол-во услуг в дневном стационаре

            sum(CASE WHEN T.is_day_hospital THEN T.tariff ELSE 0 END) AS inv_sum_tariff_day_hosp, -- сумма по тарифу в дневном стационаре


             count(distinct CASE WHEN T.is_policlinic and T.is_event THEN
                               case when T.is_phase_exam then T.service_id
                               ELSE T.event_id END END)
            as inv_count_policlinic,  -- количество услуг в поликлинике

            sum(CASE WHEN T.is_policlinic THEN T.tariff ELSE 0 END) AS inv_sum_tariff_policlinic, -- сумма по тарифу в поликлинике


            count(DISTINCT CASE WHEN T.is_ambulance THEN T.event_id END) AS inv_count_ambulance, --  кол-во услуг в скорой

            sum(CASE WHEN T.is_ambulance THEN T.tariff ELSE 0 END) AS inv_sum_tariff_ambulance, -- сумма по тарифу в скорой


            -- Принятые услуги
            sum(CASE WHEN T.is_paid and T.is_tariff THEN T.accepted_payment ELSE 0 END) as accept_sum_tariff,

            count(distinct CASE WHEN T.is_paid and T.is_event THEN
                               case when T.is_phase_exam then T.service_id
                               ELSE T.event_id END END) as accept_count_all, -- количество принятых услуг (в акте)


            count(DISTINCT CASE WHEN T.is_paid and T.is_hospital THEN T.event_id END) AS accept_count_hosp,  -- количество услуг в стационаре

            sum(CASE WHEN T.is_paid and T.is_hospital THEN T.accepted_payment ELSE 0 END) AS accept_sum_tariff_hosp, -- принятая сумма в стационаре


            count(DISTINCT CASE WHEN T.is_paid and T.is_day_hospital THEN T.event_id END) AS accept_count_day_hosp,  -- количество услуг в дневном стационаре

            sum(CASE WHEN T.is_paid and T.is_day_hospital THEN T.accepted_payment ELSE 0 END) AS accept_sum_tariff_day_hosp, -- принятая сумма в дневном стационаре

            count(distinct CASE WHEN T.is_paid and T.is_policlinic and T.is_event THEN
                               case when T.is_phase_exam then T.service_id
                               ELSE T.event_id END END)
            as accept_count_policlinic, -- количество услуг в поликлинике

            sum(CASE WHEN T.is_paid and T.is_tariff and T.is_policlinic THEn T.accepted_payment ELSE 0 END) as accept_sum_tariff_policlinic, -- принятая сумма по поликлинике

            count(distinct CASE WHEN T.is_paid and T.is_ambulance THEn T.event_id END) as accept_count_ambulance, -- количество услуг в скорой помощи

            -- Не принятые услуги
            sum(CASE WHEN T.is_not_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as sanc_sum_tariff,   -- сумма санкциий

            count(DISTINCT CASE WHEN T.is_not_paid and T.is_not_pa and T.is_hospital THEN T.event_id END) AS sanc_count_hosp, -- количество снятых услуг в стационаре

            sum(CASE WHEN T.is_not_paid and T.is_not_pa and T.is_hospital THEN T.provided_tariff ELSE 0 END) AS sanc_sum_tariff_hosp, -- сумма снятая по стационару

            count(DISTINCT CASE WHEN T.is_not_paid and T.is_not_pa and T.is_day_hospital THEN T.event_id END) AS sanc_count_day_hosp, -- количество снятых услуг в дневном стационаре

            sum(CASE WHEN  T.is_not_paid and T.is_not_pa and T.is_day_hospital THEN T.provided_tariff ELSE 0 END) AS sanc_sum_tariff_day_hosp, -- сумма снятая по дневному стационару

            count(DISTINCT CASE WHEN T.is_not_paid and T.is_not_pa and T.is_policlinic and T.is_event THEN
                    case when T.is_phase_exam then T.service_id
                    ELSE T.event_id END END) AS sanc_count_policlinic, -- количество снятых услуг в поликлинике

            sum(CASE WHEN T.is_not_paid and T.is_not_pa and T.is_policlinic  AND T.is_tariff THEN T.provided_tariff ELSE 0 END) AS sanc_sum_tariff_policlinic, -- сумма снятая по поликлинике

            count(DISTINCT CASE WHEN T.is_not_paid and T.is_not_pa and T.is_ambulance THEN T.event_id END) AS sanc_count_ambulance, -- количество снятых услуг в скорой помощи


            -- Услуги сняты сверх объёма
            count(CASE WHEN T.is_not_paid and T.is_pa THEn T.event_id END) as pa_count, -- количество санкций сверх объёма
            sum(CASE WHEN T.is_not_paid and T.is_pa THEn T.provided_tariff ELSE 0 END) as pa_sum_tariff, -- сумма санкций сверх объёма

            sum(CASE WHEN T.is_not_paid and T.is_pa and T.is_hospital THEn T.provided_tariff ELSE 0 END) as pa_sum_tariff_hosp, -- сумма санкций сверх объёма по стациоанру

            sum(CASE WHEN T.is_not_paid and T.is_pa and T.is_day_hospital THEn T.provided_tariff ELSE 0 END) as pa_sum_tariff_day_hosp, -- сумма санкций сверх объёма по дневному стационару

            sum(CASE WHEN T.is_not_paid and T.is_pa and T.is_policlinic THEn T.provided_tariff ELSE 0 END) as pa_sum_tariff_policlinic, -- сумма санкций сверх объёма по поликлинике

            -- Не подлежит к оплате (итоговая)
            count(DISTINCT CASE WHEN T.is_not_paid and T.is_event THEN
                               case when T.is_phase_exam then T.service_id
                               ELSE T.event_id END END) AS sanc_count_all,  -- количество санкций (итоговое)

            sum(CASE WHEN T.is_not_paid and T.is_tariff THEn T.provided_tariff ELSE 0 END) as sanc_sum_tariff_all

            from (
            select pe.id_pk as event_id,
                 ps.id_pk as service_id,
                 mo.id_pk as organization,
                 ps.payment_type_fk = 3 as is_not_paid,
                 ps.payment_type_fk = 2 AS is_paid,
                 ps.tariff as tariff,
                 ps.accepted_payment as accepted_payment,
                 ps.provided_tariff as provided_tariff,
                 ps.payment_kind_fk = 1 and (pe.term_fk !=4 or pe.term_fk is NULL) as is_tariff,

                 pe.term_fk = 1 and (ms.group_fk != 31 or ms.group_fk is null) as is_hospital,
                 pe.term_fk = 2 as is_day_hospital,
                 pe.term_fk = 3 or pe.term_fk is null or ms.group_fk = 31 as is_policlinic,
                 pe.term_fk = 4 As is_ambulance,

                (ms.group_fk != 19 or ms.group_fk is null) or
                (ms.group_fk = 19 and ms.subgroup_fk is not null) as is_event,
                (ms.group_fk in (25, 26)) as is_phase_exam,

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
    stat_dict['inv_sum_tariff'] = stat_obj.inv_sum_tariff
    stat_dict['inv_sum_tariff_other_mo'] = 0

    ### Предъявленные услуги

    # Сумма предъявленная рассчётная
    stat_dict['inv_sum_tariff_mo'] = stat_obj.inv_sum_tariff_mo + capitation_policlinic + capitation_ambulance

    stat_dict['inv_sum_tariff_all'] = stat_dict['inv_sum_tariff_mo']

    # Предъявленные реестры счетов за стационар
    stat_dict['inv_count_hosp'] = stat_obj.inv_count_hosp
    stat_dict['inv_sum_tariff_hosp'] = stat_obj.inv_sum_tariff_hosp

    # Предъяыленные реестры счетов за дневной стационар
    stat_dict['inv_count_day_hosp'] = stat_obj.inv_count_day_hosp
    stat_dict['inv_sum_tariff_day_hosp'] = stat_obj.inv_sum_tariff_day_hosp

    # Предъявленные реестры счетов за поликлинику
    stat_dict['inv_count_policlinic'] = stat_obj.inv_count_policlinic
    stat_dict['inv_sum_tariff_policlinic'] = stat_obj.inv_sum_tariff_policlinic

    # Предъявленные реестры счетов по скорой помощи
    stat_dict['inv_count_ambulance'] = stat_obj.inv_count_ambulance
    stat_dict['inv_sum_tariff_ambulance'] = stat_obj.inv_sum_tariff_ambulance

    ### Принятые услуги

    # Сумма принятая к оплате (без подушевого)
    stat_dict['accept_sum_tariff'] = stat_obj.accept_sum_tariff

    # Подушевое по поликлинике
    stat_dict['accept_sum_policlinic_tariff_capitation'] = capitation_policlinic

    # Подушевое по скорой
    stat_dict['accept_sum_ambulance_tariff_capitation'] = capitation_ambulance

    stat_dict['accept_sum_tariff_other_mo'] = 0

    # Сумма принятая к оплате (с подушевым)
    stat_dict['accept_sum_tariff_mo'] = stat_dict['accept_sum_tariff'] + capitation_policlinic + capitation_ambulance

    # Количество принятых услуг (в акте)
    stat_dict['accept_count_all'] = stat_obj.accept_count_all
    stat_dict['accept_sum_tariff_all'] = stat_dict['accept_sum_tariff_mo']

    # Принятые реестры счетов за стационар
    stat_dict['accept_count_hosp'] = stat_obj.accept_count_hosp
    stat_dict['accept_sum_tariff_hosp'] = stat_obj.accept_sum_tariff_hosp

    # Принятые реестры отчётов за дневной стационар
    stat_dict['accept_count_day_hosp'] = stat_obj.accept_count_day_hosp
    stat_dict['accept_sum_tariff_day_hosp'] = stat_obj.accept_sum_tariff_day_hosp

    # Принятые реестры отчётов за поликлинику
    stat_dict['accept_count_policlinic'] = stat_obj.accept_count_policlinic
    stat_dict['accept_sum_tariff_policlinic'] = stat_obj.accept_sum_tariff_policlinic + capitation_policlinic

    stat_dict['accept_count_ambulance'] = stat_obj.accept_count_ambulance
    stat_dict['accept_sum_tariff_ambulance'] = capitation_ambulance

    ### Снятые с оплаты

    # Непринятые к оплате (без подушевого)
    stat_dict['sanc_sum_tariff'] = stat_obj.sanc_sum_tariff

    # Не принятые реестры счетов за стационар
    stat_dict['sanc_count_hosp'] = stat_obj.sanc_count_hosp
    stat_dict['sanc_sum_tariff_hosp'] = stat_obj.sanc_sum_tariff_hosp

    # Не принятые реестры за дневной стационар
    stat_dict['sanc_count_day_hosp'] = stat_obj.sanc_count_day_hosp
    stat_dict['sanc_sum_tariff_day_hosp'] = stat_obj.sanc_sum_tariff_day_hosp

    # Не принятые реестры за поликлинику
    stat_dict['sanc_count_policlinic'] = stat_obj.sanc_count_policlinic
    stat_dict['sanc_sum_tariff_policlinic'] = stat_obj.sanc_sum_tariff_policlinic

    # Не принятые реестры по скорой помощи
    stat_dict['sanc_count_ambulance'] = stat_obj.sanc_count_ambulance
    stat_dict['sanc_sum_tariff_ambulance'] = 0

    # Не принятые услуги сверх объема
    stat_dict['pa_count'] = stat_obj.pa_count
    stat_dict['pa_sum_tariff'] = stat_obj.pa_sum_tariff

    # Не принятые услуги сверх объёма за стационар
    stat_dict['pa_sum_tariff_hosp'] = stat_obj.pa_sum_tariff_hosp

    # Не принятые услуги сверх объёма за дневной стационар
    stat_dict['pa_sum_tariff_day_hosp'] = stat_obj.pa_sum_tariff_day_hosp

    # Не принятые услуги сверх объёма за поликлинику
    stat_dict['pa_sum_tariff_policlinic'] = stat_obj.pa_sum_tariff_policlinic

    # Не подлежит оплате
    stat_dict['sanc_count_all'] = stat_obj.sanc_count_all
    stat_dict['sanc_sum_tariff_all'] = stat_obj.sanc_sum_tariff_all

    return stat_dict


def get_sanction_info(mo, term=0, has_pa=False):
    query = """
            select
            ps.id_pk, pe.id_pk AS event_pk,
            dep.old_code AS dep_old_code,
            mrr.id as record_id,
            mr.period AS period,
            pt.insurance_policy_number AS insurance_policy_number,
            pt.insurance_policy_series AS insurance_policy_series,
            ps.provided_tariff as provided_tariff,
            pe.term_fk AS term,
            md.code  As division_code,
            msp.code as profile_code,
            pss.error_fk AS error_id
            from medical_register mr JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                  ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                  ON ps.event_fk=pe.id_pk
            join patient pt
                  ON pt.id_pk = mrr.patient_fk
            JOIN medical_organization dep
                  ON dep.id_pk = ps.department_fk
            JOIN medical_service ms
                  ON ms.id_pk = ps.code_fk
            left join medical_division md
                  on md.id_pk = ps.division_fk
            left join medical_service_profile msp
                  on msp.id_pk = ps.profile_fk
            join provided_service_sanction pss
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
                  and mr.organization_code = %(mo)s
                  and pss.is_active
                  AND ps.payment_type_fk = 3
                  AND (ms.group_fk != 27 or ms.group_fk is NULL)
            """
    term_criterias = {1: 'AND (pe.term_fk = 1 and (ms.group_fk != 31 or ms.group_fk is null))', 2: 'and pe.term_fk=2',
                      3: 'and (pe.term_fk=3 or pe.term_fk is NULL or ms.group_fk = 31)',
                      4: 'and pe.term_fk=4', 0: ''}

    services_obj = ProvidedService.objects.raw(
        query+term_criterias[term]+(' AND pss.error_fk=75' if has_pa else ' AND pss.error_fk!=75')+' order by mrr.id',
        dict(year=func.YEAR, period=func.PERIOD, mo=mo)
    )

    query_1 = """
            select
            mo.id_pk,
            sum(CASE WHEN ps.payment_kind_fk = 1
                and (pe.term_fk !=4 or pe.term_fk is NULL) THEN ps.provided_tariff ELSE 0 end) as sanc_sum,
            count(distinct CASE WHEN (ms.group_fk != 19 or ms.group_fk is null)
                  or (ms.group_fk = 19 and ms.subgroup_fk is not null) then pe.id_pk end) as sanc_count
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
            join provided_service_sanction pss
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
                  and pss.is_active
                  AND (ms.group_fk != 27 or ms.group_fk is NULL)
                  and ps.payment_type_fk = 3
            """

    sum_obj = MedicalOrganization.objects.raw(
        query_1+term_criterias[term]+(' AND pss.error_fk=75' if has_pa else ' AND pss.error_fk!=75') +
        ' group by mo.id_pk',
        dict(year=func.YEAR, period=func.PERIOD, organization=mo)
    )

    sanc_sum = 0
    sanc_count = 0
    if len(list(sum_obj)) > 0:
        sanc_sum = sum_obj[0].sanc_sum
        sanc_count = sum_obj[0].sanc_count

    return services_obj, sanc_sum, sanc_count


def print_sanction(act_book, data, capitation_events, title, handbooks):
    services_obj, sanc_sum, sanc_count = data
    act_book.set_style()
    act_book.write_cell('', 'r')
    if title:
        act_book.write_cell(title, 'c', 4)
        act_book.write_cell(sanc_sum, 'c')
        act_book.write_cell(u'руб.', 'c')
        act_book.write_cell(sanc_count, 'c')
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
    act_book.set_style({'border': 1})
    for service in services_obj:
        error_id = service.error_id
        act_book.write_cell(service.dep_old_code, 'c')
        act_book.write_cell(str(service.profile_code or '' if service.term in [1, 2]
                                else service.division_code or ''), 'c')
        act_book.write_cell(service.record_id, 'c')
        act_book.write_cell(service.period, 'c')
        act_book.write_cell(service.insurance_policy_series.replace('\n', '') + ' ' +
                            service.insurance_policy_number
                            if service.insurance_policy_series
                            else service.insurance_policy_number, 'c')
        act_book.write_cell(handbooks['failure_cause'][handbooks['errors'][error_id]['failure_cause']]['number'], 'c')
        act_book.write_cell(handbooks['errors'][error_id]['code'], 'c')
        act_book.write_cell(u'Подуш.' if service.event_id in capitation_events or service.term == 4
                            else service.provided_tariff, 'c')
        act_book.write_cell(1, 'c')
        act_book.write_cell('', 'c')
        act_book.write_cell('', 'r')


def print_registry_sogaz_1(act_book, mo):
    handbooks = {
        'errors': func.ERRORS,
        'failure_cause': func.FAILURE_CAUSES
    }

    mo_name = func.get_mo_info(mo)['name']
    sum_dict = get_statistics(mo)

    capitation_events = func.get_capitation_events(mo_code=mo)

    act_book.set_sheet(7)
    act_book.set_style()
    act_book.write_cella(9, 0, mo_name)
    act_book.write_cella(10, 1, mo)
    # Представлены реестры счетов (все поданные)
    act_book.write_cella(12, 2, sum_dict['inv_sum_tariff'])             # всего подано по тарифу
    act_book.write_cella(13, 4, sum_dict['inv_sum_tariff_other_mo'])    # заказано в другой мо
    act_book.write_cella(14, 4, sum_dict['inv_sum_tariff_mo'])          # заявлено к оплате

    act_book.write_cella(15, 4, sum_dict['inv_sum_tariff_all'])         # всего представлено на сумму
    act_book.write_cella(18, 1, sum_dict['inv_count_hosp'])             # всего подано по стационару
    act_book.write_cella(19, 1, sum_dict['inv_sum_tariff_hosp'])
    act_book.write_cella(21, 1, sum_dict['inv_count_day_hosp'])         # всего подано по дневному стационару
    act_book.write_cella(22, 1, sum_dict['inv_sum_tariff_day_hosp'])

    act_book.write_cella(24, 1, sum_dict['inv_count_policlinic'])       # всего подано по поликлинике
    act_book.write_cella(25, 1, sum_dict['inv_sum_tariff_policlinic'])
    act_book.write_cella(27, 1, sum_dict['inv_count_ambulance'])        # всего по скорой помощи
    act_book.write_cella(28, 1, sum_dict['inv_sum_tariff_ambulance'])

    # Принятые к оплате реестры счетов
    act_book.write_cella(30, 2, sum_dict['accept_sum_tariff'])             # принято по тарифу
    # Подушевое
    act_book.write_cella(31, 2, sum_dict['accept_sum_policlinic_tariff_capitation'])
    act_book.write_cella(32, 2, sum_dict['accept_sum_ambulance_tariff_capitation'])

    act_book.write_cella(33, 3, sum_dict['accept_sum_tariff_other_mo'])    # заказано в другой мо
    act_book.write_cella(34, 2, sum_dict['accept_sum_tariff_mo'])          # принято к оплате
    act_book.write_cella(35, 1, sum_dict['accept_count_all'])              # всего принято к оплате
    act_book.write_cella(35, 4, sum_dict['accept_sum_tariff_all'])

    act_book.write_cella(37, 5, sum_dict['accept_sum_tariff_hosp'])        # принято по стационару
    act_book.write_cella(37, 7, sum_dict['accept_count_hosp'])
    act_book.write_cella(38, 5, sum_dict['accept_sum_tariff_day_hosp'])    # принято по дневному стационару
    act_book.write_cella(38, 7, sum_dict['accept_count_day_hosp'])
    act_book.write_cella(39, 5, sum_dict['accept_sum_tariff_policlinic'])  # принято по поликлинике
    act_book.write_cella(39, 7, sum_dict['accept_count_policlinic'])

    act_book.write_cella(40, 5, sum_dict['accept_sum_tariff_ambulance'])  # принято по скорой помощи
    act_book.write_cella(40, 7, sum_dict['accept_count_ambulance'])

    # Не принятые к оплате реестры счетов
    act_book.write_cella(41, 5, sum_dict['sanc_sum_tariff'])             # не принято к оплате
    act_book.write_cella(42, 5, sum_dict['sanc_sum_tariff_hosp'])        # не принято по стационару
    act_book.write_cella(42, 7, sum_dict['sanc_count_hosp'])
    act_book.write_cella(43, 5, sum_dict['sanc_sum_tariff_day_hosp'])    # не принято по дневному стационару
    act_book.write_cella(43, 7, sum_dict['sanc_count_day_hosp'])
    act_book.write_cella(44, 5, sum_dict['sanc_sum_tariff_policlinic'])  # не принято по поликлинике
    act_book.write_cella(44, 7, sum_dict['sanc_count_policlinic'])

    act_book.write_cella(45, 5, sum_dict['sanc_sum_tariff_ambulance'])  # не принято по скорой помощи
    act_book.write_cella(45, 7, sum_dict['sanc_count_ambulance'])

    act_book.write_cella(46, 5, sum_dict['pa_sum_tariff'])          # не принято сверх объема
    act_book.write_cella(46, 7, sum_dict['pa_count'])
    act_book.write_cella(47, 3, sum_dict['sanc_count_all'])              # не подлежит оплате
    act_book.write_cella(47, 5, sum_dict['sanc_sum_tariff_all'])

    # Снятая с оплаты в стационаре
    act_book.set_cursor(48, 0)
    print_sanction(
        act_book,
        data=get_sanction_info(mo, term=1),
        capitation_events=capitation_events,
        title=u'2.1.1. за стационарную медицинскую помощь на сумму:',
        handbooks=handbooks
    )
    print '1'
    print_sanction(
        act_book,
        data=get_sanction_info(mo, term=2),
        capitation_events=capitation_events,
        title=u'2.1.2. за мед. помощь в дневном стационаре  на сумму:',
        handbooks=handbooks
    )
    print '2'
    print_sanction(
        act_book,
        data=get_sanction_info(mo, term=3),
        capitation_events=capitation_events,
        title=u'2.1.3. за амбулаторно-поликлиническую помощь  на сумму:',
        handbooks=handbooks
    )
    print '3'
    print_sanction(
        act_book,
        data=get_sanction_info(mo, term=4),
        capitation_events=capitation_events,
        title=u'2.1.4. за скорую медицинскую помощь  на сумму:',
        handbooks=handbooks
    )

    act_book.set_style()
    act_book.write_cell(u'2.3. Не принято к оплате в связи с превышением '
                        u'согласованных объемов медицинских услуг на сумму:', 'c', 8)
    act_book.write_cell(sum_dict['pa_sum_tariff'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'В т.ч.:  за стационарную медицинскую помощь на сумму:', 'c', 4)
    act_book.write_cell(sum_dict['pa_sum_tariff_hosp'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'за медицинскую помощь в дневном стационаре на сумму:', 'c', 4)
    act_book.write_cell(sum_dict['pa_sum_tariff_day_hosp'], 'c')
    act_book.write_cell(u'руб.', 'r')
    act_book.write_cell(u'за амбулаторно-поликлиническую мед.помощь на сумму :', 'c', 4)
    act_book.write_cell(sum_dict['pa_sum_tariff_policlinic'], 'c')
    act_book.write_cell(u'руб.', 'r')

    print_sanction(
        act_book,
        data=get_sanction_info(mo, has_pa=True),
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


class Command(BaseCommand):

    def handle(self, *args, **options):
        get_statistics('280022')