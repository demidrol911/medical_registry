#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection
from medical_service_register.path import REESTR_EXP, BASE_DIR
from helpers.const import MONTH_NAME, ACT_CELL_POSITION
from helpers.excel_style import VALUE_STYLE, PERIOD_VALUE_STYLE
from helpers.excel_writer import ExcelWriter

ACT_PATH = ur'{dir}\{title}_{month}_{year}'
TEMP_PATH = ur'{base}\templates\excel_pattern\end_of_month\{template}.xls'

DIVISION_1 = 0
DIVISION_2 = 1
DIVISION_1_2 = 2
DIVISION_ALL_1_2 = 3


### Круглосуточный стационар
def hospital_services():
    """
    Круглосуточный стационар (число госпитализаций)
    """
    title = u'Круглосуточный стационар (число госпитализаций)'
    pattern = 'hospital_services'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.code in ('049023', '149023') THEN 100000
                 WHEN medical_service.code in ('049024', '149024') THEN 100001
                 WHEN medical_service.code in ('098951') THEN 100002
                 WHEN medical_service.code in ('098948') THEN 100003
                 WHEN medical_service.code in ('098949', '098975') THEN 100004
                 WHEN medical_service.code in ('098950') THEN 100005
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
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code, division
            """
    column_position = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
        38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
        26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        100000, 100001, 64,
        100002, 100003, 100004, 100005
    ]

    column_division = {
        (1, 3, 4, 5, 6, 7, 8, 9,
         12, 13, 14, 15, 16, 17,
         18, 19, 20, 21, 22, 23,
         24, 25, 26, 27, 28, 29,
         30, 32, 34, 35,
         100000, 100001, 64,
         100002, 100003, 100004, 100005): DIVISION_1_2,
        (2, 36, 31, 33): DIVISION_1,
        (10, 37, 11, 38): DIVISION_2
    }

    column_length = {
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
            38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            100000, 100001, 64,
            100002, 100003, 100004, 100005): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital_cost():
    """
    Круглосуточный стационар (стоимость)
    """
    title = u'Круглосуточный стационар (стоимость)'
    pattern = 'hospital_cost'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.code in ('049023', '149023') THEN 100000
                 WHEN medical_service.code in ('049024', '149024') THEN 100001
                 WHEN medical_service.code in ('098951') THEN 100002
                 WHEN medical_service.code in ('098948') THEN 100003
                 WHEN medical_service.code in ('098949', '098975') THEN 100004
                 WHEN medical_service.code in ('098950') THEN 100005
                 ELSE tariff_profile.id_pk
            END AS division,
            round(sum(provided_service.accepted_payment), 2),
            round(sum(CASE WHEN medical_service.code like '0%' THEN round(provided_service.accepted_payment, 3) END), 2),
            round(sum(CASE WHEN medical_service.code like '1%' THEN round(provided_service.accepted_payment, 3) END), 2)
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
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code, division
            """
    column_position = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
        38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
        26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        100000, 100001, 64,
        100002, 100003, 100004, 100005
    ]

    column_division = {
        (1, 3, 4, 5, 6, 7, 8, 9,
         12, 13, 14, 15, 16, 17,
         18, 19, 20, 21, 22, 23,
         24, 25, 26, 27, 28, 29,
         30, 32, 34, 35,
         100000, 100001, 64,
         100002, 100003, 100004, 100005): DIVISION_1_2,
        (2, 36, 31, 33): DIVISION_1,
        (10, 37, 11, 38): DIVISION_2
    }

    column_length = {
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
            38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            100000, 100001, 64,
            100002, 100003, 100004, 100005): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital_days():
    """
    Круглосуточный стационар (число койко-дней)
    """
    title = u'Круглосуточный стационар (число койко-дней)'
    pattern = 'hospital_days'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.code in ('049023', '149023') THEN 100000
                 WHEN medical_service.code in ('049024', '149024') THEN 100001
                 WHEN medical_service.code in ('098951') THEN 100002
                 WHEN medical_service.code in ('098948') THEN 100003
                 WHEN medical_service.code in ('098949', '098975') THEN 100004
                 WHEN medical_service.code in ('098950') THEN 100005
                 ELSE tariff_profile.id_pk
            END AS division,
            sum(provided_service.quantity),
            sum(CASE WHEN medical_service.code like '0%' THEN provided_service.quantity END),
            sum(CASE WHEN medical_service.code like '1%' THEN provided_service.quantity END)
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
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code, division
            """
    column_position = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
        38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
        26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        100000, 100001, 64,
        100002, 100003, 100004, 100005
    ]

    column_division = {
        (1, 3, 4, 5, 6, 7, 8, 9,
         12, 13, 14, 15, 16, 17,
         18, 19, 20, 21, 22, 23,
         24, 25, 26, 27, 28, 29,
         30, 32, 34, 35,
         100000, 100001, 64,
         100002, 100003, 100004, 100005): DIVISION_1_2,
        (2, 36, 31, 33): DIVISION_1,
        (10, 37, 11, 38): DIVISION_2
    }

    column_length = {
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
            38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            100000, 100001, 64,
            100002, 100003, 100004, 100005): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital_patients():
    """
    Круглосуточный стационар (численность лиц)
    """
    title = u'Круглосуточный стационар (численность лиц)'
    pattern = 'hospital_patients'
    query = """
            SELECT
            medical_organization.code,
            CASE WHEN medical_service.code in ('049023', '149023') THEN 100000
                 WHEN medical_service.code in ('049024', '149024') THEN 100001
                 WHEN medical_service.code in ('098951') THEN 100002
                 WHEN medical_service.code in ('098948') THEN 100003
                 WHEN medical_service.code in ('098949', '098975') THEN 100004
                 WHEN medical_service.code in ('098950') THEN 100005
                 ELSE tariff_profile.id_pk
            END AS division,
            count(distinct(tariff_profile.id_pk, patient.id_pk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%' THEN (tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%' THEN (tariff_profile.id_pk, patient.id_pk) END)
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
                    JOIN patient
                        ON patient.id_pk = medical_register_record.patient_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code, division
            """
    column_position = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
        38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
        26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
        100000, 100001, 64,
        100002, 100003, 100004, 100005
    ]

    column_division = {
        (1, 3, 4, 5, 6, 7, 8, 9,
         12, 13, 14, 15, 16, 17,
         18, 19, 20, 21, 22, 23,
         24, 25, 26, 27, 28, 29,
         30, 32, 34, 35,
         100000, 100001, 64,
         100002, 100003, 100004, 100005): DIVISION_1_2,
        (2, 36, 31, 33): DIVISION_1,
        (10, 37, 11, 38): DIVISION_2
    }

    column_length = {
        (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 37, 11, 36, 12, 13,
            38, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
            26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
            100000, 100001, 64,
            100002, 100003, 100004, 100005): 1}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital_hmc():
    """
    Круглосуточный стационар ВМП
    """
    title = u'Круглосуточный стационар ВМП'
    pattern = 'hospital_hmc'
    query = """
            SELECT
            medical_organization.code,
            tariff_profile.id_pk AS division,

            count(distinct(tariff_profile.id_pk, patient.id_pk)),
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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    JOIN patient
                        ON patient.id_pk = medical_register_record.patient_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND (provided_event.term_fk = 1 AND medical_service.group_fk=20)
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code, division
            """

    column_position = [56, 57, 58, 59, 60, 63, 61, 62]

    column_division = {(56, 57, 58, 59, 60, 63, 61, 62): DIVISION_ALL_1_2}

    column_length = {
        (56, 57, 58, 59, 60, 63, 61, 62): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital():
    """
    Круглосуточный стационар свод
    """
    title = u'Круглосуточный стационар свод'
    pattern = 'hospital'
    query = """
            SELECT
            medical_organization.code, 100000,

            count(distinct(tariff_profile.id_pk, patient.id_pk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                  THEN (tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                  THEN (tariff_profile.id_pk, patient.id_pk) END),

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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    JOIN patient
                        ON patient.id_pk = medical_register_record.patient_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code
            """

    column_position = [100000, ]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {
        (100000, ): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


def hospital_all():
    """
    Круглосуточный стационар + ВМП (свод)
    """
    title = u'Круглосуточный стационар + ВМП (свод)'
    pattern = 'hospital_all'
    query = """
            SELECT
            medical_organization.code, 100000,

            count(distinct(tariff_profile.id_pk, patient.id_pk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                   THEN (tariff_profile.id_pk, patient.id_pk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                   THEN (tariff_profile.id_pk, patient.id_pk) END),

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
                    LEFT JOIN tariff_profile
                        ON tariff_profile.id_pk = medical_service.tariff_profile_fk
                    JOIN patient
                        ON patient.id_pk = medical_register_record.patient_fk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND ((provided_event.term_fk = 1 AND medical_service.group_fk is null)
                      or medical_service.code in ('049023','149023', '049024',
                                                  '149024', '098951', '098948',
                                                  '098949', '098975', '098950')
                      or medical_service.group_fk = 20
                    )
                AND provided_service.payment_type_fk in (2, 4)
            group by medical_organization.code
            """
    column_position = [100000, ]

    column_division = {(100000, ): DIVISION_ALL_1_2}

    column_length = {
        (100000, ): 4}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


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


### Периодический медосмотр несовершеннолетних
def period_exam_children():
    """
    Периодический медосмотр несовершеннолетних
    """
    title = u'Периодический медосмотр несовершеннолетних'
    pattern = 'periodic_medical_examination'
    query = """
            SELECT
            medical_organization.code,

            100000 AS division,

            0, 0, count(distinct patient.id_pk),

            0, 0, count(distinct provided_service.id_pk),

            0, 0, sum(provided_service.tariff),

            0, 0, 0,

            0, 0, sum(provided_service.accepted_payment)

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
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND medical_service.code = '119151'
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [100000]

    column_division = {(100000, ): DIVISION_2}

    column_length = {(100000, ): 5}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


### Предварительные медосмотры несовершеннолетних
def prelim_exam_children():
    """
    Предварительные медосмотры несовершеннолетних
    """
    title = u'Предварительные медосмотры несовершеннолетних'
    pattern = 'preliminary_medical_examination'
    query = """
            SELECT
            medical_organization.code,

            case WHEN medical_service.code in ('119101', '119119', '119120') THEN medical_service.id_pk
                 WHEN medical_service.group_fk = 15 and medical_service.subgroup_fk = 11 THEN 100000
                 end
              AS division,

            0, 0, count(distinct patient.id_pk),

            0, 0, count(distinct provided_service.id_pk),

            0, 0, sum(provided_service.tariff),

            0, 0, 0,

            0, 0, sum(provided_service.accepted_payment)

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
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND (medical_service.code in ('119101', '119119', '119120')
                   or medical_service.group_fk = 15 and medical_service.subgroup_fk = 11)
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [8536, 8552, 8553, 100000]

    column_division = {(8536, 8552, 8553, 100000): DIVISION_2}

    column_separator = {8553: 6, 100000: 2}

    column_length = {(8536, 8552, 8553): 5, (100000, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


### Профосмотры несовешенолетних
def prev_exam_children():
    """
    Профилактический медицинский осмотр несовершеннолетних
    """
    title = u'Профилактический медицинский осмотр несовершеннолетних'
    pattern = 'preventive_medical_examination'
    query = """
            SELECT
            medical_organization.code,

            case WHEN medical_service.code in ('119080','119081') THEN 100000
                 WHEN medical_service.code in ('119082','119083') THEN 100001
                 WHEN medical_service.code in ('119084','119085') THEN 100002
                 WHEN medical_service.code in ('119086','119087') THEN 100003
                 WHEN medical_service.code in ('119088','119089') THEN 100004
                 WHEN medical_service.code in ('119090','119091') THEN 100005
                 WHEN medical_service.group_fk = 11 and medical_service.subgroup_fk = 8 THEN 100006
                 end
              AS division,


            count(distinct patient.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN patient.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN patient.id_pk END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN provided_service.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN provided_service.id_pk END),

            sum(provided_service.tariff),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.tariff END),
            sum(CASE WHEN patient.gender_fk=1
                     THEN provided_service.tariff END),

            0, 0, 0,

            sum(provided_service.accepted_payment),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.accepted_payment END),
            sum(CASE WHEN patient.gender_fk=1
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
                    JOIN patient
                        ON medical_register_record.patient_fk=patient.id_pk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND (medical_service.code in ('119080','119081',
                                              '119082','119083',
                                              '119084','119085',
                                              '119086','119087',
                                              '119088','119089',
                                              '119090','119091')
                   or medical_service.group_fk = 11 and medical_service.subgroup_fk = 8)
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [100000, 100001, 100002, 100003, 100004, 100005, 100006]

    column_division = {(100000, 100001, 100002, 100003, 100004, 100005): DIVISION_1_2,
                       (100006, ): DIVISION_ALL_1_2}

    column_separator = {100005: 17, 100006: 2}

    column_length = {(100000, 100001, 100002, 100003, 100004, 100005): 5, (100006, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


### Диспансеризация детей - сирот в трудной жизненной ситуации
def exam_children_difficult_situation():
    """
    Диспансеризация несовершеннолетних (в трудной жизненной ситуации)
    """
    title = u'Диспансеризация несовершеннолетних (в трудной жизненной ситуации)'
    pattern = 'examination_children_difficult_situation'
    query = """
            SELECT
            medical_organization.code,

            case WHEN medical_service.code in ('119020','119021') THEN 100000
                 WHEN medical_service.code in ('119022','119023') THEN 100001
                 WHEN medical_service.code in ('119024','119025') THEN 100002
                 WHEN medical_service.code in ('119026','119027') THEN 100003
                 WHEN medical_service.code in ('119028','119029') THEN 100004
                 WHEN medical_service.code in ('119030','119031') THEN 100005
                 WHEN medical_service.group_fk = 12 and medical_service.subgroup_fk = 9 THEN 100006
                 end
              AS division,


            count(distinct patient.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN patient.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN patient.id_pk END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN provided_service.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN provided_service.id_pk END),

            sum(provided_service.tariff),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.tariff END),
            sum(CASE WHEN patient.gender_fk=1
                     THEN provided_service.tariff END),

            0, 0, 0,

            sum(provided_service.accepted_payment),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.accepted_payment END),
            sum(CASE WHEN patient.gender_fk=1
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
                    JOIN patient
                        ON medical_register_record.patient_fk=patient.id_pk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND (medical_service.code in ('119020','119021',
                                              '119022','119023',
                                              '119024','119025',
                                              '119026','119027',
                                              '119028','119029',
                                              '119030','119031')
                   or medical_service.group_fk = 12 and medical_service.subgroup_fk = 9)
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [100000, 100001, 100002, 100003, 100004, 100005, 100006]

    column_division = {(100000, 100001, 100002, 100003, 100004, 100005): DIVISION_1_2,
                       (100006, ): DIVISION_ALL_1_2}

    column_separator = {100005: 16, 100006: 2}

    column_length = {(100000, 100001, 100002, 100003, 100004, 100005): 5, (100006, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


### Диспансеризация детей - сирот без попечения родителей
def exam_children_without_care():
    """
    Диспансеризация несовершеннолетних (без попечения родителей)
    """
    title = u'Диспансеризация несовершеннолетних (без попечения родителей)'
    pattern = 'examination_children_without_care'
    query = """
            SELECT
            medical_organization.code,

            case WHEN medical_service.code in ('119220', '119221') THEN 100000
                 WHEN medical_service.code in ('119222', '119223') THEN 100001
                 WHEN medical_service.code in ('119224', '119225') THEN 100002
                 WHEN medical_service.code in ('119226', '119227') THEN 100003
                 WHEN medical_service.code in ('119228', '119229') THEN 100004
                 WHEN medical_service.code in ('119230', '119231') THEN 100005
                 WHEN medical_service.group_fk = 13 and medical_service.subgroup_fk = 10 THEN 100006
                 end
              AS division,

            count(distinct patient.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN patient.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN patient.id_pk END),


            count(distinct provided_service.id_pk),
            count(distinct CASE WHEN patient.gender_fk=2
                           THEN provided_service.id_pk END),
            count(distinct CASE WHEN patient.gender_fk=1
                           THEN provided_service.id_pk END),

            sum(provided_service.tariff),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.tariff END),
            sum(CASE WHEN patient.gender_fk=1
                     THEN provided_service.tariff END),

            0, 0, 0,

            sum(provided_service.accepted_payment),
            sum(CASE WHEN patient.gender_fk=2
                     THEN provided_service.accepted_payment END),
            sum(CASE WHEN patient.gender_fk=1
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
                    JOIN patient
                        ON medical_register_record.patient_fk=patient.id_pk
                    JOIN medical_organization
                        ON medical_organization.id_pk = provided_service.organization_fk
            WHERE medical_register.year='{year}'
                AND medical_register.period='{period}'
                AND is_active
                AND (medical_service.code in ('119220', '119221',
                                              '119222', '119223',
                                              '119224', '119225',
                                              '119226', '119227',
                                              '119228', '119229',
                                              '119230', '119231')
                   or medical_service.group_fk = 13 and medical_service.subgroup_fk = 10)
                AND provided_service.payment_type_fk IN (2, 4)
            GROUP BY medical_organization.code, division
            """

    column_position = [100000, 100001, 100002, 100003, 100004, 100005, 100006]

    column_division = {(100000, 100001, 100002, 100003, 100004, 100005): DIVISION_1_2,
                       (100006, ): DIVISION_ALL_1_2}

    column_separator = {100005: 16, 100006: 2}

    column_length = {(100000, 100001, 100002, 100003, 100004, 100005): 5, (100006, ): 2}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length}, ]
    }


### Диспансеризация взрослых
def exam_adult():
    """
    Диспансеризация взрослых
    """
    title = u'Диспансеризация взрослых'
    pattern = 'examination_adult'
    query = """
            SELECT medical_register.organization_code,

         CASE WHEN medical_service.code in ('019021', '019022') THEN 100000
              WHEN medical_service.code in ('019023', '019024') THEN 100001
              end

         as division,

         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS children_receiving,

         SUM(provided_service.tariff) AS all_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS children_payment,

         SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL
             THEN round(provided_service.tariff*0.07, 2) ELSE 0 END) AS all_coef,
         SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL AND patient.gender_fk = 1
             THEN round(provided_service.tariff*0.07, 2) ELSE 0 END) AS adult_coef,
         SUM(CASE WHEN provided_service_coefficient.id_pk IS NOT NULL AND patient.gender_fk = 2
             THEN round(provided_service.tariff*0.07, 2) ELSE 0 END) AS children_coef,

         SUM(provided_service.accepted_payment) AS all_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS children_payment

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk

         LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
             (SELECT psc1.id_pk
              FROM provided_service_coefficient psc1
              WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.group_fk = 7
                  and medical_service.code in ('019021', '019023', '019022', '019024'))
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code, division
        union
        SELECT medical_register.organization_code,

        100002 as division,

         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS children_receiving,

         0, 0, 0,

         0, 0, 0,

         0, 0, 0

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.code = '019001'
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk)
                         WHERE ms2.code in ('019021', '019022')
                               AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
        union
        SELECT medical_register.organization_code,

        100003 as division,

         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS children_receiving,

         0, 0, 0,

         0, 0, 0,

         0, 0, 0

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.code = '019001'
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk)
                         WHERE ms2.code in ('019023', '019024')
                               AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
        union
        SELECT medical_register.organization_code,

        100004 as division,

         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS children_receiving,

         0, 0, 0,

         0, 0, 0,

         0, 0, 0

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.code = '019020'
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk)
                         WHERE ms2.code in ('019021', '019022')
                               AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
        union
        SELECT medical_register.organization_code,

        100005 as division,

         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS children_receiving,

         0, 0, 0,

         0, 0, 0,

         0, 0, 0

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.code = '019020'
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk)
                         WHERE ms2.code in ('019023', '019024')
                               AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
         """

    column_position = [100000, 100001, 100002, 100003, 100004, 100005]

    column_division = {(100000, 100001, 100002, 100003, 100004, 100005): DIVISION_ALL_1_2}

    column_separator = {100001: 16, 100003: 7}

    column_length = {(100000, 100001): 5, (100002, 100003, 100004, 100005): 2}

    query1 = """
             SELECT medical_register.organization_code, medical_service.id_pk as division,

         0,
         COUNT(DISTINCT patient.id_pk) AS adult_population,
         0,

         0,
         COUNT(DISTINCT provided_service.id_pk) AS adult_receiving,
         0,

         0,
         SUM(provided_service.accepted_payment) AS adult_payment,
         0

         FROM provided_service
         JOIN medical_service
             ON provided_service.code_fk = medical_service.id_pk
         JOIN provided_event
             ON provided_service.event_fk = provided_event.id_pk
         JOIN medical_register_record
             ON provided_event.record_fk = medical_register_record.id_pk
         JOIN patient
             ON patient.id_pk = medical_register_record.patient_fk
         JOIN medical_register
             ON medical_register_record.register_fk = medical_register.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             and medical_service.group_fk in (25, 26)
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code, division
         """

    column_position1 = [8399, 8398, 8397, 8395, 8394, 8396,
                        8393, 8392, 8391, 8390, 8389, 8388, 8345]
    column_division1 = {(8399, 8398, 8397, 8395, 8394, 8396, 8393,
                         8392, 8391, 8390, 8389, 8388, 8345): DIVISION_1}
    column_length1 = {(8399, 8398, 8397, 8395, 8394, 8396, 8393,
                       8392, 8391, 8390, 8389, 8388, 8345): 3}

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'separator': column_separator,
                  'column_length': column_length},
                 {'structure': (query1, column_position1, column_division1),
                  'column_length': column_length1}],
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
                 and provided_service.payment_type_fk = 2
                 and provided_event.term_fk = 3
                 and provided_event.id_pk in (
                         select distinct pe1.id_pk
                         from provided_event pe1
                         join provided_service ps1
                             ON ps1.event_fk = pe1.id_pk
                         join medical_service ms1
                             on ms1.id_pk = ps1.code_fk
                         JOIN medical_organization
                             ON medical_organization.id_pk = provided_service.organization_fk
                         where pe1.record_fk=medical_register_record.id_pk
                         and ms1.group_fk = 24 and ms1.reason_fk = 1
                         AND ps1.department_fk NOT IN (15, 88, 89)
                         AND exists (
                             SELECT 1
                             FROM patient pt
                             JOIN insurance_policy
                                  ON pt.insurance_policy_fk = insurance_policy.version_id_pk
                             JOIN person
                                  ON person.version_id_pk =(
                                      SELECT version_id_pk
                                      FROM person WHERE id = (
                                          SELECT id FROM person
                                          WHERE version_id_pk = insurance_policy.person_fk) AND is_active)
                             JOIN attachment
                                  ON attachment.id_pk = (
                                      SELECT MAX(id_pk)
                                      FROM attachment
                                      WHERE person_fk = person.version_id_pk AND status_fk = 1
                                         AND attachment.date <= '2014-11-01' AND attachment.is_active)
                             JOIN medical_organization med_org
                                  ON (med_org.id_pk = attachment.medical_organization_fk
                                      AND med_org.parent_fk IS NULL)
                                      OR med_org.id_pk = (
                                         SELECT parent_fk FROM medical_organization
                                         WHERE id_pk = attachment.medical_organization_fk)
                            WHERE pt.id_pk =  medical_register_record.patient_fk and ps1.organization_fk=med_org.id_pk))

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
                  when medical_service.group_fk = 9 then 100002
                  else medical_service.division_fk end as division,

            count(distinct(medical_register_record.patient_fk, medical_service.code like '0%')),
            count(distinct CASE WHEN medical_service.code like '0%'
                  THEN (medical_register_record.patient_fk) END),
            count(distinct CASE WHEN medical_service.code like '1%'
                  THEN (medical_register_record.patient_fk) END),


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
                 and medical_service.group_fk is null) or medical_service.group_fk = 4 or
                 medical_service.code in ('019214', '019215', '019216', '019217'))
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
def policlinic_disease__spec_treatment():
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
                JOIN insurance_policy i
                    ON p.insurance_policy_fk = i.version_id_pk
                JOIN person
                    ON person.version_id_pk = (
                        SELECT version_id_pk
                        FROM person WHERE id = (
                            SELECT id FROM person
                            WHERE version_id_pk = i.person_fk) AND is_active)
                left JOIN attachment
                  ON attachment.id_pk = (
                      SELECT MAX(id_pk)
                      FROM attachment
                      WHERE person_fk = person.version_id_pk AND status_fk = 1
                         AND attachment.date <= '2014-11-01' AND attachment.is_active)
                left JOIN medical_organization att_org
                  ON (att_org.id_pk = attachment.medical_organization_fk
                      AND att_org.parent_fk IS NULL)
                      OR att_org.id_pk = (
                         SELECT parent_fk FROM medical_organization
                         WHERE id_pk = attachment.medical_organization_fk
                      )

            WHERE mr.is_active
             AND mr.year = '{year}'
             AND mr.period = '{period}'
             and ps.payment_type_fk = 2
             and pe.term_fk = 3
             and ms.reason_fk = 1
             and (ms.group_fk = 24 and (att_org.code != mr.organization_code or att_org.code is null or ps.department_fk IN (15, 88, 89))
                  or (ms.division_fk in (399, 401, 403, 443, 444) and ms.group_fk is null))

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
                JOIN insurance_policy i
                    ON p.insurance_policy_fk = i.version_id_pk
                JOIN person
                    ON person.version_id_pk = (
                        SELECT version_id_pk
                        FROM person WHERE id = (
                            SELECT id FROM person
                            WHERE version_id_pk = i.person_fk) AND is_active)
                left JOIN attachment
                  ON attachment.id_pk = (
                      SELECT MAX(id_pk)
                      FROM attachment
                      WHERE person_fk = person.version_id_pk AND status_fk = 1
                         AND attachment.date <= '2014-11-01' AND attachment.is_active)
                left JOIN medical_organization att_org
                  ON (att_org.id_pk = attachment.medical_organization_fk
                      AND att_org.parent_fk IS NULL)
                      OR att_org.id_pk = (
                         SELECT parent_fk FROM medical_organization
                         WHERE id_pk = attachment.medical_organization_fk
                      )

            WHERE mr.is_active
             AND mr.year = '{year}'
             AND mr.period = '{period}'
             and ps.payment_type_fk = 2
             and ((pe.term_fk = 3
             and ms.reason_fk = 1
             and (ms.group_fk = 24 and (att_org.code != mr.organization_code or att_org.code is null
                  or ps.department_fk IN (15, 88, 89))
                  or ms.group_fk is null)) or ms.group_fk = 5)

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
                JOIN insurance_policy i
                    ON p.insurance_policy_fk = i.version_id_pk
                JOIN person
                    ON person.version_id_pk = (
                        SELECT version_id_pk
                        FROM person WHERE id = (
                            SELECT id FROM person
                            WHERE version_id_pk = i.person_fk) AND is_active)
                left JOIN attachment
                  ON attachment.id_pk = (
                      SELECT MAX(id_pk)
                      FROM attachment
                      WHERE person_fk = person.version_id_pk AND status_fk = 1
                         AND attachment.date <= '2014-11-01' AND attachment.is_active)
                left JOIN medical_organization att_org
                  ON (att_org.id_pk = attachment.medical_organization_fk
                      AND att_org.parent_fk IS NULL)
                      OR att_org.id_pk = (
                         SELECT parent_fk FROM medical_organization
                         WHERE id_pk = attachment.medical_organization_fk
                      )

            WHERE mr.is_active
             AND mr.year = '{year}'
             AND mr.period = '{period}'
             and ps.payment_type_fk = 2
             and((pe.term_fk = 3 and ms.reason_fk = 1
             and ((ms.group_fk = 24 and (att_org.code != mr.organization_code or att_org.code is null or ps.department_fk IN (15, 88, 89)))
                  or ms.group_fk is null) or ms.group_fk = 5)
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
                JOIN insurance_policy i
                    ON p.insurance_policy_fk = i.version_id_pk
                LEFT JOIN provided_service_coefficient
                  ON provided_service_coefficient.service_fk = ps.id_pk
                      AND provided_service_coefficient.coefficient_fk=3
                JOIN person
                    ON person.version_id_pk = (
                        SELECT version_id_pk
                        FROM person WHERE id = (
                            SELECT id FROM person
                            WHERE version_id_pk = i.person_fk) AND is_active)
                left JOIN attachment
                  ON attachment.id_pk = (
                      SELECT MAX(id_pk)
                      FROM attachment
                      WHERE person_fk = person.version_id_pk AND status_fk = 1
                         AND attachment.date <= '2014-11-01' AND attachment.is_active)
                left JOIN medical_organization att_org
                  ON (att_org.id_pk = attachment.medical_organization_fk
                      AND att_org.parent_fk IS NULL)
                      OR att_org.id_pk = (
                         SELECT parent_fk FROM medical_organization
                         WHERE id_pk = attachment.medical_organization_fk
                      )

            WHERE mr.is_active
             AND mr.year = '{year}'
             AND mr.period = '{period}'
             and ps.payment_type_fk = 2
             and((pe.term_fk = 3 and ms.reason_fk = 1
             and ((ms.group_fk = 24 and
                  (att_org.code != mr.organization_code or att_org.code is null
                    or ps.department_fk IN (15, 88, 89)))
                  or ms.group_fk is null) or ms.group_fk = 5)
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


def get_division_by(column_division, index):
    for column in column_division:
        if index in column:
            return column_division[column]


def run_sql(query):
    cursor_query = connection.cursor()
    cursor_query.execute(query)
    data = {}
    for row in cursor_query.fetchall():
        mo = row[0]
        division = row[1]
        if mo not in data:
            data[mo] = {}
        if division not in data[mo]:
            data[mo][division] = []
        last_pos = 2
        for cur_pos in xrange(5, len(row)+1, 3):
            data[mo][division].append(row[last_pos: cur_pos])
            last_pos = cur_pos
    cursor_query.close()
    return data


def print_act(year, period, data):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=data['title'],
        month=MONTH_NAME[period],
        year=year
    )
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=data['pattern'])
    print data['title']

    #print data_sum
    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], MONTH_NAME[period]]) as act_book:

        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        for sheet, data_query in enumerate(data['data']):
            print data_query.get('next', True)
            if data_query.get('next', True):
                block_index = 2
                act_book.set_sheet(sheet)
            else:
                block_index = act_book.cursor['column']
            data_sum = run_sql(data_query['structure'][0].format(year=year, period=period))
            for mo_code in data_sum:
                row_index = ACT_CELL_POSITION[mo_code]
                act_book.set_cursor(row_index, block_index)
                for division in data_query['structure'][1]:
                    division_by = get_division_by(data_query['structure'][2], division)
                    column_len = get_division_by(data_query['column_length'], division)
                    data_divisions = data_sum[mo_code].get(division, [(0, 0, 0), ]*column_len)
                    for data_division in data_divisions[: column_len]:
                        if division_by == DIVISION_1:
                            act_book.write_cell(data_division[1], 'c')
                        elif division_by == DIVISION_2:
                            act_book.write_cell(data_division[2], 'c')
                        elif division_by == DIVISION_1_2:
                            act_book.write_cell(data_division[1], 'c')
                            act_book.write_cell(data_division[2], 'c')
                        elif division_by == DIVISION_ALL_1_2:
                            act_book.write_cell(data_division[0], 'c')
                            act_book.write_cell(data_division[1], 'c')
                            act_book.write_cell(data_division[2], 'c')
                    act_book.cursor['column'] += data_query.get('separator', {}).get(division, 0)


### Распечатка нестандаотных актов
def print_act_1(year, period, data):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=data['title'],
        month=MONTH_NAME[period],
        year=year
    )
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=data['pattern'])
    print data['title']

    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], MONTH_NAME[period]]) as act_book:

        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        act_book.set_sheet(0)
        data_sum = run_sql(data[0]['structure'][0].format(year=year, period=period))
        print data


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = '2014'
        period = '10'
        #capitation_event = [row.replace('\n', '')for row in file('capitation_event')]
        acts = [
            #hospital_services(),
            #hospital_cost(),
            #hospital_days(),
            #hospital_patients(),
            #hospital_hmc(),
            #hospital(),
            #hospital_all(),

            #day_hospital_services(),
            #day_hospital_cost(),
            #day_hospital_days(),
            #day_hospital_patients(),
            #day_hospital_home_services(),
            #day_hospital_home_cost(),
            #day_hospital_home_days(),
            #day_hospital_home_patients(),
            #day_hospital_home(),
            #day_hospital(),
            #day_hospital_all(),

            #acute_care(),
            #period_exam_children(),
            #prelim_exam_children(),
            #prev_exam_children(),

            #exam_children_difficult_situation(),
            #exam_children_without_care(),

            #exam_adult(),
            #capitation_policlinic(),

            #policlinic_ambulance_primary(),
            #policlinic_ambulance_spec_visit(),
            #policlinic_ambulance_spec_cost(),
            #policlinic_ambulance_spec_patients(),
            #policlinic_ambulance_all(),

            #policlinic_preventive_spec_visit(),
            #policlinic_preventive_spec_cost(),
            #policlinic_preventive_spec_patients(),
            #policlinic_preventive_all(),

            #policlinic_disease_spec_visit(),
            #policlinic_disease_spec_treatment(),
            #policlinic_disease_spec_patients(),
            #policlinic_disease_spec_cost(),
            #policlinic_disease_primary(),
            #policlinic_disease_all(),

            #policlinic_spec_visit(),
            #policlinic_spec_patients(),
            #policlinic_spec_cost(),
            #policlinic_all(),

        ]
        for act in acts:
            print_act(year, period, act)

        print_act_1(year, period, policlinic_preventive_primary())

