#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.func import (DIVISION_1, DIVISION_2, DIVISION_1_2,
                            DIVISION_ALL_1_2, print_act)


### Поликлиника спец.мед.помощь по поводу забол. (посещения)
def policlinic_disease_spec_visit():
    """
    Поликлиника спец.мед.помощь по поводу забол. (посещения)
    """
    title = u'Поликлиника спец.мед.помощь по поводу забол. (посещения)'
    pattern = 'policlinic_disease_spec_visit'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
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
                 and medical_service.reason_fk = 1
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


### Поликлиника спец.мед.помощь по поводу забол. (обращения)
def policlinic_disease_spec_treatment():
    """
    Поликлиника спец.мед.помощь по поводу забол. (обращения)
    """
    title = u'Поликлиника спец.мед.помощь по поводу забол. (обращения)'
    pattern = 'policlinic_disease_spec_treatment'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  else medical_service.division_fk end as division,

             count(distinct provided_service.event_fk),
             count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.event_fk END),
             count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.event_fk END)

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
                 and medical_service.reason_fk = 1
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


### Поликлиника спец.мед.помощь по поводу забол. (числ. лиц)
def policlinic_disease_spec_patients():
    """
    Поликлиника спец.мед.помощь по поводу забол. (числ. лиц)
    """
    title = u'Поликлиника спец.мед.помощь по поводу забол. (числ. лиц)'
    pattern = 'policlinic_disease_spec_patients'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  when medical_service.code in ('049021', '149021') then 100002
                  when medical_service.code in ('049022', '149022') then 100003
                  else medical_service.division_fk end as division,

             count(distinct (medical_register_record.patient_fk, medical_service.division_fk,
                            medical_service.code like '0%')),
             count(distinct CASE WHEN medical_service.code like '0%'
                            THEN (medical_service.division_fk , medical_register_record.patient_fk) END),
             count(distinct CASE WHEN medical_service.code like '1%'
                            THEN (medical_service.division_fk , medical_register_record.patient_fk) END)

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
                 and medical_service.reason_fk = 1
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (5)
                 )
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


### Поликлиника спец.мед.помощь по поводу забол. (стоимость)
def policlinic_disease_spec_cost():
    """
    Поликлиника спец.мед.помощь по поводу забол. (стоимость)
    """
    title = u'Поликлиника спец.мед.помощь по поводу забол. (стоимость)'
    pattern = 'policlinic_disease_spec_cost'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (402, 418, 417) THEN 402
                  when medical_service.division_fk in (406, 421) THEN 406
                  when medical_service.division_fk in (405, 414) THEN 405
                  when medical_service.division_fk in (423, 435) THEN 423
                  when medical_service.division_fk in (425, 498) THEN 425
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  when medical_service.division_fk in (408, 433, 434) then 408
                  when medical_service.code in ('049021', '149021') then 100002
                  when medical_service.code in ('049022', '149022') then 100003
                  else medical_service.division_fk end as division,

             sum(provided_service.accepted_payment),
             sum(CASE WHEN medical_service.code like '0%'
                            THEN provided_service.accepted_payment END),
             sum(CASE WHEN medical_service.code like '1%'
                            THEN provided_service.accepted_payment END)

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
                 and medical_service.reason_fk = 1
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
                 and medical_service.group_fk is null)
                 or medical_service.group_fk in (5)
                 )
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


### Поликлиника перв.мед.помощь (по поводу заболевания)
def policlinic_disease_primary():
    """
    Поликлиника перв.мед.помощь (по поводу заболевания)
    """
    title = u'Поликлиника перв.мед.помощь (по поводу заболевания)'
    pattern = 'policlinic_disease_primary'
    query = """
            SELECT mr.organization_code,
            ms.division_fk as division,

            count(distinct(mrr.patient_fk, ms.code like '0%')),
            count(distinct CASE WHEN ms.code like '0%'
              THEN (mrr.patient_fk) END),
            count(distinct CASE WHEN ms.code like '1%'
              THEN (mrr.patient_fk) END),

            count(distinct pe.id_pk),
            count(distinct CASE WHEN ms.code like '0%' THEN pe.id_pk END),
            count(distinct CASE WHEN ms.code like '1%' THEN pe.id_pk END),

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
            and pe.term_fk = 3
            and ms.reason_fk = 1
            and ms.division_fk in (399, 401, 403, 443, 444)
            and ps.payment_kind_fk = 1
            GROUP BY mr.organization_code, division
            """

    column_position = [399, 401, 403, 443, 444]

    column_division = {(399, 401, 403, 443, 444): DIVISION_ALL_1_2}

    column_length = {(399, 401, 403, 443, 444): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника свод (по поводу заболевания)
def policlinic_disease_all():
    """
    Поликлиника свод (по поводу заболевания)
    """
    title = u'Поликлиника свод (по поводу заболевания)'
    pattern = 'policlinic_disease_all'
    query = """
            SELECT mr.organization_code,
            100000  as division,

            count(distinct(ms.division_fk, mrr.patient_fk, ms.code like '0%')),
            count(distinct CASE WHEN ms.code like '0%'
              THEN (ms.division_fk, mrr.patient_fk) END),
            count(distinct CASE WHEN ms.code like '1%'
              THEN (ms.division_fk, mrr.patient_fk) END),

            count(distinct CASE WHEN (ms.group_fk != 5 or ms.group_fk is nuLL) THEN pe.id_pk END),
            count(distinct CASE WHEN ms.code like '0%' and (ms.group_fk != 5 or ms.group_fk is nuLL) THEN pe.id_pk END),
            count(distinct CASE WHEN ms.code like '1%' and (ms.group_fk != 5 or ms.group_fk is nuLL) THEN pe.id_pk END),

            count(distinct CASE WHEN (ms.group_fk != 5 or ms.group_fk is nuLL)  THEN ps.id_pk END),
            count(distinct CASE WHEN ms.code like '0%' and (ms.group_fk != 5 or ms.group_fk is nuLL)  THEN ps.id_pk END),
            count(distinct CASE WHEN ms.code like '1%' and (ms.group_fk != 5 or ms.group_fk is nuLL)  THEN ps.id_pk END),

            sum(ps.tariff),
            COALESCE(sum(CASE WHEN ms.code like '0%' THEN ps.tariff END), 0),
            COALESCE(sum(CASE WHEN ms.code like '1%' THEN ps.tariff END), 0)

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
            and ps.payment_kind_fk = 1
            and ((pe.term_fk = 3 and ms.reason_fk = 1)
            or ms.group_fk = 5)

            GROUP BY mr.organization_code, division
            """

    column_position = [100000]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {(100000, ): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            policlinic_disease_spec_visit(),
            policlinic_disease_spec_treatment(),
            policlinic_disease_spec_patients(),
            policlinic_disease_spec_cost(),
            policlinic_disease_primary(),
            policlinic_disease_all(),
        ]
        for act in acts:
            print_act(year, period, act)

