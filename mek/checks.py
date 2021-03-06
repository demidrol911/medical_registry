# -*- coding: utf-8 -*-

from django.db import transaction
from django.db.models import Q, F
from main.funcs import howlong
from main.models import Sanction, SanctionStatus, ProvidedService


def set_sanction(service, error_code, type_sanction=SanctionStatus.SANCTION_TYPE_ADDED_BY_MEK):
    service.payment_type_id = 3
    service.accepted_payment = 0
    service.save()
    sanction = Sanction.objects.create(
        type_id=1, service=service, underpayment=service.invoiced_payment,
        is_active=True,
        error_id=error_code,
        comment=service.error_comment if 'error_comment' in dir(service) else '')

    SanctionStatus.objects.create(
        sanction=sanction,
        type=type_sanction)


def set_sanctions(service_qs, error_code):
    with transaction.atomic():
        for service in service_qs:
            set_sanction(service, error_code)


@howlong
def underpay_repeated_service(register_element):
    """
        Санкции на повторно поданные услуги
    """

    query = """
        with current_period as (select format('%%s-%%s-01', %(year)s, %(period)s)::DATE as val)

        select DISTINCT ps.id_pk from (
        select ps.id_pk as service_id,
            ps.event_fk as event_id,

            rank() over (PARTITION BY p.person_unique_id, ps.code_fk, ps.end_date, ps.start_date,
            COALESCE(ps.basic_disease_fk, 0), ps.worker_code, p.newborn_code order by format('%%s-%%s-01', mr.year, mr.period)::DATE) as rnum_repeated,

            format('%%s-%%s-01', mr.year, mr.period)::DATE as checking_period
        from provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN patient p
                on mrr.patient_fk = p.id_pk
        where mr.is_active
            and mr.organization_code = %(organization)s
            and format('%%s-%%s-01', mr.year, mr.period)::DATE between (select val from current_period) - interval '12 months' and (select val from current_period)
            and (ps.payment_type_fk = 2 or ps.payment_type_fk is NULL)
            and ps.code_fk not in (8437, 8436)
        ) as T
        join provided_service ps
            on ps.id_pk = T.service_id
        where checking_period = (select val from current_period) and rnum_repeated > 1
            AND (select count(pss.id_pk) from provided_service_sanction pss
                 where pss.service_fk = T.service_id and pss.error_fk = 64) = 0
    """
    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code'])))

    if len(services) > 0:
        print 'repeated', len(services)



    set_sanctions(services, 64)


@howlong
def underpay_ill_formed_adult_examination(register_element):
    """
        Санкции на взрослую диспансеризацю у которой в случае
        не хватает услуг (должна быть 1 платная и больше 0 бесплатных)
        проверяются случаи дата начала, которых меньше 2015-06-01
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
                                and ms2.group_fk in (7, 9)
                        ) as primary_count,
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_specialist
                                and ps2.payment_type_fk = 2
                                and ms2.group_fk in (7, 9)
                        ) as specialist_count,
                        (
                            select count(1)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            WHERE ps2.event_fk = pe1.id_pk
                                and ms2.examination_final
                                and ps2.payment_type_fk = 2
                                and ms2.group_fk in (7, 9)
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
                    and pe1.end_date < '2015-06-01'
            ) as T
            join provided_service ps
                on ps.event_fk = T.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT join provided_service_sanction pss
               on pss.service_fk = ps.id_pk and pss.error_fk = 81
        where ms.group_fk in (7, 9)
            and (primary_count != 1 or specialist_count = 0 or finals_count != 1)
            and pss.id_pk is null
            and (ps.payment_type_fk != 3 or ps.payment_type_fk is null)

    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 81)


@howlong
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
            join medical_service ms
                on ms.id_pk = ps.code_fk
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
            and (ms.group_fk != 27 or ms.group_fk is null)
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


@howlong
def underpay_cross_dates_services(register_element):
    """
        Санкции на пересечения дней в отделениях
        Поликлиника в стационаре
        И стационар в стационаре
    """
    query1 = """
        select ps.id_pk
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            join medical_service ms
                on ms.id_pk = ps.code_fk
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
                    and (ms.group_fk not in (27, 5, 3)
                         or ms.group_fk is null
                         )
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
            and (ms.group_fk != 27 or ms.group_fk IS NULL)
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 73) = 0
        order by ps.id_pk
    """

    query2 = """
        select ps.id_pk
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            join medical_service ms
                on ms.id_pk = ps.code_fk
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
                    and (ms.group_fk not in (27, 5, 3)
                         or ms.group_fk is null
                         )
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
            and (ms.group_fk not in (27, 5, 3) or ms.group_fk IS NULL)
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 82) = 0
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
    set_sanctions(services2, 82)


@howlong
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


@howlong
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


@howlong
def underpay_wrong_date_service(register_element):
    """
        Санкции на несоответствие даты оказания услуги отчётному периоду
    """
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
                on pss.service_fk = ps.id_pk and pss.error_fk = 32
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and (
                ((ps.end_date < (format('%%s-%%s-01', mr.year, mr.period)::DATE - interval '1 month') and (not mrr.is_corrected or mrr.is_corrected IS NULL) and (not ms.examination_special or ms.examination_special IS NULL))
                or (ps.end_date < (format('%%s-%%s-01', mr.year, mr.period)::DATE - interval '3 month') and mrr.is_corrected and (not ms.examination_special OR ms.examination_special IS NULL))
                or (ps.end_date >= format('%%s-%%s-01', mr.year, mr.period)::DATE + interval '1 month')
                ) or (
                    ms.examination_special = True and ms.code <> '019014'
                        and age(format('%%s-%%s-01', mr.year, mr.period)::DATE - interval '1 month', ps.end_date) > '1 year'
                ) or (
                    ms.code in ('019014')
                    and age(format('%%s-%%s-01', mr.year, mr.period)::DATE - interval '1 month', ps.end_date) > '2 year'
                )
            )
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 32)


@howlong
def underpay_wrong_age_service(register_element):
    """
        Санкции на несоответствие кода услуги возрасту
    """
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
            and (ms.group_fk NOT in (7, 9, 11, 13, 12, 15) or ms.group_fk is NULL) AND
                  NOT(ms.code between '001441' and '001460' or
                         ms.code in ('098703', '098770', '098940', '098913', '098914', '098915', '019018',
                                     '098978', '198992'))
            and ((EXTRACT(year from age(CASE WHEN mr.organization_code in ('280043', '280064')
                                               THEN ps.start_date
                                             ELSE ps.end_date
                                        END, p.birthdate)) < 18 and substr(ms.code, 1, 1) = '0')
                or (EXTRACT(year from age(CASE WHEN mr.organization_code in ('280043', '280064')
                                                  THEN ps.start_date
                                                ELSE ps.end_date
                                            END, p.birthdate)) >= 18  and substr(ms.code, 1, 1) = '1'))
            and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 35)


