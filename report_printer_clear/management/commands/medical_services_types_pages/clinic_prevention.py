#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class ClinicPreventionAllPage(MedicalServiceTypePage):

    """
    Отчёт включает в себя:
    1. Поликлиника (профосмотр)
    2. Поликлиника (прививка)
    3. Профосмотр взрослых (первичный и итоговый) см. ProphylacticExaminationAdultPage
    4. Центр здоровья
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,
                    COUNT(DISTINCT CASE WHEN service_group IN (4)
                                          THEN (0, patient_id, service_code, is_adult)
                                        WHEN service_group IN (9)
                                          THEN (2, patient_id, service_group, is_adult)
                                        ELSE (1, patient_id, service_division::varchar, is_adult)
                                   END) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (
                                             CASE WHEN service_group IN (4)
                                                    THEN (0, patient_id, service_code, is_adult)
                                                  WHEN service_group IN (9)
                                                    THEN (2, patient_id, service_group, is_adult)
                                                  ELSE (1, patient_id, service_division::varchar, is_adult)
                                             END
                                          )
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (
                                             CASE WHEN service_group IN (4)
                                                    THEN (0, patient_id, service_code, is_adult)
                                                  WHEN service_group IN (9)
                                                    THEN (2, patient_id, service_group, is_adult)
                                             ELSE (1, patient_id, service_division::varchar, is_adult)
                                             END)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_accepted) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                             ELSE 0
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                             ELSE 0
                        END) AS total_tariff_child
                FROM registry_services
                WHERE (service_term = 3
                      AND service_reason IN (2, 3)
                      AND (service_group = 24 OR service_group IS NULL)
                      AND NOT is_capitation)
                      OR (service_group = 9 AND service_code IN ('019214', '019215', '019216', '019217'))
                      OR service_group = 4
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

                  'total_tariff',
                  'total_tariff_adult',
                  'total_tariff_child')

        return ('0', 2, fields),
