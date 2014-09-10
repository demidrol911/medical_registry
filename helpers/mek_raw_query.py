# -*- coding: utf-8 -*-

# Повторно поданные услуги

# Идентификация пациента, выбор активного полиса
IDENTIFY_PATIENT = """
update patient set insurance_policy_fk = T.policy_id from (
    select DISTINCT p1.id_pk as patient_id,
    (
        CASE
        when char_length(p1.insurance_policy_number) <= 7 THEN
            (
                select version_id_pk
                from insurance_policy
                where id = (
                    select insurance_policy.id
                    from patient p2
                        JOIN insurance_policy
                            on version_id_pk = (
                                select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        series = p2.insurance_policy_series
                                        and number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                )

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
            )
        when char_length(p1.insurance_policy_number) = 9 THEN
            (
                select version_id_pk from insurance_policy where id = (
                    select insurance_policy.id
                    from patient p2
                        JOIN insurance_policy
                            on version_id_pk = (
                                select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                )
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
                )  and is_active
            )
        when char_length(p1.insurance_policy_number) = 16 THEN
            (
                select version_id_pk from insurance_policy where id = (
                    select insurance_policy.id
                    from patient p2
                        JOIN insurance_policy
                            on version_id_pk = (
                                select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        enp = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                )
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
            )
        else
            NULL
        end
    ) as policy_id
from medical_register_record
    join medical_register mr1
        on medical_register_record.register_fk = mr1.id_pk
    JOIN patient p1
        on medical_register_record.patient_fk = p1.id_pk
    where mr1.id_pk = %s and p1.insurance_policy_fk is NULL
) as T
where id_pk = T.patient_id
"""

IDENTIFY_NEWBORN_PATIENT = """
update patient set insurance_policy_fk = T.policy_id from (
    select p1.id_pk as patient_id,
        (
            CASE when char_length(p1.insurance_policy_number) <= 7 THEN
                (
                    select version_id_pk
                    from insurance_policy
                    where id = (
                        select insurance_policy.id
                        from patient p2
                            JOIN insurance_policy
                                on p2.insurance_policy_series = insurance_policy.series
                                    and p2.insurance_policy_number = insurance_policy.number
                        where p1.id_pk = p2.id_pk
                        order by insurance_policy.version_id_pk DESC
                        limit 1
                    ) and is_active
                )
            when char_length(p1.insurance_policy_number) = 9 THEN
                (
                    select version_id_pk
                    from insurance_policy
                    where id = (
                        select insurance_policy.id
                        from patient p2
                            JOIN insurance_policy
                                on p2.insurance_policy_number = insurance_policy.number
                        where p1.id_pk = p2.id_pk
                        order by insurance_policy.version_id_pk DESC
                        limit 1
                    ) and is_active
                )
            when char_length(p1.insurance_policy_number) = 16 THEN
                (
                    select version_id_pk
                    from insurance_policy
                    where id = (
                        select insurance_policy.id
                        from patient p2
                        JOIN insurance_policy
                            on p2.insurance_policy_number = insurance_policy.enp
                        where p1.id_pk = p2.id_pk
                        order by insurance_policy.version_id_pk DESC
                        limit 1
                    ) and is_active
                )
            else
                NULL
            end
        ) as policy_id
    from medical_register_record
        join medical_register mr1 on medical_register_record.register_fk = mr1.id_pk
        JOIN patient p1 on medical_register_record.patient_fk = p1.id_pk
    where mr1.id_pk = %s
        and p1.newborn_code != '0'
        and p1.insurance_policy_fk is NULL
) as T
where id_pk = T.patient_id
"""

