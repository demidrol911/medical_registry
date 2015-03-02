#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import (DIVISION_1, DIVISION_2, DIVISION_1_2,
                            DIVISION_ALL_1_2, print_act, print_act_1)


### Поликлиника перв.мед.помощь (с профилактической целью)
def policlinic_preventive_primary():
    """
    Поликлиника перв.мед.помощь (с профилактической целью)
    """
    title = u'Поликлиника перв.мед.помощь (с профилактической целью)'
    pattern = 'policlinic_preventive_primary'
    query = """
              SELECT

             medical_register.organization_code,

             case when medical_service.code in ('001038', '101038') THEN 100000
                  when medical_service.code in ('001039', '101039') THEN 100001
                  else medical_service.division_fk end as division,

            count(distinct(medical_service.reason_fk, medical_register_record.patient_fk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                  THEN (medical_service.reason_fk, medical_register_record.patient_fk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                  THEN (medical_service.reason_fk, medical_register_record.patient_fk) END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END), 0)

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
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null) or medical_service.group_fk = 4)

            group by medical_register.organization_code, division
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
             SELECT

             medical_register.organization_code,

             100000 as division,

             0,
             sum(provided_service.tariff),
             0,

             0,
             -SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL
             THEN round(provided_service.tariff*0.6, 2) ELSE 0 END),
             0,

             count(distinct case when medical_service.code in ('019214', '019215') then provided_service.id_pk end),
             count(distinct case when medical_service.code in ('019214', '019215') and patient.gender_fk = 1
                   then provided_service.id_pk end),
             count(distinct case when medical_service.code in ('019214', '019215') and patient.gender_fk = 2
                   then provided_service.id_pk end)


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
                 on medical_register_record.patient_fk = patient.id_pk

             LEFT JOIN provided_service_coefficient
                  ON provided_service_coefficient.service_fk = provided_service.id_pk
                      AND provided_service_coefficient.coefficient_fk=3

             WHERE medical_register.is_active
                 AND medical_register.year = '{year}'
                 AND medical_register.period = '{period}'
                 and provided_service.payment_type_fk = 2
                 and ((provided_event.term_fk = 3
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null) or medical_service.group_fk = 4 or
                 medical_service.code in ('019214', '019215', '019216', '019217'))
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


### Поликлиника спец.мед.помощь с профилактической целью (посещения)
def policlinic_preventive_spec_visit():
    """
    Поликлиника спец.мед.помощь с профилактической целью (посещения)
    """
    title = u'Поликлиника спец.мед.помощь с профилактической целью (посещения)'
    pattern = 'policlinic_preventive_spec_visit'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176

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
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null
            group by medical_register.organization_code, division
            """
    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
                      169, 174, 100000, 100001, 170, 178, 176): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


###Поликлиника спец.мед.помощь с профилактической целью (стоимость)
def policlinic_preventive_spec_cost():
    """
    Поликлиника спец.мед.помощь с профилактической целью (стоимость)
    """
    title = u'Поликлиника спец.мед.помощь с профилактической целью (стоимость)'
    pattern = 'policlinic_preventive_spec_cost'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176

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
                 and provided_event.term_fk = 3
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null
            group by medical_register.organization_code, division
            """
    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
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
                 and provided_event.term_fk = 3
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null
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


### Поликлиника спец.мед.помощь с профилактической целью (численность лиц)
def policlinic_preventive_spec_patients():
    """
    Поликлиника спец.мед.помощь с профилактической целью (численность лиц)
    """
    title = u'Поликлиника спец.мед.помощь с профилактической целью (численность лиц)'
    pattern = 'policlinic_preventive_spec_patients'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176

                  else medical_service.division_fk end as division,

             count(distinct (medical_service.division_fk, medical_register_record.id_pk,
                             medical_service.code like '0%')),
             count(distinct CASE WHEN medical_service.code like '0%'
                   THEN (medical_service.division_fk, medical_register_record.id_pk) END),
             count(distinct CASE WHEN medical_service.code like '1%'
                   THEN (medical_service.division_fk, medical_register_record.id_pk) END)

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
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null
            group by medical_register.organization_code, division
            """
    column_position = [409, 413, 419, 402, 407, 425, 408, 411,
                       410, 426, 406, 412, 405, 404, 499, 423,
                       169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (409, 413, 419, 402, 407, 425, 408, 411, 410, 426, 406, 412, 405, 404, 423,
         169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(409, 413, 419, 402, 407, 425, 408, 411,
                      410, 426, 406, 412, 405, 404, 499, 423,
                      169, 174, 100000, 100001, 170, 178, 176): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника свод (с профилактической целью)
def policlinic_preventive_all():
    """
    Поликлиника свод (с профилактической целью)
    """
    title = u'Поликлиника свод (с профилактической целью)'
    pattern = 'policlinic_preventive_all'
    query = """
            SELECT

             medical_register.organization_code,

             100000 as division,


            count(distinct CASE when medical_service.group_fk is NULL THEN
                  (medical_service.reason_fk, medical_service.division_fk,
                  medical_register_record.patient_fk, medical_service.code like '0%') END)+
            count(distinct CASE when medical_service.group_fk is NOT NULL
                  and medical_service.code not in ('019214', '019215') THEN
                  (medical_service.code, medical_register_record.patient_fk, medical_service.code like '0%') END),

            count(distinct CASE when medical_service.group_fk is NULL
                                     AND medical_service.code like '0%' THEN
                  (medical_service.reason_fk, medical_service.division_fk, medical_register_record.patient_fk) END)+
            count(distinct CASE when medical_service.group_fk is NOT NULL
                                     and medical_service.code not in ('019214', '019215') AND
                                     medical_service.code like '0%' THEN
                  (medical_service.code, medical_register_record.patient_fk) END),

            count(distinct CASE when medical_service.group_fk is NULL
                                     AND medical_service.code like '1%' THEN
                  (medical_service.reason_fk, medical_service.division_fk, medical_register_record.patient_fk) END)+
            count(distinct CASE when medical_service.group_fk is NOT NULL
                                     and medical_service.code not in ('019214', '019215') AND
                                     medical_service.code like '1%' THEN
                  (medical_service.code, medical_register_record.patient_fk) END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END), 0)


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
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (4) OR medical_service.code in ('019216', '019217', '019214', '019215'))

            group by medical_register.organization_code, division
            """

    column_position = [100000]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {(100000, ): 3}

    column_separator = {100000: 2}

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
                 and medical_service.reason_fk in (2, 3)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (4) OR medical_service.code in ('019216', '019217', '019214', '019215'))
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


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            policlinic_preventive_spec_visit(),
            policlinic_preventive_spec_cost(),
            policlinic_preventive_spec_patients(),
            policlinic_preventive_all(),
        ]
        for act in acts:
            print_act(year, period, act)
        print_act_1(year, period, policlinic_preventive_primary())
