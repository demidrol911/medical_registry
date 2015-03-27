#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import (
    DIVISION_1,
    DIVISION_ALL_1_2,
    print_act
)


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


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            exam_adult(),
        ]
        for act in acts:
            print_act(year, period, act)