IDENTIFY_PATIENT_BY_PERSON_ID = """
update patient
set insurance_policy_fk = T.policy_id
from (
    select DISTINCT p2.id_pk as patient_id,
        insurance_policy.version_id_pk as policy_id
    from patient p2
        join person_id
            on person_id.series = regexp_replace(p2.person_id_series, '[ -/\\_]', '')
                and person_id.number = regexp_replace(p2.person_id_number, '[ -/\\_]', '')
                and person_id.is_active

        JOIN insurance_policy
            on insurance_policy.is_active
                and insurance_policy.version_id_pk = (
                    select max(version_id_pk)
                    from insurance_policy
                    where id = (
                        select insurance_policy.id
                        from insurance_policy
                            join person
                                on person.version_id_pk = insurance_policy.person_fk
                                    and person.is_active
                                    and (
                                        (
                                            person.first_name = p2.first_name
                                            and person.middle_name = p2.middle_name
                                        ) or (
                                            person.first_name = p2.first_name
                                            and person.birthdate = p2.birthdate
                                        ) or (
                                            person.middle_name = p2.middle_name
                                            and person.birthdate = p2.birthdate
                                        )
                                    )
                        where person.version_id_pk = person_id.person_fk
                        order by insurance_policy.id desc
                        limit 1
                    )
                )
        JOIN medical_register_record
            on medical_register_record.patient_fk = p2.id_pk
        JOIN medical_register
            ON medical_register.id_pk = medical_register_record.register_fk
    where medical_register.id_pk = %s
        and p2.insurance_policy_fk is NuLL
) as T
where id_pk = T.patient_id
"""

IDENTIFY_PATIENT_BY_SNILS = """
update patient
set insurance_policy_fk = T.policy_id
from (
select DISTINCT p1.id_pk as patient_id,
    p1.last_name,
    p1.first_name,
    p1.middle_name,
    (
        select version_id_pk
        from insurance_policy
        where id = (
            select insurance_policy.id
            from patient p2
                join person
                    on p2.snils = person.snils
                        and (
                               ( p2.first_name = person.first_name
                                    or p2.middle_name = person.middle_name
                                    or p2.last_name = person.last_name
                                ) and p2.birthdate = person.birthdate
                             or (
                                p2.first_name = person.first_name
                                and p2.middle_name = person.middle_name
                            )
                        )
                JOIN insurance_policy on person.version_id_pk = insurance_policy.person_fk
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
where mr1.id_pk = %s
    and p1.insurance_policy_fk is null
    ) as T
where id_pk = T.patient_id
"""

# Дубликат услуги
DOUBLED_SERVICES = """
select ps1.id_pk
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
    JOIN (
        select mr2.id_pk as mr_pk,
            p2.id_pk as p_pk, ps2.id_pk as ps_pk,
            ps2.end_date as ps_end_date,
            ps2.code_fk as ps_code,
            ps2.basic_disease_fk as ps_basic_disease,
            ps2.worker_code as ps_worker_code,
            p2.newborn_code
        from provided_service ps2
            join provided_event
                on ps2.event_fk = provided_event.id_pk
            join medical_register_record
                on provided_event.record_fk = medical_register_record.id_pk
            join medical_register mr2
                on medical_register_record.register_fk = mr2.id_pk
            JOIN patient p2
                on medical_register_record.patient_fk = p2.id_pk
    ) as T on T.mr_pk = mr1.id_pk
        and p1.id_pk = T.p_pk
        and ps1.id_pk <> T.ps_pk
        and ps1.end_date = T.ps_end_date
        and ps1.code_fk = T.ps_code
        and ps1.basic_disease_fk = T.ps_basic_disease
        and ps1.worker_code = T.ps_worker_code
        and p1.newborn_code = T.newborn_code
where mr1.is_active
    and mr1.id_pk = %s
    order by p1.id_pk, ps1.code_fk, p1.id_pk
"""

# Добавить санкции к случаям где сняты с оплаты ключевы услуги (первичный
# или итоговые приёмы
INSERT_SANCTIONS_ON_EXAMINATIONS = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, provided_service.accepted_payment, T.error_id, provided_service.id_pk
from provided_service
    join (
        select provided_event.id_pk as event_id,
            min(provided_service_sanction.error_fk) as error_id
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
            LEFT join provided_service_sanction
                on ps1.id_pk = provided_service_sanction.service_fk
        where mr1.is_active
            and mr1.id_pk = %s
            and medical_service.group_fk in (7, 9, 11, 12, 13, 14, 15, 16)
            and ps1.payment_type_fk = 3
        group BY provided_event.id_pk
    ) as T
        on provided_service.event_fk = T.event_id
