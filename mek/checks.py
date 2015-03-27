# -*- coding: utf-8 -*-

from django.db import transaction
from django.db.models import Q, F
from main.models import Sanction, SanctionStatus, ProvidedService


def set_sanction(service, error_code):
    service.payment_type_id = 3
    service.accepted_payment = 0
    service.save()

    sanction = Sanction.objects.create(
        type_id=1, service=service, underpayment=service.invoiced_payment,
        error_id=error_code)

    SanctionStatus.objects.create(
        sanction=sanction,
        type=SanctionStatus.SANCTION_TYPE_ADDED_BY_MEK)


def set_sanctions(service_qs, error_code):
    with transaction.atomic():
        for service in service_qs:
            set_sanction(service, error_code)


def underpay_repeated_service(register_element):
    """
        Санкции на повторно поданные услуги
    """
    query = """
        select distinct ps.id_pk
        from provided_service ps
            join provided_event
                on ps.event_fk = provided_event.id_pk
            join medical_register_record
                on provided_event.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN patient p1
                on medical_register_record.patient_fk = p1.id_pk
            join insurance_policy i1
                on i1.version_id_pk = p1.insurance_policy_fk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 64
            JOIN (
                select ps.id_pk as pk, i.id as policy, ps.code_fk as code, ps.end_date,
                    ps.basic_disease_fk as disease, ps.worker_code, mr.year, mr.period
                from provided_service ps
                    join provided_event pe
                        on ps.event_fk = pe.id_pk
                    join medical_register_record mrr
                        on pe.record_fk = mrr.id_pk
                    join medical_register mr
                        on mrr.register_fk = mr.id_pk
                    JOIN patient p
                        on mrr.patient_fk = p.id_pk
                    join insurance_policy i
                        on i.version_id_pk = p.insurance_policy_fk
                where mr.is_active
                    and mr.organization_code = %(organization)s
                    and format('%%s-%%s-01', mr.year, mr.period)::DATE between format('%%s-%%s-01', %(year)s, %(period)s)::DATE - interval '5 months' and format('%%s-%%s-01', %(year)s, %(period)s)::DATE  - interval '1 months'
                    and ps.payment_type_fk in (2, 4)
            ) as T1 on i1.id = T1.policy and ps1.code_fk = T1.code
                and ps1.end_date = T1.end_date and ps1.basic_disease_fk = T1.disease
                and ps1.worker_code = T1.worker_code
        where mr1.is_active
            and mr1.year = %(year)s
            and mr1.period = %(period)s
            and mr1.organization_code = %(organization)s
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    return set_sanctions(services, 64)
    #return [(rec.pk, 1, rec.invoiced_payment, 64) for rec in services]


def underpay_repeated_examination(register_element):
    """
        Санкции на повторно поданную диспансеризацию
        в рамках 2014 года
    """
    query1 = """
        select id_pk from provided_service where event_fk in (
            select distinct ps1.event_fk
            from provided_service ps1
                join medical_service
                    On ps1.code_fk = medical_service.id_pk
                join provided_event pe1
                    on ps1.event_fk = pe1.id_pk
                join medical_register_record
                    on pe1.record_fk = medical_register_record.id_pk
                join medical_register mr1
                    on medical_register_record.register_fk = mr1.id_pk
                JOIN patient p1
                    on medical_register_record.patient_fk = p1.id_pk
                join insurance_policy i1
                    on i1.version_id_pk = p1.insurance_policy_fk
            where mr1.is_active
                and mr1.year = %(year)s
                and mr1.period = %(period)s
                and mr1.organization_code = %(organization)s

                and medical_service.group_fk in (6, 7, 8, 10, 12, 13)
                and ps1.tariff > 0
                and EXISTS (
                    select 1
                    from provided_service ps2
                        join medical_service ms2
                            On ps2.code_fk = ms2.id_pk
                        join provided_event pe2
                            on ps2.event_fk = pe2.id_pk
                        join medical_register_record
                            on pe2.record_fk = medical_register_record.id_pk
                        join medical_register mr2
                            on medical_register_record.register_fk = mr2.id_pk
                        JOIN patient p2
                            on medical_register_record.patient_fk = p2.id_pk
                        join insurance_policy i2
                            on i2.version_id_pk = p2.insurance_policy_fk
                    WHERE mr2.is_active
                        and mr2.year = '2014'
                        and i1.id = i2.id
                        and pe1.id_pk <> pe2.id_pk
                        and ps1.id_pk <> ps2.id_pk
                        and NOT ((ps1.end_date = ps2.end_date) and (mr1.organization_code = mr1.organization_code))
                        and ms2.group_fk in (6, 7, 8, 10, 12, 13)
                        and ps2.payment_type_fk in (2, 4)
                        and ps2.accepted_payment > 0
                )
            )
        except
        select distinct ps1.id_pk
        from provided_service ps1
            join provided_event pe1
                on ps1.event_fk = pe1.id_pk
            join medical_register_record
                on pe1.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN provided_service_sanction pss
                on pss.service_fk = ps1.id_pk
        where mr1.is_active
            and mr1.year = %(year)s
            and mr1.period = %(period)s
            and mr1.organization_code = %(organization)s
            and pss.error_fk = 64
    """

    query2 = """
        select id_pk from provided_service where event_fk in (
            select distinct ps1.event_fk
            from provided_service ps1
                join medical_service
                    On ps1.code_fk = medical_service.id_pk
                join provided_event pe1
                    on ps1.event_fk = pe1.id_pk
                join medical_register_record
                    on pe1.record_fk = medical_register_record.id_pk
                join medical_register mr1
                    on medical_register_record.register_fk = mr1.id_pk
                JOIN patient p1
                    on medical_register_record.patient_fk = p1.id_pk
                join insurance_policy i1
                    on i1.version_id_pk = p1.insurance_policy_fk
            where mr1.is_active
                and mr1.year = %(year)s
                and mr1.period = %(period)s
                and mr1.organization_code = %(organization)s

                and medical_service.group_fk in (25, 26)
                and ps1.tariff > 0
                and EXISTS (
                    select 1
                    from provided_service ps2
                        join medical_service ms2
                            On ps2.code_fk = ms2.id_pk
                        join provided_event pe2
                            on ps2.event_fk = pe2.id_pk
                        join medical_register_record
                            on pe2.record_fk = medical_register_record.id_pk
                        join medical_register mr2
                            on medical_register_record.register_fk = mr2.id_pk
                        JOIN patient p2
                            on medical_register_record.patient_fk = p2.id_pk
                        join insurance_policy i2
                            on i2.version_id_pk = p2.insurance_policy_fk
                    WHERE mr2.is_active
                        and mr2.year = '2014'
                        and i1.id = i2.id
                        and pe1.id_pk <> pe2.id_pk
                        and ps1.id_pk <> ps2.id_pk
                        and NOT ((ps1.end_date = ps2.end_date) and (mr1.organization_code = mr1.organization_code))
                        and ms2.group_fk in (26, 25)
                        and ps2.payment_type_fk in (2, 4)
                        and ps2.accepted_payment > 0
                )
            )
        except
        select distinct ps1.id_pk
        from provided_service ps1
            join provided_event pe1
                on ps1.event_fk = pe1.id_pk
            join medical_register_record
                on pe1.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN provided_service_sanction pss
                on pss.service_fk = ps1.id_pk
        where mr1.is_active
            and mr1.year = %(year)s
            and mr1.period = %(period)s
            and mr1.organization_code = %(organization)s
            and pss.error_fk = 64
    """

    services1 = ProvidedService.objects.raw(
        query1, dict(year=register_element['year'],
                     period=register_element['period'],
                     organization=register_element['organization_code']))

    services2 = ProvidedService.objects.raw(
        query2, dict(year=register_element['year'],
                     period=register_element['period'],
                     organization=register_element['organization_code']))

    set_sanctions(services1, 64)
    set_sanctions(services2, 64)


def underpay_ill_formed_adult_examination(register_element):
    """
        Санкции на взрослую диспансеризацю у которой в случае
        не хватает услуг (должна быть 1 платная и больше 0 бесплатных)
    """
    query = """
        select ps.id_pk
        from
            (
                select distinct pe1.id_pk, (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_primary
                                and ps2.payment_type_fk = 2
                                and ms2.group_fk = ms.group_fk
                        ) as primary_count,
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_specialist
                                and ps2.payment_type_fk = 2
                                and ms2.group_fk = ms.group_fk
                        ) as specialist_count,
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_final
                                and ps2.payment_type_fk = 2
                                and ms2.group_fk = ms.group_fk
                        ) as finals_count
                from provided_event pe1
                    join medical_register_record
                        on pe1.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                where mr1.is_active
                    and mr1.year = %s
                    and mr1.period = %s
                    and mr1.organization_code = %s
                    --and medical_service.group_fk in (7, 9)
                    --and pss.id_pk is NULL
            ) as T
            join provided_service ps
                on ps.event_fk = T.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT join provided_service_sanction pss
               on pss.service_fk = ps.id_pk and pss.error_fk = 34
        where ms.group_fk in (7, 9)
            and (primary_count != 1 or specialist_count = 0 or finals_count != 1)
            and pss.id_pk is null
            and (ps.payment_type_fk != 3 or ps.payment_type_fk is null)
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 34)


