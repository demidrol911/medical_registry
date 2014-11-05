#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection
from medical_service_register.path import REESTR_EXP, BASE_DIR
from helpers.excel_writer import ExcelWriter
from helpers.excel_style import VALUE_STYLE, PERIOD_VALUE_STYLE
from helpers.const import MONTH_NAME, ACT_CELL_POSITION
from tfoms.management.commands.register_function import (calculate_capitation_tariff,
                                                         get_mo_register)
import time

ACT_PATH = ur'{dir}\{title}_{month}_{year}'
TEMP_PATH = ur'{base}\templates\excel_pattern\end_of_month\{template}.xls'


### Структура для актов дневного стационара
def get_day_hospital_structure(calc):
    day_hospital_query = """
         SELECT medical_register.organization_code,
         COUNT(DISTINCT (patient.id_pk, medical_division.term_fk,
               medical_service.group_fk, medical_service.tariff_profile_fk)) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN (patient.id_pk, medical_division.term_fk, medical_service.group_fk,
                     medical_service.tariff_profile_fk) END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN (patient.id_pk, medical_division.term_fk,
                     medical_service.group_fk, medical_service.tariff_profile_fk) END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitaliztion,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_hospitalization,

         SUM(round(provided_service.quantity, 2)) AS all_quantity,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS adult_quantity,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS children_quantity,

         SUM(round(provided_service.accepted_payment, 2)) AS all_accepted_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN round(provided_service.accepted_payment, 2) ELSE 0 END) AS adult_accepted_payment,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN round(provided_service.accepted_payment, 2) ELSE 0 END) AS children_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             JOIN medical_division
                 ON medical_division.id_pk = provided_service.division_fk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND provided_service.payment_type_fk in (2, 4)
             AND ({condition})
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Дневной стационар',
             'pattern': 'day_hospital',
             'sum': [
                 {'query': calc((day_hospital_query,
                                """
                                (provided_event.term_fk=2 and
                                 medical_division.term_fk in (10, 11) and
                                 medical_service.group_fk is null)
                                 or medical_service.group_fk in (17, 28)
                                 """)),
                  'separator_length': 2},
                 {'query': calc((day_hospital_query,
                                 """
                                 provided_event.term_fk=2 and
                                 medical_service.group_fk = 28
                                 """)),
                  'separator_length': 2}
             ]},
            {'title': u'Дневной стационар на дому',
             'pattern': 'day_hospital_home',
             'sum': [
                 {'query': calc((day_hospital_query,
                                 """
                                 provided_event.term_fk=2 and
                                 medical_division.term_fk=12 and
                                 medical_service.group_fk is null
                                 """)),
                  'separator_length': 2}
             ]},
            {'title': u'Дневной стационар свод',
             'pattern': 'day_hospital_all',
             'sum': [
                 {'query': calc((day_hospital_query,
                                 """
                                 (provided_event.term_fk=2 and medical_service.group_fk is null)
                                 or medical_service.group_fk in (17, 28)
                                 """)),
                  'separator_length': 2}
             ]}]


### Структура актов по стоматологии
def get_stomatology_structure(calc):
    stomatology_disease_query = """
         SELECT medical_register.organization_code,

         COUNT(DISTINCT patient.id_pk) AS all_population,
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

         COUNT(DISTINCT patient.id_pk) AS all_population,
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

         COUNT(DISTINCT patient.id_pk) AS all_population,
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
               THEN (patient.id_pk, medical_service.subgroup_fk) END) AS all_population,
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
                  'separator_length': 15},
                 {'query': calc((stomatology_proph_or_ambulance_query, '13')),
                  'separator_length': 12},
                 {'query': calc((stomatology_proph_or_ambulance_query, '14')),
                  'separator_length': 12},
                 {'query': calc((stomatology_emergency_query, '17')),
                  'separator_length': 18},
                 {'query': calc((stomatology_total_query, '12, 13, 14, 17')),
                  'separator_length': 21}]},
            ]


