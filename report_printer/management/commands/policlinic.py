#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.func import (DIVISION_1, DIVISION_2, DIVISION_1_2,
                            DIVISION_ALL_1_2, print_act, print_act_1)


### Поликлиника спец.мед.помощь свод (посещения)
def policlinic_spec_visit():
    """
    Поликлиника спец.мед.помощь свод (посещения)
    """
    title = u'Поликлиника спец.мед.помощь свод (посещения)'
    pattern = 'policlinic_spec_visit'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498, 179, 212) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  when medical_service.division_fk in (409, 163, 196) then 409
                  when medical_service.division_fk in (413, 167, 200) then 409
                  else medical_service.division_fk end as division,

             count(distinct provided_service.id_pk),
             count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
             count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END)

             FROM provided_service
             JOIN medical_service
                 ON provided_service.code_fk = medical_service.id_pk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk

             WHERE medical_register.is_active
                 AND medical_register.year = '{year}'
                 AND medical_register.period = '{period}'
                 and provided_service.payment_type_fk = 2
                 and provided_event.term_fk = 3
                 and medical_service.reason_fk in (1, 2, 3, 5)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null
            group by medical_register.organization_code, division
            """

    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       100002, 100003,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         100002, 100003,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
                      100002, 100003,
                      169, 174, 100000, 100001, 170, 178, 176): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника спец.мед.помощь свод (численность лиц)
def policlinic_spec_patients():
    """
    Поликлиника спец.мед.помощь свод (численность лиц)
    """
    title = u'Поликлиника спец.мед.помощь свод (численность лиц)'
    pattern = 'policlinic_spec_patients'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498, 179, 212) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  when medical_service.division_fk in (409, 163, 196) then 409
                  when medical_service.division_fk in (413, 167, 200) then 409
                  when medical_service.code in ('049021', '149021') then 100002
                  when medical_service.code in ('049022', '149022') then 100003
                  else medical_service.division_fk end as division,

             count(distinct (medical_service.reason_fk, medical_register_record.patient_fk,
                             medical_service.division_fk,
                             medical_service.code like '0%')),
             count(distinct CASE WHEN medical_service.code like '0%'
                            THEN (medical_service.reason_fk, medical_service.division_fk ,
                                  medical_register_record.patient_fk) END),
             count(distinct CASE WHEN medical_service.code like '1%'
                            THEN (medical_service.reason_fk, medical_service.division_fk ,
                                  medical_register_record.patient_fk) END)

             FROM provided_service
             JOIN medical_service
                 ON provided_service.code_fk = medical_service.id_pk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk

             WHERE medical_register.is_active
                 AND medical_register.year = '{year}'
                 AND medical_register.period = '{period}'
                 and provided_service.payment_type_fk = 2
                 and ((provided_event.term_fk = 3
                 and medical_service.reason_fk in (1, 2, 3, 5)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (5))
            group by medical_register.organization_code, division
            """
    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       100002, 100003,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         100002, 100003,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
                      100002, 100003,
                      169, 174, 100000, 100001, 170, 178, 176): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника спец.мед.помощь свод (стоимость)