@howlong
def underpay_wrong_examination_age_group(register_element):
    """
        Санкции на несоответствие кода услуги возрастной группе
        по диспансеризации проведённой раннее 2015-06-01
    """
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
                on pss.service_fk = ps.id_pk and pss.error_fk = 83
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

    set_sanctions(services, 83)


@howlong
def underpay_not_paid_in_oms(register_element):
    """
        Санкции на диагнозы и услуги не оплачиваемые по ТП ОМС
    """
    services1 = ProvidedService.objects.filter(
        basic_disease__is_paid=False,
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code'],
    ).filter(~Q(event__record__register__organization_code='280043'))\
     .extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 58) = 0'])

    services2 = ProvidedService.objects.filter(
        code__is_paid=False,
        event__record__register__is_active=True,
        event__record__register__year=register_element['year'],
        event__record__register__period=register_element['period'],
        event__record__register__organization_code=register_element['organization_code']
    ).extra(where=['(select count(id_pk) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 59) = 0'])

    set_sanctions(services1, 58)
    set_sanctions(services2, 59)


@howlong
def underpay_examination_event(register_element):
    """
        Санкции на случаи со снятыми услугами
        по диспансеризации и профосмотрам
        (если снят с оплаты первичный или итоговый приём снимается весь случай)
    """
    query = '''
            SELECT provided_service.id_pk, 1, accepted_payment, T.error_id
            FROM provided_service
            JOIN (
                SELECT pe1.id_pk AS event_id,
                pss.error_fk AS error_id,
                COUNT(DISTINCT CASE WHEN ps1.payment_type_fk = 3
                                         AND (ms.examination_primary OR ms.examination_final)
                                      THEN ps1.id_pk
                               END) AS excluded_services,
                COUNT(DISTINCT CASE WHEN ps1.payment_type_fk = 2
                                      THEN ps1.id_pk
                               END) AS accepted_services
                FROM provided_service ps1
                    JOIN medical_service ms
                       ON ms.id_pk = ps1.code_fk
                    JOIN provided_event pe1
                       ON ps1.event_fk = pe1.id_pk
                    JOIN medical_register_record
                       ON pe1.record_fk = medical_register_record.id_pk
                    JOIN medical_register mr1
                       ON medical_register_record.register_fk = mr1.id_pk
                    LEFT JOIN provided_service_sanction pss
                        ON pss.id_pk = (
                              SELECT in_pss.id_pk
                              FROM provided_service in_ps
                                  JOIN provided_service_sanction in_pss
                                     ON in_ps.id_pk = in_pss.service_fk
                                  JOIN medical_error in_me
                                     ON in_me.id_pk = in_pss.error_fk
                              WHERE in_ps.event_fk = ps1.event_fk
                                    AND in_pss.is_active
                              ORDER BY in_me.weight DESC
                              LIMIT 1
                        )
                WHERE mr1.is_active
                   AND mr1.year = %s
                   AND mr1.period = %s
                   AND mr1.organization_code = %s
                   AND ms.group_fk IN (7, 9, 11, 12, 13, 15, 16)
                GROUP BY event_id, error_id
              ) AS T
               ON T.event_id = provided_service.event_fk
            LEFT JOIN provided_service_sanction
               ON provided_service_sanction.service_fk = provided_service.id_pk
                  AND provided_service_sanction.error_fk = T.error_id
            WHERE provided_service_sanction.id_pk IS NULL
                  AND T.excluded_services > 0
                  AND T.accepted_services > 0
    '''

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    errors = [(rec.pk, 1, rec.accepted_payment, rec.error_id) for rec in list(services)]
    errors_pk = [rec[0] for rec in errors]

    ProvidedService.objects.filter(pk__in=errors_pk).update(
        accepted_payment=0, payment_type=3)

    with transaction.atomic():
        for rec in errors:
            set_sanction(ProvidedService.objects.get(pk=rec[0]), rec[3],
                         SanctionStatus.SANCTION_TYPE_ADDED_MAX_ERROR_BY_MEK)


@howlong
def underpay_invalid_stomatology_event(register_element):
    """
        Санкции на отсутствие совместных услуг в случаях по стоматологии
    """
    query = """
        select ps.id_pk
        FROM (
                select
                    pe.id_pk as event_id,
                    ps.end_date,
                    ps.start_date,
                    sum(
                        case when ms.subgroup_fk is NULL
                                and ms.group_fk = 19
                                and ms.subgroup_fk is null
                        THEN 1
                        ELSE 0
                        END
                    ) as service,
                    sum(
                        case when ms.subgroup_fk in (12, 13, 14, 17)
                        then 1
                        else 0
                        end
                    ) as admission
                from provided_service ps
                    join medical_service ms
                        On ps.code_fk = ms.id_pk
                    left join medical_service_subgroup msg
                        on ms.subgroup_fk = msg.id_pk
                    join provided_event pe
                        on ps.event_fk = pe.id_pk
                    join medical_register_record
                        on pe.record_fk = medical_register_record.id_pk
                    join patient p1
                        on p1.id_pk = medical_register_record.patient_fk
                    join medical_register mr1
                        on medical_register_record.register_fk = mr1.id_pk
                    LEFT join provided_service_sanction pss
                        on pss.service_fk = ps.id_pk and pss.error_fk = 84
                where mr1.is_active
                    and mr1.year = %(year)s
                    and mr1.period = %(period)s
                    and mr1.organization_code = %(organization)s
                    and (ms.group_fk = 19 or (ms.subgroup_fk in (12, 13, 14, 17) and ms.group_fk is null))
                GROUP BY pe.id_pk, ps.end_date, ps.start_date
            ) as T
            join provided_service ps
                on ps.event_fk = T.event_id
        where
            (admission > 1
            or service = 0
            or admission = 0)
            and (select count(*) from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 84) = 0
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 84)


@howlong
def underpay_invalid_outpatient_event(register_element):
    """
        Санкции на отсутствие совместных услуг в случаях по поликлинике
    """
    query = """
        select ps.id_pk
        from
            (
                select provided_event.id_pk as event_id,
                    count(case when ms.reason_fk = 1 and provided_service.tariff > 0 then 1 else null end) as on_disease_primary,
                    count(case when ms.reason_fk = 1 and provided_service.tariff = 0 then 1 else null end) as on_disease_secondary,
                    count(case when ms.reason_fk = 2 and provided_service.tariff > 0 then 1 else null end) as on_prevention,
                    count(case when ms.reason_fk = 5 and provided_service.tariff > 0 then 1 else null end) as on_emergency
                from
                    provided_service
                    JOIN medical_service ms
                        on ms.id_pk = provided_service.code_fk
                    join provided_event
                        on provided_event.id_pk = provided_service.event_fk
                    join medical_register_record
                        on medical_register_record.id_pk = provided_event.record_fk
                    join medical_register
                        on medical_register_record.register_fk = medical_register.id_pk
                where
                    medical_register.is_active
                    and medical_register.year = %s
                    and medical_register.period = %s
                    and medical_register.organization_code = %s
                    and provided_event.term_fk = 3
                    --and department.level <> 3
                    and ms.reason_fk in (1, 2, 5) and (ms.group_fk not in (19, 27)
                        or ms.group_fk is NUll)
                group by provided_event.id_pk
            ) as T
            JOIN provided_service ps
                on ps.event_fk = T.event_id
        WHERE
            NOT (
                (on_disease_primary = 1 and on_disease_secondary > 0 and on_prevention = 0 and on_emergency = 0)
                or (on_disease_primary = 1 and on_disease_secondary = 0 and on_prevention = 0 and on_emergency = 0)
                or (on_disease_primary = 0 and on_disease_secondary = 0 and on_prevention = 1 and on_emergency = 0)
                or (on_disease_primary = 0 and on_disease_secondary = 0 and on_prevention = 0 and on_emergency = 1)
            )
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                 and error_fk = 85) = 0
    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 85)