### Структура актов для круглосуточного стационара
def get_hospital_structure(calc):
    hospital_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT (patient.id_pk, medical_service.group_fk,
                         medical_service.tariff_profile_fk)) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN (patient.id_pk, medical_service.group_fk,
                     medical_service.tariff_profile_fk) END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN (patient.id_pk, medical_service.group_fk,
                     medical_service.tariff_profile_fk) END) AS children_population,

         COUNT(DISTINCT CASE WHEN (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
               THEN provided_service.id_pk END) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               AND (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
               THEN provided_service.id_pk END) AS adult_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               AND (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
               THEN provided_service.id_pk END) AS children_hospitalization,

         SUM(CASE WHEN (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS all_quantity,
         SUM(CASE WHEN medical_service.code like '0%'
             AND (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS adult_quantity,
         SUM(CASE WHEN medical_service.code like '1%'
             AND (medical_service.group_fk IS NULL OR medical_service.group_fk in (1, 2, 20))
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS children_quantity,

         SUM(provided_service.accepted_payment) AS all_accepted_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_accepted_payment,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.accepted_payment ELSE 0 END) AS children_accepted_payment
         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND provided_service.payment_type_fk in (2, 4)
             AND ({condition})
         GROUP BY medical_register.organization_code
         """

    hospital_total_query = """
         SELECT
         medical_register.organization_code,
         SUM(round(provided_service.tariff, 2)) AS all_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=2
             THEN provided_service.tariff*0.015 ELSE 0 END) all_caf_coef,

         -SUM(CASE WHEN provided_service_coefficient.coefficient_fk=6
             THEN round(provided_service.tariff*0.7, 2) ELSE 0 END) all_exc_vol,

         SUM(provided_service.accepted_payment) AS all_accepted_payment
         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient
                 ON provided_service_coefficient.service_fk = provided_service.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND provided_service.payment_type_fk in (2, 4)
             AND ({condition})
         GROUP BY medical_register.organization_code
         """

    hospital_hmc_query = """
         SELECT
         DISTINCT medical_register.organization_code,
         COUNT(DISTINCT (patient.id_pk, medical_service.tariff_profile_fk)) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN (patient.id_pk, medical_service.tariff_profile_fk) END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN (patient.id_pk, medical_service.tariff_profile_fk) END) AS children_population,

         COUNT(provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_hospitalization,

         SUM(round(provided_service.quantity, 2)) AS all_quantity,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS adult_quantity,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN round(provided_service.quantity, 2) ELSE 0 END) AS children_quantity,

         SUM(provided_service.accepted_payment) AS all_accepted_payment,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.accepted_payment ELSE 0 END) AS adult_accepted_payment,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.accepted_payment ELSE 0 END) AS children_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND provided_service.payment_type_fk in (2, 4)
             AND medical_service.group_fk = 20
             AND medical_service.tariff_profile_fk in ({condition})
         GROUP BY medical_register.organization_code
         """

    hospital_hmc_total_query = """
         SELECT
         medical_register.organization_code, SUM(provided_service.tariff) AS all_tariff
         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
         WHERE medical_register.is_active
             AND medical_register.year = '{year}'
             AND medical_register.period = '{period}'
             AND provided_service.payment_type_fk in (2, 4)
             AND medical_service.group_fk = 20
             AND medical_service.tariff_profile_fk in ({condition})
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Круглосуточный стационар',
             'pattern': 'hospital',
             'sum': [
                 {'query': calc((hospital_query,
                                 """
                                 (provided_event.term_fk = 1 AND medical_service.group_fk IS NULL)
                                  OR medical_service.group_fk in (1, 2, 3)
                                  """)),
                  'separator_length': 2},
                 {'query': calc((hospital_total_query,
                                 """
                                 (provided_event.term_fk = 1 AND
                                  medical_service.group_fk IS NULL)
                                  OR medical_service.group_fk in (1, 2, 3)
                                  """)),
                  'separator_length': 2}]},
            {'title': u'Круглосуточный стационар ВМП',
             'pattern': 'hospital_hmc',
             'sum': [
                 {'query': calc((hospital_hmc_query, '56')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '57')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '58')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '59')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '60')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '63')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '61')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '62')),
                  'separator_length': 0},
                 {'query': calc((hospital_hmc_query, '56, 57, 58, 59, 60, 63, 61, 62')),
                  'separator_length': 2},
                 {'query': calc((hospital_hmc_total_query, '56, 57, 58, 59, 60, 63, 61, 62')),
                  'separator_length': 0}]},
            {'title': u'Круглосуточный стационар свод',
             'pattern': 'hospital_all',
             'sum': [{
                 'query': calc((hospital_query,
                                """
                                (provided_event.term_fk = 1 AND medical_service.group_fk IS NULL)
                                OR medical_service.group_fk in (1, 2, 3, 20)
                                """)),
                 'separator_length': 0
             }]}]


