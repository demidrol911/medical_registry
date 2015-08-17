#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from main.funcs import howlong
from main.models import ProvidedService, MedicalRegister, \
    ProvidedServiceCoefficient, Sanction

from mek.checks import set_sanction
from mek import checks

from datetime import datetime

import re


def get_register_element():
    register_element = MedicalRegister.objects.filter(
        is_active=True, year='2015', status_id__in=(1, 5, 500),
    ) \
        .values('organization_code',
                'year',
                'period',
                'status') \
        .distinct().first()
    return register_element


STATUS_WORKING = 11
STATUS_MEK = 3
STATUS_AFTER_EXPERTS = 5
STATUS_FINISHED = 8


def set_status(register_element, status_code):
    MedicalRegister.objects.filter(
        is_active=True, year=register_element['year'],
        period=register_element['period'],
        organization_code=register_element['organization_code']) \
             .update(status=status_code)


def get_services(register_element):
    """
        Выборка всех услуг для МО
    """

    query = """
    select DISTINCT provided_service.id_pk,
        provided_service.tariff,
        provided_service.quantity,
        provided_service.payment_type_fk as payment_type_code,
        provided_service.start_date,
        provided_service.end_date,

        (select count(distinct ps2.id_pk)
                from provided_service ps2
                    join medical_service ms2
                        on ms2.id_pk = ps2.code_fk
                where ps2.event_fk = provided_event.id_pk
                    and (ms2.group_fk != 27 or ms2.group_fk is null)) 
                        AS count_services_in_event,

        medical_service.code as service_code,
        (
            select min(ps2.start_date)
            from provided_service ps2
            where ps2.event_fk = provided_event.id_pk
        ) as event_start_date,
        case
        WHEN (
                select count(ps2.id_pk)
                from provided_service ps2
                    join medical_service ms2
                        on ms2.id_pk = ps2.code_fk
                where ps2.event_fk = provided_event.id_pk
                   and (ms2.group_fk != 27 or ms2.group_fk is null)
            ) = 1
            and medical_service.reason_fk = 1
            and provided_event.term_fk=3
            and (medical_service.group_fk = 24 or medical_service.group_fk is NULL)
        THEN tariff_basic.capitation
        WHEN medical_service.group_fk = 19
            THEN COALESCE(medical_service.uet, 0)*tariff_basic.value
        ELSE
            tariff_basic.value
        END as expected_tariff,
        provided_event.term_fk as service_term,
        medical_service.examination_special as service_examination_special,
        medical_service.group_fk as service_group,
        medical_service.subgroup_fk as service_subgroup,
        medical_service.examination_group as service_examination_group,
        medical_service.tariff_profile_fk as service_tariff_profile,
        medical_service.reason_fk as reason_code,
        medical_service.vmp_group,
        provided_event.examination_result_fk as examination_result,
        COALESCE(
                (
                    select tariff_nkd.value
                    from tariff_nkd
                    where start_date = (
                        select max(start_date)
                        from tariff_nkd
                        where start_date <= greatest('2015-01-01'::DATE, provided_service.end_date) and start_date >= '2015-01-01'::DATE
                            and profile_fk = medical_service.tariff_profile_fk
                            and is_children_profile = provided_service.is_children_profile
                            and "level" = department.level
                    ) and profile_fk = medical_service.tariff_profile_fk
                        and is_children_profile = provided_service.is_children_profile
                        and (( provided_event.term_fk = 1 and "level" = department.level)
                            or (provided_event.term_fk = 2)
                        )
                    order by start_date DESC
                    limit 1
                ), 1
        ) as nkd,
        case when medical_service.tariff_profile_fk IN (12) and medical_register.organization_code in ('280068', '280012', '280059')
        THEN (
                case when medical_organization.regional_coefficient = 1.6 then 34661
                when medical_organization.regional_coefficient = 1.7 then 36827
                WHEN medical_organization.regional_coefficient = 1.8 THEN 38994
                END
        ) else 0 end as alternate_tariff,
        medical_organization.is_agma_cathedra,
        medical_organization.level as level,
        patient.insurance_policy_fk as patient_policy,
        patient.birthdate as patient_birthdate,
        person.deathdate as person_deathdate,
        insurance_policy.stop_date as policy_stop_date,
        operation.reason_stop_fk as stop_reason,
        insurance_policy.type_fk as policy_type,
        medical_register.organization_code,
        provided_event.comment as event_comment,
        provided_service.comment as service_comment,
        medical_register_record.is_corrected as record_is_corrected,
        CASE medical_service.group_fk
        when 19 THEN
            (
                select 1
                from provided_service inner_ps
                    join medical_service inner_ms
                        on inner_ps.code_fk = inner_ms.id_pk
                where inner_ps.event_fk = provided_event.id_pk
                    and inner_ms.group_fk = 19 and inner_ms.subgroup_fk = 17
                    and inner_ps.end_date = provided_service.end_date
            )
        ELSE
            NULL
        END as coefficient_4,
        examination_tariff.value as examination_tariff,
        medical_register.type as register_type,
        COALESCE(
            (
                select "value"
                from hitech_service_nkd
                where start_date = (select max(start_date) from hitech_service_nkd where start_date <= provided_service.end_date)
                    and vmp_group = medical_service.vmp_group
                order by start_date DESC
                limit 1
            ), 1
        ) as vmp_nkd,
        provided_event.end_date as event_end_date

    from
        provided_service
        join provided_event
            on provided_event.id_pk = provided_service.event_fk
        join medical_register_record
            on medical_register_record.id_pk = provided_event.record_fk
        join patient
            on patient.id_pk = medical_register_record.patient_fk
        left join insurance_policy
            on patient.insurance_policy_fk = insurance_policy.version_id_pk
        left join person
            on person.version_id_pk = insurance_policy.person_fk
        left join operation
            on operation.insurance_policy_fk = insurance_policy.version_id_pk
                and operation.id_pk = (
                    select op.id_pk
                    from operation op
                        join operation_status os
                            on op.id_pk = os.operation_fk
                    where op.insurance_policy_fk = insurance_policy.version_id_pk
                        and os.timestamp = (
                            select min(timestamp)
                            from operation_status
                            where operation_status.operation_fk = op.id_pk)
                    order by timestamp desc limit 1)
        join medical_register
            on medical_register_record.register_fk = medical_register.id_pk
        JOIN medical_service
            on medical_service.id_pk = provided_service.code_fk
        join medical_organization
            on medical_organization.code = medical_register.organization_code
                and medical_organization.parent_fk is null
        JOIN medical_organization department
            on department.id_pk = provided_service.department_fk
        LEFT join tariff_basic
            on tariff_basic.service_fk = provided_service.code_fk
                and tariff_basic.group_fk = department.tariff_group_fk
                and tariff_basic.start_date =
                GREATEST(
                    (select max(start_date)
                     from tariff_basic
                     where start_date <= provided_service.end_date
                     and group_fk = department.tariff_group_fk
                     and service_fk = provided_service.code_fk),
                    (CASE WHEN (medical_service.tariff_profile_fk = 107
                               and medical_organization.code = '280005')
                               or medical_service.code = '001203'
                               or medical_service.tariff_profile_fk in (
                                                   268, 269,
                                                   235, 236, 237)
                        then '2015-03-01' ELSE '2015-01-01' END) :: DATE
                )

        LEFT JOIN examination_tariff
            on medical_register.type = 3
                and examination_tariff.service_fk = provided_service.code_fk
                and examination_tariff.age = EXTRACT(year from provided_event.end_date) - extract(year from patient.birthdate)
                and examination_tariff.gender_fk = patient.gender_fk
                and examination_tariff.regional_coefficient = medical_organization.regional_coefficient
                and examination_tariff.start_date =
                    GREATEST(
                        (select max(start_date)
                         from examination_tariff
                         where start_date <= provided_event.end_date
                         and service_fk = provided_service.code_fk),
                         '2015-06-01'
                    )
    where medical_register.is_active
        and medical_register.year = %(year)s
        and medical_register.period = %(period)s
        and medical_register.organization_code = %(organization_code)s
    """

    if register_element['status'] in (5, 500):
        query += ' and provided_service.payment_type_fk is NULL'

    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization_code=register_element[
                        'organization_code'])))
    print 'total services: ', len(services)
    return services