@howlong
def underpay_outpatient_event(register_element):
    """
        Санкции на случаи, если хоть одна услуга снята с оплаты
        кроме ошибки ZD
    """
    query = """
        select T.error_code, provided_service.id_pk
        from provided_service
        JOIN medical_service ms ON ms.id_pk = provided_service.code_fk
        join
            (
                select DISTINCT provided_event.id_pk as event_id,
                    pss.error_fk as error_code
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
                    join provided_service_sanction pss
                        on pss.id_pk = (
                            select pssi.id_pk
                            from provided_service_sanction pssi
                                join medical_error mei
                                    on mei.id_pk = pssi.error_fk
                            WHERE pssi.service_fk = ps1.id_pk
                                  and pssi.is_active
                                  and pssi.error_fk <> 70
                            ORDER BY mei.weight DESC
                            limit 1
                        )
                where mr1.is_active
                    and mr1.year = %s
                    and mr1.period = %s
                    and mr1.organization_code = %s
                    AND (medical_service.group_fk != 27 or medical_service.group_fk is NULL)
                    and ps1.payment_type_fk = 3
            ) as T
            on provided_service.event_fk = T.event_id
        LEFT JOIN provided_service_sanction pss
            on pss.service_fk = provided_service.id_pk
                and pss.error_fk = T.error_code AND pss.is_active
        where (ms.group_fk != 27 or ms.group_fk is NULL)
        and pss.id_pk is null
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    errors = [(rec.pk, 1, rec.accepted_payment, rec.error_code) for rec in list(services)]
    errors_pk = [rec[0] for rec in errors]

    ProvidedService.objects.filter(pk__in=errors_pk).update(
        accepted_payment=0, payment_type=3)

    with transaction.atomic():
        for rec in errors:
            set_sanction(ProvidedService.objects.get(pk=rec[0]), rec[3],
                         SanctionStatus.SANCTION_TYPE_ADDED_MAX_ERROR_BY_MEK)


@howlong
def underpay_invalid_hitech_service_diseases(register_element):
    """
        Санкции на несоответствие диагноза методу оказания помощи
        (для высокотехнологической медицинской помощи)
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
                on pss.service_fk = ps.id_pk and pss.error_fk = 86
        where
            mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and mr.type = 2
            and hsmd.id_pk is NULL
            and (select id_pk from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 86) is null
    """

    services2 = ProvidedService.objects.raw(
        query2, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    set_sanctions(services2, 86)


@howlong
def underpay_invalid_hitech_service_kind(register_element):
    """
    Санкции на несоответствие методу ВМП виду
    (для высокотехнологической медицинской помощи)
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
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            LEFT JOIN hitech_kind_method hkm
                on hkm.method_fk = pe.hitech_method_fk
                   and hkm.kind_fk = pe.hitech_kind_fk
                   and ms.vmp_group = hkm.vmp_group
                   and hkm.is_active
        where
            mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and mr.type = 2
            and hkm.id_pk is NULL
            and (select id_pk from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 103) is null
    """

    services2 = ProvidedService.objects.raw(
        query2, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    set_sanctions(services2, 103)


@howlong
def underpay_adult_examination_service_count(register_element):
    """
        Санкции на отсутствие совместных услуг в случае по диспансеризации взрослых
        первого и второго этапа
    """
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
                 where service_fk = provided_service.id_pk and error_fk = 87) = 0
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
                 where service_fk = provided_service.id_pk and error_fk = 88) = 0
    )
    """

    services1 = ProvidedService.objects.raw(
        query1, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    services2 = ProvidedService.objects.raw(
        query2, [register_element['year'], register_element['period'],
                 register_element['organization_code']])

    set_sanctions(services1, 87)
    set_sanctions(services2, 88)


@howlong
def underpay_ill_formed_children_examination(register_element):
    """
        Санкции на отсутствие совместных услуг в случае по диспансеризации детей
    """
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

    set_sanctions(services, 89)


@howlong
def underpay_wrong_age_examination_children_adopted(register_element):
    """
        Санкции на несоответствие кода услуги возрастной группе по диспансеризации
        детей без попечения родителей
    """
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
                on pss.service_fk = ps.id_pk and pss.error_fk = 90
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

    set_sanctions(services, 90)


@howlong
def underpay_wrong_age_examination_children_difficult(register_element):
    """
        Санкции на несоответствие кода услуги возрастной группе по диспансеризации
        детей в трудной жизненной ситуаации
    """
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
            ) and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 91) = 0
    """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 91)


@howlong
def underpay_duplicate_examination_in_current_register(register_element):
    """
        Санкции на повторно поданную диспансеризацию и профосмотры в текущем периоде
    """
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

    set_sanctions(services, 92)


@howlong
def underpay_service_term_kind_mismatch(register_element):
    """
        Санкции на несоответствие вида медицинской помощи условию оказания
    """
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


@howlong
def underpay_service_term_mismatch(register_element):
    """
        Санкции на несоответствие кода услуги условию оказания
    """
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
            and mr.organization_code not in ('280107')
            and pss.id_pk is null
            and (ms.group_fk != 27 or ms.group_fk is null)
            and pe.term_fk in (1, 2)
            and tp.term_fk != pe.term_fk
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 76)


@howlong
def underpay_second_phase_examination(register_element):
    """
        Санкции на услуги второго этапа диспансеризации взрослых,
        если первый этап был снят с оплаты
    """
    query = """
        select ps.id_pk
        from medical_register mr JOIN medical_register_record mrr ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps ON ps.event_fk=pe.id_pk
            JOIN medical_service ms ON ms.id_pk = ps.code_fk
            join patient pt ON pt.id_pk = mrr.patient_fk
            join
                (
                    select distinct mr1.id_pk as mr_id, p1.person_unique_id as person_unique_id
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
                        where
                             mr1.year = %(year)s
                             and mr1.period = %(period)s
                             and mr1.organization_code = %(organization)s
                             and ps1.payment_type_fk = 3
                             AND medical_service.group_fk = 7
                        group BY mr_id, person_unique_id
                ) as T
                on pt.person_unique_id = T.person_unique_id and mr.id_pk = T.mr_id
        where
            ms.group_fk in (25, 26)
            and ps.payment_type_fk = 2
            and (select count(id_pk) from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 93) = 0
    """
    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 93)


@howlong
def underpay_neurologist_first_phase_exam(register_element):
    """
        Санкции на услуги невролога по диспансеризации взрослых, оказанные раннее 2015-04-01,
        если первичный приём проведён после 2015-04-01
    """
    query = """
            select ps2.id_pk
            FROM provided_service ps2
            where ps2.event_fk in (
                select DISTINCT ps1.event_fk
                from (
                    select pe.id_pk AS event_id
                    FROM medical_register mr
                        JOIN medical_register_record mrr
                           ON mr.id_pk = mrr.register_fk
                        JOIN provided_event pe
                           ON mrr.id_pk = pe.record_fk
                        JOIN provided_service ps
                           ON ps.event_fk = pe.id_pk
                        JOIN medical_service ms
                           ON ms.id_pk = ps.code_fk
                    WHERE mr.is_active
                       AND mr.period = %(period)s
                       AND mr.year = %(year)s
                       AND mr.organization_code = %(organization)s
                       AND ps.payment_type_fk = 2
                       AND ms.code = '019001'
                       AND ps.start_date >= '2015-04-01'
                 ) as T
                 JOIN provided_service ps1
                    ON ps1.event_fk = T.event_id
                 JOIN medical_service ms1
                    ON ms1.id_pk = ps1.code_fk
                 where
                     ms1.code = '019020'
                     and ps1.start_date <= '2015-04-01'
                     AND ps1.payment_type_fk = 2)
            """
    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 94)


@howlong
def underpay_multi_division_disease_events(register_element):
    query = """
        SELECT DISTINCT ps.id_pk
        from (
            select
            pe.id_pk AS event_id
            from medical_register mr JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
            JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
            where mr.is_active and mr.year = %(year)s
                and mr.period = %(period)s
                AND mr.organization_code = %(organization)s
                AND (ms.group_fk not in (27, 19) or ms.group_fk is null)
                AND ps.payment_type_fk = 2
                AND pe.term_fk = 3
            group by event_id
            HAVING count(distinct ms.division_fk) > 1
            ) AS T
            join provided_service ps
                 ON ps.event_fk = T.event_id
        where (select count(*) from provided_service_sanction where error_fk = 78 and service_fk = ps.id_pk) = 0
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 78)