### Структура актов по скорой помощи
def get_acute_care_structure(calc):
    acute_care_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT (patient.id_pk, medical_service.division_fk, medical_service.code like '0%')) AS all_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN (patient.id_pk, medical_service.division_fk) END) AS adult_population,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN (patient.id_pk, medical_service.division_fk) END) AS children_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '0%'
               THEN provided_service.id_pk END) AS adult_hospitalization,
         COUNT(DISTINCT CASE WHEN medical_service.code like '1%'
               THEN provided_service.id_pk END) AS children_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN medical_service.code like '0%'
             THEN provided_service.tariff ELSE 0 END) AS adult_tariff,
         SUM(CASE WHEN medical_service.code like '1%'
             THEN provided_service.tariff ELSE 0 END) AS children_tariff

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND provided_event.term_fk = 4
               AND medical_service.division_fk in ({condition})
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'СМП финансирование по подушевому нормативу (кол-во, основной тариф)',
             'pattern': 'acute_care',
             'sum': [
                 {'query': calc((acute_care_query, '456')),
                  'separator_length': 0, 'len': 9},
                 {'query': calc((acute_care_query, '455')),
                  'separator_length': 0, 'len': 9},
                 {'query': calc((acute_care_query, '457')),
                  'separator_length': 0, 'len': 9},
                 {'query': calc((acute_care_query, '458')),
                  'separator_length': 0, 'len': 9},
                 {'query': calc((acute_care_query, '456, 455, 457, 458')),
                  'separator_length': 0, 'len': 9}]}]


### Структура актов периодических медосмотров
def get_periodic_med_exam_structure(calc):
    periodic_med_exam_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT patient.id_pk) AS all_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,

         SUM(CASE WHEN provided_service_coefficient IS NULL
             THEN 0 ELSE round(provided_service.tariff*1.07, 2) END),

         SUM(provided_service.accepted_payment) AS all_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND medical_service.group_fk=16 and medical_service.subgroup_fk is NULL
               {condition}
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Периодический медицинский осмотр несовершеннолетних',
             'pattern': 'periodic_medical_examination',
             'sum': [
                 {'query': calc((periodic_med_exam_query, '')),
                  'separator_length': 0, 'len': 5}]}]


### Структура актов предварительных медосмотров
def get_preliminary_med_exam_structure(calc):
    preliminary_med_exam_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NULL
             THEN 0 ELSE round(provided_service.tariff*1.07, 2) END),

         SUM(provided_service.accepted_payment) AS all_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND {condition}
         GROUP BY medical_register.organization_code
         """

    preliminary_med_exam_spec_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT patient.id_pk) AS all_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND {condition}
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Предварительный медицинский осмотр несовершеннолетних',
             'pattern': 'preliminary_medical_examination',
             'sum': [
                 {'query': calc((preliminary_med_exam_query,
                                 "medical_service.code='119101'")),
                  'separator_length': 0, 'len': 5},
                 {'query': calc((preliminary_med_exam_query,
                                 "medical_service.code='119119'")),
                  'separator_length': 0, 'len': 5},
                 {'query': calc((preliminary_med_exam_query,
                                 "medical_service.code='119120'")),
                  'separator_length': 0, 'len': 5},
                 {'query': calc((preliminary_med_exam_query,
                                 """
                                  medical_service.code in
                                  ('119101', '119119', '119120')
                                  """)),
                  'separator_length': 1, 'len': 5},
                 {'query': calc((preliminary_med_exam_spec_query,
                                 """
                                 medical_service.group_fk=15 and
                                 medical_service.subgroup_fk=11
                                 """)),
                  'separator_length': 2, 'len': 2},
                 {'query': calc((preliminary_med_exam_query,
                                 """
                                 medical_service.group_fk=15 and
                                 (medical_service.subgroup_fk=11
                                 or medical_service.code in ('119101', '119119', '119120'))
                                 """)),
                  'separator_length': 0, 'len': 5}
             ]}]


### Структура актов профиактических осмотров
def get_preventive_med_exam_structure(calc):
    preventive_med_exam_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,


         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    preventive_med_exam_total_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(provided_service.accepted_payment) AS all_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    preventive_med_exam_spec_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND (medical_service.group_fk=11 AND medical_service.subgroup_fk=8)
               {condition}
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Профилактический медицинский осмотр несовершеннолетних',
             'pattern': 'preventive_medical_examination',
             'sum': [
                 {'query': calc((preventive_med_exam_query,
                                 """
                                  medical_service.code in ('119051', '119080', '119081')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_query,
                                 """
                                 medical_service.code in ('119052', '119082', '119083')
                                 """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_query,
                                 """
                                 medical_service.code in ('119053', '119084', '119085')
                                 """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_query,
                                 """
                                 medical_service.code in ('119054', '119086', '119087')
                                 """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_query,
                                """
                                medical_service.code in ('119055', '119088', '119089')
                                """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_query,
                                 """
                                 medical_service.code in ('119056', '119090', '119091')
                                 """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((preventive_med_exam_total_query,
                                 """
                                 medical_service.code in (
                                     '119051', '119052', '119053',
                                     '119054', '119055', '119056',
                                     '119080', '119081', '119082',
                                     '119083', '119084', '119085',
                                     '119086', '119087', '119088',
                                     '119089', '119090', '119091')
                                 """)),
                  'separator_length': 2, 'len': 15},
                 {'query': calc((preventive_med_exam_spec_query, '')),
                  'separator_length': 2,  'len': 6},
                 {'query': calc((preventive_med_exam_total_query,
                                 """
                                 medical_service.group_fk=11 AND
                                 (medical_service.subgroup_fk=8
                                  OR medical_service.code in (
                                      '119051', '119052', '119053',
                                      '119054', '119055', '119056',
                                      '119080', '119081', '119082',
                                      '119083', '119084', '119085',
                                      '119086', '119087', '119088',
                                      '119089', '119090', '119091'))
                                """)),
                  'separator_length': 0, 'len': 15},

             ]}]