def identify_patient(register_element):
    """
        Иденитификация пациентов по фио, полису, снилс, паспорту.
        В различных вариациях
    """
    query1 = """
        update patient set insurance_policy_fk = T.policy_id from (
        select DISTINCT p1.id_pk as patient_id, (
            select max(version_id_pk)
            from insurance_policy
            where id = (
                select insurance_policy.id
                from patient p2
                    JOIN insurance_policy
                        on version_id_pk = (
                            CASE
                            when char_length(p1.insurance_policy_number) <= 6 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        series = p2.insurance_policy_series
                                        and number = trim(leading '0' from p2.insurance_policy_number)
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                ))
                            when char_length(p1.insurance_policy_number) between 7 and 8 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        series = p2.insurance_policy_series
                                        and number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                ))
                            when char_length(p1.insurance_policy_number) = 9 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                ))
                            when char_length(p1.insurance_policy_number) = 16 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select insurance_policy.id from insurance_policy
                                        join person
                                            on insurance_policy.person_fk = person.version_id_pk
                                                and (
                                                    (person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name
                                                        and person.birthdate = p2.birthdate)
                                                    or

                                                    ((
                                                        (person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name)
                                                        or (person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        ) or (person.last_name = p2.last_name
                                                        and person.middle_name = p2.middle_name)
                                                    ) and person.birthdate = p2.birthdate)
                                                    or (
                                                        person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name
                                                    ) or (
                                                        regexp_replace(regexp_replace((person.last_name || person.first_name || person.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g') = regexp_replace(regexp_replace((p2.last_name || p2.first_name || p2.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g')
                                                    )
                                                )

                                    where
                                        enp = p2.insurance_policy_number
                                    order by stop_date desc NULLS FIRST
                                    LIMIT 1
                                ))
                            else
                                NULL
                            end
                        )
                    join person
                        on insurance_policy.person_fk = person.version_id_pk
                            and (
                                (
                                    (
                                        p2.first_name = person.first_name
                                        or p2.middle_name = person.middle_name
                                        or p2.last_name = person.last_name
                                    ) and p2.birthdate = person.birthdate
                                ) or (
                                    p2.first_name = person.first_name
                                    and p2.middle_name = person.middle_name
                                ) or (p2.snils = person.snils)
                            )
                where p1.id_pk = p2.id_pk
                order by insurance_policy.version_id_pk DESC
                limit 1
            ) and is_active
        ) as policy_id
        from medical_register_record
        join medical_register mr1
            on medical_register_record.register_fk = mr1.id_pk
        JOIN patient p1
            on medical_register_record.patient_fk = p1.id_pk
        where mr1.is_active
            and mr1.year = %s
            and mr1.period = %s
            and mr1.organization_code = %s
            and p1.insurance_policy_fk is null) as T
        where id_pk = T.patient_id
    """

    query2 = """
        update patient set insurance_policy_fk = T.policy_id from (
        select DISTINCT p1.id_pk as patient_id,
            (
                select version_id_pk
                from insurance_policy
                where id = (
                    select insurance_policy.id
                    from patient p2
                        JOIN insurance_policy
                            on version_id_pk = (
                                CASE
                                when char_length(p1.insurance_policy_number) <= 8 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            series = p2.insurance_policy_series
                                            and number = p2.insurance_policy_number
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))
                                when char_length(p1.insurance_policy_number) = 9 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            number = p2.insurance_policy_number
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))
                                when char_length(p1.insurance_policy_number) = 16 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            enp = p2.insurance_policy_number
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))
                                else
                                    NULL
                                end
                            )
                    where p1.id_pk = p2.id_pk
                    order by insurance_policy.version_id_pk DESC
                    limit 1
                ) and is_active
            ) as policy_id
        from medical_register_record
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN patient p1
                on medical_register_record.patient_fk = p1.id_pk
        where mr1.is_active
            and mr1.year = %s
            and mr1.period = %s
            and mr1.organization_code = %s
            and p1.insurance_policy_fk is null
            and p1.newborn_code != '0'
            ) as T
        where id_pk = T.patient_id
    """

    query3 = """
        update patient set insurance_policy_fk = T.policy_id from (
            select DISTINCT p2.id_pk as patient_id,
                insurance_policy.version_id_pk as policy_id
            from patient p2
                join person_id
                    on person_id.id = (
                        select id from (
                            select person_id.id, stop_date
                            from person_id
                                join person
                                    on person.version_id_pk = person_id.person_fk
                                join insurance_policy
                                    on insurance_policy.person_fk = person.version_id_pk
                            where translate(upper(regexp_replace(person_id.series, '[ -/\\_]', '', 'g')), 'IOT', '1ОТ') = translate(upper(regexp_replace(p2.person_id_series, '[ -/\\_]', '', 'g')), 'IOT', '1ОТ')
                                and translate(upper(regexp_replace(person_id.number, '[ -/\\_]', '', 'g')), 'IOT', '1ОТ') = translate(upper(regexp_replace(p2.person_id_number, '[ -/\\_]', '', 'g')), 'IOT', '1ОТ')
                            order by insurance_policy.stop_date desc nulls first
                            limit 1
                        ) as T
                    ) and person_id.is_active

                JOIN person
                    ON person.version_id_pk = (
                        select max(version_id_pk)
                        from person
                        where id = (
                            select id from (
                            select DISTINCT person.id, stop_date
                            from person
                                join insurance_policy
                                    on person.version_id_pk = insurance_policy.person_fk
                            where replace(last_name, 'Ё', 'Е') = replace(p2.last_name, 'Ё', 'Е')
                                and replace(first_name, 'Ё', 'Е') = replace(p2.first_name, 'Ё', 'Е')
                                and replace(middle_name, 'Ё', 'Е') = replace(p2.middle_name, 'Ё', 'Е')
                                and birthdate = p2.birthdate
                            ORDER BY stop_date DESC NULLS FIRST
                            limit 1) as T
                        )
                    )
                join insurance_policy
                    on person.version_id_pk = insurance_policy.person_fk
                        and insurance_policy.is_active
                JOIN medical_register_record
                    on medical_register_record.patient_fk = p2.id_pk
                JOIN medical_register
                    ON medical_register.id_pk = medical_register_record.register_fk
            where medical_register.is_active
                and medical_register.year = %s
                and medical_register.period = %s
                and medical_register.organization_code = %s
                and p2.insurance_policy_fk is null
        ) as T where id_pk = T.patient_id
    """

    query4 = """
        update patient set insurance_policy_fk = T.policy_id from (
        select DISTINCT p2.id_pk as patient_id,
            insurance_policy.version_id_pk as policy_id
        from patient p2
            JOIN person
                ON person.version_id_pk = (
                    select max(version_id_pk)
                    from person
                    where id = (
                        select id from (
                        select DISTINCT person.id, stop_date
                        from person
                            join insurance_policy
                                on person.version_id_pk = insurance_policy.person_fk
                        where replace(first_name, 'Ё', 'Е') = replace(p2.first_name, 'Ё', 'Е')
                            and replace(middle_name, 'Ё', 'Е') = replace(p2.middle_name, 'Ё', 'Е')
                            and birthdate = p2.birthdate
                            and regexp_replace(person.snils, '[ -/\\_]', '', 'g') = regexp_replace(p2.snils, '[ -/\\_]', '', 'g')
                        ORDER BY stop_date DESC NULLS FIRST
                        limit 1) as T
                    )
                )
            join insurance_policy
                on person.version_id_pk = insurance_policy.person_fk
                    and insurance_policy.is_active
            JOIN medical_register_record
                on medical_register_record.patient_fk = p2.id_pk
            JOIN medical_register
                ON medical_register.id_pk = medical_register_record.register_fk
        where medical_register.is_active
            and medical_register.year = %s
            and medical_register.period = %s
            and medical_register.organization_code = %s
            and p2.insurance_policy_fk is null
        ) as T where id_pk = T.patient_id
    """
    cursor = connection.cursor()
    print u'идентификация по фио, снилс и полису'
    cursor.execute(query1, [register_element['year'],
                            register_element['period'],
                            register_element['organization_code']])
    transaction.commit()
    print u'идентификация новорожденных'
    cursor.execute(query2, [register_element['year'],
                            register_element['period'],
                            register_element['organization_code']])
    transaction.commit()
    print u'идентификация по паспорту'
    cursor.execute(query3, [register_element['year'],
                            register_element['period'],
                            register_element['organization_code']])
    transaction.commit()
    print u'идентификация по СИНЛС'
    cursor.execute(query4, [register_element['year'],
                            register_element['period'],
                            register_element['organization_code']])
    transaction.commit()
    cursor.close()