def underpay_duplicate_services(register_element):
    """
        Санкции на дубликатные услуги
    """
    query = """
        select ps.id_pk
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN (
                select medical_register_record.patient_fk, ps1.code_fk,
                    ps1.basic_disease_fk, ps1.end_date, ps1.worker_code,
                    count(1)
                from provided_service ps1
                    join provided_event
                        on ps1.event_fk = provided_event.id_pk
                    join medical_register_record
                        on provided_event.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                where mr1.is_active
                    and mr1.year = %(year)s
                    and mr1.period = %(period)s
                    and mr1.organization_code = %(organization)s
                group by medical_register_record.patient_fk, ps1.code_fk,
                    ps1.basic_disease_fk, ps1.end_date, ps1.worker_code
                HAVING count(1) > 1
            ) as T on T.patient_fk = mrr.patient_fk and T.code_fk = ps.code_fk
                and ps.basic_disease_fk = T.basic_disease_fk and
                ps.end_date = T.end_date and ps.worker_code = T.worker_code
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 67
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and pss.id_pk is null
        EXCEPT
        select P.min from (
            select medical_register_record.patient_fk, ps1.code_fk,
                ps1.basic_disease_fk, ps1.end_date, ps1.worker_code,
                min(ps1.id_pk)
            from provided_service ps1
                join provided_event
                    on ps1.event_fk = provided_event.id_pk
                join medical_register_record
                    on provided_event.record_fk = medical_register_record.id_pk
                join medical_register mr1
                    on medical_register_record.register_fk = mr1.id_pk
            where mr1.is_active
                    and mr1.year = %(year)s
                    and mr1.period = %(period)s
                    and mr1.organization_code = %(organization)s
            group by medical_register_record.patient_fk, ps1.code_fk,
                ps1.basic_disease_fk, ps1.end_date, ps1.worker_code
        ) as P
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 67)


def underpay_cross_dates_services(register_element):
    """
        Санкции на пересечения дней в отделениях
        Поликлиника в стационаре
        И стационар в стационаре
    """
    query1 = """
        select ps.id_pk, T.id_pk
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 73
            JOIN (
                select medical_register_record.patient_fk, ps1.start_date, ps1.end_date, ps1.id_pk
                from provided_service ps1
                    JOIN medical_service ms
                        on ps1.code_fk = ms.id_pk
                    join provided_event
                        on ps1.event_fk = provided_event.id_pk
                    join medical_register_record
                        on provided_event.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                where mr1.is_active
                    and mr1.year = %(year)s
                    and mr1.year = %(year)s
                    and mr1.period = %(period)s
                    and mr1.organization_code = %(organization)s
                    and provided_event.term_fk = 1
                    and ms.group_fk not in (27, 5, 3)
            ) as T on T.patient_fk = mrr.patient_fk and (
                (ps.start_date > T.start_date and ps.start_date < T.end_date)
                or (ps.end_date > T.start_date and ps.end_date < T.end_date)
                and T.id_pk != ps.id_pk
            )
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and pe.term_fk = 3
        order by ps.id_pk
    """

    query2 = """
        select ps.id_pk, T.id_pk
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 73
            JOIN (
                select medical_register_record.patient_fk, ps1.start_date, ps1.end_date, ps1.id_pk
                from provided_service ps1
                    JOIN medical_service ms
                        on ps1.code_fk = ms.id_pk
                    join provided_event
                        on ps1.event_fk = provided_event.id_pk
                    join medical_register_record
                        on provided_event.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                where mr1.is_active
                    and mr1.year = %(year)s
                    and mr1.period = %(period)s
                    and mr1.organization_code = %(organization)s
                    and provided_event.term_fk in (1, 2)
                    and ms.group_fk not in (27, 5, 3)
            ) as T on T.patient_fk = mrr.patient_fk and (
                (ps.start_date > T.start_date and ps.start_date < T.end_date)
                or (ps.end_date > T.start_date and ps.end_date < T.end_date)
                and T.id_pk != ps.id_pk
            )
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and pe.term_fk in (1, 2)
        order by ps.id_pk
    """

    services1 = ProvidedService.objects.raw(
        query1, dict(year=register_element['year'],
                     period=register_element['period'],
                     organization=register_element['organization_code']))

    services2 = ProvidedService.objects.raw(
        query2, dict(year=register_element['year'],
                     period=register_element['period'],
                     organization=register_element['organization_code']))

    set_sanctions(services1, 73)
    set_sanctions(services2, 73)


def underpay_disease_gender(register_element):
    """
        Санкции на несоответствие пола диагнозу
    """
    services = ProvidedService.objects.filter(
        ~Q(event__record__patient__gender=F('basic_disease__gender')),
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code']
    ).extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 29) = 0'])

    set_sanctions(services, 29)


def underpay_service_gender(register_element):
    """
        Санкции на несоответствие пола услуге
    """
    services = ProvidedService.objects.filter(
        ~Q(event__record__patient__gender=F('code__gender')),
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code']
    ).extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 41) = 0'])

    return set_sanctions(services, 41)


def underpay_wrong_date_service(register_element):
    query = """
        select ps.id_pk--, i.id, ps.code_fk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN insurance_policy i
                on i.version_id_pk = p.insurance_policy_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 32
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and (
                ((ps.end_date < (format('%s-%s-01', mr.year, mr.period)::DATE - interval '2 month') and not mrr.is_corrected and not ms.examination_special)
                or (ps.end_date < (format('%s-%s-01', mr.year, mr.period)::DATE - interval '3 month') and mrr.is_corrected and not ms.examination_special)
                or (ps.end_date >= format('%s-%s-01', mr.year, mr.period)::DATE + interval '1 month')
                ) or (
                    ms.examination_special = True
                        and age(format('%s-%s-01', mr.year, mr.period)::DATE - interval '1 month', ps.end_date) > '1 year'
                )
            )
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 32)