@howlong
def underpay_multi_subgrouped_stomatology_events(register_element):
    """
        Санкции на услуги по стоматологии, если в одном случае подано больше одного
        приёма
    """
    query = """
            select provided_service.id_pk from provided_service join (
                select
                    pe.id_pk, count(distinct ps.id_pk) as count_services
                from medical_register mr JOIN medical_register_record mrr
                    ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                    ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                    ON ps.event_fk=pe.id_pk
                JOIN medical_organization mo
                    ON mo.id_pk = ps.organization_fk
                join patient pt
                    on pt.id_pk = mrr.patient_fk
                JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                where
                    mr.is_active
                    and mr.year = %(year)s
                    and mr.period = %(period)s
                    and mr.organization_code = %(organization)s
                    and ms.group_fk = 19
                    and ms.subgroup_fk is not null
                group by 1
                order by 2
            ) as T on T.id_pk = event_fk
            and T.count_services > 1
            where (select count(*) from provided_service_sanction
                where service_fk = provided_service.id_pk and error_fk = 95) = 0
            """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 95)


@howlong
def underpay_hitech_with_small_duration(register_element):
    """
        Санкции на услуги высокотехнологичной медицинской помощи,
        если средняя длительность, поданная больницей, составляет меньше 40 процентов
        от установленного норматива
    """
    query = """
        select ps.id_pk from (
        select ps.event_fk as event_id, ps.tariff, ps.quantity, ps.end_date - ps.start_date, ms.code, ps.end_date,
            COALESCE(
                (
                    select "value"
                    from hitech_service_nkd
                    where start_date = (select max(start_date) from hitech_service_nkd where start_date = '2017-01-01')
                        and vmp_group = ms.vmp_group
                    order by start_date DESC
                    limit 1
                ), 1
            ) as nkd,
            ms.vmp_group,
            ms.tariff_profile_fk

        from provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            JOIN medical_organization department
                on department.id_pk = ps.department_fk
        where
            mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and mr.type = 2) as T
            JOIN provided_service ps
                on ps.event_fk = T.event_id
        WHERE T.quantity / T.nkd * 100 < 40
            and (select count(*) from provided_service_sanction
                 where service_fk = ps.id_pk and error_fk = 96) = 0
    """
    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 96)