def update_patient_attachment_code(register_element):
    query = """
        update patient set attachment_code = T.code
        from (
        SELECT DISTINCT p.id_pk, att_org.code
        FROM medical_register_record mrr
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN medical_register mr
                ON mrr.register_fk = mr.id_pk
            JOIN insurance_policy i
                ON p.insurance_policy_fk = i.version_id_pk
            JOIN person
                ON person.version_id_pk = (
                    SELECT version_id_pk
                    FROM person WHERE id = (
                        SELECT id FROM person
                        WHERE version_id_pk = i.person_fk) AND is_active)
            LEFT JOIN attachment
              ON attachment.id_pk = (
                  SELECT MAX(id_pk)
                  FROM attachment
                  WHERE person_fk = person.version_id_pk AND status_fk = 1
                     AND attachment.date <= (format('%%s-%%s-%%s', mr.year, mr.period, '01')::DATE) AND attachment.is_active)
            LEFT JOIN medical_organization att_org
              ON (att_org.id_pk = attachment.medical_organization_fk
                  AND att_org.parent_fk IS NULL)
                  OR att_org.id_pk = (
                     SELECT parent_fk FROM medical_organization
                     WHERE id_pk = attachment.medical_organization_fk
                  )
        WHERE mr.is_active
         AND mr.year = %(year)s
         AND mr.period = %(period)s
         and mr.organization_code = %(organization)s
         ) as T
        Where T.id_pk = patient.id_pk
    """

    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