def underpay_wrong_age_service(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 35
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and NOT (ms.group_fk in (20, 7, 9, 10, 11, 12, 13, 14, 15, 16)
                or ms.code between '001441' and '001460' or
                 ms.code in ('098703', '098770', '098940', '098913', '098914', '019018'))
            and (
                (age(ps.end_date, p.birthdate) < '18 year' and substr(ms.code, 1, 1) = '0')
                or (age(ps.end_date, p.birthdate) >= '18 year' and substr(ms.code, 1, 1) = '1')
            and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 35)


def underpay_wrong_examination_age_group(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 35
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and (date_part('year', ps.end_date) - date_part('year', p.birthdate)) >= 4
            and ((group_fk = 11
                and ps.tariff > 0
                and ms.examination_group != (
                    select "group"
                    from examination_age_bracket
                    where age = (date_part('year', ps.end_date) - date_part('year', p.birthdate))
                )) or (group_fk = 7
                and ms.examination_group != (
                    select "group"
                    from examination_age_bracket
                    where age = (date_part('year', ps.end_date) - date_part('year', p.birthdate))))
            )
            and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 35)


def underpay_not_paid_in_oms(register_element):
    """
        Санкции на диагнозы и услуги не оплачиваемые по ТП ОМС
    """
    services1 = ProvidedService.objects.filter(
        basic_disease__is_paid=False,
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code']
    ).extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 58) = 0'])

    services2 = ProvidedService.objects.filter(
        code__is_paid=False,
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code']
    ).extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 59) = 0'])

    return set_sanctions(services1, 58) + set_sanctions(services2, 59)