@howlong
def underpay_incorrect_examination_events(register_element):
    """
        Санкции на неверно оформленные случаи по диспансеризации взрослых
    """
    query = """
        select ps.id_pk from (
        select event_id, total, required, required_interview, required_therapy, round(total/greatest(required, 1)::NUMERIC * 100, 0) as service_percentage, extra
        from (
            select pe.id_pk event_id,
                (
                    select count(
                        case
                        when aes.service_fk = 8355 and aes.age < 36 and aes.gender_fk = 1 then NULL
                        when aes.service_fk = 8355 and aes.age < 45 and aes.gender_fk = 2 THEN NULL
                        ELSE 1
                        END
                    )
                    from provided_service
                        join examination_tariff aes
                            on aes.gender_fk = p.gender_fk
                                and aes.service_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                                and mo.regional_coefficient = aes.regional_coefficient
                                and aes.start_date =
                                    GREATEST(
                                        (select max(start_date)
                                         from examination_tariff
                                         where start_date <= pe.end_date
                                         and service_fk = ps.code_fk),
                                         '2015-06-01'
                                    )
                    WHERE provided_service.event_fk = pe.id_pk
                ) total,
                (
                    select count(
                        case
                        when examination_tariff.service_fk = 8355 and examination_tariff.age < 36 and examination_tariff.gender_fk = 1 then NULL
                        when examination_tariff.service_fk = 8355 and examination_tariff.age < 45 and examination_tariff.gender_fk = 2 THEN NULL
                        ELSE 1
                        END
                    )
                    from examination_tariff
                    where gender_fk = p.gender_fk
                        and age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                        and mo.regional_coefficient = regional_coefficient
                        and start_date =
                            GREATEST(
                                (select max(start_date)
                                 from examination_tariff
                                 where start_date <= pe.end_date
                                 and service_fk = ps.code_fk),
                                 '2015-06-01'
                            )
                ) required,
                (
                    select count(provided_service.id_pk)
                    from provided_service
                        LEFT join examination_tariff aes
                            on aes.gender_fk = p.gender_fk
                                and aes.service_fk = provided_service.code_fk
                                and aes.age = extract(YEAR from (select max(end_date) from provided_service where event_fk = pe.id_pk)) - EXTRACT(YEAR FROM p.birthdate)
                                and mo.regional_coefficient = aes.regional_coefficient
                                and aes.start_date =
                                    GREATEST(
                                        (select max(start_date)
                                         from examination_tariff
                                         where start_date <= pe.end_date
                                         and service_fk = ps.code_fk),
                                         '2015-06-01'
                                    )
                    WHERE provided_service.event_fk = pe.id_pk and provided_service.code_fk <> 8339
                        and aes.id_pk is null
                        and provided_service.tariff > 0
                ) extra,
                sum(case when ms.code in ('019002') THEN 1 ELSE 0 END) as required_interview,
                sum(case when ms.code in ('019021', '019023', '019022', '019024') THEN 1 ELSE 0 END) as required_therapy
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
                join medical_organization mo
                    on mo.parent_fk is null and mo.code = mr.organization_code
            WHERE
                mr.is_active
                and mr.year = %(year)s
                and mr.period = %(period)s
                and mr.organization_code = %(organization)s
                and ms.group_fk = 7
                and ms.code <> '019001'
                and pe.end_date >= '2015-06-01'
            GROUP BY 1, 2, 3, 4
        ) as T) as T2
        join provided_service ps
            on ps.event_fk = T2.event_id
        WHERE (service_percentage < 85 or required_interview <> 1 or required_therapy <> 1 or extra > 0)
            and (select count(1) from provided_service_sanction where error_fk = 97 and service_fk = ps.id_pk) = 0
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 97)


@howlong
def underpay_old_examination_services(register_element):
    """
        Санкции на услуги по взрослой диспансеризации, дата оказания которых
        меньше даты проведения опроса (анкетирования)
    """
    query = """
        select ps.id_pk
        from provided_service ps
            join provided_event pe
                on pe.id_pk = ps.event_fk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk

        WHERE mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s

            and ms.code not in ('019001')
            and ps.end_date < (select max(end_date) from provided_service where event_fk = pe.id_pk and code_fk = 8347)
            and mr.type = 3
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 70) = 0
            and pe.end_date > '2015-06-01'
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    for service in services:
        service.payment_type_id = 3
        service.accepted_payment = 0
        service.calculated_payment = 0
        service.save()

        sanction = Sanction.objects.create(
            type_id=1, service=service,
            underpayment=service.invoiced_payment,
            is_active=True,
            error_id=70)

        SanctionStatus.objects.create(
            sanction=sanction,
            type=SanctionStatus.SANCTION_TYPE_ADDED_BY_MEK)


@howlong
def underpay_incorrect_preventive_examination_event(register_element):
    """
        Санкции на отсутвие совместных услуг по профосмотрам взрослых
    """
    query = """
        select ps.id_pk
        from
            (
                select pe.id_pk event_id,
                    count(case when ps.code_fk in (10771, 10772) then 1 else NULL END) as "first",
                    count(case when ps.code_fk in (10773, 10774) then 1 else NULL END) as "last"

                from provided_service ps
                    join provided_event pe
                        on pe.id_pk = ps.event_fk
                    JOIN medical_register_record mrr
                        on mrr.id_pk = pe.record_fk
                    JOIN medical_register mr
                        on mr.id_pk = mrr.register_fk
                    JOIN patient p
                        on p.id_pk = mrr.patient_fk
                    JOIN medical_organization dep
                        on dep.id_pk = ps.department_fk
                    JOIN medical_Service ms
                        on ms.id_pk = ps.code_fk
                WHERE mr.is_active
                    and mr.year = %(year)s
                    and mr.period = %(period)s
                    and mr.organization_code = %(organization)s
                    and ps.payment_type_fk = 2
                    --and mr.status_fk > 4
                    and ms.group_fk = 9
                group by pe.id_pk
            ) as T
            join provided_service ps
                on ps.event_fk = T.event_id

        where T.first <> 1 or T.last <> 1
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 98) = 0
    """

    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 98)


@howlong
def underpay_repeated_preventive_examination_event(register_element):
    """
        Санкции на дубликаты по профосмотрам несовершеннолетних
    """
    query = """
        select DISTINCT id_pk from (
        select
            DISTINCT
            ps.event_fk as event_id,
            row_number() over (PARTITION BY p.person_unique_id, ms.code order by pe.end_date, pe.id_pk, ms.code) as rnum_repeated,
            p.last_name, p.first_name, p.middle_name
        from provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN patient p
                on mrr.patient_fk = p.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
        where mr.is_active
            and mr.organization_code = %(organization)s
            and mr.year = %(year)s
            and mr.period = %(period)s
            and ms.group_fk = 11
            and ps.payment_type_fk = 2
            and ps.tariff > 0
            and ms.code in ('119084',
                '119085',
                '119086',
                '119087',
                '119088',
                '119089',
                '119090',
                '119091'
            )
        ) as T
            join provided_service
                on event_fk = event_id
        where rnum_repeated > 1
            and (select count(1) from provided_service_sanction where service_fk = provided_service.id_pk and error_fk = 99) = 0
    """

    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code'])))
    if len(services) > 0:
        print 'repeated_prevent', len(services)

    set_sanctions(services, 99)


@howlong
def underpay_services_at_weekends(register_element):
    """
        Санкции на услуги оказанные в выходной день
    """

    """
        select
            ps.id_pk
        from
            provided_service ps
            join provided_event pe
                on pe.id_pk = ps.event_fk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join medical_organization mo
                on mo.code = mr.organization_code
                    and mo.parent_fk is null
        WHERE mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (
                (pe.term_fk = 3 and (ms.reason_fk != 5 or ms.reason_fk is null)
                    and extract(DOW FROM ps.start_date) IN (6, 0) and (ms.group_fk <> 31 or ms.group_fk is NULL))
            )
    """

    """
        select
            ps.id_pk
        from
            provided_service ps
            join provided_event pe
                on pe.id_pk = ps.event_fk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join medical_organization mo
                on mo.code = mr.organization_code
                    and mo.parent_fk is null
        WHERE mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (
                (
                    pe.term_fk = 3 and (ms.reason_fk <> 5 or ms.reason_fk is null)

                    and (
                        ms.group_fk <> 31 or ms.group_fk is NULL
                    ) and (
                        select count(*)
                        from provided_service ps1
                            join medical_service ms1
                                on ps1.code_fk = ms1.id_pk
                        where ps1.event_fk = pe.id_pk and ms1.subgroup_fk = 17
                    ) = 0

                    and extract(DOW FROM ps.start_date) = any (
                        case
                        when mr.organization_code in ('280054', '280023', '280004', '280070') THEN ARRAY[0]
                        ELSE ARRAY[6,0]
                        END
                    )
                )
            )

    """

    query = """
        select
            ps.id_pk
        from
            provided_service ps
            join provided_event pe
                on pe.id_pk = ps.event_fk
            join medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            join medical_organization mo
                on mo.code = mr.organization_code
                    and mo.parent_fk is null
        WHERE mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (
                pe.term_fk = 3 and (ms.reason_fk <> 5 or ms.reason_fk is null)
                and (ms.group_fk not in (31, 19, 3, 5) or ms.group_fk is NULL)
                and extract(DOW FROM ps.start_date) IN (6, 0)
            )
    """
    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization=register_element['organization_code']))

    set_sanctions(services, 52)