def update_payment_kind(register_element):
    query = """
        update provided_service set payment_kind_fk = T.payment_kind_code
        from (
        select distinct ps1.id_pk service_pk, T1.pk, ps1.payment_type_fk,
            medical_service.code, ps1.end_date, T1.end_date, T1.period,
            case provided_event.term_fk
            when 3 then
                CASE
                    ((medical_service.group_fk = 24 and medical_service.reason_fk in (1, 2, 3, 8) and provided_event.term_fk=3)
                      or (((select count(ps2.id_pk)
                              from provided_service ps2
                              join medical_service ms2 on ms2.id_pk = ps2.code_fk
                              where ps2.event_fk = ps1.event_fk and
                              (ms2.group_fk != 27 or ms2.group_fk is null)) = 1
                           and medical_service.reason_fk = 1
                           and medical_service.group_fk is NULL and provided_event.term_fk=3)
                           and ps1.department_fk NOT IN (
                                90,
                                91,
                                92,
                                111,
                                115,
                                123,
                                124,
                                134))
                    )
                    AND ps1.department_fk NOT IN (15, 88, 89)
                when TRUE THEN
                    CASE p1.attachment_code = mr1.organization_code -- если пациент прикреплён щас к МО
                    when true THEN -- прикреплён
                        CASE
                        when T1.pk is not NULL
                            and T1.attachment_code = mr1.organization_code -- и был прикреплён тогда
                        THEN 2
                        when T1.pk is not NULL
                            and T1.attachment_code != mr1.organization_code -- и не был прикреплён тогда
                        THEN 3

                        ELSE 2
                        END
                    else -- не приреплён
                        CASE
                        when T1.pk is not NULL
                            and T1.attachment_code = mr1.organization_code
                        THEN 2
                        else 1
                        END
                    END
                ELSE
                    1
                END
            when 4 then 2
            else 1
            END as payment_kind_code
        from provided_service ps1
            join medical_service
                On ps1.code_fk = medical_service.id_pk
            join provided_event
                on ps1.event_fk = provided_event.id_pk
            join medical_register_record
                on provided_event.record_fk = medical_register_record.id_pk
            join medical_register mr1
                on medical_register_record.register_fk = mr1.id_pk
            JOIN patient p1
                on medical_register_record.patient_fk = p1.id_pk
            left join insurance_policy i1
                on i1.version_id_pk = p1.insurance_policy_fk
            LEFT JOIN (
                select ps.id_pk as pk, i.id as policy, ps.code_fk as code, ps.end_date,
                    ps.basic_disease_fk as disease, ps.worker_code, mr.year, mr.period,
                    p.attachment_code
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
                    and format('%%s-%%s-%%s', mr.year, mr.period, '01')::DATE between format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE - interval '4 months' and format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE - interval '1 months'
                    and ps.payment_type_fk = 3
            ) as T1 on i1.id = T1.policy and ps1.code_fk = T1.code
                and ps1.end_date = T1.end_date and ps1.basic_disease_fk = T1.disease
                and ps1.worker_code = T1.worker_code
        where mr1.is_active
            and mr1.year = %(year)s
            and mr1.period = %(period)s
            and mr1.organization_code = %(organization)s

        ORDER BY payment_kind_code, T1.pk) as T
        where provided_service.id_pk = T.service_pk
    """

    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


