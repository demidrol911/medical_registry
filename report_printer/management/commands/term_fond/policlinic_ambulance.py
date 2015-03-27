#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import (
    DIVISION_2, DIVISION_1_2,
    DIVISION_ALL_1_2, print_act
)


### Поликлиника перв.мед.помощь (в неотложной форме)
def policlinic_ambulance_primary():
    """
    Поликлиника перв.мед.помощь (в неотложной форме)
    """
    title = u'Поликлиника перв.мед.помощь (в неотложной форме)'
    pattern = 'policlinic_ambulance_primary'
    query = """
         SELECT medical_register.organization_code,
         medical_service.division_fk as division,

         count(distinct(medical_register_record.patient_fk, medical_service.code like '0%')),
         count(distinct CASE WHEN medical_service.code like '0%'
                  THEN (medical_register_record.patient_fk) END),
         count(distinct CASE WHEN medical_service.code like '1%'
                  THEN (medical_register_record.patient_fk) END),

         count(distinct provided_service.id_pk),
         count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
         count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

         sum(provided_service.tariff),
         COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.tariff END), 0),
         COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.tariff END), 0)

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
             and medical_service.reason_fk = 5
             and medical_service.division_fk in (399, 401, 403, 443, 444)

        group by medical_register.organization_code, division
        """

    column_position = [399, 401, 403, 443, 444]

    column_division = {(399, 401, 403, 443, 444): DIVISION_ALL_1_2}

    column_length = {(399, 401, 403, 443, 444): 3}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника спец.мед.помощь в неотложной форме (посещения)
def policlinic_ambulance_spec_visit():
    """
    Поликлиника спец.мед.помощь в неотложной форме (посещения)
    """
    title = u'Поликлиника спец.мед.помощь в неотложной форме (посещения)'
    pattern = 'policlinic_ambulance_spec_visit'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (163, 196) THEN 163
                  when medical_service.division_fk in (167, 200) THEN 167
                  when medical_service.division_fk in (179, 212) then 179
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
                 and medical_service.reason_fk = 5
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
            group by medical_register.organization_code, division
            """
    column_position = [163, 167, 419, 402, 407, 179, 408, 411, 410, 426, 406, 412, 405, 404, 499,
                       423, 169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (163, 167, 419, 402, 407, 179, 408,
         411, 410, 426, 406, 412, 405, 404, 423, 169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(163, 167, 419, 402, 407, 179, 408,
                      411, 410, 426, 406, 412, 405, 404,
                      499, 423, 169, 174, 100000, 100001, 170, 178, 176): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника спец.мед.помощь в неотложной форме (стоимость)
def policlinic_ambulance_spec_cost():
    """
    Поликлиника спец.мед.помощь в неотложной форме (стоимость)
    """
    title = u'Поликлиника спец.мед.помощь в неотложной форме (стоимость)'
    pattern = 'policlinic_ambulance_spec_cost'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (163, 196) THEN 163
                  when medical_service.division_fk in (167, 200) THEN 167
                  when medical_service.division_fk in (179, 212) then 179
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
                 and medical_service.reason_fk = 5
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
            group by medical_register.organization_code, division
            """
    column_position = [163, 167, 419, 402, 407, 179, 408, 411, 410, 426, 406, 412, 405, 404, 499,
                       423, 169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (163, 167, 419, 402, 407, 179, 408,
         411, 410, 426, 406, 412, 405, 404, 423, 169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(163, 167, 419, 402, 407, 179, 408,
                      411, 410, 426, 406, 412, 405, 404,
                      499, 423, 169, 174, 100000, 100001, 170, 178, 176): 1}
    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника спец.мед.помощь в неотложной форме (численность лиц)
def policlinic_ambulance_spec_patients():
    """
    Поликлиника спец.мед.помощь в неотложной форме (численность лиц)
    """
    title = u'Поликлиника спец.мед.помощь в неотложной форме (численность лиц)'
    pattern = 'policlinic_ambulance_spec_patients'
    query = """
            SELECT

             medical_register.organization_code,

             case when medical_service.division_fk in (163, 196) THEN 163
                  when medical_service.division_fk in (167, 200) THEN 167
                  when medical_service.division_fk in (179, 212) then 179
                  when medical_service.division_fk in (169, 202, 415) then 169
                  when medical_service.division_fk in (174, 207, 420) then 174
                  when medical_service.division_fk in (170, 203, 416) then 170
                  when medical_service.division_fk in (178, 211, 424) then 178
                  when medical_service.division_fk in (176, 209, 422) then 176
                  else medical_service.division_fk end as division,

             count(distinct (medical_register_record.patient_fk, medical_service.code like '0%')),
             count(distinct CASE WHEN medical_service.code like '0%' THEN medical_register_record.patient_fk END),
             count(distinct CASE WHEN medical_service.code like '1%' THEN medical_register_record.patient_fk END)

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
                 and medical_service.reason_fk = 5
                 and medical_service.division_fk not in (399, 401, 403, 443, 444)
            group by medical_register.organization_code, division
            """
    column_position = [163, 167, 419, 402, 407, 179, 408, 411, 410, 426, 406, 412, 405, 404, 499,
                       423, 169, 174, 100000, 100001, 170, 178, 176]

    column_division = {
        (163, 167, 419, 402, 407, 179, 408,
         411, 410, 426, 406, 412, 405, 404, 423, 169, 174, 100000, 100001, 170, 178, 176): DIVISION_1_2,
        (499, ): DIVISION_2}

    column_length = {(163, 167, 419, 402, 407, 179, 408,
                      411, 410, 426, 406, 412, 405, 404,
                      499, 423, 169, 174, 100000, 100001, 170, 178, 176): 1}
    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Поликлиника свод (в неотложной форме)
def policlinic_ambulance_all():
    """
    Поликлиника свод (в неотложной форме)
    """
    title = u'Поликлиника свод (в неотложной форме)'
    pattern = 'policlinic_ambulance_all'
    query = """
            SELECT

             medical_register.organization_code,

             100000 as division,

             count(distinct(medical_service.division_fk, medical_register_record.patient_fk,
                   medical_service.code like '0%')),
             count(distinct CASE WHEN medical_service.code like '0%'
                      THEN (medical_service.division_fk, medical_register_record.patient_fk) END),
             count(distinct CASE WHEN medical_service.code like '1%'
                      THEN (medical_service.division_fk, medical_register_record.patient_fk) END),

             count(distinct provided_service.id_pk),
             count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
             count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

             sum(provided_service.tariff),
             COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.tariff END), 0),
             COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.tariff END), 0)

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
                 and medical_service.reason_fk = 5

            group by medical_register.organization_code, division
            """
    column_position = [100000]

    column_division = {
        (100000, ): DIVISION_ALL_1_2}

    column_length = {(100000, ): 3}

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
            policlinic_ambulance_primary(),
            policlinic_ambulance_spec_visit(),
            policlinic_ambulance_spec_cost(),
            policlinic_ambulance_spec_patients(),
            policlinic_ambulance_all(),
        ]
        for act in acts:
            print_act(year, period, act)