def underpay_examination_event(register_element):
    """
        Санкции на случаи со снятыми услугами
    """
    query = """
        select provided_service.id_pk, 1, accepted_payment, T.error_id
        from provided_service
            join (
                select distinct pe1.id_pk as event_id, pss.error_fk as error_id
                from provided_service ps1
                    join medical_service ms
                        On ps1.code_fk = ms.id_pk
                    join provided_event pe1
                        on ps1.event_fk = pe1.id_pk
                    join medical_register_record
                        on pe1.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                    LEFT join provided_service_sanction pss
                        on pss.id_pk = (
                            select provided_service_sanction.id_pk
                            from provided_service_sanction
                                join medical_error
                                    on provided_service_sanction.error_fk = medical_error.id_pk
                            WHERE provided_service_sanction.service_fk = ps1.id_pk
                            ORDER BY weight, provided_service_sanction.id_pk DESC
                            LIMIT 1
                        )
                where mr1.is_active
                    and mr1.year = %s
                    and mr1.period = %s
                    and mr1.organization_code = %s
                    and ms.group_fk in (7, 9, 11, 12, 13, 15, 16)
                    and (ms.examination_primary or ms.examination_final)
                    and ps1.payment_type_fk = 3
                    and exists (
                        select 1
                        from provided_service
                        where event_fk = pe1.id_pk
                            and payment_type_fk = 2
                    )
                    and pss.error_fk is not null) as T
                ON T.event_id = provided_service.event_fk
            LEFT JOIN provided_service_sanction
                on provided_service_sanction.service_fk = provided_service.id_pk
                    and provided_service_sanction.error_fk = T.error_id
        WHERE provided_service_sanction.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    errors = [(rec.pk, 1, rec.accepted_payment, rec.error_id) for rec in list(services)]
    errors_pk = [rec[0] for rec in errors]

    ProvidedService.objects.filter(pk__in=errors_pk).update(
        accepted_payment=0, payment_type=3)

    errors_objs = []
    for rec in errors:
        errors_objs.append(Sanction(service_id=rec[0], type_id=1,
                                    underpayment=rec[2], error_id=rec[3]))

    Sanction.objects.bulk_create(errors_objs)


def underpay_invalid_stomatology_event(register_element):
    """
        Санкции на неверно оформленные случаи стоматологии
    """
    query = """
        select ps1.id_pk
        from provided_service ps1
            join medical_organization
                on ps1.department_fk = medical_organization.id_pk
            join medical_service
                On ps1.code_fk = medical_service.id_pk
            left join medical_service_subgroup
                on medical_service.subgroup_fk = medical_service_subgroup.id_pk
            join provided_event pe1
                on ps1.event_fk = pe1.id_pk
            join medical_register_record
                on pe1.record_fk = medical_register_record.id_pk
            join patient p1
                on p1.id_pk = medical_register_record.patient_fk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 34
        where mr1.is_active
            and mr1.year = %s
            and mr1.period = %s
            and mr1.organization_code = %s
            and (
                    (
                        medical_service.subgroup_fk is NULL
                        and medical_service.group_fk = 19
                        and not exists (
                            SELECT 1
                            from provided_service ps2
                            join medical_service
                                On ps2.code_fk = medical_service.id_pk
                            join provided_event pe2
                                on ps2.event_fk = pe2.id_pk
                            join medical_register_record
                                on pe2.record_fk = medical_register_record.id_pk
                            join medical_register mr2
                                on medical_register_record.register_fk = mr2.id_pk
                            where pe1.id_pk = pe2.id_pk
                                and ps1.end_date = ps2.end_date
                                and medical_service.subgroup_fk in (12, 13, 14, 17)
                                and ps2.payment_type_fk = 2
                            )
                    ) OR (
                        medical_service.subgroup_fk in (12, 13, 14, 17)
                        and not exists (
                            SELECT 1
                            from provided_service ps2
                            join medical_service
                                On ps2.code_fk = medical_service.id_pk
                            join provided_event pe2
                                on ps2.event_fk = pe2.id_pk
                            join medical_register_record
                                on pe2.record_fk = medical_register_record.id_pk
                            join medical_register mr2
                                on medical_register_record.register_fk = mr2.id_pk
                            where pe1.id_pk = pe2.id_pk
                                and ps1.end_date = ps2.end_date
                                and medical_service.subgroup_fk is NULL
                                and medical_service.group_fk = 19
                                and ps2.payment_type_fk = 2
                        )
                    )
            )
            and ps1.payment_type_fk <> 3
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 34)