def update_wrong_date(register_element):
    query1 = '''
             UPDATE
                 provided_service
             SET start_date = '1900-01-01'
             WHERE id_pk in (
                 SELECT
                     ps.id_pk
                 FROM medical_register mr
                     JOIN medical_register_record mrr
                        ON mr.id_pk = mrr.register_fk
                     JOIN provided_event pe
                        ON mrr.id_pk = pe.record_fk
                     JOIN provided_service ps
                        ON ps.event_fk = pe.id_pk
                 WHERE mr.is_active
                       AND mr.year = %(year)s
                       AND mr.period = %(period)s
                       AND mr.organization_code = %(organization)s
                       AND ps.start_date < '1900-01-01'
             )
             '''

    query2 = '''
             UPDATE
                 provided_service
             SET end_date = '1900-01-01'
             WHERE id_pk in (
                 SELECT
                     ps.id_pk
                 FROM medical_register mr
                     JOIN medical_register_record mrr
                        ON mr.id_pk = mrr.register_fk
                     JOIN provided_event pe
                        ON mrr.id_pk = pe.record_fk
                     JOIN provided_service ps
                        ON ps.event_fk = pe.id_pk
                 WHERE mr.is_active
                       AND mr.year = %(year)s
                       AND mr.period = %(period)s
                       AND mr.organization_code = %(organization)s
                       AND ps.end_date < '1900-01-01'
             )
             '''

    cursor = connection.cursor()
    cursor.execute(query1, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()

    cursor = connection.cursor()
    cursor.execute(query2, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


@howlong
def calculate_tariff(register_element):
    min_date_for_stopped_policy = datetime.strptime('2011-01-01', '%Y-%m-%d').date()
    with transaction.atomic():
        for row, service in enumerate(get_services(register_element)):
            payment_type = service.payment_type_code
            if row % 1000 == 0:
                print row

            if not payment_type:

                if not service.patient_policy:
                    set_sanction(service, 54)
                    payment_type = 3

                elif service.person_deathdate \
                        and service.person_deathdate < service.start_date:
                    set_sanction(service, 56)
                    payment_type = 3

                elif service.policy_stop_date:
                    if service.policy_stop_date < service.start_date \
                            and service.stop_reason in (1, 3, 4):
                        set_sanction(service, 53)
                        payment_type = 3

                    if service.policy_type == 1 and service.policy_stop_date < \
                            min_date_for_stopped_policy:
                        set_sanction(service, 54)
                        payment_type = 3

            payments = get_payments_sum(service)

            service.calculated_payment = payments['calculated_payment']
            service.provided_tariff = payments['provided_tariff']

            if (payments['tariff'] - float(service.tariff)) >= 0.01 or \
                    (payments['tariff'] - float(service.tariff)) <= -0.01:
                set_sanction(service, 61)
                payment_type = 3
            else:
                service.accepted_payment = payments['accepted_payment']
                service.invoiced_payment = payments['accepted_payment']

                if not payment_type:
                    service.payment_type_id = 2
                    payment_type = 2

            service.save()


SERVICE_COMMENT_PATTERN = re.compile(r'^(?P<endovideosurgery>[0-1]?)(?:[0-1]?)'
                                     r'(?:[0-1]?)(?:[0-1]?)'
                                     r'(?P<mobile_brigade>[0-1]?)'
                                     r'(?P<single_visit>[0-1]?)'
                                     r'(?P<curation_coefficient>[0-1]?)'
                                     r'(?P<full_paid_pso>[0-1]?)'
                                     r'(?P<thrombolytic_therapy>[0-1]?)'
                                     r'(?P<aood_x_ray>[0-1]?)$')
                                        # Родовспоможение в 11 разряде с 01.06.2015


def get_payments_sum(service):
    tariff = 0
    accepted_payment = 0
    comment_match = SERVICE_COMMENT_PATTERN.match(service.service_comment)
    if comment_match:
        is_endovideosurgery = comment_match.group('endovideosurgery') == '1'
        is_mobile_brigade = comment_match.group('mobile_brigade') == '1'
        is_single_visit = comment_match.group('single_visit') == '1'
        is_curation_coefficient = comment_match.group('curation_coefficient') == '1'
        is_full_paid_pso = comment_match.group('full_paid_pso') == '1'
        is_thrombolytic_therapy = comment_match.group('thrombolytic_therapy') == '1'
        is_aood_x_ray = comment_match.group('aood_x_ray') == '1'
    else:
        is_endovideosurgery = False
        is_mobile_brigade = False
        is_single_visit = False
        is_curation_coefficient = False
        is_full_paid_pso = False
        is_thrombolytic_therapy = False
        is_aood_x_ray = False

    provided_tariff = float(service.tariff)

    if service.alternate_tariff:
        tariff = float(service.alternate_tariff)
    else:
        tariff = float(service.expected_tariff or 0)

    if service.register_type == 3 and service.event_end_date >= datetime.strptime('2015-06-01', '%Y-%m-%d').date():
        tariff = float(service.examination_tariff or 0)

    term = service.service_term
    nkd = service.nkd or 1

    if service.service_group == 20:
        nkd = 1

    ### Неонатология 11 - я группа
    if service.service_group == 20 and service.vmp_group == 11:
        nkd = 70

    if service.service_group in (3, 5):
        term = 3

    if term in (1, 2):
        days = float(service.quantity)

        if term == 1:
            duration_coefficient = 70
            # КСГ 76, 77, 78
            if service.service_code in (
                    '098964', '098965', '098966',
                    '098967', '098968', '098969'):
                duration_coefficient = 50

            if is_endovideosurgery or service.service_code in ('098913', '098940'):
                duration_coefficient = 0

            if service.service_group == 20:
                duration_coefficient = 0

            if service.service_group == 2 and is_full_paid_pso:
                duration_coefficient = 0

            if (service.organization_code == '280013' and service.service_tariff_profile in (24, 30)) or \
                    (service.organization_code == '280005' and service.service_tariff_profile in (24, 67)):
                duration_coefficient = 50

        elif term == 2:
            duration_coefficient = 90

            if is_endovideosurgery:
                duration_coefficient = 50

        duration = (days / float(nkd)) * 100

        if duration < duration_coefficient:
            tariff = round(tariff / float(nkd) * float(service.quantity), 2)

        if service.service_tariff_profile == 999:
            if service.service_code != '098710':
                tariff = 0

        accepted_payment = tariff

        if term == 1:
            # Коэффициент курации
            if service.quantity >= nkd * 2 and service.service_group != 20 \
                    and is_curation_coefficient:
                accepted_payment += round(accepted_payment * 0.25, 2)
                provided_tariff += round(provided_tariff * 0.25, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=7)

            # Коэффициенты КПГ
            if service.service_tariff_profile == 36 and \
                    (service.level == 1 or service.organization_code in ('280027', '280075')):
                accepted_payment += round(accepted_payment * 0.38, 2)
                provided_tariff += round(provided_tariff * 0.38, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=8)

            if service.service_tariff_profile == 10:
                accepted_payment += round(accepted_payment * 0.34, 2)
                provided_tariff += round(provided_tariff * 0.34, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=9)

            if service.service_tariff_profile == 28 and \
                    service.organization_code == "280064":
                accepted_payment += round(accepted_payment * 0.65, 2)
                provided_tariff += round(provided_tariff * 0.65, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=10)

            if service.service_tariff_profile == 37 and \
                    service.organization_code == "280064":
                accepted_payment += round(accepted_payment * 0.8, 2)
                provided_tariff += round(provided_tariff * 0.8, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=11)

            if service.service_tariff_profile == 38 and \
                    service.organization_code == "280064":
                accepted_payment += round(accepted_payment * 0.47, 2)
                provided_tariff += round(provided_tariff * 0.47, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=12)

            if service.service_group == 2 and is_full_paid_pso:
                accepted_payment -= round(accepted_payment * 0.4, 2)
                provided_tariff -= round(provided_tariff * 0.4, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=13)

            if service.service_code in ('098901', '198901', '098912', '198912') and \
                    service.organization_code in ('280084', '280027') and \
                    is_full_paid_pso:
                accepted_payment += round(accepted_payment * 0.3, 2)
                provided_tariff += round(provided_tariff * 0.3, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=14)

            if service.service_code in ('098901', '198901', '098912', '198912') and \
                    service.organization_code in ('280084', '280027') and \
                    is_thrombolytic_therapy:
                accepted_payment += round(accepted_payment * 1, 2)
                provided_tariff += round(provided_tariff * 1, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=15)

        # Новые коффициенты по медицинской реабилитации в дневном стационаре
        if term == 2:
            if service.service_tariff_profile == 50 and \
                    service.organization_code in ("280064", "280003"):
                accepted_payment += round(accepted_payment * 0.2, 2)
                provided_tariff += round(provided_tariff * 0.2, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=16)

            if service.service_tariff_profile == 2 and \
                    service.organization_code in ("280064", "280003"):
                accepted_payment += round(accepted_payment * 0.1, 2)
                provided_tariff += round(provided_tariff * 0.1, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=17)

            if service.service_tariff_profile == 41 and \
                    service.organization_code in ("280064", "280003"):
                accepted_payment += round(accepted_payment * 0.4, 2)
                provided_tariff += round(provided_tariff * 0.4, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=18)

    elif term == 3 or term is None:
        quantity = service.quantity or 1

        single_visit_exception_group = (7, 8, 25, 26, 9, 10, 11, 12,
                                        13, 14, 15, 16)

        if service.service_group in (29, 31):
            accepted_payment = tariff
        else:
            accepted_payment = tariff * float(quantity)
            tariff *= float(quantity)

        if is_mobile_brigade and service.service_group in (7,  11, 15, 16,  12, 13,  4, 9):
            accepted_payment += round(accepted_payment * 0.07, 2)
            provided_tariff += round(provided_tariff * 0.07, 2)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=5)

        if service.coefficient_4:
            accepted_payment += round(accepted_payment * 0.2, 2)
            provided_tariff += round(provided_tariff * 0.2, 2)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=4)

        if service.organization_code == '280005' \
                and service.service_code in ('001203', '001204') \
                and service.count_services_in_event > 1:
                #and is_aood_x_ray\
            accepted_payment += round(accepted_payment * 1.9, 2)
            provided_tariff += round(provided_tariff * 1.9, 2)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=19)

    elif service.event.term_id == 4:
        quantity = service.quantity or 1
        accepted_payment = tariff * float(quantity)
        provided_tariff *= float(quantity)
    else:
        raise ValueError(u'Strange term')

    return {'tariff': round(tariff, 2),
            'calculated_payment': round(accepted_payment, 2),
            'accepted_payment': round(accepted_payment, 2),
            'provided_tariff': round(provided_tariff, 2)}


