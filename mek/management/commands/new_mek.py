#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from main.funcs import howlong, round_money
from main.models import ProvidedService, MedicalRegister, \
    ProvidedServiceCoefficient, Sanction
from main.data_cache import COEFFICIENT_TYPES
from decimal import Decimal
from mek.checks import set_sanction
from mek import checks, comments, correct

from datetime import datetime
from main.logger import get_logger

logger = get_logger(__name__)


def get_register_element():
    register_element = MedicalRegister.objects.filter(
        is_active=True, year='2018', status_id__in=(500, 6) #,  organization_code='280029'
    ) \
        .values('organization_code',
                'year',
                'period',
                'status') \
        .distinct().first()
    return register_element


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
                services.*,

                CASE -- тарифы рассчитываются по КСГ
                    WHEN is_ksg_payment THEN ksg_tariff_basic.value
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

                    -- тарифы по стоматологии
                    WHEN medical_service.group_fk = 19
                    THEN
                        (CASE WHEN (select count(distinct ps1.id_pk)
                        from provided_service ps1
                        join medical_service ms1 ON ms1.id_pk = ps1.code_fk
                        where ps1.event_fk = services.event_fk and ms1.subgroup_fk = 12) = 1
                        THEN -- разовое по заболеванию
                            (select tariff_basic.capitation from provided_service ps1
                                         join medical_service ms1 ON ms1.id_pk = ps1.code_fk
                                         JOIN tariff_basic on tariff_basic.service_fk = ps1.code_fk
                            and tariff_basic.group_fk = services.department_tariff_group
                            and tariff_basic.start_date =
                            GREATEST((select max(start_date)
                                 from tariff_basic
                                 where start_date <= ps1.end_date
                                 and group_fk =services.department_tariff_group
                                 and service_fk = ps1.code_fk), '2018-01-01'::DATE)
                                     where ps1.event_fk = services.event_fk and ms1.subgroup_fk = 12) / 2.7
                                 ELSE (select distinct tariff_basic.value from provided_service ps1
                                         join medical_service ms1 ON ms1.id_pk = ps1.code_fk
                                         JOIN tariff_basic on tariff_basic.service_fk = ps1.code_fk
                            and tariff_basic.group_fk = services.department_tariff_group
                            and tariff_basic.start_date =
                            GREATEST((select max(start_date)
                                 from tariff_basic
                                 where start_date <= ps1.end_date
                                 and group_fk =services.department_tariff_group
                                 and service_fk = ps1.code_fk), '2018-01-01'::DATE)
                                        where ps1.event_fk = services.event_fk and ms1.subgroup_fk is not null) /
                               (CASE (select max(ms1.subgroup_fk) from provided_service ps1
                                   join medical_service ms1 ON ms1.id_pk = ps1.code_fk
                                   where ps1.event_fk = services.event_fk and ms1.subgroup_fk is not null)
                                   when 12 THEN 8.5
                                   when 13 THEN 2.7
                                   when 14 THEN 8.5
                                   WHEN 17 THEN 3.9 END)
                         END) * COALESCE(medical_service.uet, 0)

                    -- тарифы по диспансеризации взрослых I этап
                    WHEN medical_service.group_fk = 7
                    THEN (CASE WHEN services.end_date < (
                              select max(ps1.end_date) from provided_service ps1
                              where ps1.event_fk = services.event_fk and ps1.code_fk = 8347) THEN 0
                           ELSE examination_tariff.value
                           END)
                    -- тарифы по диспансеризации взрослых II этап
                    WHEN medical_service.group_fk in (25, 26)
                         THEN examination_tariff.value
                    when medical_service.group_fk = 11
                         THEN (
                            CASE when medical_service.code in ('119330', '119331', '119332', '119333', '119336', '119337')
                                      and (select count(distinct ps1.id_pk) from provided_service ps1
                                      where ps1.event_fk = services.event_fk and ps1.code_fk = 18298) = 1
                                 THEN tariff_basic.capitation
                            ELSE tariff_basic.value
                            END
                         )
                    -- тариф по умолчанию
                    ELSE tariff_basic.value
                END as expected_tariff,

                COALESCE (hitech_service_nkd.value, 1) AS nkd,

                -- Признаки для рассчётов коэффициентов
                -- КСЛП
                -- Возрастная группа
                CASE WHEN patient_age < 1 THEN 1
                     WHEN patient_age >= 1 and patient_age < 4 THEN 2
                     WHEN patient_age >= 75 THEN 3
                END age_type,

                -- Наличие тяжёлой сопутствующей патологии
                is_ksg_payment and EXISTS (
                SELECT 1 FROM ksg_serious_pathology where disease_fk in (select disease_fk from provided_event_additional_disease where event_fk = services.event_fk)
                ) AS is_serious_pathology,

                -- Проведение в рамках одной госпитализации в полном объеме нескольких видов противоопухолевого лечения из разных КСГ
                is_ksg_payment and EXISTS (
                  select 1
                  from
                  (
                     select count(distinct case when service_type = 1 then id_pk end) chemotherapy,
                        count(distinct case when service_type = 2 then id_pk end) radiation_therapy,
                        count(distinct case when service_type = 3 then id_pk end) surgery
                        from ksg_antioncotumor_therapy
                     where service_fk in (select code_fk from provided_service where event_fk = services.event_fk)
                  ) AS T where (chemotherapy > 0 and radiation_therapy > 0) or (chemotherapy > 0 and surgery > 0) or (radiation_therapy > 0 and surgery > 0) or radiation_therapy > 1
                ) AS is_few_kind_antioncotumor_therapy,

                -- 4 Проведение однотипных операций на парных органах
                is_ksg_payment and (EXISTS (
                select 1 from ksg_similar_surgical_operation_on_paired_organs where operation_fk in (select code_fk from provided_service where event_fk = services.event_fk
                and quantity > 1)
                ) or (
                    select count(distinct id_pk) from provided_service where event_fk = services.event_fk
                    and code_fk in (select operation_fk from ksg_similar_surgical_operation_on_paired_organs) and quantity > 0
                    group by code_fk
                    having count(distinct id_pk) > 1
                ) is not null )  AS is_ksg_similar_surgical_operation_on_paired_organs,

                -- 3 Проведение сочетанных хирургических вмешательств
                is_ksg_payment and EXISTS (
                     select 1
                        from ksg_combined_surgical_operation
                     where first_operation_fk in (select code_fk from provided_service where event_fk = services.event_fk)
                           and second_operation_fk in (select code_fk from provided_service where event_fk = services.event_fk)
                ) AS is_combined_surgical_operation,

                CASE WHEN is_ksg_payment THEN (
                    CASE WHEN EXISTS (
                           SELECT 1 FROM ksg_grouping
                           join medical_service ms1 ON ms1.id_pk = ksg_grouping.service_fk
                           WHERE ksg_fk = ksg.id_pk
                              and ksg_grouping.disease_fk is null
                              and ms1.code ilike 'A16%%'
                              AND ksg_grouping.start_date = '2018-01-01'
                              AND ksg_grouping.service_fk IN (
                                  SELECT code_fk FROM provided_service
                                  WHERE event_fk = services.event_fk
                            )
                         ) THEN 1
                         ELSE 2
                    END
                )
                ELSE 0
                END AS ksg_type,

                 (services.service_term = 1 and ((services.disease_code in ('O14.1', 'O34.2', 'O36.3', 'O36.4', 'O42.2')
                  and services.quantity >= 2) or (services.quantity >= 6))
                  and services.ksg_smo in ('2', '4', '5')
                  and services.disease_code not in ('O60.0')
                  and services.event_division_id in (
                        29, 57
                  )
                  and EXISTS(
                      SELECT 1 FROM ksg_pregnant_double_payment where service_fk in (select code_fk from provided_service where event_fk = services.event_fk)
                  )) AS is_pregnant_double_payment,
                  EXISTS(
                      SELECT 1 FROM ksg_pregnant_double_payment where service_fk in (select code_fk from provided_service where event_fk = services.event_fk) and ksg = 4
                  ) AS is_pregnant_double_payment_4_ksg,
                  EXISTS(
                      SELECT 1 FROM ksg_pregnant_double_payment where service_fk in (select code_fk from provided_service where event_fk = services.event_fk) and ksg = 5
                  ) AS is_pregnant_double_payment_5_ksg,

                 (select kmc.coefficient_fk from ksg_managerial_coefficient kmc where kmc.ksg_fk =  ksg.id_pk
                     and kmc.start_date = GREATEST((select max(kmc1.start_date)
                     from ksg_managerial_coefficient kmc1
                     where kmc1.start_date <= services.event_end_date
                           and kmc1.ksg_fk = ksg.id_pk), '2018-01-01'))

                   AS managerial_coefficient_id,

                 is_ksg_payment and EXISTS(select ke.id_pk from ksg_exclusion ke where ke.ksg_fk = ksg.id_pk
                                                                and ke.exclusion_type_fk = 1) AS ksg_full_payment,
                 is_ksg_payment and EXISTS(select ke.id_pk from ksg_exclusion ke where ke.ksg_fk = ksg.id_pk
                                                                and ke.exclusion_type_fk = 2) AS ksg_overlong_exclusion,
                 is_ksg_payment and EXISTS(select ke.id_pk from ksg_exclusion ke where ke.ksg_fk = ksg.id_pk
                                                                and ke.exclusion_type_fk = 3) AS kuc_not_applicable,
                 is_ksg_payment and ksg.kpg_fk = 17 AS is_neonatology,
                 is_ksg_payment and ksg.kpg_fk = 38 AS is_geriatrics

    FROM (
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
            provided_event.basic_disease_fk,
            provided_event.id_pk AS event_id,
            ms.code AS service_code,
            idc.idc_code AS disease_code,
            provided_event.division_fk AS event_division_id,

            provided_event.term_fk as service_term,
            COALESCE(ksg.coefficient, 0) AS ksg_coefficient,

            department.regional_coefficient  AS regional_coefficient,
            provided_event.examination_result_fk as examination_result,
            provided_event.ksg_smo AS ksg_smo,

            patient.person_unique_id as patient_policy,
            patient.birthdate as patient_birthdate,
            patient.gender_fk AS patient_gender,
            EXTRACT(YEAR from age(provided_event.start_date, patient.birthdate)) AS patient_age,

            medical_register.organization_code,
            provided_event.comment as event_comment,
            provided_service.comment as service_comment,
            medical_register_record.is_corrected as record_is_corrected,

            medical_register.type as register_type,

            provided_event.end_date as event_end_date,
            provided_event.start_date as event_start_date,

            provided_event.term_fk in (1, 2) and
            (ms.group_fk not in (20, 3, 42, 27) or ms.group_fk is null) AS is_ksg_payment,

            provided_event.treatment_result_fk in (2, 12, 7, 8, 10, 48, 49, 5, 6, 15, 16) AS is_interrupted,
            provided_service.quantity <= 3 AS is_shortened_event,

            -- Исключение для эндоскопической хирургии в ГП1
            CASE WHEN medical_register.organization_code = '280036'
                  AND provided_service.comment = '100000' THEN 2
             -- Исключение для женских консультаций 1 и 2 и травматологии ГКБ
             WHEN department.old_code in ('0121001', '0121002', '0301010')
                  and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null) THEN 2
             WHEN department.old_code in ('0115025')
                  and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null)
               THEN department.day_hospital_level
             -- Ивановская больница отделение мед реабилитации
             WHEN medical_register.organization_code = '280007' AND provided_event.division_fk in (364, 366, 367, 370, 382)
                  and provided_event.term_fk = 1 THEN 2
             -- Межмуниципальные травматологические центры
             WHEN medical_register.organization_code in ('280068', '280012', '280059')
                  and ms.tariff_profile_fk in (12, 13) and provided_event.term_fk = 1 THEN 2
             WHEN provided_event.term_fk = 1 THEN department.level
             WHEN provided_event.term_fk = 2 THEN department.day_hospital_level
             ELSE department.level
             END AS department_level,

            CASE WHEN medical_register.organization_code = '280036'
                  AND provided_service.comment = '100000' THEN 2
             -- Исключение для женских консультаций 1 и 2 и травматологии ГКБ
             WHEN department.old_code in ('0121001', '0121002', '0301010')
                  and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null) THEN 2
             WHEN department.old_code in ('0115025')
                  and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null)
               THEN medical_organization.day_hospital_level
             -- Ивановская больница отделение мед реабилитации
             WHEN medical_register.organization_code = '280007' AND provided_event.division_fk in (364, 366, 367, 370, 382)
                  and provided_event.term_fk = 1 THEN 2
             -- Межмуниципальные травматологические центры
             WHEN medical_register.organization_code in ('280068', '280012', '280059')
                  and ms.tariff_profile_fk in (12, 13) and provided_event.term_fk = 1 THEN 2
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
             WHEN department.old_code in ('0115025')
                  and (provided_event.term_fk not in (1, 2) or provided_event.term_fk is null)
               THEN department.alternate_tariff_group_fk
             -- Ивановская больница отделение мед реабилитации
             WHEN medical_register.organization_code = '280007' AND provided_event.division_fk in (364, 366, 367, 370, 382)
                  and provided_event.term_fk = 1 THEN 19
             WHEN provided_event.term_fk = 1 THEN department.tariff_group_fk
             WHEN provided_event.term_fk = 2 THEN department.alternate_tariff_group_fk
             ELSE department.tariff_group_fk
             END AS department_tariff_group,

            -- Ивановская больница отделение мед реабилитации
            CASE WHEN medical_register.organization_code = '280007' AND provided_event.division_fk in (364, 366, 367, 370, 382)
               and provided_event.term_fk = 1 THEN 50
            -- Межмуниципальные травматологические центры
            WHEN medical_register.organization_code in ('280068', '280012', '280059')
            and ms.tariff_profile_fk in (12, 13) and provided_event.term_fk = 1 THEN 50
            ELSE (
                 select khlc.coefficient_fk from ksg_hospital_level_coefficient khlc where
                          khlc.organization_fk = department.id_pk
                          and provided_event.term_fk = 1
                          and khlc.start_date <= provided_event.end_date
                          order by khlc.start_date desc
                          limit 1
            )
            END AS hospital_level_coefficient
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
        left join idc ON idc.id_pk = provided_event.basic_disease_fk
        LEFT JOIN ksg ON ksg.code::VARCHAR = provided_event.ksg_smo AND ksg.start_date = '2018-01-01'
             AND ksg.term_fk = provided_event.term_fk
        where medical_register.is_active
            and medical_register.year = %(year)s
            and medical_register.period = %(period)s
            and medical_register.organization_code = %(organization_code)s
    ) AS services
    join medical_service ON medical_service.id_pk = services.code_fk

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
         and service_fk = services.code_fk), '2018-01-01'::DATE)

    -- Тариф по диспансеризации взрослых (исключение)
    LEFT JOIN examination_tariff
    on services.register_type in (3, 4)
        and examination_tariff.service_fk = services.code_fk
        and examination_tariff.age = EXTRACT(year from services.event_end_date) - extract(year from services.patient_birthdate)
        and examination_tariff.gender_fk = services.patient_gender
        and examination_tariff.regional_coefficient = services.regional_coefficient
        and examination_tariff.start_date =
        GREATEST((select max(start_date)
              from examination_tariff
              where start_date <= services.event_end_date
              and service_fk = services.code_fk), '2017-01-01'::DATE)

    -- Базовая ставка для КСГ
    LEFT JOIN ksg_tariff_basic
        ON ksg_tariff_basic.term_fk = services.service_term
        and ksg_tariff_basic.regional_coefficient = services.regional_coefficient
        and ksg_tariff_basic.start_date = GREATEST((select max(start_date)
              from ksg_tariff_basic
              where start_date <= services.event_end_date
              and term_fk = services.service_term
              and regional_coefficient = services.regional_coefficient), '2018-01-01'::DATE)

    LEFT JOIN ksg ON ksg.code::VARCHAR = services.ksg_smo AND ksg.start_date = '2018-01-01'
    AND ksg.term_fk = services.service_term

    -- нкд для ВМП (исключение)
    LEFT JOIN hitech_service_nkd
    ON hitech_service_nkd.start_date = (
        select max(start_date)
        from hitech_service_nkd where start_date <= services.end_date
        and vmp_group = medical_service.vmp_group
        )
    """

    services = list(ProvidedService.objects.raw(
        query, dict(year=register_element['year'],
                    period=register_element['period'],
                    organization_code=register_element[
                        'organization_code'])))
    print 'total services: ', len(services)
    return services


@howlong
def identify_patient(register_element):
    """
        Иденитификация пациентов по фио, полису, снилс, паспорту.
        В различных вариациях
    """
    query_correct = """
        update patient set last_name = case when last_name = 'НЕТ' then '' else last_name end,
                   first_name = case when first_name = 'НЕТ' then '' else first_name end,
                   middle_name = case when middle_name = 'НЕТ' then '' else middle_name end
        where id_pk in (
            select p.id_pk
            FROM medical_register mr
            JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
            JOIN patient p
                  ON p.id_pk = mrr.patient_fk
            WHERE mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
                and (p.last_name = 'НЕТ' or p.first_name = 'НЕТ' or p.middle_name = 'НЕТ')
                and p.newborn_code = '0'
    )
    """

    query = """
        UPDATE patient set person_unique_id = CASE WHEN T.is_active THEN T.person_unique_id END, person_unique_id1 = CASE WHEN T.is_active THEN T.person_unique_id END, insurance_policy_fk = T.uploading_policy_id
        FROM (
            SELECT distinct p.id_pk AS patient_id, up.person_unique_id, u_pol.id_pk AS uploading_policy_id, (
                                    CASE WHEN u_pol.stop_date is null THEN True
                                         ELSE (
                                             CASE WHEN ps.start_date <= u_pol.stop_date THEN True
                                                  ELSE (
                                                      EXISTS (
                                                            select 1
                                                            from uploading_person up1
                                                            join uploading_policy u_pol1 ON u_pol1.uploading_person_fk = up1.id_pk
                                                            where up1.person_unique_id = up.person_unique_id
                                                                  and u_pol1.stop_date is null
                                                      )
                                                  )
                                             END
                                         )
                                    END) AS is_active
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
            join uploading_policy u_pol ON u_pol.id_pk = (
                select
                case when char_length(p.insurance_policy_number) <= 6 THEN
                (select id_pk from uploading_policy
                     where
                     CASE when series <> '' THEN (series = p.insurance_policy_series
                                                  and number = trim(leading '0' from p.insurance_policy_number))
                          ELSE (p.insurance_policy_series || trim(leading '0' from p.insurance_policy_number) = number)
                     END

                    order by stop_date DESC NULLS FIRST
                    LIMIT 1
                )
                when char_length(p.insurance_policy_number) between 7 and 8 THEN
                (select id_pk from uploading_policy
                    where
                    CASE WHEN series <> '' THEN series = p.insurance_policy_series
                                                and number = p.insurance_policy_number
                    ELSE (p.insurance_policy_series || p.insurance_policy_number) = number
                    END
                    order by stop_date DESC NULLS FIRST
                    LIMIT 1
                )
                when char_length(p.insurance_policy_number) = 9 THEN
                (select id_pk from uploading_policy where
                    number = p.insurance_policy_number
                    order by stop_date DESC NULLS FIRST
                    LIMIT 1
                )
                when char_length(p.insurance_policy_number) = 16 THEN
                (select id_pk from uploading_policy
                    where
                    enp = p.insurance_policy_number
                    order by stop_date desc NULLS FIRST
                    LIMIT 1
                )
                END)
            join uploading_person up_by_policy ON up_by_policy.id_pk = u_pol.uploading_person_fk
            join uploading_person up ON up.id_pk = (
                 select max(up1.id_pk)
                 from uploading_person up1
                 where
                     up1.person_unique_id = up_by_policy.person_unique_id
                     and CASE WHEN p.newborn_code != '0' Then True
                         ELSE (regexp_replace(regexp_replace((up1.last_name || up1.first_name || up1.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g')
                               = regexp_replace(regexp_replace((p.last_name || p.first_name || p.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g') and p.birthdate = up1.birthdate)
                               or (up1.first_name = p.first_name and up1.middle_name = p.middle_name and up1.birthdate = p.birthdate)
                               or (
                                   CASE WHEN length(p.snils) = 14 and p.snils = up1.snils THEN
                                        (up1.last_name = p.last_name and up1.middle_name = p.middle_name and up1.birthdate = p.birthdate)
                                        or (up1.last_name = p.last_name and up1.first_name = p.first_name and up1.birthdate = p.birthdate)
                                        or (up1.last_name = p.last_name and up1.first_name = p.first_name and up1.middle_name = p.middle_name)
                                   END
                               )
                         END
                 )

            WHERE mr.is_active
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
        ) AS T
        WHERE patient.id_pk = T.patient_id

    """
    cursor = connection.cursor()
    cursor.execute(query_correct, [register_element['year'],
                           register_element['period'],
                           register_element['organization_code']])
    transaction.commit()

    print u'идентификация по фио, снилс и полису'
    cursor.execute(query, [register_element['year'],
                           register_element['period'],
                           register_element['organization_code']])
    transaction.commit()

    cursor.close()

@howlong
def update_patient_attachment_code(register_element):
    query = """
        UPDATE patient SET attachment_code = T.attachment_organization
        FROM (
            SELECT DISTINCT p.id_pk, up_att_org.code AS attachment_organization

            FROM medical_register_record mrr
                JOIN patient p
                    on p.id_pk = mrr.patient_fk
                JOIN medical_register mr
                    ON mrr.register_fk = mr.id_pk

                LEFT JOIN uploading_person up ON up.id = (
                   (select up1.id from uploading_person up1
                          join uploading_policy u_pol1 ON up1.id_pk = u_pol1.uploading_person_fk
                          where up1.person_unique_id = p.person_unique_id
                          order by u_pol1.stop_date desc  nulls first
                          limit 1)
                )
                LEFT JOIN uploading_attachment ua ON ua.id_pk = (
                    SELECT id_pk
                    FROM uploading_attachment ua1
                    WHERE ua1.id = up.id
                          and ua1.start_date <= format('%%s-%%s-%%s', mr.year, mr.period, '01')::DATE
                    ORDER by ua1.start_date DESC
                    LIMIT 1
                )
                LEFT JOIN medical_organization up_att_org ON up_att_org.id_pk = ua.organization_fk
            WHERE mr.is_active
                 AND mr.year = %(year)s
                 AND mr.period = %(period)s
                 and mr.organization_code = %(organization)s
         ) AS T
        WHERE T.id_pk = patient.id_pk
    """

    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()

    cursor.close()


@howlong
def update_payment_kind(register_element):
    # По подушевому оплачиваются все услуги поликлиники, оказанные прикреплённому застрахованному
    # Есть ряд исключений оплата за единицу объема:
    # 1. При диспансерном наблюдении женщин в период беременности в Свободненской больнице,
    # прикреплённых с Свободненской поликлинике
    # 2. При разовых посещениях и обращениях в связи с заболеванием в Свободенской больнице
    # по профилю акушерство и гинекология, прикреплённых к Свободненской поликлинике
    # 3. При разовых посещениях и обращениях в свзяи с заболеванием в Свободненской больнице,
    # по профилю травматология и ортопедия, прикрепленных к медицинским организациям г. Свободного
    # 4. При разовых посещениях и обращениях в связи с заболеванием по врачебным специальностям,
    # за исключением профиля терапия, застрахованных лиц (взрослое население), прикреплённых к Свободненской больнице
    # в Свободненская поликлиника, в Свободненской ДВОМЦ и в МСЧ на космодроме Восточный
    # 5. При посещениях к среднему медицинскому персоналу, ведущему самостоятельный приём застрахованных лиц,
    # прикреплённых к НУЗ Февральск РЖД в ФАП Селемджинской больницы

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
                         (mr1.organization_code = '280001' AND medical_service.tariff_profile_fk = 241 AND p1.attachment_code = '280052')
                          OR (mr1.organization_code = '280001' AND medical_service.reason_fk = 1 AND medical_service.tariff_profile_fk = 93 AND p1.attachment_code = '280052')
                          OR (mr1.organization_code = '280001' AND medical_service.reason_fk = 1 AND medical_service.tariff_profile_fk = 108 AND p1.attachment_code IN ('280052', '280076', '280125'))
                          OR (mr1.organization_code in ('280052', '280076', '280125') AND medical_service.reason_fk = 1 AND medical_service.tariff_profile_fk != 120
                              AND medical_service.code ILIKE '0%%'  AND Extract (year from age(ps1.end_date, p1.birthdate)) >= 18 AND p1.attachment_code = '280001')
                          OR (mr1.organization_code = '280025' and medical_service.tariff_profile_fk = 137 and p1.attachment_code = '280015')
                      )
                      AND ps1.department_fk NOT IN (15, 88, 89, 232)
                when TRUE THEN (
                                    CASE WHEN at_stat.id_pk IS NULL THEN 1
                                         ELSE 2
                                    END
                                )
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
            left join attachment_statistics at_stat
                on at_stat.organization = mr1.organization_code AND at_stat.at = format('%%s-%%s-%%s', mr1.year, mr1.period, '01')::DATE
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


@howlong
def update_payment_kind_newborn(register_element):
    """
    При оказаниии первичной медико-санитарной помощи детям с момента рождения до получения
    полиса обязательного медицинского страхования, но не более 30 дней, оплата осуществляется
    за единицу объёма медицинской помощи - за посещение, обращение (законченный случай)
    за медицинскую услугу
    см. Дополнительное соглашение № 9 от 22.09.2016
    """
    query = """
        UPDATE provided_event SET newborn_tariff_payment = True
        WHERE id_pk in (
            SELECT distinct pe.id_pk
            FROM medical_register mr
            JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
                  ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
                  ON ps.event_fk=pe.id_pk
            JOIN medical_service ms
                  ON ms.id_pk = ps.code_fk
            JOIN patient p ON p.id_pk = mrr.patient_fk
            left join uploading_person up ON up.id_pk = (
                select up1.id_pk from uploading_person up1
                   join uploading_policy u_pol1 ON up1.id_pk = u_pol1.uploading_person_fk
                   where (regexp_replace(regexp_replace((up1.last_name || up1.first_name || up1.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g')
                         = regexp_replace(regexp_replace((p.last_name || p.first_name || p.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g') and p.birthdate = up1.birthdate)
                   AND u_pol1.start_date <= ps.start_date
                             limit 1
                )

            WHERE mr.is_active
                and mr.year = %(year)s
                and mr.period = %(period)s
                and mr.organization_code = %(organization)s
                and pe.term_fk = 3
                and (ms.group_fk is null or ms.group_fk = 24)
                and (ps.start_date - p.birthdate <= 30)
                and up.id_pk is null
                and pe.kind_fk in (1, 5, 6)
        )
    """

    query2 = """
        UPDATE provided_service SET payment_kind_fk = 1
            WHERE event_fk in (
                SELECT distinct pe.id_pk
                FROM medical_register mr
                JOIN medical_register_record mrr
                      ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                      ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                      ON ps.event_fk=pe.id_pk
                WHERE mr.is_active
                    and mr.year = %(year)s
                    and mr.period = %(period)s
                    and mr.organization_code = %(organization)s
                    and pe.newborn_tariff_payment
            )
    """

    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))
    transaction.commit()


    # Проставить payment_kind_fk значением 1, там где newborn_tariff_payment истина
    cursor.execute(query2, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))
    transaction.commit()
    cursor.close()


@howlong
def update_payment_kind_not_attachment(register_element):
    """
    При обращении по поводу заболевания с кратностью не менее двух посещений по поводу
    одного заболевания застрахованных лиц, прикрепленных к иным медицинским
    организациям расположенным в других муниципальных образованиях
    см. Доп.соглашение № 8 от 09.09.2016
    """
    query = """
        update provided_service set payment_kind_fk = 1
        where event_fk in (
            select pe.id_pk
                from medical_register mr
                JOIN medical_register_record mrr
                      ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                      ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                      ON ps.event_fk=pe.id_pk
                JOIN medical_service ms
                      ON ms.id_pk = ps.code_fk
                join patient p ON p.id_pk = mrr.patient_fk
                join medical_organization att ON att.code = p.attachment_code and att.parent_fk is null
                join medical_organization mo ON mo.code =  mr.organization_code  and mo.parent_fk is null
                left join lateral (
                    select count(distinct ps1.id_pk) AS count_services
                    from provided_service ps1
                       join medical_service ms1 ON ms1.id_pk = ps1.code_fk
                    where (ms1.group_fk is null or ms1.group_fk not in (27, 3, 5, 42))
                           and ps1.event_fk = ps.event_fk
                ) AS Y ON True
                where mr.is_active
                    and mr.year = %(year)s
                    and mr.period = %(period)s
                    and mr.organization_code = %(organization)s
                    and pe.term_fk = 3
                    and (p.attachment_code != mr.organization_code)
                    and (ms.reason_fk = 1 AND Y.count_services > 1) and (ms.group_fk is null or ms.group_fk = 24)
                    and att.region_fk != mo.region_fk
        )
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
def update_ksg(register_element):
    print u'Проставляем КСГ'
    # Рассчёт КСГ по стационару и дневному стационару (по группировщикам)
    ksg_general_query = """
        UPDATE provided_event SET ksg_smo = T.ksg_code
        FROM (
            SELECT
                event_id,
                ksg_calc.coefficient AS ksg_coef,
                ksg_calc.code AS ksg_code,
                MAX(ksg_calc.coefficient) over (PARTITION by event_id) AS max_ksg_coeff
            FROM  (SELECT
                pe.id_pk AS event_id,
                pe.basic_disease_fk AS disease_id,
                add_disease.disease_fk AS secondary_disease_id,
                ps.code_fk AS code_id,
                age(pe.start_date, pt.birthdate) AS patient_age,
                (CASE WHEN MAX(ps.quantity) OVER (PARTITION by pe.id_pk) <= 3 THEN 1 ELSE 0 END) AS event_duration,
                pt.gender_fk AS gender,
                EXISTS(
                select 1 FROM provided_service op
                    JOIN medical_service ms_op
                       ON ms_op.id_pk = op.code_fk
                WHERE op.event_fk = pe.id_pk
                      AND (ms_op.code ILIKE 'A%%' or ms_op.code ILIKE 'B%%')) AS has_op_event,
                (ms.code ILIKE 'A%%' or ms.code ILIKE 'B%%') AS is_op_service,
                pe.term_fk AS service_term,
                mts.id_pk AS scheme_id
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
                LEFT JOIN provided_event_additional_disease add_disease
                   ON add_disease.event_fk = pe.id_pk
                LEFT JOIN medicine_therapy_scheme mts
                   ON mts.code = ANY(regexp_split_to_array(pe.comment, ';'))
            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND mr.organization_code = %(organization)s
                AND pe.term_fk in (1, 2)
            ) AS mo_services
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
                        AND (CASE WHEN k.age = 1 THEN patient_age <= '28 days' and patient_age >= '0 days'
                                  WHEN k.age = 2 THEN patient_age <= '90 days' and patient_age >= '29 days'
                                  WHEN k.age = 3 THEN patient_age <= '1 years' and patient_age >= '91 days'
                                  WHEN k.age = 4 THEN patient_age <= '2 years'
                                  WHEN k.age = 5 THEN patient_age <= '18 years'
                                  WHEN k.age = 6 THEN patient_age > '18 years'
                                  ELSE TRUE
                             END)
                        AND (CASE WHEN k.gender_fk IS NOT NULL THEN k.gender_fk = gender ELSE TRUE END)
                        AND (CASE WHEN k.duration <> 0 THEN k.duration = event_duration ELSE TRUE END)
                        AND (CASE WHEN k.medicine_therapy_scheme_fk IS NOT NULL THEN k.medicine_therapy_scheme_fk = scheme_id ELSE TRUE END)
                        AND k.start_date = '2018-01-01'
                WHERE
                    ksg.term_fk = service_term
                ORDER BY k.secondary_disease_fk DESC NULLS LAST, k.service_fk DESC NULLS LAST, k.age asc nulls last,
                         k.duration desc nulls last, k.gender_fk DESC NULLS LAST, k.medicine_therapy_scheme_fk DESC NULLS LAST
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
                        AND (CASE WHEN k.age = 1 THEN patient_age <= '28 days' and patient_age >= '0 days'
                                  WHEN k.age = 2 THEN patient_age <= '90 days' and patient_age >= '29 days'
                                  WHEN k.age = 3 THEN patient_age <= '1 years' and patient_age >= '91 days'
                                  WHEN k.age = 4 THEN patient_age <= '2 years'
                                  WHEN k.age = 5 THEN patient_age <= '18 years'
                                  WHEN k.age = 6 THEN patient_age > '18 years'
                                  ELSE TRUE
                             END)
                        AND (CASE WHEN k.gender_fk IS NOT NULL THEN k.gender_fk = gender ELSE TRUE END)
                        AND (CASE WHEN k.duration <> 0 THEN k.duration = event_duration ELSE TRUE END)
                        AND (CASE WHEN k.medicine_therapy_scheme_fk IS NOT NULL THEN k.medicine_therapy_scheme_fk = scheme_id ELSE TRUE END)
                        AND k.start_date = '2018-01-01'
                WHERE
                    ksg.term_fk = service_term
                ORDER BY k.disease_fk DESC NULLS LAST, k.secondary_disease_fk DESC NULLS LAST, k.age asc nulls last,
                         k.duration desc nulls last, k.gender_fk DESC NULLS LAST, k.medicine_therapy_scheme_fk DESC NULLS LAST
                LIMIT 1
            ) AS ksg_byservice ON (ksg_bydisease.defined_by_diagnosis = False
                                   OR ksg_bydisease.defined_by_diagnosis IS NULL)

            LEFT JOIN ksg ksg_calc ON (
                --КСГ, в которых не предусмотрена возможность выбора между критерием диагноза и услуги
                CASE WHEN EXISTS(select 1 from ksg_choice_exclusion kce
                                 where
                                 (CASE WHEN kce.ksg_bydisease_fk is null
                                  THEN kce.ksg_byservice_fk = ksg_byservice.id_pk
                                  ELSE kce.ksg_bydisease_fk = ksg_bydisease.id_pk and kce.ksg_byservice_fk = ksg_byservice.id_pk
                                  END))
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
        UPDATE provided_event SET ksg_smo = '233'
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
                LEFT JOIN provided_event_additional_disease add_disease
                   ON add_disease.event_fk = pe.id_pk
                JOIN disease_grouping dg
                   ON (dg.disease_id = ps.basic_disease_fk OR dg.disease_id = add_disease.disease_fk)
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

            payments = get_payments_sum(service)

            service.calculated_payment = payments['calculated_payment']
            service.provided_tariff = payments['provided_tariff']

            if (service.is_ksg_payment and ((payments['accepted_payment'] - Decimal(service.tariff)) >= 0.00105 or \
                    (payments['accepted_payment'] - Decimal(service.tariff)) <= -0.00105)) or \
                    (not service.is_ksg_payment and ((payments['tariff'] - Decimal(service.tariff)) >= 0.00105 or \
                    (payments['tariff'] - Decimal(service.tariff)) <= -0.00105)):
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
    event_comment_list = service.event_comment.split(';')
    is_mobile_brigade = len(service.service_comment) >= 5 and service.service_comment[4] == '1' \
        or 'MB' in service.service_comment.split(';')
    is_mobile_stom_cab = (service.service_comment == '0000001')
    is_provision_bed_for_agent = 'KSLP7' in event_comment_list
    is_reanimation = 'KSLP10' in event_comment_list
    is_stimulation_of_superovulation = 'KSLP11' in event_comment_list
    is_complete_cycle_eco = 'KSLP12' in event_comment_list
    is_not_complete_cycle_eco = 'KSLP13' in event_comment_list


    provided_tariff = Decimal(service.tariff)

    tariff = Decimal(service.expected_tariff or 0)

    term = service.service_term

    if service.service_group in (3, 5):
        term = 3

    if term in (1, 2) and service.is_ksg_payment:
        # Оплата по двум КСГ
        if service.is_pregnant_double_payment:
            if service.ksg_smo == '2' and service.is_pregnant_double_payment_4_ksg:
                ksg_coefficient_pregnant = Decimal(0.98)
            elif service.ksg_smo == '2' and service.is_pregnant_double_payment_5_ksg:
                ksg_coefficient_pregnant = Decimal(1.01)
            elif service.ksg_smo in ('4', '5'):
                ksg_coefficient_pregnant = Decimal(0.93)
            tariff *= (Decimal(service.ksg_coefficient) + ksg_coefficient_pregnant)
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=41)
            ProvidedServiceCoefficient.objects.filter(
                service=service, coefficient_id=41).update(value=ksg_coefficient_pregnant)
        else:
            tariff *= Decimal(service.ksg_coefficient)

        if service.is_ksg_payment and (service.is_shortened_event or service.is_interrupted):
            if term == 1:
                # Перечень КСГ (круглосуточного стационара), по которым оплата осуществляется в полном объёме независимо
                # от длительности лечения
                if service.ksg_full_payment:
                    duration_coefficient = 100
                else:
                    # Оказана хирургическая операция являющаяся основным квалификационным критерием (КСГ хирургическая)
                    # и длительность составила 3 дня и менее
                    if service.ksg_type == 1 and service.is_shortened_event:
                        duration_coefficient = 80
                    # и длительность составила более 3 дня и случай прерванный
                    elif service.ksg_type == 1 and not service.is_shortened_event and service.is_interrupted:
                        duration_coefficient = 85

                    # Указанная хирургическая операция не выполнена, оновной квалификационный критерий диагноз
                    # (КСГ терапевтическая)
                    # и длительность составила 3 дня и менее
                    elif service.ksg_type == 2 and service.is_shortened_event:
                        duration_coefficient = 50
                    # и длительность составила более 3 дня и случай прерванный
                    elif service.ksg_type == 2 and not service.is_shortened_event and service.is_interrupted:
                        duration_coefficient = 60

            elif term == 2:
                # Оказана хирургическая операция являющаяся основным квалификационным критерием (КСГ хирургическая)
                # и длительность составила 3 дня и менее
                if service.ksg_type == 1 and service.is_shortened_event:
                    duration_coefficient = 80
                # и длительность составила 3 дня и менее
                elif service.ksg_type == 1 and not service.is_shortened_event and service.is_interrupted:
                    duration_coefficient = 85

                # Указанная хирургическая операция не выполнена, оновной квалификационный критерий диагноз
                # (КСГ терапевтическая)
                # и длительность составила 3 дня и менее
                elif service.ksg_type == 2 and service.is_shortened_event:
                    duration_coefficient = 50
                # и длительность составила более 3 дня и случай прерванный
                elif service.ksg_type == 2 and not service.is_shortened_event and service.is_interrupted:
                        duration_coefficient = 60

            tariff = (tariff*duration_coefficient)/100
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=42)
            ProvidedServiceCoefficient.objects.filter(
                service=service, coefficient_id=42).update(value=round_money(Decimal(duration_coefficient)/100))

        accepted_payment = tariff

        if term == 1:
            # КУС коэффициент уровня оказания стационарной медиицнской помощи (круглосуточный стационар)
            if not service.kuc_not_applicable:
                if service.hospital_level_coefficient:
                    accepted_payment = accepted_payment * Decimal(COEFFICIENT_TYPES[service.hospital_level_coefficient]['value'])
                    ProvidedServiceCoefficient.objects.get_or_create(
                        service=service, coefficient_id=service.hospital_level_coefficient)

            # круглосуточный стационар Коэффициент сложности лечения пациента КСЛП
            kslp_coeffs = []

            #1 Проведение в рамках одной госпитализации в полном объеме
            #нескольких видов противоопухолевого лечения, относящихся
            #к разным КСГ (перечень возможных сочетаний КСГ представлен в Инструкции)
            if service.is_few_kind_antioncotumor_therapy:
                kslp_coeffs.append(29)
            #3 Проведение сочетанных хирургических вмешательств
            if service.is_combined_surgical_operation:
                kslp_coeffs.append(31)
            #4 Проведение однотипных операций на парных органах
            if service.is_ksg_similar_surgical_operation_on_paired_organs:
                kslp_coeffs.append(32)
            #5 Сложность лечения пациента, связанная с возрастом (госпитализация детей до 1 года)*
            if service.age_type == 1 and not service.is_neonatology:
                kslp_coeffs.append(33)
            #6 Сложность лечения пациента, связанная с возрастом (госпитализация детей от 1 до 4 лет)
            if service.age_type == 2:
                kslp_coeffs.append(34)
            #7 Необходимость предоставления спального места и питания законному представителю (дети до 4 лет)
            if service.age_type in (1, 2) and is_provision_bed_for_agent:
                kslp_coeffs.append(35)
            #8 Сложность лечения пациента, связанная с возрастом (лица старше 75 лет)
            if service.age_type == 3 and not service.is_geriatrics:
                kslp_coeffs.append(36)
            #9 Наличие у пациента тяжелой сопутствующей патологии, осложнений заболеваний, сопутствующих заболеваний,
            # влияющих на сложность лечения пациента
            if service.is_serious_pathology:
                kslp_coeffs.append(37)

            #Суммарное значение КСЛП при наличии нескольких критериев не может превышать 1.8
            kslp_coeffs.sort(key=lambda x: COEFFICIENT_TYPES[x]['value'], reverse=True)
            kslp_coeffs_total = Decimal(0)
            kslp_coeffs_all = Decimal(0)
            for coeff_id in kslp_coeffs:
                coeff_value = Decimal(COEFFICIENT_TYPES[coeff_id]['value'] - 1)
                kslp_coeffs_total = kslp_coeffs_total + coeff_value
                if kslp_coeffs_total > Decimal(0.8):
                    break
                else:
                    kslp_coeffs_all = kslp_coeffs_all + coeff_value
                    ProvidedServiceCoefficient.objects.get_or_create(
                        service=service, coefficient_id=coeff_id)

            #2 Сверхдлительные сроки госпитализации, обусловленные медицинскими показаниями
            #КСЛП – коэффициент сложности лечения пациента;
            #Кдл – коэффициент длительности, учитывающий расходы на медикаменты, питание,
            #и частично на другие статьи расходов.
            #Рекомендуемое значение – 0,25 для обычных отделений, 0,4 – для реанимационных отделений.
            #Конкретный размер устанавливается в тарифном соглашении;
            #ФКД – фактическое количество койко-дней;
            #НКД – нормативное количество койко-дней (30 дней, за исключением КСГ, для которых установлен срок 45 дней).
            #КСЛП по сверхдлительным срокам госпитализации прибавляется без ограничения итогового значения
            overlong_coeff = Decimal(0)
            if (service.quantity > 30 and not service.ksg_overlong_exclusion) or \
                    (service.quantity > 45 and service.ksg_overlong_exclusion):
                kdl = Decimal(0.4) if is_reanimation else Decimal(0.25)
                ksg_nkd = 45 if service.ksg_overlong_exclusion else 30
                overlong_coeff = round_money(((service.quantity - ksg_nkd) / ksg_nkd) * kdl)

                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=30)
                ProvidedServiceCoefficient.objects.filter(
                    service=service, coefficient_id=30).update(value=1+overlong_coeff)
            accepted_payment = accepted_payment + accepted_payment * (kslp_coeffs_all + overlong_coeff)

            #10 КУ управленческий коэффициент
            if service.managerial_coefficient_id:
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=service.managerial_coefficient_id)
                accepted_payment = accepted_payment * Decimal(COEFFICIENT_TYPES[service.managerial_coefficient_id]['value'])
        if term == 2:
            if service.ksg_smo == '5' and is_stimulation_of_superovulation:
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=244)
                accepted_payment = accepted_payment * Decimal(COEFFICIENT_TYPES[244]['value'])
            if service.ksg_smo == '5' and is_complete_cycle_eco:
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=245)
                accepted_payment = accepted_payment * Decimal(COEFFICIENT_TYPES[245]['value'])
            if service.ksg_smo == '5' and is_not_complete_cycle_eco:
                ProvidedServiceCoefficient.objects.get_or_create(
                    service=service, coefficient_id=246)
                accepted_payment = accepted_payment * Decimal(COEFFICIENT_TYPES[246]['value'])

    elif term in (1, 2) and not service.is_ksg_payment:
        accepted_payment = tariff
    elif term == 3 or term is None:
        quantity = service.quantity or 1

        if service.service_group in (29, 31):
            accepted_payment = tariff
        else:
            accepted_payment = tariff * quantity
            tariff = tariff * quantity

        # диспансеризации мобильные бригады
        if is_mobile_brigade and service.service_group in (7,  11, 15, 16,  12, 13,  4, 9):
            accepted_payment = accepted_payment + round_money(accepted_payment * Decimal(0.07))
            provided_tariff = provided_tariff + round_money(provided_tariff * Decimal(0.07))
            ProvidedServiceCoefficient.objects.get_or_create(
                service=service, coefficient_id=5)

    elif service.event.term_id == 4:
        quantity = service.quantity or 1
        accepted_payment = tariff * quantity
        provided_tariff = provided_tariff * quantity
    else:
        raise ValueError(u'Strange term')

    return {'tariff': round_money(tariff),
            'calculated_payment': round_money(accepted_payment),
            'accepted_payment': round_money(accepted_payment),
            'provided_tariff': round_money(provided_tariff)}


def main():
    register_element = get_register_element()

    while register_element:
        print register_element
        logger.info(u'%s начала проходить МЭК', register_element['organization_code'])

        current_period = '%s-%s-01' % (register_element['year'],
                                       register_element['period'])
        current_period = datetime.strptime(current_period, '%Y-%m-%d').date()

        set_status(register_element, 20)

        if register_element['status'] == 6:
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
            update_payment_kind_newborn(register_element)
            update_payment_kind_not_attachment(register_element)
            update_wrong_date(register_element)
            update_ksg(register_element)
            checks.check_so_fucking_fond(register_element)

            checks.check_ksg(register_element)
            checks.check_service_ksg(register_element)
            checks.check_second_service_in_event(register_element)
            checks.check_pathology_pregnant_women(register_element)
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
            checks.underpay_wrong_examination_children_age(register_element)
            checks.underpay_wrong_age_examination_children_adopted(register_element)
            checks.underpay_wrong_age_examination_children_difficult(register_element)

            checks.underpay_wrong_age_prelim_examination_children(register_element)
            checks.underpay_wrong_age_examination_adult(register_element)

            checks.underpay_service_term_mismatch(register_element)
            checks.underpay_service_term_kind_mismatch(register_element)
            checks.underpay_incorrect_examination_events(register_element)
            checks.underpay_incorrect_examination_events_2018(register_element)
            checks.underpay_hitech_with_small_duration(register_element)
            checks.underpay_wrong_adult_examination_not_attachment(register_element)
            checks.underpay_wrong_hospital_quantity(register_element)
            #checks.check_license(register_element)
            checks.underpay_ill_formed_children_examination2(register_element)

        print 'iterate tariff', register_element
        calculate_tariff(register_element)
        checks.underpay_old_examination_services(register_element)

        print u'stomat, outpatient, examin'
        if register_element['status'] == 500:
            checks.underpay_repeated_service(register_element)
            checks.underpay_repeated_preventive_examination_event(register_element)
            checks.underpay_wrong_service_after_death(register_element)
            checks.check_cross_date(register_element)
            checks.check_adult_examination_single_visit(register_element)
            checks.underpay_outpatient_event(register_element)

            #update_payment_kind(register_element)
            #update_payment_kind_newborn(register_element)
            #update_patient_attachment_code(register_element)
            #calculate_tariff(register_element)
            #update_payment_kind_newborn(register_element)
            #update_payment_kind(register_element)
            #identify_patient(register_element)
            #checks.underpay_repeated_service(register_element)
            #checks.underpay_duplicate_examination_in_current_register(register_element)
            #checks.check_adult_examination_single_visit(register_element)
        else:
            checks.underpay_wrong_service_after_death(register_element)
            checks.underpay_wrong_very_old_policy(register_element)
            checks.underpay_wrong_person_in_other_company(register_element)
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
            checks.check_cross_date(register_element)
            checks.check_wrong_operation_dates(register_element)
            checks.check_adult_examination_single_visit(register_element)
            checks.underpay_outpatient_event(register_element)

        correct.update_wrong_accepted_payment(register_element)
        correct.update_wrong_invoiced_payment(register_element)
        correct.update_accepted_payment_non_payment_services(register_element)
        correct.update_payment_type_services_operations(register_element)
        comments.comment_not_active_policy(register_element)
        correct.delete_wrong_du(register_element)
        print Sanction.objects.filter(
            service__event__record__register__is_active=True,
            service__event__record__register__year=register_element['year'],
            service__event__record__register__period=register_element['period'],
            service__event__record__register__organization_code=register_element['organization_code']
        ).count()

        if register_element['status'] == 6:
            set_status(register_element, 8)
        #elif register_element['status'] in (5, 500):
        #    set_status(register_element, 8)

        logger.info(u'%s закончила проходить МЭК', register_element['organization_code'])

        register_element = get_register_element()


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()
