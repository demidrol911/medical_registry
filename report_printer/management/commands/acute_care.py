#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.func import (DIVISION_1, DIVISION_2, DIVISION_1_2,
                            DIVISION_ALL_1_2, print_act)


### СМП финансирование по подушевому нормативу
def acute_care():
    """
    СМП финансирование по подушевому нормативу
    """
    title = u'СМП финансирование по подушевому нормативу'
    pattern = 'acute_care'
    query = """
            SELECT
            medical_organization.code,

            medical_division.id_pk AS division,

            count(distinct(medical_division.id_pk, patient.id_pk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                THEN (medical_division.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                THEN (medical_division.id_pk, patient.id_pk) END),

            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%'
                           THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%'
                           THEN provided_service.id_pk END),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%'
                        THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%'
                        THEN provided_service.accepted_payment END), 0)

            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    JOIN patient
                        ON medical_register_record.patient_fk=patient.id_pk
                    JOIN medical_division
                        ON medical_division.id_pk = medical_service.division_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND provided_event.term_fk = 4
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [456, 455, 457, 458]

    column_division = {(456, 455, 457, 458): DIVISION_ALL_1_2}

    column_length = {(456, 455, 457, 458): 3}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


###Поликлиника фин-ние по подушевому нормативу (посещения по поводу заболевания)
def capitation_policlinic():
    """
    Поликлиника фин-ние по подушевому нормативу (посещения по поводу заболевания)
    """
    title = u'Поликлиника фин-ние по подушевому нормативу (посещения по поводу заболевания)'
    pattern = 'capitation_policlinic'
    query = """
            SELECT medical_register.organization_code,

            medical_service.division_fk as division,

            count(distinct(medical_register_record.patient_fk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                  THEN (medical_register_record.patient_fk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                  THEN (medical_register_record.patient_fk) END),

            count(distinct provided_event.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_event.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_event.id_pk END),

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
                AND provided_service.payment_type_fk = 2
                AND provided_event.term_fk = 3
                AND medical_service.reason_fk = 1
                AND provided_service.payment_kind_fk in (2, 3)

            GROUP BY medical_register.organization_code, division
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


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            acute_care(),
            capitation_policlinic(),
        ]
        for act in acts:
            print_act(year, period, act)