def main():
    register_element = get_register_element()

    while register_element:
        print register_element

        current_period = '%s-%s-01' % (register_element['year'],
                                       register_element['period'])
        current_period = datetime.strptime(current_period, '%Y-%m-%d').date()

        set_status(register_element, 11)

        if register_element['status'] == 1:
            ProvidedServiceCoefficient.objects.filter(
                service__event__record__register__is_active=True,
                service__event__record__register__year=register_element['year'],
                service__event__record__register__period=register_element['period'],
                service__event__record__register__organization_code=register_element['organization_code']
            ).delete()

            Sanction.objects.filter(
                service__event__record__register__is_active=True,
                service__event__record__register__year=register_element['year'],
                service__event__record__register__period=register_element['period'],
                service__event__record__register__organization_code=register_element['organization_code']
            ).delete()

            ProvidedService.objects.filter(
                event__record__register__is_active=True,
                event__record__register__year=register_element['year'],
                event__record__register__period=register_element['period'],
                event__record__register__organization_code=register_element['organization_code']
            ).update(payment_type=None)

            identify_patient(register_element)
            update_patient_attachment_code(register_element)
            update_payment_kind(register_element)
            update_wrong_date(register_element)

            checks.underpay_repeated_service(register_element)
            checks.underpay_wrong_date_service(register_element)
            checks.underpay_duplicate_services(register_element)
            checks.underpay_cross_dates_services(register_element)
            checks.underpay_disease_gender(register_element)
            checks.underpay_service_gender(register_element)
            checks.underpay_wrong_age_service(register_element)
            checks.underpay_not_paid_in_oms(register_element)
            checks.underpay_invalid_hitech_service_diseases(register_element)

            # -- эта проверка уже не нужна
            #checks.underpay_wrong_age_adult_examination(register_element)

            checks.underpay_wrong_examination_age_group(register_element)
            checks.underpay_wrong_age_examination_children_adopted(register_element)
            checks.underpay_wrong_age_examination_children_difficult(register_element)
            checks.underpay_service_term_mismatch(register_element)
            checks.underpay_service_term_kind_mismatch(register_element)
            checks.underpay_wrong_gender_examination(register_element)
            checks.underpay_incorrect_examination_events(register_element)
            checks.underpay_old_examination_services(register_element)
            checks.underpay_hitech_with_small_duration(register_element)

        print 'iterate tariff', register_element
        calculate_tariff(register_element)

        print u'stomat, outpatient, examin'
        if register_element['status'] == 500:
            checks.underpay_repeated_service(register_element)
            checks.underpay_duplicate_examination_in_current_register(register_element)
        else:
            checks.underpay_invalid_stomatology_event(register_element)
            checks.underpay_repeated_service(register_element)
            checks.underpay_invalid_outpatient_event(register_element)
            checks.underpay_examination_event(register_element)
            checks.underpay_ill_formed_children_examination(register_element)
            checks.underpay_ill_formed_adult_examination(register_element)
            checks.underpay_duplicate_examination_in_current_register(register_element)

            checks.underpay_second_phase_examination(register_element)
            checks.underpay_neurologist_first_phase_exam(register_element)
            checks.underpay_multi_division_disease_events(register_element)
            checks.underpay_multi_subgrouped_stomatology_events(register_element)
            checks.underpay_outpatient_event(register_element)
            checks.underpay_incorrect_preventive_examination_event(register_element)
            checks.underpay_repeated_preventive_examination_event(register_element)
        print Sanction.objects.filter(
            service__event__record__register__is_active=True,
            service__event__record__register__year=register_element['year'],
            service__event__record__register__period=register_element['period'],
            service__event__record__register__organization_code=register_element['organization_code']
        ).count()

        if register_element['status'] == 1:
            set_status(register_element, 3)
        elif register_element['status'] in (5, 500):
            set_status(register_element, 8)

        register_element = get_register_element()


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()
