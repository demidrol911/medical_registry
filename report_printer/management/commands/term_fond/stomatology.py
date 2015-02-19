#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import print_act_2, run_sql1


### Стоматология
def stomatology(calc):
    """
    Стоматология
    """
    stomatology_disease_query = """
         SELECT medical_register.organization_code,

         COUNT(DISTINCT (patient.id_pk, medical_service.code like '0%')) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN patient.id_pk END) AS adult_population,

         COUNT(DISTINCT provided_service.event_fk) AS all_treatment,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN provided_service.event_fk END) AS adult_treatment,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN provided_service.event_fk END) AS adult_treatment,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL
               THEN provided_service.id_pk END) AS all_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_receiving,

         SUM(provided_service.quantity*medical_service.uet) AS all_uet,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS adult_uet,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS children_uet,

         SUM(provided_service.accepted_payment) AS all_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN medical_service.code like '1%'
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
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.group_fk = 19
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk
                                 AND provided_service.end_date = ps2.end_date
                                 AND provided_service.start_date = ps2.start_date)
                         WHERE ms2.subgroup_fk in ({condition})
                               AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
         """

    stomatology_proph_or_ambulance_query = """
         SELECT medical_register.organization_code,

         COUNT(DISTINCT (patient.id_pk, medical_service.code like '0%')) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
              THEN patient.id_pk END) AS adult_population,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL
              THEN provided_service.id_pk END) AS all_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '0%'
              THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '1%'
              THEN provided_service.id_pk END) AS children_receiving,

         SUM(provided_service.quantity*medical_service.uet) AS all_uet,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS adult_uet,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS children_uet,

         SUM(provided_service.accepted_payment) AS all_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN medical_service.code like '1%'
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
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.group_fk = 19
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk
                                 AND provided_service.end_date = ps2.end_date
                                 AND provided_service.start_date = ps2.start_date
                                 )
                         WHERE ms2.subgroup_fk in ({condition})
                             AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
         """

    stomatology_emergency_query = """
         SELECT medical_register.organization_code,

         COUNT(DISTINCT (patient.id_pk, medical_service.code like '0%')) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN patient.id_pk END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN patient.id_pk END) AS adult_population,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL
               THEN provided_service.id_pk END) AS all_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_receiving,

         SUM(provided_service.quantity*medical_service.uet) AS all_uet,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS adult_uet,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS children_uet,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.tariff ELSE 0 END) AS adult_tariff,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.tariff ELSE 0 END) AS children_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS all_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND medical_service.code like '0%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS adult_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND medical_service.code like '1%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS children_emergency,

         SUM(provided_service.accepted_payment) AS all_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN medical_service.code like '1%'
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
        LEFT JOIN provided_service_coefficient
             ON provided_service_coefficient.service_fk=provided_service.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.group_fk = 19
                     AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk
                                 AND provided_service.end_date = ps2.end_date
                                 AND provided_service.start_date = ps2.start_date
                                 )
                         WHERE ms2.subgroup_fk in ({condition})
                             AND ps2.payment_type_fk = 2
                        )
                 )
             AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
         """

    stomatology_total_query = """
         SELECT medical_register.organization_code,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL
               THEN (patient.id_pk, medical_service.subgroup_fk, medical_service.code like '0%') END) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '0%'
               THEN (patient.id_pk, medical_service.subgroup_fk) END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '1%'
               THEN (patient.id_pk, medical_service.subgroup_fk) END) AS adult_population,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk=12
               THEN provided_service.event_fk END) AS all_treatment,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk=12 AND medical_service.code like '0%'
               THEN provided_service.event_fk END) AS adult_treatment,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk=12 AND medical_service.code like '1%'
               THEN provided_service.event_fk END) AS adult_treatment,

         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL
               THEN provided_service.id_pk END) AS all_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_receiving,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NOT NULL AND medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_receiving,

         SUM(provided_service.quantity*medical_service.uet) AS all_uet,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS adult_uet,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.quantity*medical_service.uet ELSE 0 END) AS children_uet,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.tariff ELSE 0 END) AS adult_tariff,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.tariff ELSE 0 END) AS children_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS all_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND medical_service.code like '0%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS adult_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND medical_service.code like '1%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS children_emergency,

         SUM(provided_service.accepted_payment) AS all_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_payment,
         SUM(CASE WHEN medical_service.code like '1%'
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
         LEFT JOIN provided_service_coefficient
             ON provided_service_coefficient.service_fk=provided_service.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND (medical_service.group_fk = 19
                  AND EXISTS (
                         SELECT 1
                         FROM provided_service ps2
                         JOIN medical_service ms2
                             ON ps2.code_fk = ms2.id_pk
                         JOIN provided_event pe2
                             ON (pe2.id_pk = ps2.event_fk
                                 AND pe2.id_pk = provided_event.id_pk
                                 AND provided_service.end_date = ps2.end_date
                                 AND provided_service.start_date = ps2.start_date
                                 )
                         WHERE ms2.subgroup_fk in ({condition})
                             AND ps2.payment_type_fk = 2
                        )
                 )
              AND provided_service.payment_type_fk = 2
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Стоматология',
             'pattern': 'stomatology',
             'sum': [
                 {'query': calc((stomatology_disease_query, '12')),
                  'separator_length': 0, 'len': 15},
                 {'query': calc((stomatology_proph_or_ambulance_query, '13')),
                  'separator_length': 0, 'len': 12},
                 {'query': calc((stomatology_proph_or_ambulance_query, '14')),
                  'separator_length': 0, 'len': 12},
                 {'query': calc((stomatology_emergency_query, '17')),
                  'separator_length': 0, 'len': 18},
                 {'query': calc((stomatology_total_query, '12, 13, 14, 17')),
                  'separator_length': 0, 'len': 21}]},
            ]


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        calc = run_sql1(year, period)
        acts = [
           stomatology(calc),
        ]
        for act in acts:
            for rule in act:
                print rule['title']
                print_act_2(year, period, rule)