@howlong
def underpay_wrong_clinic_event(register_element):
    """
       Санкции на неверно оформленный случай по поликлинике
    """
    query = """
        select ps.id_pk
        from
            (
                select provided_event.id_pk as event_id,
                    count(case when provided_service.tariff > 0 then 1 else null end) as count_primary
                from
                    provided_service
                    JOIN medical_service ms
                        on ms.id_pk = provided_service.code_fk
                    join provided_event
                        on provided_event.id_pk = provided_service.event_fk
                    join medical_register_record
                        on medical_register_record.id_pk = provided_event.record_fk
                    join medical_register
                        on medical_register_record.register_fk = medical_register.id_pk
                where
                    medical_register.is_active
                    and medical_register.year = %s
                    and medical_register.period = %s
                    and medical_register.organization_code = %s
                    and provided_event.term_fk = 3
                    and ms.reason_fk in (1, 2, 5) and (ms.group_fk not in (19, 27)
                        or ms.group_fk is NUll)
                group by provided_event.id_pk
            ) as T
            JOIN provided_service ps
                on ps.event_fk = T.event_id
        WHERE
            T.count_primary > 1
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                 and error_fk = 100) = 0
        """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 100)


@howlong
def check_ksg(register_element):
    """
    Проверяет соответствие КСГ которую поставила больница КСГ которую поставила МО
    """
    query = """
            select distinct ps.id_pk
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                join medical_service ms ON ms.id_pk = ps.code_fk
            WHERE mr.is_active
                AND mr.year = %s
                AND mr.period = %s
                AND mr.organization_code = %s
                and pe.term_fk in (1, 2) and (ms.group_fk <> 20 or ms.group_fk is null)
                and mr.type = 1
                and (pe.ksg_mo <> pe.ksg_smo or pe.ksg_mo is null or pe.ksg_smo is null)
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                     and error_fk = 109) = 0
    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    set_sanctions(services, 109)


@howlong
def underpay_adult_examination_with_double_services(register_element):
    """
    Снять нахрен весь случай по диспансеризации, в котором
    есть кратные услуги
    """
    query = """
            SELECT DISTINCT ps.id_pk
            FROM provided_service ps
            JOIN (
                SELECT pe.id_pk AS event_id,
                       ms.code,
                       count(distinct ps.id_pk) AS count_double
                FROM provided_service ps
                    JOIN medical_service ms
                        ON ms.id_pk = ps.code_fk
                    JOIN provided_event pe
                        ON ps.event_fk = pe.id_pk
                    JOIN medical_register_record mrr
                        ON mrr.id_pk = pe.record_fk
                    JOIN medical_register mr
                        ON mr.id_pk = mrr.register_fk
                WHERE mr.is_active
                    AND mr.year = %s
                    AND mr.period = %s
                    AND mr.organization_code = %s
                    AND ps.payment_type_fk = 2
                    AND ms.group_fk = 7
                    AND ps.tariff > 0
                GROUP BY event_id, ms.code
            ) AS T ON ps.event_fk = T.event_id
            WHERE T.count_double > 1
                 AND (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                 AND error_fk = 102) = 0
            """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])
    set_sanctions(services, 102)


@howlong
def underpay_wrong_age_prelim_examination_children(register_element):
    """
        Санкции на несоответствие кода услуги возрастной группе по
        предварительным медосмотрам детей
    """
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
                and ((ms.code = '119101' and not Extract (year from age(ps.end_date, p.birthdate)) between 0 and 6) or
                     (ms.code = '119119' and not Extract (year from age(ps.end_date, p.birthdate)) between 6 and 17) or
                     (ms.code = '119120' and not Extract (year from age(ps.end_date, p.birthdate)) between 15 and 17))
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 105) = 0
            """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 105)


@howlong
def underpay_wrong_age_examination_adult(register_element):
    """
        Санкции на несоответствие кода услуги возрасту
        по профосмотрам взрослых
    """
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
                and (ms.code in ('019216', '019217') and not EXTRACT (year from age(ps.end_date, p.birthdate)) >= 18)
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 106) = 0
            """

    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 106)


@howlong
def underpay_wrong_adult_examination_not_attachment(register_element):
    """
        Снятие случая по диспансеризации для неприкреплённого пациента к данной медицинской
        организации
    """
    query = """
        select id_pk from provided_service where event_fk in (
            select distinct pe.id_pk
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

                LEFT JOIN uploading_person up ON up.id = (
                   (select up1.id from uploading_person up1
                          join uploading_policy u_pol1 ON up1.id_pk = u_pol1.uploading_person_fk
                          where up1.person_unique_id = p.person_unique_id
                          order by u_pol1.stop_date desc  nulls first
                          limit 1)
                )

                left join uploading_attachment ua ON ua.id_pk = (
                    select ua1.id_pk
                    from uploading_attachment ua1
                    where ua1.id = up.id and ua1.start_date <= pe.end_date
                    order by ua1.start_date desc
                    limit 1
                )

                left join uploading_attachment ua2 ON ua2.id_pk = (
                    select ua1.id_pk
                    from uploading_attachment ua1
                    where ua1.id = up.id and ua1.confirmation_date <= pe.end_date
                    order by ua1.confirmation_date desc
                    limit 1
                )

                left join uploading_attachment ua3 ON ua3.id_pk = (CASE WHEN ua.id_pk is null and ua2.id_pk is not null THEN ua2.id_pk
                                                                        WHEN ua.id_pk is not null and ua2.id_pk is null THEN ua.id_pk
                                                                        WHEN ua.id_pk is not null and ua2.id_pk is not null and ua2.confirmation_date > ua.confirmation_date THEN ua2.id_pk
                                                                        ELSE ua.id_pk END)


                left join medical_organization up_att_org ON up_att_org.id_pk = ua3.organization_fk
            WHERE mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and ms.group_fk in (7, 25, 26)
                and (up_att_org.id_pk is null or up_att_org.code != mr.organization_code)
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 107) = 0
        )

    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 107)


