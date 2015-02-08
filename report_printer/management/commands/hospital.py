#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.func import (DIVISION_1, DIVISION_2, DIVISION_1_2,
                            DIVISION_ALL_1_2, print_act)


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


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            hospital_services(),
            hospital_cost(),
            hospital_days(),
            hospital_patients(),
            hospital_hmc(),
            hospital(),
            hospital_all()
        ]
        for act in acts:
            print_act(year, period, act)
