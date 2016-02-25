#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class DayHospitalClinicPage(MedicalServiceTypePage):

    """
    Отчёт включает в себя три вида помощи
    1. Первичная (терапия, педиатрия, врач общей практики)
    2. Специальная (приёмы врачей специалистов) + ЭКО + Гемодиализ и перитонеальный диализ
    По Гемодиализу и перитонеальному диализу считается только стоимость
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_tariff_profile IN (42, 40, 41) THEN '0'
                         ELSE '1'
                    END AS group_field,

                    COUNT(DISTINCT CASE WHEN service_group != 42 OR service_group IS NULL
                                          THEN (patient_id, service_tariff_profile)
                                    END) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT CASE WHEN service_group != 42 OR service_group IS NULL
                                          THEN service_id
                                   END) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(CASE WHEN service_group != 42 OR service_group IS NULL
                               THEN service_quantity
                        END) AS count_days,
                    SUM(CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                               THEN service_quantity
                        END) AS count_days_child,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                        END) AS total_tariff_child,

                    SUM(CASE WHEN psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku_child,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                        END) AS total_accepted_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                        END) AS total_accepted_child
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                    LEFT JOIN tariff_coefficient tc
                      ON tc.id_pk = psc.coefficient_fk
                    JOIN medical_division md
                      ON md.id_pk = event_division_id
                WHERE (service_term = 2 AND service_group IS NULL
                      AND md.term_fk = 11) OR service_group IN (17, 42)
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients',
                  'count_patients_adult',
                  'count_patients_child',

                  'count_services',
                  'count_services_adult',
                  'count_services_child',

                  'count_days',
                  'count_days_adult',
                  'count_days_child',

                  'total_tariff',
                  'total_tariff_adult',
                  'total_tariff_child',

                  'coeff_ku',
                  'coeff_ku_adult',
                  'coeff_ku_child',

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return ('0', 2, fields),


class DayHospitalClinicTotalPage(MedicalServiceTypePage):

    """
    Отчёт включает в себя три вида помощи
    1. Первичная (терапия, педиатрия, врач общей практики)
    2. Специальная (приёмы врачей специалистов) + ЭКО + Гемодиализ и перитонеальный диализ
    По Гемодиализу и перитонеальному диализу считается только стоимость
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '1' AS group_field,

                    COUNT(DISTINCT CASE WHEN service_group != 42 OR service_group IS NULL
                                          THEN (patient_id, service_tariff_profile)
                                    END) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT CASE WHEN service_group != 42 OR service_group IS NULL
                                          THEN service_id
                                   END) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(CASE WHEN service_group != 42 OR service_group IS NULL
                               THEN service_quantity
                        END) AS count_days,
                    SUM(CASE WHEN is_adult AND (service_group != 42 OR service_group IS NULL)
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult AND (service_group != 42 OR service_group IS NULL)
                               THEN service_quantity
                        END) AS count_days_child,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                        END) AS total_tariff_child,

                    SUM(CASE WHEN psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk = 26
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_ku_child,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                        END) AS total_accepted_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                        END) AS total_accepted_child
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                    LEFT JOIN tariff_coefficient tc
                      ON tc.id_pk = psc.coefficient_fk
                    JOIN medical_division md
                      ON md.id_pk = event_division_id
                WHERE (service_term = 2 AND service_group IS NULL
                      AND md.term_fk = 11) OR service_group IN (17, 42)
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients',
                  'count_patients_adult',
                  'count_patients_child',

                  'count_services',
                  'count_services_adult',
                  'count_services_child',

                  'count_days',
                  'count_days_adult',
                  'count_days_child',

                  'total_tariff',
                  'total_tariff_adult',
                  'total_tariff_child',

                  'coeff_ku',
                  'coeff_ku_adult',
                  'coeff_ku_child',

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return ('1', 38, fields),