### Структура актов для диспансеризации детей сирот (без попечения родителей)
def get_examination_children_without(calc):
    exam_children_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,


         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    exam_children_total_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(provided_service.accepted_payment) AS all_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    exam_children_spec_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND (medical_service.group_fk=13 AND medical_service.subgroup_fk=10)
               {condition}
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Диспансеризация несовершеннолетних (без попечения родителей)',
             'pattern': 'examination_children_without_care',
             'sum': [
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119220', '119221')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119222', '119223')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119224', '119225')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119226', '119227')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119228', '119229')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119230', '119231')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_total_query,
                                 """
                                 medical_service.code in (
                                     '119220', '119221',
                                     '119222', '119223',
                                     '119224', '119225',
                                     '119226', '119227',
                                     '119228', '119229',
                                     '119230', '119231')
                                  """)),
                  'separator_length': 1, 'len': 15},
                 {'query': calc((exam_children_spec_query, '')),
                  'separator_length': 2, 'len': 6},
                 {'query': calc((exam_children_total_query,
                                 """
                                 medical_service.group_fk=13 AND
                                 (medical_service.subgroup_fk=10
                                  OR medical_service.code in (
                                     '119220', '119221',
                                     '119222', '119223',
                                     '119224', '119225',
                                     '119226', '119227',
                                     '119228', '119229',
                                     '119230', '119231'))
                                """)),
                  'separator_length': 0, 'len': 15}]}]


