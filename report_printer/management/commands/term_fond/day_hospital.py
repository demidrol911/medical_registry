#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import (
    DIVISION_1, DIVISION_2,
    DIVISION_1_2, DIVISION_ALL_1_2,
    print_act
)


### Дневной стационар
def day_hospital_services():
    """
    Дневной стационар (выбывшие больные)
    """
    title = u'Дневной стационар (выбывшие больные)'
    pattern = 'day_hospital_services'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.group_fk = 28 THEN 100000
                 WHEN medical_service.group_fk = 17 THEN 100001
                 ELSE tariff_profile.id_pk
            END AS division,
            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (28, 17))
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_cost():
    """
    Дневной стационар (стоимость)
    """
    title = u'Дневной стационар (стоимость)'
    pattern = 'day_hospital_cost'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.group_fk = 28 THEN 100000
                 WHEN medical_service.group_fk = 17 THEN 100001
                 ELSE tariff_profile.id_pk
            END AS division,
            sum(provided_service.accepted_payment),
            sum(CASE WHEN medical_service.code like '0%'
                     THEN provided_service.accepted_payment END),
            sum(CASE WHEN medical_service.code like '1%'
                     THEN provided_service.accepted_payment END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (28, 17))
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_days():
    """
    Дневной стационар (пациенто-дни)
    """
    title = u'Дневной стационар (пациенто-дни)'
    pattern = 'day_hospital_days'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.group_fk = 28 THEN 100000
                 WHEN medical_service.group_fk = 17 THEN 100001
                 ELSE tariff_profile.id_pk
            END AS division,
            sum(provided_service.quantity),
            sum(CASE WHEN medical_service.code like '0%'
                     THEN provided_service.quantity END),
            sum(CASE WHEN medical_service.code like '1%'
                     THEN provided_service.quantity END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (28, 17))
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_patients():
    """
    Дневной стационар (численность лиц)
    """
    title = u'Дневной стационар (численность лиц)'
    pattern = 'day_hospital_patients'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.group_fk = 28 THEN 100000
                 WHEN medical_service.group_fk = 17 THEN 100001
                 ELSE tariff_profile.id_pk
            END AS division,
            count(distinct (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk)),
            count(distinct CASE WHEN medical_service.code like '0%'
                     THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                     THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END)
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
                        ON medical_register_record.patient_fk = patient.id_pk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (28, 17))
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_home_services():
    """
    Дневной стационар на дому (выбывшие больные)
    """
    title = u'Дневной стационар на дому (выбывшие больные)'
    pattern = 'day_hospital_home_services'
    query = """
            SELECT
            medical_organization.code,
            tariff_profile.id_pk AS division,
            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk = 12
                     AND medical_service.group_fk IS NULL)
                     )
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_home_cost():
    """
    Дневной стационар на дому (стоимость)
    """
    title = u'Дневной стационар на дому (стоимость)'
    pattern = 'day_hospital_home_cost'
    query = """
            SELECT
            medical_organization.code,
            tariff_profile.id_pk AS division,
            sum(provided_service.accepted_payment),
            sum(CASE WHEN medical_service.code like '0%'
                     THEN provided_service.accepted_payment END),
            sum(CASE WHEN medical_service.code like '1%'
                     THEN provided_service.accepted_payment END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk = 12
                     AND medical_service.group_fk IS NULL)
                     )
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_home_days():
    """
    Дневной стационар на дому (пациенто-дни)
    """
    title = u'Дневной стационар на дому (пациенто-дни)'
    pattern = 'day_hospital_home_days'
    query = """
            SELECT
            medical_organization.code,
            tariff_profile.id_pk AS division,
            sum(provided_service.quantity),
            sum(CASE WHEN medical_service.code like '0%'
                     THEN provided_service.quantity END),
            sum(CASE WHEN medical_service.code like '1%'
                     THEN provided_service.quantity END)
            FROM provided_service
                    JOIN provided_event
                        ON provided_event.id_pk=provided_service.event_fk
                    JOIN medical_register_record
                        ON medical_register_record.id_pk=provided_event.record_fk
                    JOIN medical_register
                        ON medical_register.id_pk=medical_register_record.register_fk
                    JOIN medical_service
                        ON medical_service.id_pk=provided_service.code_fk
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk = 12
                     AND medical_service.group_fk IS NULL)
                     )
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_home_patients():
    """
    Дневной стационар на дому (численность лиц)
    """
    title = u'Дневной стационар на дому (численность лиц)'
    pattern = 'day_hospital_home_patients'
    query = """
            SELECT
            medical_organization.code,
            tariff_profile.id_pk AS division,
            count(distinct (tariff_profile.id_pk, patient.id_pk,  medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                     THEN (tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                     THEN (tariff_profile.id_pk, patient.id_pk) END)
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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk = 12
                     AND medical_service.group_fk IS NULL)
                     )
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [
        39,  40,  41,  42,  43,  44,
        45,  46,  47,  48,  49,  50,
        51,  52,  53, 100000, 100001
    ]

    column_division = {
        (39, 43, 45, 46, 47,
         48, 49, 51, 52, 53,
         100000, 100001): DIVISION_1_2,
        (40, 41, 44, 50): DIVISION_2,
        (42, ): DIVISION_1
    }

    column_length = {
        (39,  40,  41,  42,  43,  44,
         45,  46,  47,  48,  49,  50,
         51,  52,  53, 100000, 100001): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital_home():
    """
    Дневной стационар на дому свод
    """
    title = u'Дневной стационар на дому свод'
    pattern = 'day_hospital_home'
    query = """
            SELECT
            medical_organization.code,
            100000 AS division,

            count(distinct(tariff_profile.id_pk, patient.id_pk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%' THEN (tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN (tariff_profile.id_pk, patient.id_pk) END),

            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

            sum(provided_service.quantity),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.quantity END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.quantity END), 0),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END), 0)

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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk = 12
                     AND medical_service.group_fk IS NULL)
                     )
                AND provided_service.payment_type_fk IN (2, 4)
            group by medical_organization.code, division
            """

    column_position = [100000, ]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {(100000, ): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def day_hospital():
    """
    Дневной стационар (свод)
    """
    title = u'Дневной стационар (свод)'
    pattern = 'day_hospital'
    query = """
            SELECT
            medical_organization.code,

            100000 AS division,

            count(distinct(medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk,
                           medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END),

            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

            sum(provided_service.quantity),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.quantity END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.quantity END), 0),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END), 0)

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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (17, 28))
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division

            UNION
                SELECT
                medical_organization.code,

                100001 AS division,

                count(distinct(tariff_profile.id_pk, patient.id_pk,
                               medical_service.code like '0%')),
                count(distinct CASE WHEN medical_service.code like '0%'
                            THEN (tariff_profile.id_pk, patient.id_pk) END),
                count(distinct CASE WHEN medical_service.code like '1%'
                            THEN (tariff_profile.id_pk, patient.id_pk) END),

                count(distinct provided_service.id_pk),
                count(distinct CASE WHEN medical_service.code like '0%'
                            THEN provided_service.id_pk END),
                count(distinct CASE WHEN medical_service.code like '1%'
                            THEN provided_service.id_pk END),

                sum(provided_service.quantity),
                COALESCE(sum(CASE WHEN medical_service.code like '0%'
                               THEN provided_service.quantity END), 0),
                COALESCE(sum(CASE WHEN medical_service.code like '1%'
                               THEN provided_service.quantity END), 0),

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
                        LEFT JOIN tariff_profile
                            ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                        LEFT JOIN medical_division
                            ON medical_division.id_pk = provided_service.division_fk
                        LEFT JOIN medical_service_term
                            ON medical_service_term.id_pk = medical_division.term_fk
                        JOIN medical_organization
                            ON medical_organization.id_pk = provided_service.organization_fk
                WHERE medical_register.year='{year}'
                    AND medical_register.period='{period}'
                    AND is_active
                    And medical_service.group_fk=28
                    AND provided_service.payment_type_fk IN (2, 4)
                GROUP BY medical_organization.code, division
            """

    column_position = [100000, 100001]

    column_division = {(100000, 100001): DIVISION_ALL_1_2}

    column_separator = {100000: 2}

    column_length = {(100000, 100001): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


def day_hospital_all():
    """
    Дневной стационар свод + на дому свод
    """
    title = u'Дневной стационар свод + на дому свод'
    pattern = 'day_hospital_all'
    query = """
            SELECT
            medical_organization.code,

            100000 AS division,

            count(distinct(medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk,
                           medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                THEN (medical_service_term.id_pk, tariff_profile.id_pk, patient.id_pk) END),

            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN medical_service.code like '0%' THEN provided_service.id_pk END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN provided_service.id_pk END),

            sum(provided_service.quantity),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.quantity END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.quantity END), 0),

            sum(provided_service.accepted_payment),
            COALESCE(sum(CASE WHEN medical_service.code like '0%' THEN provided_service.accepted_payment END), 0),
            COALESCE(sum(CASE WHEN medical_service.code like '1%' THEN provided_service.accepted_payment END), 0)

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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    LEFT JOIN medical_division
                        ON medical_division.id_pk = provided_service.division_fk
                    LEFT JOIN medical_service_term
                        ON medical_service_term.id_pk = medical_division.term_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 2
                     AND medical_service_term.id_pk IN (10, 11, 12)
                     AND medical_service.group_fk IS NULL)
                     OR medical_service.group_fk IN (17, 28))
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division

            UNION
                SELECT
                medical_organization.code,

                100001 AS division,

                count(distinct(tariff_profile.id_pk, patient.id_pk, medical_service.code like '0%')),
                count(distinct CASE WHEN medical_service.code like '0%'
                            THEN (tariff_profile.id_pk, patient.id_pk) END),
                count(distinct CASE WHEN medical_service.code like '1%'
                            THEN (tariff_profile.id_pk, patient.id_pk) END),

                count(distinct provided_service.id_pk),
                count(distinct CASE WHEN medical_service.code like '0%'
                            THEN provided_service.id_pk END),
                count(distinct CASE WHEN medical_service.code like '1%'
                            THEN provided_service.id_pk END),

                sum(provided_service.quantity),
                COALESCE(sum(CASE WHEN medical_service.code like '0%'
                               THEN provided_service.quantity END), 0),
                COALESCE(sum(CASE WHEN medical_service.code like '1%'
                               THEN provided_service.quantity END), 0),

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
                        LEFT JOIN tariff_profile
                            ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                        LEFT JOIN medical_division
                            ON medical_division.id_pk = provided_service.division_fk
                        LEFT JOIN medical_service_term
                            ON medical_service_term.id_pk = medical_division.term_fk
                        JOIN medical_organization
                            ON medical_organization.id_pk = provided_service.organization_fk
                WHERE medical_register.year='{year}'
                    AND medical_register.period='{period}'
                    AND is_active
                    And medical_service.group_fk=28
                    AND provided_service.payment_type_fk IN (2, 4)
                GROUP BY medical_organization.code, division
            """

    column_position = [100000, 100001]

    column_division = {(100000, 100001): DIVISION_ALL_1_2}
    column_separator = {100000: 2}

    column_length = {(100000, 100001): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            day_hospital_services(),
            day_hospital_cost(),
            day_hospital_days(),
            day_hospital_patients(),
            day_hospital_home_services(),
            day_hospital_home_cost(),
            day_hospital_home_days(),
            day_hospital_home_patients(),
            day_hospital_home(),
            day_hospital(),
            day_hospital_all(),
        ]
        for act in acts:
            print_act(year, period, act)
