#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import (
    DIVISION_2, DIVISION_1_2,
    DIVISION_ALL_1_2, print_act
)


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


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            period_exam_children(),
            prelim_exam_children(),
            prev_exam_children(),

            exam_children_difficult_situation(),
            exam_children_without_care(),
        ]
        for act in acts:
            print_act(year, period, act)