def underpay_invalid_outpatient_event(register_element):
    """
        Санкции на неверно оформленные услуги по поликлинике с заболеванием
    """
    query = """
        select id_pk from provided_service
        where event_fk in (
            select distinct provided_event.id_pk
            from
                provided_service
                join medical_organization department
                    on department.id_pk = provided_service.department_fk
                JOIN medical_service ms
                    on ms.id_pk = provided_service.code_fk
                join provided_event
                    on provided_event.id_pk = provided_service.event_fk
                join medical_register_record
                    on medical_register_record.id_pk = provided_event.record_fk
                join medical_register
                    on medical_register_record.register_fk = medical_register.id_pk
                LEFT join provided_service_sanction pss
                    on pss.service_fk = ps.id_pk and pss.error_fk = 34
            where
                medical_register.is_active
                and medical_register.year = %s
                and medical_register.period = %s
                and medical_register.organization_code = %s
                --and department.level <> 3
                and ((
                        select count(1)
                        from provided_service
                            join medical_service
                                on provided_service.code_fk = medical_service.id_pk
                        where provided_service.event_fk = provided_event.id_pk
                            and provided_service.tariff > 0
                            and medical_service.reason_fk = 1 and (medical_service.group_fk != 19
                                or medical_service.group_fk is NUll)
                    ) > 1 or (
                        (
                            select count(1)
                            from provided_service
                                join medical_service
                                    on provided_service.code_fk = medical_service.id_pk
                            where provided_service.event_fk = provided_event.id_pk
                                and provided_service.tariff > 0
                                and medical_service.reason_fk = 1 and (medical_service.group_fk != 19
                                    or medical_service.group_fk is NUll)
                        ) = 0 and (
                            select count(1)
                            from provided_service
                                join medical_service
                                    on provided_service.code_fk = medical_service.id_pk
                            where provided_service.event_fk = provided_event.id_pk
                                and provided_service.tariff = 0
                                and medical_service.reason_fk = 1 and (medical_service.group_fk != 19
                                    or medical_service.group_fk is NUll)
                        ) >= 1

                    )
                )
        ) and payment_type_fk != 3
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 34)


def underpay_outpatient_event(register_element):
    """
        Санкции на случаи поликлиники по заболеваниям со снятыми услугами
    """
    query = """
    select T.error_code, provided_service.id_pk
    from provided_service
        join medical_organization department
            on provided_service.department_fk = department.id_pk
        JOIN medical_service ms ON ms.id_pk = provided_service.code_fk
        join
            (
                select provided_event.id_pk as event_id,
                    min(provided_service_sanction.error_fk) as error_code
                from provided_service ps1
                    join medical_service
                        on medical_service.id_pk = ps1.code_fk
                    join provided_event
                        on ps1.event_fk = provided_event.id_pk
                    join medical_register_record
                        on provided_event.record_fk = medical_register_record.id_pk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                    JOIN patient p1
                        on medical_register_record.patient_fk = p1.id_pk
                    join provided_service_sanction
                        on ps1.id_pk = provided_service_sanction.service_fk
                    join medical_error
                        on provided_service_sanction.error_fk = medical_error.id_pk
                            and medical_error.weight = (select max(weight) from medical_error where id_pk in (select error_fk from provided_service_sanction where service_fk = ps1.id_pk))
                where mr1.is_active
                    and mr1.year = %s
                    and mr1.period = %s
                    and mr1.organization_code = %s
                    AND (
                           ((medical_service.group_fk != 19 or medical_service.group_fk is NULL) AND ps1.tariff > 0)
                           or
                           (medical_service.group_fk = 19 AND medical_service.subgroup_fk is NOT NULL)
                           )
                    and ps1.payment_type_fk = 3
                    group BY provided_event.id_pk
            ) as T
            on provided_service.event_fk = T.event_id
        LEFT JOIN provided_service_sanction pss
            on pss.service_fk = provided_service.id_pk and pss.error_fk = T.error_code
    where (ms.group_fk != 27 or ms.group_fk is NULL)
        AND pss.id_pk is NULL
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    errors = [(rec.pk, 1, rec.accepted_payment, rec.error_code) for rec in list(services)]
    errors_pk = [rec[0] for rec in errors]

    ProvidedService.objects.filter(pk__in=errors_pk).update(
        accepted_payment=0, payment_type=3)

    errors_objs = []
    for rec in errors:
        errors_objs.append(Sanction(service_id=rec[0], type_id=1,
                                    underpayment=rec[2], error_id=rec[3]))

    Sanction.objects.bulk_create(errors_objs)


