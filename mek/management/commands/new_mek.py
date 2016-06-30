#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from main.funcs import howlong
from main.models import ProvidedService, MedicalRegister, \
    ProvidedServiceCoefficient, Sanction

from mek.checks import set_sanction
from mek import checks

from datetime import datetime
from main.logger import get_logger

logger = get_logger(__name__)


def get_register_element():
    register_element = MedicalRegister.objects.filter(
        is_active=True, year='2016', status_id__in=(1, 5, 500),
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
            with services AS (
                select DISTINCT

                        provided_service.id_pk,
                        provided_service.code_fk,
                        provided_service.tariff,
                        provided_service.quantity,
                        provided_service.is_children_profile,
                        provided_service.payment_type_fk as payment_type_code,
                        provided_service.start_date,
                        provided_service.end_date,
                        provided_service.event_fk,

                        provided_event.term_fk as service_term,

                        department.regional_coefficient  AS regional_coefficient,
                        provided_event.examination_result_fk as examination_result,
                        provided_event.ksg_smo AS ksg_smo,

                        patient.insurance_policy_fk as patient_policy,
                        patient.birthdate as patient_birthdate,
                        patient.gender_fk AS patient_gender,

                        medical_register.organization_code,
                        provided_event.comment as event_comment,
                        provided_service.comment as service_comment,
                        medical_register_record.is_corrected as record_is_corrected,

                        medical_register.type as register_type,

                        provided_event.end_date as event_end_date,

                        -- Исключение для эндоскопической хирургии в ГП1
                    CASE WHEN medical_register.organization_code = '280036'
                              AND provided_service.comment = '100000' THEN 2
                         -- Исключение для женских консультаций 1 и 2 и травматологии ГКБ
                         WHEN department.old_code in ('0121001', '0121002', '0301010')
                              and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null) THEN 2
                         WHEN provided_event.term_fk = 1 THEN department.level
                         WHEN provided_event.term_fk = 2 THEN department.day_hospital_level
                         ELSE department.level
                         END AS department_level,

                    CASE WHEN medical_register.organization_code = '280036'
                              AND provided_service.comment = '100000' THEN 2
                         -- Исключение для женских консультаций 1 и 2 и травматологии ГКБ
                         WHEN department.old_code in ('0121001', '0121002', '0301010')
                              and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null) THEN 2
                         WHEN provided_event.term_fk = 1 THEN medical_organization.level
                         WHEN provided_event.term_fk = 2 THEN medical_organization.day_hospital_level
                         ELSE medical_organization.level
                         END AS organization_level,

                        -- Исключение для эндоскопической хирургии в ГП1
                    case WHEN medical_register.organization_code = '280036'
                              AND provided_service.comment = '100000' THEN 19
                         -- Исключение для женских консультаций 1 и 2 и травматологии ГКБ
                         WHEN department.old_code in ('0121001', '0121002', '0301010')
                              and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null) THEN 19
                         WHEN provided_event.term_fk = 1 THEN department.tariff_group_fk
                         WHEN provided_event.term_fk = 2 THEN department.alternate_tariff_group_fk
                         ELSE department.tariff_group_fk
                         END AS department_tariff_group,

                    provided_event.ksg_smo in (
                         '66', '67', '68', '87', '88', '89', '90', '91', '180', '181',
                         '182', '300', '301', '302', '303', '304', '305', '306',
                         '307', '308'
                    ) and
                    ( ms.group_fk in (1, 2)
                      or ms.code in ('098995', '098996', '098997', '098606',
                                     '098607', '098608', '098609', '198611',
                                     '198612', '198613', '198614', '198615',
                                     '198995', '198996', '198997',
                                     '198616', '198617')
                    ) AS is_payment_by_ksg

                from provided_service
                join provided_event
                    on provided_event.id_pk = provided_service.event_fk
                join medical_register_record
                    on medical_register_record.id_pk = provided_event.record_fk
                join patient
                    on patient.id_pk = medical_register_record.patient_fk
                join medical_register
                    on medical_register_record.register_fk = medical_register.id_pk
                JOIN medical_organization department
                            on department.id_pk = provided_service.department_fk
                join medical_organization ON
                    medical_organization.id_pk = provided_service.organization_fk
                join medical_service ms ON ms.id_pk = provided_service.code_fk
                where medical_register.is_active
                    and medical_register.year = %(year)s
                    and medical_register.period = %(period)s
                    and medical_register.organization_code = %(organization_code)s
            )
            select
                services.id_pk,
                medical_service.code as service_code,
                medical_service.name AS service_name,
                medical_service.examination_special as service_examination_special,
                medical_service.group_fk as service_group,
                medical_service.subgroup_fk as service_subgroup,
                medical_service.examination_group as service_examination_group,
                medical_service.tariff_profile_fk as service_tariff_profile,
                medical_service.reason_fk as reason_code,
                medical_service.vmp_group,

                person.deathdate as person_deathdate,
                insurance_policy.stop_date as policy_stop_date,
                operation.reason_stop_fk as stop_reason,
                insurance_policy.type_fk as policy_type,
                services.*,

                CASE -- тарифы рассчитываются по КСГ
                    WHEN services.is_payment_by_ksg THEN tariff_ksg.value

                    -- тарифы на разовое посещение по поликлинике
                    WHEN (
                            select count(ps2.id_pk)
                            from provided_service ps2
                                join medical_service ms2
                                    on ms2.id_pk = ps2.code_fk
                            where ps2.event_fk = services.event_fk
                               and (ms2.group_fk NOT IN (27, 3, 5, 42) or ms2.group_fk is null)
                        ) = 1
                        and medical_service.reason_fk = 1
                        and services.service_term =3
                        and (medical_service.group_fk = 24 or medical_service.group_fk is NULL)
                    THEN tariff_basic.capitation

                    -- тарифы по неотложной скорой помощи по стоматологии во внерабочее время
                    WHEN
                         medical_service.group_fk = 19 AND
                        (
                            select count(inner_ps.id_pk)
                            from provided_service inner_ps
                                join medical_service inner_ms
                                    on inner_ps.code_fk = inner_ms.id_pk
                            where inner_ps.event_fk = services.event_fk
                                and inner_ms.group_fk = 19 and inner_ms.subgroup_fk = 17
                                and inner_ps.end_date = services.end_date
                        ) >= 1 THEN COALESCE(medical_service.uet, 0)*tariff_basic.capitation

                    -- тарифы по стоматологии
                    WHEN medical_service.group_fk = 19
                        THEN COALESCE(medical_service.uet, 0)*tariff_basic.value
                    -- тарифы по диспансеризации взрослых
                    WHEN medical_service.group_fk = 7
                        THEN (CASE WHEN services.end_date < (
                                      select ps1.end_date from provided_service ps1
                                      where ps1.event_fk = services.event_fk and ps1.code_fk = 8347) THEN 0
                               ELSE examination_tariff.value
                               END)

                    -- стационар 7) оплата в травматологических центрах
                    WHEN medical_service.tariff_profile_fk IN (12, 13) and services.organization_code in ('280068', '280012', '280059')
                         THEN (
                             case when services.regional_coefficient = 1.6 then 34661
                             when services.regional_coefficient = 1.7 then 36827
                             WHEN services.regional_coefficient = 1.8 THEN 38994
                             END
                         )

                    -- тариф по умолчанию
                    ELSE tariff_basic.value
                END as expected_tariff,

                CASE WHEN services.service_comment = '000000001'
                       THEN (SELECT tariff_ksg.value
                             FROM tariff_ksg
                             WHERE tariff_ksg.regional_coefficient = services.regional_coefficient
                                 AND tariff_ksg.level = services.department_level
                                 AND tariff_ksg.ksg_fk = 326
                             AND tariff_ksg.start_date= GREATEST(
                                 (SELECT max(start_date)
                                 FROM tariff_ksg
                                 WHERE start_date <= services.end_date
                                    AND "level" = services.department_level
                                    AND ksg_fk = 326
                                 ), '2016-05-01'::DATE)) * 0.6
                END AS trombolitic_therapy_tariff,

                COALESCE (CASE WHEN services.is_payment_by_ksg THEN tariff_nkd_ksg.value
                               WHEN medical_service.group_fk = 20 THEN hitech_service_nkd.value
                          ELSE tariff_nkd.value
                          END, 1) AS nkd

            FROM services
            join medical_service ON medical_service.id_pk = services.code_fk
            left join insurance_policy
                on services.patient_policy = insurance_policy.version_id_pk
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

            -- Основной тариф
            LEFT JOIN tariff_basic
                on tariff_basic.service_fk = services.code_fk
                and tariff_basic.group_fk = services.department_tariff_group
                and tariff_basic.start_date =
                    GREATEST(
                        (select max(start_date)
                         from tariff_basic
                         where start_date <= services.end_date
                         and group_fk =services.department_tariff_group
                     and service_fk = services.code_fk), '2016-01-01'::DATE)

            -- Тариф по диспансеризации взрослых (исключение)
            LEFT JOIN examination_tariff
                on services.register_type = 3
                    and examination_tariff.service_fk = services.code_fk
                    and examination_tariff.age = EXTRACT(year from services.event_end_date) - extract(year from services.patient_birthdate)
                    and examination_tariff.gender_fk = services.patient_gender
                    and examination_tariff.regional_coefficient = services.regional_coefficient
                    and examination_tariff.start_date =
                        GREATEST((select max(start_date)
                                  from examination_tariff
                                  where start_date <= services.event_end_date
                                  and service_fk = services.code_fk),
                        '2016-01-01')

            LEFT JOIN ksg ON ksg.code::VARCHAR = services.ksg_smo AND ksg.start_date = '2016-01-01'
                AND ksg.term_fk = services.service_term

            -- Тариф для услуг рассчитываемых по КСГ (исключение)
            lEFT JOIN tariff_ksg
                ON tariff_ksg.regional_coefficient = services.regional_coefficient
                    AND tariff_ksg.level = services.department_level
                    AND tariff_ksg.ksg_fk = ksg.id_pk
                    AND tariff_ksg.start_date=
                    GREATEST((select max(start_date)
                              from tariff_ksg
                              where start_date <= services.end_date
                              and "level" = services.department_level
                              AND ksg_fk = ksg.id_pk),
                    '2016-05-01'::DATE)

            -- Основной нкд
            left JOIN tariff_nkd
                ON tariff_nkd.profile_fk = medical_service.tariff_profile_fk
                    and tariff_nkd.is_children_profile = services.is_children_profile
                    and tariff_nkd."level" = services.department_level
                    and tariff_nkd.start_date = (
                           select max(start_date)
                           from tariff_nkd
                           where start_date <= greatest('2016-01-01'::DATE, services.end_date) and start_date >= '2016-01-01'::DATE
                               and profile_fk = medical_service.tariff_profile_fk
                               and is_children_profile = services.is_children_profile
                               and "level" = services.department_level
                        )
            -- нкд для ВМП (исключение)
            LEFT JOIN hitech_service_nkd
                ON hitech_service_nkd.start_date = (
                    select max(start_date)
                    from hitech_service_nkd where start_date <= services.end_date
                        and vmp_group = medical_service.vmp_group
                )

            -- нкд для услуг рассчитываемых по КСГ (исключение)
            lEFT JOIN tariff_nkd_ksg
                ON tariff_nkd_ksg.level = services.department_level
                    AND tariff_nkd_ksg.ksg_fk = ksg.id_pk
                    AND tariff_nkd_ksg.start_date= GREATEST(
                        (select max(start_date)
                         from tariff_nkd_ksg
                         where start_date <= services.end_date
                             and "level" = services.department_level
                             AND ksg_fk = ksg.id_pk
                         ), '2016-05-01'::DATE)
    """

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
                                ) or (p2.snils = person.snils
                                    and p2.first_name = person.first_name
                                    and p2.birthdate = person.birthdate)
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
    # По подушевому оплачиваются все услуги поликлиники, оказанные прикреплённому застрахованному
    # кроме профилей Травматология и ортопедия, Акушерство и гинекология в Свободненской больнице

    # По подушевому оплачивается вся скорая помощь кроме услуг тромболизиса
    query = """
        update provided_service set payment_kind_fk = T.payment_kind_code
        from (
        select distinct ps1.id_pk service_pk, T1.pk, ps1.payment_type_fk,
            medical_service.code, ps1.end_date, T1.end_date, T1.period,
            case
            when provided_event.term_fk = 3 then
                CASE
                    ((medical_service.group_fk = 24 OR medical_service.group_fk is null)
                      and medical_service.reason_fk in (1, 2, 3, 8) and provided_event.term_fk=3)
                      AND not (
                         mr1.organization_code = '280001' AND medical_service.tariff_profile_fk in (108, 93, 241)
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
            when provided_event.term_fk = 4 and medical_service.subgroup_fk not in (32, 38, 44, 50) then 2
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


def update_ksg(register_element):
    print u'Проставляем КСГ'
    # Рассчёт КСГ по стационару и дневному стационару
    ksg_general_query = """
        WITH mo_services AS (
            SELECT
                ps.id_pk AS service_id,
                pe.id_pk AS event_id,
                pe.basic_disease_fk AS disease_id,
                s_idc.id_pk AS secondary_disease_id,
                ps.code_fk AS code_id,
                age(pe.start_date, pt.birthdate) AS patient_age,
                ms.code AS s_code,
                (CASE WHEN MAX(ps.quantity) OVER (PARTITION by pe.id_pk) <= 3 THEN 1 ELSE 0 END) AS event_duration,
                pt.gender_fk AS gender,

                (SELECT COUNT(DISTINCT op.id_pk)
                 FROM provided_service op
                    JOIN medical_service ms_op
                       ON ms_op.id_pk = op.code_fk
                WHERE op.event_fk = pe.id_pk
                      AND (ms_op.code ILIKE 'A%%' or ms_op.code ILIKE 'B%%')) > 0 AS has_op_event,
                (ms.code ILIKE 'A%%' or ms.code ILIKE 'B%%') AS is_op_service,

                pe.term_fk AS service_term
            FROM provided_service ps
                JOIN provided_event pe
                   ON ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                   ON mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                   ON mr.id_pk = mrr.register_fk
                JOIN patient pt
                   ON pt.id_pk = mrr.patient_fk
                JOIN medical_service ms
                   ON ms.id_pk = ps.code_fk
                LEFT JOIN provided_event_concomitant_disease conc_d
                   ON conc_d.event_fk = pe.id_pk
                LEFT JOIN provided_event_complicated_disease comp_d
                   ON comp_d.event_fk = pe.id_pk
                LEFT JOIN idc s_idc
                   ON s_idc.id_pk = conc_d.disease_fk OR s_idc.id_pk = comp_d.disease_fk
            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND mr.organization_code = %(organization)s
                AND pe.term_fk in (1, 2)
        )
        UPDATE provided_event SET ksg_smo = T.ksg_code
        FROM (
            SELECT
                event_id,
                ksg_calc.coefficient AS ksg_coef,
                ksg_calc.code AS ksg_code,
                MAX(ksg_calc.coefficient) over (PARTITION by event_id) AS max_ksg_coeff
            FROM mo_services
            -- Рассчёт КСГ по диагнозу
                LEFT JOIN LATERAL (
                    SELECT
                        ksg.*, k.service_fk IS NOT NULL AND k.service_fk = code_id AS defined_by_diagnosis
                    FROM ksg
                        JOIN ksg_grouping k ON ksg.id_pk = k.ksg_fk
                            AND mo_services.disease_id = k.disease_fk
                            AND (CASE WHEN k.secondary_disease_fk IS NOT NULL
                                        THEN k.secondary_disease_fk = secondary_disease_id
                                      ELSE True
                                 END)
                            AND (CASE WHEN k.service_fk IS NOT NULL THEN  k.service_fk = code_id ELSE True END)
                            AND (CASE WHEN k.age = 1 THEN patient_age < '28 days'
                                      WHEN k.age = 2 THEN patient_age < '90 days'
                                      WHEN k.age = 3 THEN patient_age < '1 years'
                                      WHEN k.age = 4 THEN patient_age < '18 years'
                                      WHEN k.age = 5 THEN patient_age >= '18 years'
                                      ELSE TRUE
                                 END)
                            AND (CASE WHEN k.gender_fk IS NOT NULL THEN k.gender_fk = gender ELSE TRUE END)
                            AND (CASE WHEN k.duration <> 0 THEN k.duration = event_duration ELSE TRUE END)
                            AND k.start_date = '2016-01-01'
                    WHERE
                        ksg.term_fk = service_term
                    ORDER BY k.secondary_disease_fk DESC NULLS LAST, k.service_fk DESC NULLS LAST, k.age desc,
                             k.duration desc, k.gender_fk DESC NULLS LAST
                    LIMIT 1
                ) AS ksg_bydisease ON (is_op_service OR (NOT is_op_service AND NOT has_op_event))

            -- Рассчёт КСГ по услуге
                LEFT JOIN LATERAL (
                    SELECT ksg.*
                    FROM ksg
                        JOIN ksg_grouping k ON ksg.id_pk = k.ksg_fk
                            AND mo_services.code_id = k.service_fk
                            AND (CASE WHEN k.disease_fk IS NOT NULL THEN k.disease_fk = disease_id ELSE True END)
                            AND (CASE WHEN k.secondary_disease_fk IS NOT NULL
                                        THEN k.secondary_disease_fk = secondary_disease_id
                                      ELSE True
                                 END)
                            AND (CASE WHEN k.age = 1 THEN patient_age < '28 days'
                                      WHEN k.age = 2 THEN patient_age < '90 days'
                                      WHEN k.age = 3 THEN patient_age < '1 years'
                                      WHEN k.age = 4 THEN patient_age < '18 years'
                                      WHEN k.age = 5 THEN patient_age >= '18 years'
                                      ELSE TRUE
                                 END)
                            AND (CASE WHEN k.gender_fk IS NOT NULL THEN k.gender_fk = gender ELSE TRUE END)
                            AND (CASE WHEN k.duration <> 0 THEN k.duration = event_duration ELSE TRUE END)
                            AND k.start_date = '2016-01-01'
                    WHERE
                        ksg.term_fk = service_term
                    ORDER BY k.disease_fk DESC NULLS LAST, k.secondary_disease_fk DESC NULLS LAST, k.age desc,
                             k.duration desc, k.gender_fk DESC NULLS LAST
                    LIMIT 1
                ) AS ksg_byservice ON NOT ksg_bydisease.defined_by_diagnosis

            LEFT JOIN ksg ksg_calc ON (
                CASE WHEN service_term = 1 AND
                         ((ksg_byservice.code=11 AND ksg_bydisease.code=9) OR
                         (ksg_byservice.code=12 AND ksg_bydisease.code=9) OR
                         (ksg_byservice.code=11 AND ksg_bydisease.code=10) OR
                         (ksg_byservice.code=73 AND ksg_bydisease.code=18) OR
                         (ksg_byservice.code=74 AND ksg_bydisease.code=18) OR
                         (ksg_byservice.code=154 AND ksg_bydisease.code=160) OR
                         (ksg_byservice.code=281 AND ksg_bydisease.code=280) OR
                         (ksg_byservice.code=281 AND ksg_bydisease.code=188) OR
                         (ksg_byservice.code=226 AND ksg_bydisease.code=223) OR
                         (ksg_byservice.code=34 AND ksg_bydisease.code=223) OR
                         (ksg_byservice.code=237 AND ksg_bydisease.code=252) OR
                         ksg_byservice.code in (300, 301, 302, 303, 304, 305, 306, 307, 308)
                         )
                       THEN ksg_byservice.id_pk
                     WHEN COALESCE(ksg_bydisease.coefficient, 0) >= COALESCE(ksg_byservice.coefficient, 0)
                       THEN ksg_bydisease.id_pk
                     WHEN COALESCE(ksg_bydisease.coefficient, 0) < COALESCE(ksg_byservice.coefficient, 0)
                       THEN ksg_byservice.id_pk
                     ELSE NULL
                END) = ksg_calc.id_pk
        ) AS T
        WHERE T.event_id = id_pk AND T.ksg_code IS NOT NULL AND T.ksg_coef = T.max_ksg_coeff
        """

    cursor = connection.cursor()
    cursor.execute(ksg_general_query, dict(
        year=register_element['year'],
        period=register_element['period'],
        organization=register_element['organization_code']))
    transaction.commit()

    # Рассчёт КСГ по множественной травме (политравма)
    multiple_trauma_query = """
        WITH disease_grouping AS (
            SELECT
                idc.id_pk AS disease_id,
                CASE WHEN idc.idc_code IN ('S02.0', 'S02.1', 'S04.0', 'S05.7', 'S06.1', 'S06.2', 'S06.3', 'S06.4',
                                           'S06.5', 'S06.6', 'S06.7', 'S07.0', 'S07.1', 'S07.8', 'S09.0', 'S11.0',
                                           'S11.1', 'S11.2', 'S11.7', 'S15.0', 'S15.1', 'S15.2', 'S15.3', 'S15.7',
                                           'S15.8', 'S15.9', 'S17.0', 'S17.8', 'S18') THEN '_T1'     -- голова, шея

                     WHEN idc.idc_code IN ('S12.0', 'S12.9', 'S13.0', 'S13.1', 'S13.3', 'S14.0', 'S14.3', 'S22.0',
                                           'S23.0', 'S23.1', 'S24.0', 'S32.0', 'S32.1', 'S33.0', 'S33.1', 'S33.2',
                                           'S33.4', 'S34.0', 'S34.3', 'S34.4') THEN '_T2'    -- позвоночник

                     WHEN idc.idc_code IN ('S22.2', 'S22.4', 'S22.5', 'S25.0', 'S25.1', 'S25.2', 'S25.3', 'S25.4',
                                           'S25.5', 'S25.7', 'S25.8', 'S25.9', 'S26.0', 'S27.0', 'S27.1', 'S27.2',
                                           'S27.4', 'S27.5', 'S27.6', 'S27.8',
                                           'S28.0', 'S28.1') THEN '_T3'    -- грудная клетка

                     WHEN idc.idc_code IN ('S35.0', 'S35.1', 'S35.2', 'S35.3', 'S35.4', 'S35.5', 'S35.7', 'S35.8',
                                           'S35.9', 'S36.0', 'S36.1', 'S36.2', 'S36.3', 'S36.4', 'S36.5', 'S36.8',
                                           'S36.9', 'S37.0', 'S38.3') THEN '_T4'    -- живот

                     WHEN idc.idc_code IN ('S32.3', 'S32.4', 'S32.5', 'S36.6', 'S37.1', 'S37.2', 'S37.4', 'S37.5',
                                           'S37.6', 'S37.8', 'S38.0', 'S38.2') THEN '_T5'    -- таз

                     WHEN idc.idc_code IN ('S42.2', 'S42.3', 'S42.4', 'S42.8', 'S45.0', 'S45.1', 'S45.2', 'S45.7',
                                           'S45.8', 'S47' , 'S48.0', 'S48.1', 'S48.9', 'S52.7', 'S55.0', 'S55.1',
                                           'S55.7', 'S55.8', 'S57.0', 'S57.8', 'S57.9', 'S58.0', 'S58.1', 'S58.9',
                                           'S68.4', 'S71.7', 'S72.0', 'S72.1', 'S72.2', 'S72.3', 'S72.4', 'S72.7',
                                           'S75.0', 'S75.1', 'S75.2', 'S75.7', 'S75.8', 'S77.0', 'S77.1', 'S77.2',
                                           'S78.0', 'S78.1', 'S78.9', 'S79.7', 'S82.1', 'S82.2', 'S82.3', 'S82.7',
                                           'S85.0', 'S85.1', 'S85.5', 'S85.7', 'S87.0', 'S87.8', 'S88.0', 'S88.1',
                                           'S88.9', 'S95.7', 'S95.8', 'S95.9',
                                           'S97.0', 'S97.8', 'S98.0') THEN '_T6'    -- конечности

                     WHEN idc.idc_code IN ('S02.7',  'S12.7', 'S22.1', 'S27.7', 'S29.7', 'S31.7', 'S32.7', 'S36.7',
                                           'S38.1', 'S39.6', 'S39.7', 'S37.7', 'S42.7', 'S49.7', 'T01.1', 'T01.8',
                                           'T01.9', 'T02.0', 'T02.1', 'T02.2', 'T02.3', 'T02.4', 'T02.5', 'T02.6',
                                           'T02.7', 'T02.8', 'T02.9', 'T04.0', 'T04.1', 'T04.2', 'T04.3', 'T04.4',
                                           'T04.7', 'T04.8', 'T04.9', 'T05.0', 'T05.1', 'T05.2', 'T05.3', 'T05.4',
                                           'T05.5', 'T05.6', 'T05.8', 'T05.9', 'T06.0', 'T06.1', 'T06.2', 'T06.3',
                                           'T06.4', 'T06.5', 'T06.8', 'T07') THEN '_T7'    -- множественная травма

                     WHEN idc.idc_code IN ('J94.2', 'J94.8', 'J94.9', 'J93', 'J93.0', 'J93.1', 'J93.8', 'J93.9',
                                           'J96.0', 'N17', 'T79.4', 'R57.1', 'R57.8') THEN '_R' -- тяжесть случая
                     ELSE NULL
                END AS anatomical_region
            FROM idc
        )
        UPDATE provided_event SET ksg_smo = '216'
        FROM (
            SELECT
                pe.id_pk AS event_id,
                COUNT(DISTINCT CASE WHEN dg.anatomical_region != '_R' THEN dg.anatomical_region END) AS count_disease,
                COUNT(DISTINCT CASE WHEN dg.anatomical_region = '_R' THEN dg.anatomical_region END) AS has_R,
                COUNT(DISTINCT CASE WHEN dg.anatomical_region = '_T7' THEN dg.anatomical_region END) AS has_T7
            FROM provided_service ps
                JOIN provided_event pe
                   on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                   on mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                   on mr.id_pk = mrr.register_fk
                JOIN patient pt
                   ON pt.id_pk = mrr.patient_fk
                JOIN medical_service ms
                   ON ms.id_pk = ps.code_fk
                LEFT JOIN provided_event_complicated_disease pecompd
                   ON pecompd.event_fk = pe.id_pk
                LEFT JOIN provided_event_concomitant_disease peconcd
                   ON peconcd.event_fk = pe.id_pk
                JOIN disease_grouping dg
                   ON (dg.disease_id = ps.basic_disease_fk
                       OR dg.disease_id = pecompd.disease_fk
                       OR dg.disease_id = peconcd.disease_fk)
            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND mr.organization_code = %(organization)s
                AND pe.term_fk = 1
                AND dg.anatomical_region IS NOT NULL
            GROUP BY event_id) AS T
        WHERE id_pk = T.event_id AND T.has_R > 0 and T.count_disease >= (CASE WHEN T.has_T7 > 0 THEN 1 ELSE 2 END)
        """
    cursor = connection.cursor()
    cursor.execute(multiple_trauma_query, dict(
        year=register_element['year'],
        period=register_element['period'],
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


def get_payments_sum(service):
    is_endovideosurgery = (service.service_comment == '100000')
    is_curation_coefficient = (service.service_comment == '0000001')
    is_mobile_brigade = (service.service_comment == '000010')
    is_trombolitic_therapy = (service.service_comment == '000000001')
    is_mobile_stom_cab = (service.service_comment == '0000001')

    provided_tariff = float(service.tariff)

    tariff = float(service.expected_tariff or 0)
    nkd = service.nkd or 1

    # При проведении больным с ОКС в ПСО тромболитической терапии с последующим переводом в РСЦ
    if is_trombolitic_therapy:
        tariff = service.trombolitic_therapy_tariff
        nkd = 1

    term = service.service_term

    # Исключение для ФГКУ 411 ВГ МО РФ
    if service.organization_code == '280010' and service.service_tariff_profile == 25:
        tariff = 20493
    if service.organization_code == '280010' and service.service_tariff_profile in (27, 1, 5):
        tariff = 17533

    # Исключение для Ивановской
    if service.organization_code == '280007' and service.service_tariff_profile in (1, ):
        tariff = 17533

    # Исключение для Белогорской НУЗ
    if service.organization_code == '280065' and service.service_tariff_profile in (1, 27):
        if service.service_code[0] == '0':
            tariff = 17533
        elif service.service_code[0] == '1':
            tariff = 18216
    if service.organization_code == '280084' and service.service_tariff_profile in (27, ) \
        and service.department_level == 1:
        if service.service_code[0] == '0':
            tariff = 24108
        elif service.service_code[0] == '1':
            tariff = 25047

    # Исключение для Магдагачи
    if service.organization_code == '280029' and service.service_tariff_profile in (25, ):
        if service.service_code[0] == '0':
            tariff = 21774
        elif service.service_code[0] == '1':
            tariff = 26612

    if service.service_group in (3, 5):
        term = 3

    if term in (1, 2):
        days = float(service.quantity)

        if term == 1:
            duration_coefficient = 70
            # стационар 3) КСГ 88, 89, 90, 91 менее 50%
            if service.service_group in (1, 2) and service.ksg_smo in ('88', '89', '90', '91'):
                duration_coefficient = 50

            # стационар 4) эндовидеохирургия по полному тарифу
            if is_endovideosurgery:
                duration_coefficient = 0

            # стационар 8) акушерство и гинекология (койки для беременных и рожениц)
            if service.service_tariff_profile == 31:
                duration_coefficient = 0

            if service.service_group == 20:
                duration_coefficient = 0

            # новшество с 4 февраля (нигде не прописанное)
            if (service.organization_code == '280013' and service.service_tariff_profile in (24, 30)) or \
                    (service.organization_code == '280005' and service.service_tariff_profile in (24, 67)):
                duration_coefficient = 50

        elif term == 2:
            # дневной стационар 2) длительность лечения менее 90% для эндовидеохирургии менне 50%
            duration_coefficient = 90

            if is_endovideosurgery:
                duration_coefficient = 50

        duration = (days / float(nkd)) * 100

        if duration < duration_coefficient:
            tariff = round(tariff / float(nkd) * float(service.quantity), 2)

        accepted_payment = tariff

        if term == 1:
            # стационар 5) Коэффициент сложности лечения пациента КСЛП
            if service.quantity >= 30 and not (service.service_group == 20 or service.ksg_smo in (88, 89, 90, 91))\
                    and is_curation_coefficient:
                accepted_payment += round(accepted_payment * 0.25, 2)
                provided_tariff += round(provided_tariff * 0.25, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=7)

            # стационар 6) Управленческий коэффициент (КУ)
            # КПГ терапия
            if service.service_tariff_profile == 36 and \
                    (service.organization_level == 1 or service.organization_code in ('280027', '280075')):
                accepted_payment += round(accepted_payment * 0.38, 2)
                provided_tariff += round(provided_tariff * 0.38, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=8)

            # КПГ педиатрия
            if service.service_tariff_profile == 10 and service.organization_level in (1, 2):
                accepted_payment += round(accepted_payment * 0.34, 2)
                provided_tariff += round(provided_tariff * 0.34, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=9)
        if term == 2:
            # дневной стационар 3) Управленческий коэффициент (КУ)
            # КПГ медицинская реабилитация
            if service.service_tariff_profile == 282:
                accepted_payment += round(accepted_payment * 0.4, 2)
                provided_tariff += round(provided_tariff * 0.4, 2)
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=26)

    elif term == 3 or term is None:
        quantity = service.quantity or 1

        if service.service_group in (29, 31):
            accepted_payment = tariff
        else:
            accepted_payment = tariff * float(quantity)
            tariff *= float(quantity)

        # диспансеризации мобильные бригады
        if is_mobile_brigade and service.service_group in (7,  11, 15, 16,  12, 13,  4, 9):
            accepted_payment += round(accepted_payment * 0.07, 2)
            provided_tariff += round(provided_tariff * 0.07, 2)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=5)

        # мобильные стоматологические кабинеты
        if is_mobile_stom_cab and service.service_group == 19:
            accepted_payment += round(accepted_payment * 0.07, 2)
            provided_tariff += round(provided_tariff * 0.07, 2)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=27)

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
        logger.info(u'%s начала проходить МЭК', register_element['organization_code'])

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
            update_ksg(register_element)

            checks.check_rsc_pso_ksg(register_element)
            checks.underpay_repeated_service(register_element)
            checks.underpay_wrong_date_service(register_element)
            checks.underpay_duplicate_services(register_element)
            checks.underpay_cross_dates_services(register_element)
            checks.underpay_disease_gender(register_element)
            checks.underpay_service_gender(register_element)
            checks.underpay_wrong_age_service(register_element)
            checks.underpay_not_paid_in_oms(register_element)
            checks.underpay_invalid_hitech_service_diseases(register_element)
            checks.underpay_invalid_hitech_service_kind(register_element)

            checks.underpay_wrong_examination_age_group(register_element)
            checks.underpay_wrong_age_examination_children_adopted(register_element)
            checks.underpay_wrong_age_examination_children_difficult(register_element)

            checks.underpay_wrong_age_prelim_examination_children(register_element)
            checks.underpay_wrong_age_examination_adult(register_element)

            checks.underpay_service_term_mismatch(register_element)
            checks.underpay_service_term_kind_mismatch(register_element)
            checks.underpay_incorrect_examination_events(register_element)
            checks.underpay_hitech_with_small_duration(register_element)

        print 'iterate tariff', register_element
        calculate_tariff(register_element)
        checks.underpay_old_examination_services(register_element)

        print u'stomat, outpatient, examin'
        if register_element['status'] == 500:
            checks.underpay_repeated_service(register_element)
            checks.underpay_duplicate_examination_in_current_register(register_element)
        else:
            checks.underpay_invalid_stomatology_event(register_element)
            checks.underpay_repeated_service(register_element)
            checks.underpay_invalid_outpatient_event(register_element)
            checks.underpay_wrong_clinic_event(register_element)
            checks.underpay_examination_event(register_element)
            checks.underpay_ill_formed_children_examination(register_element)
            checks.underpay_ill_formed_adult_examination(register_element)
            checks.underpay_duplicate_examination_in_current_register(register_element)

            checks.underpay_second_phase_examination(register_element)
            checks.underpay_neurologist_first_phase_exam(register_element)
            checks.underpay_multi_division_disease_events(register_element)
            checks.underpay_multi_subgrouped_stomatology_events(register_element)
            checks.underpay_incorrect_preventive_examination_event(register_element)
            checks.underpay_repeated_preventive_examination_event(register_element)
            checks.underpay_adult_examination_with_double_services(register_element)
            checks.underpay_outpatient_event(register_element)
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

        logger.info(u'%s закончила проходить МЭК', register_element['organization_code'])

        register_element = get_register_element()


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()