def policlinic_spec_cost():
    """
    Поликлиника спец.мед.помощь свод (стоимость)
    """
    title = u'Поликлиника спец.мед.помощь свод (стоимость)'
    pattern = 'policlinic_spec_cost'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498, 179, 212) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  when medical_service.division_fk in (409, 163, 196) then 409
                  when medical_service.division_fk in (413, 167, 200) then 409
                  when medical_service.code in ('049021', '149021') then 100002
                  when medical_service.code in ('049022', '149022') then 100003
                  else medical_service.division_fk end as division,

             sum(provided_service.accepted_payment),
             sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END),
             sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END)

             FROM provided_service
             JOIN medical_service
                 ON provided_service.code_fk = medical_service.id_pk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk

             WHERE medical_register.is_active
                 AND medical_register.year = '{year}'
                 AND medical_register.period = '{period}'
                 and provided_service.payment_type_fk = 2
                 and ((provided_event.term_fk = 3
                 and medical_service.reason_fk in (1, 2, 3, 5)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (5))
            group by medical_register.organization_code, division
            """
    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       100002, 100003,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         100002, 100003,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
                      100002, 100003,
                      169, 174, 100000, 100001, 170, 178, 176): 1}

    column_separator = {176: 5}

    query1 = """
             SELECT

             medical_register.organization_code,

             100000 as division,

             0,
             sum(provided_service.tariff),
             0,

             0,
             -SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL
             THEN round(provided_service.tariff*0.6, 2) ELSE 0 END),
             0


             FROM provided_service
             JOIN medical_service
                 ON provided_service.code_fk = medical_service.id_pk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk

              LEFT JOIN provided_service_coefficient
                  ON provided_service_coefficient.service_fk = provided_service.id_pk
                      AND provided_service_coefficient.coefficient_fk=3

             WHERE medical_register.is_active
                 AND medical_register.year = '{year}'
                 AND medical_register.period = '{period}'
                 and provided_service.payment_type_fk = 2
                 and ((provided_event.term_fk = 3
                 and medical_service.reason_fk in (1, 2, 3, 5)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (5))
            group by medical_register.organization_code, division
            """

    column_position1 = [100000]

    column_division1 = {(100000, ): DIVISION_1}

    column_length1 = {(100000, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length},
                 {'structure': (query1, column_position1, column_division1),
                  'column_length': column_length1,
                  'next': False}]
    }


### Поликлиника свод
def policlinic_all():
    """
    Поликлиника свод
    """
    title = u'Поликлиника свод'
    pattern = 'policlinic_all'
    query = """
            SELECT mr.organization_code,
            100000  as division,

            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk = 24)
                       THEN (ms.reason_fk, ms.division_fk, mrr.patient_fk, ms.code like '0%') END)+
            count(distinct CASE WHEN (ms.group_fk in (4, 5, 9))
                       THEN (ms.group_fk, mrr.patient_fk, ms.code like '0%') END),

            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk = 24) and ms.code like '0%'
              THEN (ms.reason_fk, ms.division_fk, mrr.patient_fk) END)+
            count(distinct CASE WHEN (ms.group_fk in (4, 5, 9) and ms.code like '0%')
                       THEN (ms.group_fk, mrr.patient_fk) END),

            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk = 24) and ms.code like '1%'
              THEN (ms.reason_fk, ms.division_fk, mrr.patient_fk) END)+
            count(distinct CASE WHEN (ms.group_fk in (4, 5, 9) and ms.code like '1%')
                       THEN (ms.group_fk, mrr.patient_fk) END),

            count(distinct case when (ms.group_fk is NULL or ms.group_fk = 24) and ms.reason_fk = 1 then pe.id_pk END),
            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk = 24)
                                 and ms.reason_fk = 1 and ms.code like '0%' THEN pe.id_pk END),
            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk = 24)
                                 and ms.reason_fk = 1 and ms.code like '1%' THEN pe.id_pk END),

            count(distinct case when (ms.group_fk is NULL or ms.group_fk in (24, 4, 9)) THEN ps.id_pk END),
            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk in (24, 4, 9))
                       and ms.code like '0%' THEN ps.id_pk END),
            count(distinct CASE WHEN (ms.group_fk is NULL or ms.group_fk in (24, 4, 9))
                       and ms.code like '1%' THEN ps.id_pk END),


            sum(ps.accepted_payment),
            COALESCE(sum(CASE WHEN ms.code like '0%' THEN ps.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN ms.code like '1%' THEN ps.accepted_payment END), 0)

            FROM provided_service ps
            JOIN medical_service ms
                ON ps.code_fk = ms.id_pk
            JOIN provided_event pe
                ON ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                ON pe.record_fk = mrr.id_pk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN medical_register mr
                ON mrr.register_fk = mr.id_pk
            WHERE mr.is_active
            AND mr.year = '{year}'
            AND mr.period = '{period}'
            and ps.payment_type_fk = 2
            and(((pe.term_fk = 3 and ms.reason_fk = 1 and ps.payment_kind_fk = 1) or ms.group_fk = 5)
            or (((pe.term_fk = 3 and ms.reason_fk in (2, 3) and ms.group_fk is null)
              or ms.group_fk in (4) OR ms.code in ('019216', '019217', '019214', '019215')))
            or (pe.term_fk = 3 and ms.reason_fk = 5))

            GROUP BY mr.organization_code, division
            """

    column_position = [100000]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {(100000, ): 4}

    column_separator = {100000: 2}

    query1 = """
             SELECT

             mr.organization_code,

             100000 as division,

             0,
             sum(ps.tariff),
             0,

             0,
             -SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL
             THEN round(ps.tariff*0.6, 2) ELSE 0 END),
             0

             FROM provided_service ps
                JOIN medical_service ms
                    ON ps.code_fk = ms.id_pk
                JOIN provided_event pe
                    ON ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    ON pe.record_fk = mrr.id_pk
                JOIN patient p
                    on p.id_pk = mrr.patient_fk
                JOIN medical_register mr
                    ON mrr.register_fk = mr.id_pk
                LEFT JOIN provided_service_coefficient
                  ON provided_service_coefficient.service_fk = ps.id_pk
                      AND provided_service_coefficient.coefficient_fk=3

            WHERE mr.is_active
                AND mr.year = '{year}'
                AND mr.period = '{period}'
                and ps.payment_type_fk = 2
                and(((pe.term_fk = 3 and ms.reason_fk = 1 and ps.payment_kind_fk = 1) or ms.group_fk = 5)
                or (((pe.term_fk = 3 and ms.reason_fk in (2, 3) and ms.group_fk is null)
                  or ms.group_fk in (4) OR ms.code in ('019216', '019217', '019214', '019215')))
                or (pe.term_fk = 3 and ms.reason_fk = 5))

            GROUP BY mr.organization_code, division
            """

    column_position1 = [100000]

    column_division1 = {(100000, ): DIVISION_1}

    column_length1 = {(100000, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length},
                 {'structure': (query1, column_position1, column_division1),
                  'column_length': column_length1,
                  'next': False}]
    }


### Поликлиника перв.мед.помощь (свод)
def policlinic_primary():
    """
    Поликлиника перв.мед.помощь (свод)
    """
    title = u'Поликлиника перв.мед.помощь (свод)'
    pattern = 'policlinic_primary'
    query = """
            select
            mr.organization_code,

            case when ms.code in ('001038', '101038') THEN 100000
                  when ms.code in ('001039', '101039') THEN 100001
                  else ms.division_fk end as division,

            count(distinct(ms.reason_fk, mrr.patient_fk, ms.code like '0%')),
            count(distinct CASE WHEN ms.code like '0%'
                  THEN (ms.reason_fk, mrr.patient_fk) END),
            count(distinct CASE WHEN ms.code like '1%'
                  THEN (ms.reason_fk, mrr.patient_fk) END),


            count(distinct ps.id_pk),
            count(distinct CASE WHEN ms.code like '0%' THEN ps.id_pk END),
            count(distinct CASE WHEN ms.code like '1%' THEN ps.id_pk END),

            sum(ps.accepted_payment),
            COALESCE(sum(CASE WHEN ms.code like '0%' THEN ps.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN ms.code like '1%' THEN ps.accepted_payment END), 0)

            FROM provided_service ps
            JOIN medical_service ms
                ON ps.code_fk = ms.id_pk
            JOIN provided_event pe
                ON ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                ON pe.record_fk = mrr.id_pk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            JOIN medical_register mr
                ON mrr.register_fk = mr.id_pk
            WHERE mr.is_active
                 AND mr.year = '{year}'
                 AND mr.period = '{period}'
                 and ps.payment_type_fk = 2
                 and((pe.term_fk = 3 and ms.reason_fk = 1 and ps.payment_kind_fk = 1
                      and ms.division_fk in (399, 401, 403, 443, 444))

                 or ((pe.term_fk = 3 and ms.reason_fk in (2, 3) and ms.group_fk is null and ms.division_fk in (399, 401, 403, 443, 444))
                      or ms.group_fk = 4)

                 or (pe.term_fk = 3 and ms.reason_fk = 5 and ms.division_fk in (399, 401, 403, 443, 444)))

                GROUP BY mr.organization_code, division
            union
            SELECT
            medical_register.organization_code,

            100002 as division,


            count(distinct(medical_register_record.patient_fk, patient.gender_fk)),
            count(distinct CASE WHEN patient.gender_fk = 1
              THEN (medical_register_record.patient_fk) END),
            count(distinct CASE WHEN patient.gender_fk = 2
              THEN (medical_register_record.patient_fk) END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN patient.gender_fk = 1 THEN provided_service.id_pk END),
            count(distinct CASE WHEN patient.gender_fk = 2 THEN provided_service.id_pk END),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN patient.gender_fk = 1 THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN patient.gender_fk = 2 THEN provided_service.accepted_payment END), 0)

            FROM provided_service
            JOIN medical_service
                ON provided_service.code_fk = medical_service.id_pk
            JOIN provided_event
                ON provided_service.event_fk = provided_event.id_pk
            JOIN medical_register_record
                ON provided_event.record_fk = medical_register_record.id_pk
            JOIN medical_register
                ON medical_register_record.register_fk = medical_register.id_pk
            join patient
                on patient.id_pk = medical_register_record.patient_fk

            WHERE medical_register.is_active
                AND medical_register.year = '{year}'
                AND medical_register.period = '{period}'
                and provided_service.payment_type_fk = 2
                and medical_service.code in ('019214', '019215', '019216', '019217')
            group by medical_register.organization_code, division
            """

    column_position = [399, 100002, 401, 403, 100000, 100001,  443, 444]

    column_division = {(399, 100002, 401, 403, 100000, 100001,  443, 444): DIVISION_ALL_1_2}

    column_length = {(399, 100002, 401, 403, 100000, 100001,  443, 444): 3}

    column_separator = {444: 11}

    query1 = """
             select
             mr.organization_code,

             100000 as division,

             0,
             sum(ps.tariff),
             0,

             0,
             -SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL
             THEN round(ps.tariff*0.6, 2) ELSE 0 END),
             0,

             count(distinct case when ms.code in ('019214', '019215') then ps.id_pk end),
             count(distinct case when ms.code in ('019214', '019215') and p.gender_fk = 1
               then ps.id_pk end),
             count(distinct case when ms.code in ('019214', '019215') and p.gender_fk = 2
               then ps.id_pk end)

             FROM provided_service ps
             JOIN medical_service ms
                ON ps.code_fk = ms.id_pk
             JOIN provided_event pe
                ON ps.event_fk = pe.id_pk
             JOIN medical_register_record mrr
                ON pe.record_fk = mrr.id_pk
             JOIN patient p
                on p.id_pk = mrr.patient_fk
             JOIN medical_register mr
                ON mrr.register_fk = mr.id_pk
             LEFT JOIN provided_service_coefficient
                ON provided_service_coefficient.service_fk = ps.id_pk
                   AND provided_service_coefficient.coefficient_fk=3

             WHERE mr.is_active
             AND mr.year = '{year}'
             AND mr.period = '{period}'
             and ps.payment_type_fk = 2
             and((pe.term_fk = 3 and ms.reason_fk = 1 and ps.payment_kind_fk = 1
                  and ms.division_fk in (399, 401, 403, 443, 444))

             or ((pe.term_fk = 3 and ms.reason_fk in (2, 3) and ms.group_fk is null
                  and ms.division_fk in (399, 401, 403, 443, 444))
                  or ms.group_fk = 4 or ms.code in ('019214', '019215', '019216', '019217'))

             or (pe.term_fk = 3 and ms.reason_fk = 5 and ms.division_fk in (399, 401, 403, 443, 444)))

             GROUP BY mr.organization_code, division
             """

    column_position1 = [100000]

    column_division1 = {(100000, ): DIVISION_1}

    column_length1 = {(100000, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length},
                 {'structure': (query1, column_position1, column_division1),
                  'column_length': column_length1,
                  'next': False}]
    }


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            policlinic_spec_visit(),
            policlinic_spec_patients(),
            policlinic_spec_cost(),
            policlinic_all(),
        ]
        for act in acts:
            print_act(year, period, act)
        print_act_1(year, period, policlinic_primary())