def underpay_invalid_hitech_service_diseases(register_element):
    query1 = """
        select ps.id_pk
        from
            provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            LEFT JOIN hitech_service_kind_disease hskd
                on hskd.kind_fk = pe.hitech_kind_fk
                    and hskd.disease_fk = ps.basic_disease_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 77
        where
            mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and hskd.id_pk is null
            and mr.type = 2
    """

    query2 = """
        select ps.id_pk
        from provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            LEFT JOIN hitech_service_method_disease hsmd
                on hsmd.method_fk = pe.hitech_method_fk
                    and hsmd.disease_fk = ps.basic_disease_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 78
        where
            mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and mr.type = 2
            and hsmd.id_pk is NULL
            and (select id_pk from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 78) is null
    """

    services1 = ProvidedService.objects.raw(
        query1, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    services2 = ProvidedService.objects.raw(
        query2, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    set_sanctions(services1, 77)
    set_sanctions(services2, 78)


def underpay_wrong_age_adult_examination(register_element):
    query = """
        select id_pk from provided_service where event_fk in (
        select DISTINCT pe.id_pk
        from provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            join medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 35
        where ms.group_fk IN (7, 25, 26)
            and substr(pe.comment, 5, 1) = '0'
            and (extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk and tariff > 0)) - EXTRACT(YEAR FROM p.birthdate)) not in (
                select DISTINCT age from adult_examination_service
            )
            and mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s)
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 35)


def underpay_adult_examination_service_count(register_element):
    query1 = """
        select id_pk from provided_service where event_fk in (
        select DISTINCT event_id
        from (
            select DISTINCT pe.id_pk event_id, p.birthdate, p.gender_fk,
                (
                    select count(provided_service.id_pk)
                    from provided_service
                        join adult_examination_service aes
                            on aes.stage = 1
                                and aes.gender_fk = p.gender_fk
                                and (aes.is_required or aes.is_one_of)
                                and aes.code_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                    WHERE provided_service.event_fk = pe.id_pk
                        and provided_service.payment_type_fk != 3
                ) total,
                (
                    select count(1)
                    from adult_examination_service
                    where stage = 1 and gender_fk = p.gender_fk
                        and is_required
                        and age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                ) required,
                (
                    select count(provided_service.id_pk)
                    from provided_service
                        join adult_examination_service aes
                            on aes.stage = 1
                                and aes.gender_fk = p.gender_fk
                                and aes.is_one_of
                                and aes.code_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                    WHERE provided_service.event_fk = pe.id_pk
                        and provided_service.payment_type_fk != 3
                ) one_of

            from provided_service ps
                JOIN medical_service ms
                    on ps.code_fk = ms.id_pk
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN patient p
                    on p.id_pk = mrr.patient_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
            WHERE
                mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and ms.group_fk = 7
        ) as T
        where required > 0 and one_of = 1
            and total < ceil(trunc((required+one_of) * 0.85, 1))
            and (select count(1) from provided_service_sanction
                 where service_fk = provided_service.id_pk and error_fk = 34) = 0
    )
    """

    query2 = """
    select id_pk from provided_service where event_fk in (
        select T.event_id
        from (
            select DISTINCT pe.id_pk event_id,
                (
                    select count(provided_service.id_pk)
                    from provided_service
                        join adult_examination_service aes
                            on aes.stage = 2
                                and aes.gender_fk = p.gender_fk
                                and (aes.is_required or aes.is_one_of)
                                and aes.code_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                    WHERE provided_service.event_fk = pe.id_pk
                        and (provided_service.payment_type_fk != 3 or provided_service.payment_type_fk is null)
                ) total,
                (
                    select count(1)
                    from adult_examination_service
                    where stage = 2 and gender_fk = p.gender_fk
                        and is_required
                        and age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                ) required,
                (
                    select count(provided_service.id_pk)
                    from provided_service
                        join adult_examination_service aes
                            on aes.stage = 2
                                and aes.gender_fk = p.gender_fk
                                and aes.is_one_of
                                and aes.code_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                    WHERE provided_service.event_fk = pe.id_pk
                        and provided_service.payment_type_fk != 3
                ) one_of

            from provided_service ps
                JOIN medical_service ms
                    on ps.code_fk = ms.id_pk
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN patient p
                    on p.id_pk = mrr.patient_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
            WHERE
                mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and ms.group_fk in (25, 26)
        ) as T
        where required > 0
            and total < ceil(trunc((required+one_of) * 0.85, 1))
            and (select count(1) from provided_service_sanction
                 where service_fk = provided_service.id_pk and error_fk = 34) = 0
    )
    """

    services1 = ProvidedService.objects.raw(
        query1, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    services2 = ProvidedService.objects.raw(
        query2, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    set_sanctions(services1, 34)
    set_sanctions(services2, 34)


def underpay_ill_formed_children_examination(register_element):
    query = """
    select id_pk from provided_service where event_fk in (
        select distinct pe1.id_pk
        from provided_service ps1
            join medical_service
                On ps1.code_fk = medical_service.id_pk
            join provided_event pe1
                on ps1.event_fk = pe1.id_pk
            join medical_register_record
                on pe1.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN patient p
                on p.id_pk = medical_register_record.patient_fk
        where mr1.is_active
            and mr1.year = %s
            and mr1.period = %s
            and mr1.organization_code = %s
            and ps1.payment_type_fk != 3
            and medical_service.group_fk in (11, 12, 13, 15, 16)
            and (
                (
                    (date_part('year', ps1.end_date) - date_part('year', p.birthdate)) > 3
                    and NOT (
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_primary
                                and ps2.payment_type_fk = 2
                        ) = 1 and EXISTS (
                            select 1
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_specialist
                                and ps2.payment_type_fk = 2
                        )
                    )
                ) OR (
                    (date_part('year', ps1.end_date) - date_part('year', p.birthdate)) <= 3
                    and NOT (
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_primary
                                and ps2.payment_type_fk = 2
                        ) = 1
                    )
                )
            )
        ) and payment_type_fk != 3
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 34)