@howlong
def underpay_wrong_hospital_quantity(register_element):
    """
        Снятие услуги в стационаре, количество койко-дней которой не соответствует периоду лечения
    """
    query = """
            select distinct ps.id_pk
            from provided_service ps
                JOIN medical_service ms
                    on ms.id_pk = ps.code_fk
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
            WHERE mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and pe.term_fk = 1
                and ps.tariff > 0
                and (ms.group_fk is null or ms.group_fk = 20)
                and (CASE WHEN (ps.end_date - ps.start_date) = 0
                            THEN 1
                          ELSE (ps.end_date - ps.start_date)
                     END) <> ps.quantity
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 108) = 0
    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])

    return set_sanctions(services, 108)


@howlong
def underpay_wrong_service_after_death(register_element):
    """
        Снятие услуги оказанной после смерти
    """
    query = """
        SELECT distinct ps.id_pk
        FROM medical_register mr
        JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
        JOIN medical_service ms
              ON ms.id_pk = ps.code_fk
        JOIN patient p
              ON p.id_pk = mrr.patient_fk
        join uploading_person up ON up.person_unique_id = p.person_unique_id
        WHERE mr.is_active
            and mr.year = %s
            and mr.period = %s
            and mr.organization_code = %s
            and up.deathdate is not null
            and up.deathdate < ps.start_date
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 56) = 0
    """
    services = list(ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']]))

    if len(services) > 0:
        print 'after_death', len(services)

    return set_sanctions(services, 56)


def check_service_ksg(register_element):
    """
    Проверяет соответствие КСГ коду услуги
    """

    query = '''
            select distinct ps.id_pk
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                join medical_service ms ON ms.id_pk = ps.code_fk
                join ksg ON ksg.code::VARCHAR = pe.ksg_smo AND ksg.start_date = '2017-01-01'
                            AND ksg.term_fk = pe.term_fk
                left join ksg_payment service_check ON service_check.service_code_fk = ps.code_fk
                left join ksg_payment ksg_check ON ksg_check.ksg_fk = ksg.id_pk
            WHERE mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and pe.term_fk in (1, 2)
                and ((service_check is not null and not exists (
                     select 1 from ksg_payment where ksg_fk = ksg.id_pk
                )) or (ksg_check is not null and not exists (
                     select 1 from ksg_payment where service_code_fk = ps.code_fk
                )))
                and (ms.group_fk <> 27 or ms.group_fk is null)
                and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                     and error_fk = 101) = 0
    '''

    services = ProvidedService.objects.raw(query, [register_element['year'], register_element['period'],
                                                   register_element['organization_code']])

    set_sanctions(services, 101)


def check_second_service_in_event(register_element):
    """
    Проверка на наличичие второй услуги с деньгами в случаях дневного и круглосуточного стационаров
    """

    query = '''
            select ps.id_pk from (
                select pe.id_pk AS event_id, count(distinct ps.id_pk)
                from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                join medical_service ms ON ms.id_pk = ps.code_fk
                WHERE mr.is_active
                    and mr.year = %s
                    and mr.period = %s
                    and mr.organization_code = %s
                    and pe.term_fk in (1, 2)
                    and ps.tariff > 0
                    and (ms.group_fk not in (3, 5, 42) or ms.group_fk is null)
                group by event_id
                having count(distinct ps.id_pk) > 1
            ) AS T
            join provided_service ps ON ps.event_fk = T.event_id
            where (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                   and error_fk = 78) = 0
    '''

    services = ProvidedService.objects.raw(query, [register_element['year'], register_element['period'],
                                                   register_element['organization_code']])

    set_sanctions(services, 78)


def check_pathology_pregnant_women(register_element):
    """
    Проверка на соответствие кода отделения патологии беременных коду услуги патология беременных
    """

    query = '''
            select ps.id_pk
                from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                join medical_service ms ON ms.id_pk = ps.code_fk
                WHERE mr.is_active
                    and mr.year = %s
                    and mr.period = %s
                    and mr.organization_code = %s
                    and pe.term_fk = 1
                    and (CASE when pe.division_fk in (29, 57) THEN ms.code not in ('098914', '198914') END  or
                         CASE when ms.code in ('098914', '198914') THEN pe.division_fk not in (29, 57) END )
                    and (ms.group_fk not in (27) or ms.group_fk is null)
                    and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                       and error_fk = 110) = 0
        '''

    services = ProvidedService.objects.raw(query, [register_element['year'], register_element['period'],
                                                   register_element['organization_code']])

    set_sanctions(services, 110)


@howlong
def underpay_wrong_person_in_other_company(register_element):
    """
        Снятие услуги оказаной лицу, застрахованному в другой страховой кампании
    """
    query = """
        SELECT distinct ps.id_pk
        FROM medical_register mr
        JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
        JOIN medical_service ms
              ON ms.id_pk = ps.code_fk
        JOIN patient p
              ON p.id_pk = mrr.patient_fk
        join uploading_policy u_pol2 ON u_pol2.id_pk = (
              select u_pol.id_pk
              from uploading_person up
              join uploading_policy u_pol ON u_pol.uploading_person_fk = up.id_pk
              where up.person_unique_id = p.person_unique_id
              order by u_pol.stop_date desc nulls first
              limit 1
        )
        WHERE mr.is_active
              and mr.year = %s
              and mr.period = %s
              and mr.organization_code = %s
              and ((u_pol2.stop_date < ps.start_date and u_pol2.stop_reason in (1, 3, 4)))
              and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 53) = 0
    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])
    return set_sanctions(services, 53)


@howlong
def underpay_wrong_very_old_policy(register_element):
    """
        Снятие услуги по полису погашенному раньше 2011 года
    """
    query = """
        SELECT distinct ps.id_pk, mr.organization_code
        FROM medical_register mr
        JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
        JOIN medical_service ms
              ON ms.id_pk = ps.code_fk
        JOIN patient p
              ON p.id_pk = mrr.patient_fk
        join uploading_policy u_pol2 ON u_pol2.id_pk = (
              select u_pol.id_pk
              from uploading_person up
              join uploading_policy u_pol ON u_pol.uploading_person_fk = up.id_pk
              where up.person_unique_id = p.person_unique_id
              order by u_pol.stop_date desc nulls first
              limit 1
        )
        WHERE mr.is_active
              and mr.year = %s
              and mr.period = %s
              and mr.organization_code = %s
              and u_pol2.stop_date is not null
              and u_pol2.stop_date < '2011-01-01'
              and u_pol2.type_fk = 1
              and u_pol2.stop_date < ps.start_date
              and (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 54) = 0
    """
    services = ProvidedService.objects.raw(
        query, [register_element['year'], register_element['period'],
                register_element['organization_code']])
    return set_sanctions(services, 54)


def check_so_fucking_fond(register_element):
    """
    Услуги, оказанные ООО Лабостом  пациентам прикреплённым к МО г. Благовещенска снимаются с оплаты
    и услуги оказанные ООО Здоровье пациентам прикреплённых к МО г. Белогорска и Свободненская РЖД снимаются с оплаты
    """

    query = '''
         select
            distinct ps.id_pk
            from medical_register mr
            JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                  ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                  ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
                  ON mo.id_pk = ps.organization_fk
            JOIN medical_service ms
                  ON ms.id_pk = ps.code_fk
            join patient p ON p.id_pk = mrr.patient_fk
            where mr.is_active
                  and mr.year = %s
                  and mr.period = %s
                  and mr.organization_code = %s
                  and pe.term_fk = 3
                  and (ms.reason_fk <> 5 or ms.reason_fk is null)
                  and CASE WHEN mr.organization_code in ('280120') THEN p.attachment_code in (select code from medical_organization where region_fk = 112495)
                           WHEN mr.organization_code in ('280110') THEN p.attachment_code in (select code from medical_organization where region_fk = 112587)
                      END
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                   and error_fk = 31 ) = 0
        '''
    services = ProvidedService.objects.raw(query, [register_element['year'], register_element['period'],
                                                   register_element['organization_code']])

    set_sanctions(services, 31)