### Структура актов для диспансеризации детей сирот (в трудной ситуации)
def get_examination_children_difficult_situation(calc):
    exam_children_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,


         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL AND patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    exam_children_total_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT CASE WHEN medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1 AND medical_service.subgroup_fk IS NULL
               THEN (patient.id_pk, medical_service.id_pk) END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization,

         SUM(provided_service.tariff) AS all_tariff,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.tariff ELSE 0 END) AS all_female_tariff,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.tariff ELSE 0 END) AS all_male_tariff,

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 2
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_female_coeff,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk IS NOT NULL and patient.gender_fk = 1
             THEN round(provided_service.tariff*1.07, 2) ELSE 0 END) AS all_male_coeff,

         SUM(provided_service.accepted_payment) AS all_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 2
             THEN provided_service.accepted_payment ELSE 0 END) AS all_female_accepted_payment,
         SUM(CASE WHEN patient.gender_fk = 1
             THEN provided_service.accepted_payment ELSE 0 END) AS all_male_accepted_payment

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk
             LEFT JOIN provided_service_coefficient ON provided_service_coefficient.id_pk =
                 (SELECT psc1.id_pk
                  FROM provided_service_coefficient psc1
                  WHERE provided_service.id_pk = psc1.service_fk and psc1.coefficient_fk=5 LIMIT 1)

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND ({condition})
         GROUP BY medical_register.organization_code
         """

    exam_children_spec_query = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT patient.id_pk) AS all_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN patient.id_pk END) AS all_female_population,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN patient.id_pk END) AS all_male_population,

         COUNT(DISTINCT provided_service.id_pk) AS all_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 2
               THEN provided_service.id_pk END) AS all_female_hospitalization,
         COUNT(DISTINCT CASE WHEN patient.gender_fk = 1
               THEN provided_service.id_pk END) AS all_male_hospitalization

         FROM provided_service
             JOIN medical_service
                 ON medical_service.id_pk = provided_service.code_fk
             JOIN provided_event
                 ON provided_service.event_fk = provided_event.id_pk
             JOIN medical_register_record
                 ON provided_event.record_fk = medical_register_record.id_pk
             JOIN medical_register
                 ON medical_register_record.register_fk = medical_register.id_pk
             JOIN patient
                 ON medical_register_record.patient_fk = patient.id_pk

         WHERE medical_register.is_active
               AND medical_register.year = '{year}'
               AND medical_register.period = '{period}'
               AND provided_service.payment_type_fk in (2, 4)
               AND (medical_service.group_fk=12 AND medical_service.subgroup_fk=9)
               {condition}
         GROUP BY medical_register.organization_code
         """

    return [{'title': u'Диспансеризация несовершеннолетних (в трудной жизненной ситуации)',
             'pattern': 'examination_children_difficult_situation',
             'sum': [
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119020', '119021')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119022', '119023')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119024', '119025')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119026', '119027')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119028', '119029')
                                  """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_query,
                                 """
                                 medical_service.code in ('119030', '119031')
                                 """)),
                  'separator_length': 0, 'len': 10},
                 {'query': calc((exam_children_total_query,
                                 """
                                 medical_service.code in (
                                     '119020', '119021',
                                     '119022', '119023',
                                     '119024', '119025',
                                     '119026', '119027',
                                     '119028', '119029',
                                     '119030', '119031')
                                  """)),
                  'separator_length': 1, 'len': 15},
                 {'query': calc((exam_children_spec_query, '')),
                  'separator_length': 2, 'len': 6},
                 {'query': calc((exam_children_total_query,
                                 """
                                 medical_service.group_fk=12 AND
                                 (medical_service.subgroup_fk=9
                                  OR medical_service.code in (
                                     '119020', '119021',
                                     '119022', '119023',
                                     '119024', '119025',
                                     '119026', '119027',
                                     '119028', '119029',
                                     '119030', '119031'))
                                """)),
                  'separator_length': 0, 'len': 15}]}]


### Структура акта по подушевому для поликлинники
def get_capitation_amb_care_structure(year, period):
    result_data = {}
    for mo_code in get_mo_register(year, period):
        capitation_tariff = calculate_capitation_tariff(3, year, period, mo_code)
        result_data[mo_code] = [0, ]*24
        result_data[mo_code][1] = capitation_tariff['male']['population']['adult']
        result_data[mo_code][2] = capitation_tariff['female']['population']['adult']
        result_data[mo_code][3] = capitation_tariff['male']['population']['children']
        result_data[mo_code][4] = capitation_tariff['female']['population']['children']
        result_data[mo_code][0] = result_data[mo_code][1]+result_data[mo_code][2] + \
            result_data[mo_code][3]+result_data[mo_code][4]

        result_data[mo_code][5] = capitation_tariff['male']['tariff']['adult']
        result_data[mo_code][6] = capitation_tariff['male']['tariff']['children']

        result_data[mo_code][8] = capitation_tariff['male']['population_tariff']['adult']
        result_data[mo_code][9] = capitation_tariff['female']['population_tariff']['adult']
        result_data[mo_code][10] = capitation_tariff['male']['population_tariff']['children']
        result_data[mo_code][11] = capitation_tariff['female']['population_tariff']['children']
        result_data[mo_code][7] = result_data[mo_code][8]+result_data[mo_code][9] + \
            result_data[mo_code][10]+result_data[mo_code][11]

        result_data[mo_code][12] = capitation_tariff['male']['coefficient_value']['adult']-1 \
            if capitation_tariff['male']['coefficient_value']['adult'] else 0
        result_data[mo_code][13] = capitation_tariff['male']['coefficient_value']['children']-1 \
            if capitation_tariff['male']['coefficient_value']['children'] else 0

        result_data[mo_code][15] = capitation_tariff['male']['coefficient']['adult']
        result_data[mo_code][16] = capitation_tariff['female']['coefficient']['adult']
        result_data[mo_code][17] = capitation_tariff['male']['coefficient']['children']
        result_data[mo_code][18] = capitation_tariff['female']['coefficient']['children']
        result_data[mo_code][14] = result_data[mo_code][15]+result_data[mo_code][16] + \
            result_data[mo_code][17]+result_data[mo_code][18]

        result_data[mo_code][20] = capitation_tariff['male']['accepted_payment']['adult']
        result_data[mo_code][21] = capitation_tariff['female']['accepted_payment']['adult']
        result_data[mo_code][22] = capitation_tariff['male']['accepted_payment']['children']
        result_data[mo_code][23] = capitation_tariff['female']['accepted_payment']['children']
        result_data[mo_code][19] = result_data[mo_code][20]+result_data[mo_code][21] + \
            result_data[mo_code][22]+result_data[mo_code][23]

    return [{'title': u'Подушевой норматив (амбулаторная помощь)',
             'pattern': 'capitation_ambulatory_care',
             'sum': [{'query': result_data, 'separator_length': 0, 'len': 24}]}]


### Структура акта для подушевого по скорой помощи
def get_capitation_acute_care_structure(year, period):
    result_data = {}
    for mo_code in get_mo_register(year, period):
        capitation_tariff = calculate_capitation_tariff(4, year, period, mo_code)
        result_data[mo_code] = [0, ]*11
        result_data[mo_code][1] = capitation_tariff['male']['population']['adult']
        result_data[mo_code][2] = capitation_tariff['female']['population']['adult']
        result_data[mo_code][3] = capitation_tariff['male']['population']['children']
        result_data[mo_code][4] = capitation_tariff['female']['population']['children']
        result_data[mo_code][0] = result_data[mo_code][1]+result_data[mo_code][2] + \
            result_data[mo_code][3]+result_data[mo_code][4]

        result_data[mo_code][5] = capitation_tariff['male']['tariff']['adult']

        result_data[mo_code][7] = capitation_tariff['male']['accepted_payment']['adult']
        result_data[mo_code][8] = capitation_tariff['female']['accepted_payment']['adult']
        result_data[mo_code][9] = capitation_tariff['male']['accepted_payment']['children']
        result_data[mo_code][10] = capitation_tariff['female']['accepted_payment']['children']
        result_data[mo_code][6] = result_data[mo_code][7]+result_data[mo_code][8] + \
            result_data[mo_code][9]+result_data[mo_code][10]

    return [{'title': u'Подушевой норматив (СМП)',
             'pattern': 'capitation_acute_care',
             'sum': [{'query': result_data, 'separator_length': 0, 'len': 11}]}]


def run_sql(year, period):
    def run(query):
        pattern_query, condition = query
        text_query = pattern_query.format(year=year, period=period,
                                          condition=condition)
        cursor = connection.cursor()
        cursor.execute(text_query)
        result_sum = {mo_data[0]: [value for value in mo_data[1:]]
                      for mo_data in cursor.fetchall()}
        cursor.close()
        print '***'
        return result_sum
    return lambda query: run(query)


def print_act(year, period, rule):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=rule['title'],
        month=MONTH_NAME[period],
        year=year)
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=rule['pattern'])
    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], ]) as act_book:
        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        block_index = 2
        for condition in rule['sum']:
            result_data = condition['query']
            if result_data:
                total_sum = [0, ]*len(result_data.values()[0])
                print '*', len(total_sum)
                for mo_code, value in result_data.iteritems():
                    act_book.set_cursor(ACT_CELL_POSITION[mo_code], block_index)
                    for index, cell_value in enumerate(value):
                        total_sum[index] += cell_value
                        act_book.write_cell(cell_value, 'c')
                act_book.set_cursor(101, block_index)
                for cell_value in total_sum:
                    act_book.write_cell(cell_value, 'c')
            block_index += condition['len'] + \
                condition['separator_length']


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        start = time.clock()

        calc = run_sql(year, period)

        acts_structure = [
            #get_day_hospital_structure(calc),
            #get_stomatology_structure(calc),
            #get_hospital_structure(calc),
            #get_acute_care_structure(calc),
            ##get_periodic_med_exam_structure(calc),
            ##get_preliminary_med_exam_structure(calc),
            ##get_preventive_med_exam_structure(calc),
            #get_capitation_amb_care_structure(year, period),
            #get_capitation_acute_care_structure(year, period),
            ##get_examination_children_without(calc),
            ##get_examination_children_difficult_situation(calc)
        ]

        for structure in acts_structure:
            for rule in structure:
                print rule['title']
                print_act(year, period, rule)
        elapsed = time.clock() - start
        print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed//60), int(elapsed % 60))