def underpay_wrong_examination_attachment(register_element):
    query = """
        select distinct ps1.id_pk--, 1, ps1.invoiced_payment, 1
        from provided_service ps1
            join medical_service
                On ps1.code_fk = medical_service.id_pk
            join provided_event pe1
                on ps1.event_fk = pe1.id_pk
            join medical_register_record
                on pe1.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN patient p1
                on medical_register_record.patient_fk = p1.id_pk
            join insurance_policy
                on p1.insurance_policy_fk = insurance_policy.version_id_pk
            join person
                on person.version_id_pk = (
                    select version_id_pk
                    from person where id = (
                        select id
                        from person
                        where version_id_pk = insurance_policy.person_fk
                    ) and is_active
                )
            join attachment
                on attachment.id_pk = (
                    select max(id_pk)
                    from attachment
                    where person_fk = person.version_id_pk and status_fk = 1
                        and confirmation_date <= (
                            select max(end_date)
                            from provided_service
                            where event_fk = pe1.id_pk
                        )
                        and attachment.is_active
                )
            join medical_organization medOrg
                on (
                    medOrg.id_pk = attachment.medical_organization_fk and
                    medOrg.parent_fk is null
                ) or medOrg.id_pk = (
                    select parent_fk
                    from medical_organization
                    where id_pk = attachment.medical_organization_fk
                )
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 1
        WHERE mr1.is_active
            and mr1.year = %s
            and mr1.period = %s
            and mr1.organization_code = %s
            and mr1.organization_code != medOrg.code
            and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 1)


def underpay_wrong_age_examination_children_adopted(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 35
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and (
                (ms.code in ('119220', '119221') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 0 and 2) or
                (ms.code in ('119222', '119223') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 3 and 4) or
                (ms.code in ('119224', '119225') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 5 and 6) or
                (ms.code in ('119226', '119227') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 7 and 13) or
                (ms.code in ('119228', '119228') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) = 14) or
                (ms.code in ('119230', '119231') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 15 and 17)
            ) and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 35)


def underpay_wrong_age_examination_children_difficult(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and (
                (ms.code in ('119020', '119021') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 0 and 2) or
                (ms.code in ('119022', '119023') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 3 and 4) or
                (ms.code in ('119024', '119025') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 5 and 6) or
                (ms.code in ('119026', '119027') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 7 and 13) or
                (ms.code in ('119028', '119028') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) = 14) or
                (ms.code in ('119030', '119031') and not (date_part('year', ps.end_date) - date_part('year', p.birthdate)) between 15 and 17)
            ) and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 35) = 0
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 35)


def underpay_duplicate_examination_in_current_register(register_element):
    query = """
        select ps.id_pk
        from provided_event pe
            JOIN (
                select record_fk, count(*)
                from provided_event where id_pk in (
                    select DISTINCT pe.id_pk
                    from provided_service ps
                        join medical_service ms
                            on ms.id_pk = ps.code_fk
                        JOIN provided_event pe
                            on pe.id_pk = ps.event_fk
                        JOIN medical_register_record mrr
                            on mrr.id_pk = pe.record_fk
                        JOIN medical_register mr
                            ON mr.id_pk = mrr.register_fk
                    WHERE mr.is_active
                        and mr.year = %(year)s
                        and mr.period = %(period)s
                        and mr.organization_code = %(organization)s
                        and ms.group_fk in (7, 9, 12, 13, 15, 16)
                        and ps.payment_type_fk = 2
                )
                group by record_fk
                having count(*) > 1
            ) as T1 on pe.id_pk = (select max(id_pk) from provided_event where record_fk = T1.record_fk)

            join provided_service ps
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            JOIN patient p
                on p.id_pk = mrr.patient_fk

    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 64)


def underpay_service_term_kind_mismatch(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 79
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and pss.id_pk is null
            and NOT (
                (pe.term_fk = 1 and pe.kind_fk in (3, 4, 10, 11 ))
                or (pe.term_fk = 2 and pe.kind_fk in (3, 10, 11))
                OR (pe.term_fk = 3 and pe.kind_fk in (1, 4, 5, 6, 7))
                or (pe.term_fk = 4 and pe.kind_fk in (2, 8, 9))
            )
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 79)


def underpay_service_term_mismatch(register_element):
    query = """
        select ps.id_pk
        from provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN tariff_profile tp
                on tp.id_pk = ms.tariff_profile_fk
            LEFT JOIN provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.error_fk = 76
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and pss.id_pk is null
            and pe.term_fk in (1, 2)
            and tp.term_fk != pe.term_fk
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    #print len(services) #, type(services)

    return set_sanctions(services, 76)