@howlong
def check_cross_date(register_element):
    """
    Пересечение дней в отделения с учётом предыдущих периодов
    """

    query = '''
        select distinct ps.id_pk, min(T.id_pk) AS service2_id, min(T.id_pk) AS error_comment
        FROM provided_service ps
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record mrr
                on pe.record_fk = mrr.id_pk
            join medical_register mr
                on mrr.register_fk = mr.id_pk
            join medical_service ms
                on ms.id_pk = ps.code_fk
            join patient p ON p.id_pk = mrr.patient_fk
            JOIN (
                select mrr1.patient_fk, ps1.start_date, ps1.end_date, ps1.id_pk, p1.person_unique_id,
                       mr1.organization_code, mr1.period, p1.birthdate, p1.newborn_code
                from provided_service ps1
                    JOIN medical_service ms1
                        on ps1.code_fk = ms1.id_pk
                    join provided_event pe1
                        on ps1.event_fk = pe1.id_pk
                    join medical_register_record mrr1
                        on pe1.record_fk = mrr1.id_pk
                    join medical_register mr1
                        on mrr1.register_fk = mr1.id_pk
                    join patient p1 ON p1.id_pk = mrr1.patient_fk
                    where mr1.is_active
                          and format('%%s-%%s-01', mr1.year, mr1.period)::DATE <= format('%%s-%%s-01', %(year)s, %(period)s)::DATE
                          and format('%%s-%%s-01', mr1.year, mr1.period)::DATE >= format('%%s-%%s-01', %(year)s, %(period)s)::DATE - interval '4 months'
                          and mr1.organization_code = %(organization_code)s
                    and pe1.term_fk in (1, 2)
                    and ps1.payment_type_fk = 2
                    and (ms1.group_fk not in (27, 5, 3, 32, 40) or ms1.group_fk is null)

            ) as T on T.person_unique_id = p.person_unique_id and p.birthdate = T.birthdate and (
               (ps.start_date <= T.start_date and ps.end_date >= T.end_date)
                or (ps.start_date <= T.start_date and ps.end_date < T.end_date and ps.end_date > T.start_date)

                or (T.start_date <= ps.start_date and T.end_date >= ps.end_date)
                or (T.start_date <= ps.start_date and T.end_date < ps.end_date and T.end_date > ps.start_date))
                and T.id_pk != ps.id_pk and mr.organization_code = T.organization_code and p.newborn_code = T.newborn_code
                and ps.id_pk > T.id_pk

        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization_code)s
            and pe.term_fk in (1, 2)
            and (ms.group_fk not in (27, 5, 3, 32, 40) or ms.group_fk IS NULL)
            and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                   and error_fk = 82) = 0
            group by ps.id_pk
        '''

    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'], period=register_element['period'],
                    organization_code=register_element['organization_code'])))
    if len(services) > 0:
        print 'cross_date', len(services)

    return set_sanctions(services, 82)


def check_wrong_operation_dates(register_element):
    """
       Снятие услуги в дневном и круглосуточном стационаре, если период проведения операции несоответствует
       периоду лечения
    """
    query = '''
        select
            ps.id_pk
        from medical_register mr
        JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
        JOIN medical_service ms
              ON ms.id_pk = ps.code_fk
        where mr.is_active
              and mr.year = %(year)s
              and mr.period = %(period)s
              and mr.organization_code = %(organization_code)s
              and pe.term_fk in (1, 2)
              and (ms.group_fk not in (3, 5) or ms.group_fk is null)
              and ps.tariff > 0
              and EXISTS (
                  select 1 from provided_service ps1
                         join medical_service ms1 ON ps1.code_fk = ms1.id_pk
                         where ms1.group_fk = 27 and ps1.event_fk = ps.event_fk
                               and ps1.start_date not between ps.start_date and ps.end_date
                  )
              and (select count(1) from provided_service_sanction where service_fk = ps.id_pk
                   and error_fk = 111) = 0
    '''
    services = ProvidedService.objects.raw(
        query, dict(year=register_element['year'], period=register_element['period'],
                    organization_code=register_element['organization_code']))
    return set_sanctions(services, 111)


@howlong
def check_adult_examination_single_visit(register_element):
    """
    Снятие случая по диспансеризации взрослых, профосмотрам взрослых, диспансеризации детей сирот,
    комплексного обсследования в Центре здоровья, которые уже были оплачены в текущем году
    """
    query = '''
        select ps.id_pk, T1.* from (
            select distinct pe.id_pk AS event_id, min(T.event_id) AS error_comment
            FROM provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                join medical_register_record mrr
                    on pe.record_fk = mrr.id_pk
                join medical_register mr
                    on mrr.register_fk = mr.id_pk
                join medical_service ms
                    on ms.id_pk = ps.code_fk
                join patient p ON p.id_pk = mrr.patient_fk
                JOIN (
                    select pe1.id_pk AS event_id, p1.person_unique_id, ms1.group_fk
                    from provided_service ps1
                        JOIN medical_service ms1
                            on ps1.code_fk = ms1.id_pk
                        join provided_event pe1
                            on ps1.event_fk = pe1.id_pk
                        join medical_register_record mrr1
                            on pe1.record_fk = mrr1.id_pk
                        join medical_register mr1
                            on mrr1.register_fk = mr1.id_pk
                        join patient p1 ON p1.id_pk = mrr1.patient_fk
                        where mr1.is_active
                              and mr1.year = %(year)s
                              and ps1.payment_type_fk = 2
                              and (ms1.group_fk in (7, 9, 25, 26) or ms1.code in ('001038', '101038'))
                ) as T on T.person_unique_id = p.person_unique_id and ms.group_fk = T.group_fk
                     and pe.id_pk > T.event_id
            where mr.is_active
                and mr.year = %(year)s
                and mr.period = %(period)s
                and mr.organization_code = %(organization_code)s
                and (ms.group_fk in (7, 9, 25, 26, 12, 13) or ms.code in ('001038', '101038'))
                group by pe.id_pk
        ) AS T1
        join provided_service ps ON ps.event_fk = T1.event_id
        where (select count(1) from provided_service_sanction where service_fk = ps.id_pk and error_fk = 92) = 0
    '''

    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'], period=register_element['period'],
                    organization_code=register_element['organization_code'])))
    if len(services) > 0:
        print 'adult_exam_single', len(services)

    return set_sanctions(services, 92)