where provided_service.payment_type_fk <> 3
"""

# Обновить услуги к случаям где сняты с оплаты ключевы услуги (первичный
# или итоговые приёмы
UPDATE_SANCTIONS_ON_EXAMINATIONS = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
where event_fk in (select provided_event.id_pk
from provided_service ps1
join medical_service on medical_service.id_pk = ps1.code_fk
join provided_event on ps1.event_fk = provided_event.id_pk
join medical_register_record on provided_event.record_fk = medical_register_record.id_pk
join medical_register mr1 on medical_register_record.register_fk = mr1.id_pk
JOIN patient p1 on medical_register_record.patient_fk = p1.id_pk
LEFT join provided_service_sanction on ps1.id_pk = provided_service_sanction.service_fk
where mr1.is_active
and mr1.id_pk = %s
and medical_service.group_fk in (7, 9, 11, 12, 13, 14, 15, 16)

and ps1.payment_type_fk = 3)
"""

INSERT_SANCTIONS_ON_STOMATOLOGY = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, ps1.accepted_payment, 34, ps1.id_pk
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
where mr1.is_active
    and mr1.id_pk = %s
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
                        on medical_register_record.register_fk = mr1.id_pk
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
                    on medical_register_record.register_fk = mr1.id_pk
                where pe1.id_pk = pe2.id_pk
                    and ps1.end_date = ps2.end_date
                    and medical_service.subgroup_fk is NULL
                    and medical_service.group_fk = 19
                    and ps2.payment_type_fk = 2)
        )

    )
    and ps1.payment_type_fk <> 3
"""

UPDATE_SANCTIONS_ON_STOMATOLOGY = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
where id_pk in (
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
    where mr1.is_active
        and mr1.id_pk = %s
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
                            on medical_register_record.register_fk = mr1.id_pk
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
                            on medical_register_record.register_fk = mr1.id_pk
                        where pe1.id_pk = pe2.id_pk
                            and ps1.end_date = ps2.end_date
                            and medical_service.subgroup_fk is NULL
                            and medical_service.group_fk = 19
                            and ps2.payment_type_fk = 2
                    )
                )
        )
        and ps1.payment_type_fk <> 3
    )
"""

