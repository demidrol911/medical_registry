#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection
from medical_service_register.path import REESTR_EXP, MONTH_NAME, BASE_DIR
from helpers.excel_writer import ExcelWriter
from helpers.excel_style import VALUE_STYLE, PERIOD_VALUE_STYLE

ACT_CELL_POSITION = {
    '280003': 20, '280005': 21, '280043': 22, '280013': 23,
    '280018': 24, '280054': 25, '280026': 27, '280036': 28,
    '280085': 29, '280038': 30, '280066': 31, '280064': 32,
    '280069': 33, '280004': 34, '280082': 35, '280083': 36,
    '280028': 37, '280086': 38, '280088': 39, '280091': 40,
    '280093': 41, '280096': 42, '280017': 45, '280065': 46,
    '280010': 47, '280001': 49, '280052': 50, '280016': 51,
    '280076': 52, '280075': 54, '280019': 55, '280024': 57,
    '280068': 59, '280067': 61, '280022': 62, '280084': 64,
    '280070': 65, '280029': 67, '280037': 68, '280078': 70,
    '280059': 72, '280074': 73, '280061': 74, '280027': 76,
    '280041': 77, '280023': 78, '280040': 80, '280025': 82,
    '280015': 83, '280012': 85, '280009': 86, '280007': 88,
    '280002': 90, '280039': 92, '280071': 94, '280080': 96,
    '280053': 98, '280020': 100
}


