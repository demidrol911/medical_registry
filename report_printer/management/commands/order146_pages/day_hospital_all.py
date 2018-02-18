#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class DayHospitalAllPage(MedicalServiceTypePage):
    """
    Лист принятых услуг по
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
                    CASE WHEN md.term_fk = 12 or (md.term_fk = 11 and service_tariff_profile IN (42, 40)) THEN '1'
                         ELSE '0'
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
                WHERE service_term = 2 AND (service_group IS NULL OR service_group IN (17, 42, 28) OR service_group not in (46))
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

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return (('0', 2, fields),
                ('1', 14, fields))


class DayHospitalPrimaryPage(MedicalServiceTypePage):
    """
    Лист принятых услуг по
    1. Первичная (терапия, педиатрия, врач общей практики)
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

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
                WHERE service_term = 2 AND service_group IS NULL and (md.term_fk = 12 or (md.term_fk = 11 and service_tariff_profile IN (42, 40)))
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

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return ('0', 2, fields),


class DayHospitalSpecPage(MedicalServiceTypePage):
    """
    Лист принятых услуг по
    1. Специализированная
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

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
                WHERE service_term = 2 AND service_group IS NULL and not(md.term_fk = 12 or (md.term_fk = 11 and service_tariff_profile IN (42, 40)))
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

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return ('0', 2, fields),