INSERT_SANCTIONS_ON_WRONG_DISEASE_EVENT = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, provided_service.accepted_payment, 34, provided_service.id_pk
from provided_service where event_fk in (
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
    where
        medical_register.id_pk = %s
        and department.level <> 3
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
                ) = 1 and (
                    select count(1)
                    from provided_service
                        join medical_service
                            on provided_service.code_fk = medical_service.id_pk
                    where provided_service.event_fk = provided_event.id_pk
                        and provided_service.tariff = 0
                        and medical_service.reason_fk = 1 and (medical_service.group_fk != 19
                            or medical_service.group_fk is NUll)
                ) = 0
            ) or (
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

UPDATE_SANCTIONS_ON_WRONG_DISEASE_EVENT = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
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
    where
        medical_register.id_pk = %s
        and department.level <> 3
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
                ) = 1 and (
                    select count(1)
                    from provided_service
                        join medical_service
                            on provided_service.code_fk = medical_service.id_pk
                    where provided_service.event_fk = provided_event.id_pk
                        and provided_service.tariff = 0
                        and medical_service.reason_fk = 1 and (medical_service.group_fk != 19
                            or medical_service.group_fk is NUll)
                ) = 0
            ) or (
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

INSERT_SANCTIONS_ON_DISEASE_EVENT = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, provided_service.accepted_payment, T.error_id, provided_service.id_pk
from provided_service
    join medical_organization department
        on provided_service.department_fk = department.id_pk
    join
        (
            select provided_event.id_pk as event_id,
                min(provided_service_sanction.error_fk) as error_id
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
                LEFT join provided_service_sanction
                    on ps1.id_pk = provided_service_sanction.service_fk
            where mr1.is_active
                and mr1.id_pk = %s
                and (
                    medical_service.reason_fk = 1
                    and (
                        medical_service.group_fk != 19
                        or medical_service.group_fk is NUll
                    )
                )
                and ps1.payment_type_fk = 3
                group BY provided_event.id_pk
        ) as T
        on provided_service.event_fk = T.event_id
where provided_service.payment_type_fk <> 3
    and department.level <> 3
"""

UPDATE_SANCTIONS_ON_DISEASE_EVENT = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
where id_pk in (
    select provided_service.id_pk
    from provided_service
        join medical_organization department
            on provided_service.department_fk = department.id_pk
        join
            (
                select provided_event.id_pk as event_id,
                    min(provided_service_sanction.error_fk) as error_id
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
                    LEFT join provided_service_sanction
                        on ps1.id_pk = provided_service_sanction.service_fk
                where mr1.is_active
                    and mr1.id_pk = %s
                    and (
                        medical_service.reason_fk = 1
                        and (
                            medical_service.group_fk != 19
                            or medical_service.group_fk is NUll
                        )
                    )
                    and ps1.payment_type_fk = 3
                    group BY provided_event.id_pk
            ) as T
            on provided_service.event_fk = T.event_id
    where provided_service.payment_type_fk <> 3
        and department.level <> 3
)
"""

INSERT_SANCTION_ON_CODE_DISEASE = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, ps.accepted_payment, 40, ps.id_pk
from
    provided_service ps
    join provided_event pe
        on ps.event_fk = pe.id_pk
    join medical_register_record mrr
        on mrr.id_pk = pe.record_fk
    JOIN medical_register mr
        on mr.id_pk = mrr.register_fk

where
    mr.id_pk = %s
    and not exists (
        SELECT 1
        from medical_service_disease
        where service_fk = ps.code_fk
            and disease_fk = ps.basic_disease_fk
    )
    and ps.payment_type_fk != 3
    and mr.type not in (3, 4, 5, 6, 7, 8, 9, 10)
"""

UPDATE_SANCTION_ON_CODE_DISEASE = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
where id_pk in (
    select ps.id_pk
    from
        provided_service ps
        join provided_event pe
            on ps.event_fk = pe.id_pk
        join medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
    where
        mr.id_pk = %s
        and not exists (
            SELECT 1
            from medical_service_disease
            where service_fk = ps.code_fk
                and disease_fk = ps.basic_disease_fk
        )
        and ps.payment_type_fk != 3
        and mr.type not in (3, 4, 5, 6, 7, 8, 9, 10)
)
"""

INSERT_SANCTION_ON_HITECH_CODE_DISEASE = """
insert into provided_service_sanction(type_fk, underpayment, error_fk, service_fk)
select 1, ps.accepted_payment, 77, ps.id_pk
from
    provided_service ps
    join provided_event pe
        on ps.event_fk = pe.id_pk
    join medical_register_record mrr
        on mrr.id_pk = pe.record_fk
    JOIN medical_register mr
        on mr.id_pk = mrr.register_fk

where
    mr.id_pk = %s
    and not exists (
        SELECT 1
        from hitech_service_kind_disease
        where kind_fk = pe.hitech_kind_fk
            and disease_fk = ps.basic_disease_fk
    )
    and ps.payment_type_fk != 3
    and mr.type = 2
"""

UPDATE_SANCTION_ON_HITECH_CODE_DISEASE = """
update provided_service set payment_type_fk = 3, accepted_payment = 0
where id_pk in (
    select ps.id_pk
    from
        provided_service ps
        join provided_event pe
            on ps.event_fk = pe.id_pk
        join medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
    where
        mr.id_pk = %s
        and not exists (
            SELECT 1
            from hitech_service_kind_disease
            where kind_fk = pe.hitech_kind_fk
                and disease_fk = ps.basic_disease_fk
        )
        and ps.payment_type_fk != 3
        and mr.type = 2
)
"""