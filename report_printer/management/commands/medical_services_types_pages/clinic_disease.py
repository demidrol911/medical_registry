#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class ClinicDiseaseTreatmentAllPage(MedicalServiceTypePage):

    """
    Отчёт вклчает в себя:
    1. Поликлиника (заболевание)
    2. Гемодиализ и перитонеальный диализ при поликлинике
    3. Компьютерная и магнитно-резонансная томография
    4. Комплексаная пренатальная диагностика и скринниговое ультразвуковое исследование
    По гемодиализу и перитональному диализу, компьютерной и магнитно-резонансной томографии,
    скриниговому УЗИ и комплексной пренатальной диагностики учитывается только стоимость
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,
                    COUNT(DISTINCT CASE WHEN service_group IN (29, 5, 41)
                                          THEN NULL
                                        ELSE (patient_id, service_division:: varchar, is_adult)
                                   END) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (
                                             CASE WHEN service_group IN (29, 5, 41) THEN NULL
                                                  ELSE (patient_id, service_division:: varchar, is_adult)
                                             END
                                          )
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (
                                             CASE WHEN service_group IN (29, 5, 41) THEN NULL
                                                  ELSE (patient_id, service_division :: varchar, is_adult)
                                             END
                                          )
                                   END) AS count_patients_child,

                    COUNT(DISTINCT CASE WHEN service_group NOT IN (29, 5, 41) OR service_group IS NULL
                                          THEN event_id
                                   END) AS count_treatments,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group NOT IN (29, 5, 41) OR service_group IS NULL)
                                          THEN event_id
                                   END) AS count_treatments_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group NOT IN (29, 5, 41) OR service_group IS NULL)
                                          THEN event_id
                                   END) AS count_treatments_child,

                    COUNT(DISTINCT CASE WHEN service_group NOT IN (29, 5, 41) OR service_group IS NULL
                                          THEN service_id
                                   END) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult AND (service_group NOT IN (29, 5, 41) OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND (service_group NOT IN (29, 5, 41) OR service_group IS NULL)
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_child
                FROM registry_services
                WHERE (service_term = 3
                      AND service_reason = 1
                      AND (service_group = 24 OR service_group IS NULL)
                      AND NOT is_capitation
                      AND (SELECT
                              COUNT(DISTINCT inner_ps.id_pk)
                              FROM provided_service inner_ps
                                  JOIN medical_service inner_ms
                                     ON inner_ms.id_pk = inner_ps.code_fk
                              WHERE
                                 inner_ps.event_fk = event_id
                                 AND (inner_ms.group_fk is NULL
                                      OR inner_ms.group_fk in (24))
                                 AND inner_ms.reason_fk = 1
                           )>1
                      ) OR service_group IN (29, 5, 41)
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients',
                  'count_patients_adult',
                  'count_patients_child',

                  'count_treatments',
                  'count_treatments_adult',
                  'count_treatments_child',

                  'count_services',
                  'count_services_adult',
                  'count_services_child',

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')

        return ('0', 2, fields),


class ClinicDiseaseSingleVisitAllPage(MedicalServiceTypePage):

    """
    Отчёт включает в себя:
    1. Поликлиника (заболевание) разовые посещения
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,
                    COUNT(DISTINCT (patient_id, service_division, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_division)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_division)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_child
                FROM registry_services
                WHERE service_term = 3
                      AND service_reason = 1
                      AND (service_group = 24 OR service_group IS NULL)
                      AND NOT is_capitation
                      AND (SELECT
                              COUNT(DISTINCT inner_ps.id_pk)
                              FROM provided_service inner_ps
                                  JOIN medical_service inner_ms
                                     ON inner_ms.id_pk = inner_ps.code_fk
                              WHERE
                                 inner_ps.event_fk = event_id
                                 AND (inner_ms.group_fk is NULL
                                      OR inner_ms.group_fk in (24))
                                 AND inner_ms.reason_fk = 1
                           )=1
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