### Структура для актов дневного стационара
def get_day_hospital_structure():
    DAY_HOSPITAL_QUERY = """
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
                 {'query': (DAY_HOSPITAL_QUERY,
                            """
                            (provided_event.term_fk=2 and
                             medical_division.term_fk in (10, 11) and
                             medical_service.group_fk is null)
                             or medical_service.group_fk in (17, 28)
                            """),
                  'cell_count': 12,
                  'separator_length': 2},
                 {'query': (DAY_HOSPITAL_QUERY,
                            """
                            provided_event.term_fk=2 and
                            medical_service.group_fk = 28
                            """),
                  'cell_count': 12,
                  'separator_length': 2}
             ]},
            {'title': u'Дневной стационар на дому',
             'pattern': 'day_hospital_home',
             'sum': [
                 {'query': (DAY_HOSPITAL_QUERY,
                            """
                            provided_event.term_fk=2 and
                            medical_division.term_fk=12 and
                            medical_service.group_fk is null
                            """),
                  'cell_count': 12,
                  'separator_length': 2}
             ]},
            {'title': u'Дневной стационар свод',
             'pattern': 'day_hospital_all',
             'sum': [
                 {'query': (DAY_HOSPITAL_QUERY,
                            """
                            (provided_event.term_fk=2 and medical_service.group_fk is null)
                             or medical_service.group_fk in (17, 28)
                            """),
                  'cell_count': 12,
                  'separator_length': 2}
             ]}]


### Структура актов по стоматологии
def get_stomatology_structure():
    STOMATOLOGY_DISEASE_QUERY = """
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

    STOMATOLOGY_PROPH_OR_AMBULANCE_QUERY = """
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

    STOMATOLOGY_EMERGENCY_QUERY = """
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

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS all_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4 AND medical_service.code like '0%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS adult_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4 AND medical_service.code like '1%'
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

    STOMATOLOGY_TOTAL_QUERY = """
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

         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS all_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4 AND medical_service.code like '0%'
             THEN round(provided_service.tariff*0.2, 2) ELSE 0 END) AS adult_emergency,
         SUM(CASE WHEN provided_service_coefficient.coefficient_fk=4 AND medical_service.code like '1%'
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
                 {'query': (STOMATOLOGY_DISEASE_QUERY, '12'),
                  'cell_count': 15,
                  'separator_length': 0},
                 {'query': (STOMATOLOGY_PROPH_OR_AMBULANCE_QUERY, '13'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (STOMATOLOGY_PROPH_OR_AMBULANCE_QUERY, '14'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (STOMATOLOGY_EMERGENCY_QUERY, '17'),
                  'cell_count': 18,
                  'separator_length': 0},
                 {'query': (STOMATOLOGY_TOTAL_QUERY, '12, 13, 14, 17'),
                  'cell_count': 21,
                  'separator_length': 0}]},
            ]


### Структура актов для круглосуточного стационара
def get_hospital_structure():
    HOSPITAL_QUERY = """
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

    HOSPITAL_TOTAL_QUERY = """
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

    HOSPITAL_HMC_QUERY = """
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

    HOSPITAL_HMC_TOTAL_QUERY = """
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
                 {'query': (HOSPITAL_QUERY,
                            """
                            (provided_event.term_fk = 1 AND medical_service.group_fk IS NULL)
                            OR medical_service.group_fk in (1, 2, 3)
                            """),
                  'cell_count': 12,
                  'separator_length': 2},
                 {'query': (HOSPITAL_TOTAL_QUERY,
                            """
                            (provided_event.term_fk = 1 AND
                            medical_service.group_fk IS NULL)
                            OR medical_service.group_fk in (1, 2, 3)
                            """),
                  'cell_count': 4,
                  'separator_length': 2}]},
            {'title': u'Круглосуточный стационар ВМП',
             'pattern': 'hospital_hmc',
             'sum': [
                 {'query': (HOSPITAL_HMC_QUERY, '56'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '57'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '58'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '59'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '60'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '63'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '61'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '62'),
                  'cell_count': 12,
                  'separator_length': 0},
                 {'query': (HOSPITAL_HMC_QUERY, '56, 57, 58, 59, 60, 63, 61, 62'),
                  'cell_count': 12,
                  'separator_length': 2},
                 {'query': (HOSPITAL_HMC_TOTAL_QUERY, '56, 57, 58, 59, 60, 63, 61, 62'),
                  'cell_count': 1,
                  'separator_length': 0}]},
            {'title': u'Круглосуточный стационар свод',
             'pattern': 'hospital_all',
             'sum': [{
                 'query': (HOSPITAL_QUERY,
                           """
                           (provided_event.term_fk = 1 AND medical_service.group_fk IS NULL)
                           OR medical_service.group_fk in (1, 2, 3, 20)
                           """),
                 'cell_count': 12,
                 'separator_length': 0
             }]}]


### Структура актов по скорой помощи
def get_acute_care_structure():
    ACUTE_CARE_QUERY = """
         SELECT
         medical_register.organization_code,
         COUNT(DISTINCT (patient.id_pk, medical_service.division_fk)) AS all_population,
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
                 {'query': (ACUTE_CARE_QUERY, '456'),
                  'cell_count': 9,
                  'separator_length': 0},
                 {'query': (ACUTE_CARE_QUERY, '455'),
                  'cell_count': 9,
                  'separator_length': 0},
                 {'query': (ACUTE_CARE_QUERY, '457'),
                  'cell_count': 9,
                  'separator_length': 0},
                 {'query': (ACUTE_CARE_QUERY, '458'),
                  'cell_count': 9,
                  'separator_length': 0},
                 {'query': (ACUTE_CARE_QUERY, '456, 455, 457, 458'),
                  'cell_count': 9,
                  'separator_length': 0}]}]


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        target_dir = REESTR_EXP % (year, period)
        act_path_t = ur'{dir}\{title}_{month}_{year}'
        temp_path_t = ur'{base}\templates\excel_pattern\end_of_month\{template}.xls'
        query_cursor = connection.cursor()

        acts_structure = [
            get_day_hospital_structure(),
            get_stomatology_structure(),
            get_hospital_structure(),
            get_acute_care_structure()
        ]

        for structure in acts_structure:

            for rule in structure:
                print rule['title']
                act_path = act_path_t.format(dir=target_dir,
                                             title=rule['title'],
                                             month=MONTH_NAME[period],
                                             year=year)
                temp_path = temp_path_t.format(base=BASE_DIR,
                                               template=rule['pattern'])
                print temp_path

                with ExcelWriter(act_path, template=temp_path,
                                 sheet_names=[MONTH_NAME[period], ]) \
                        as act_book:
                    act_book.set_overall_style({'font_size': 11, 'border': 1})
                    act_book.set_cursor(4, 2)
                    act_book.set_style(PERIOD_VALUE_STYLE)
                    act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
                    act_book.set_style(VALUE_STYLE)
                    block_index = 2
                    for condition in rule['sum']:
                        total_sum = []
                        query_cursor.execute(
                            condition['query'][0].format(
                                year=year, period=period,
                                condition=condition['query'][1]))

                        for mo_data in query_cursor.fetchall():
                            if not total_sum:
                                total_sum = [0, ]*condition['cell_count']
                            act_book.set_cursor(ACT_CELL_POSITION[mo_data[0]], block_index)

                            for index, cell_value in enumerate(mo_data[1:]):
                                total_sum[index] += cell_value
                                act_book.write_cell(cell_value, 'c')

                        act_book.set_cursor(101, block_index)
                        for cell_value in total_sum:
                            act_book.write_cell(cell_value, 'c')

                        block_index += condition['cell_count'] + \
                            condition['separator_length']
        query_cursor.close()
