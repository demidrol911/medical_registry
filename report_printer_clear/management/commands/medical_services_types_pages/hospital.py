#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class HospitalPage(MedicalServiceTypePage):

    """
    Отчёт включает в себя:
    1. Круглосуточный стационар кроме ВМП
    2. Неотложная помощь в приёмном отделении только для АОДКБ и АОИБ
    По неотложной помощи в приёмном отделении учитываются только суммы по основному тарифу
    и принятая сумма
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

                    COUNT(DISTINCT CASE WHEN service_group NOT IN (31, 3) OR service_group is NULL
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                             AND (service_group NOT IN (31, 3) OR service_group is NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                             AND (service_group NOT IN (31, 3) OR service_group is NULL)
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT CASE WHEN service_group NOT IN (31, 3) OR service_group is NULL
                                          THEN service_id
                                   END) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                             AND (service_group NOT IN (31, 3) OR service_group is NULL)
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                             AND (service_group NOT IN (31, 3) OR service_group is NULL)
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(CASE WHEN service_group NOT IN (31, 3) OR service_group is NULL
                               THEN service_quantity
                        END) AS count_days,
                    SUM(CASE WHEN is_adult
                                  AND (service_group NOT IN (31, 3) OR service_group is NULL)
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult
                                   AND (service_group NOT IN (31, 3) OR service_group is NULL)
                               THEN service_quantity
                        END) AS count_days_child,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                        END) AS total_tariff_child,

                    SUM(CASE WHEN psc_curation.id_pk IS NOT NULL
                                  AND psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(0.25 * service_tariff * tc.value, 2)
                             ELSE 0
                        END) +
                        SUM(CASE WHEN psc_curation.id_pk IS NOT NULL
                                   THEN ROUND(0.25 * service_tariff, 2)
                                 ELSE 0
                            END
                    ) AS coeff_kskp,
                    SUM(CASE WHEN is_adult
                                  AND psc_curation.id_pk IS NOT NULL
                                  AND psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(0.25 * service_tariff * tc.value, 2)
                             ELSE 0
                        END) +
                        SUM(CASE WHEN is_adult
                                      AND psc_curation.id_pk IS NOT NULL
                                   THEN ROUND(0.25 * service_tariff, 2)
                                 ELSE 0
                            END
                    ) AS coeff_kskp_adult,
                    SUM(CASE WHEN NOT is_adult
                                  AND psc_curation.id_pk IS NOT NULL
                                  AND psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(0.25 * service_tariff * tc.value, 2)
                             ELSE 0
                        END) +
                        SUM(CASE WHEN NOT is_adult
                                      AND psc_curation.id_pk IS NOT NULL
                                   THEN ROUND(0.25 * service_tariff, 2)
                                 ELSE 0
                            END
                    ) AS coeff_kskp_child,

                    SUM(CASE WHEN psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_kpg,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END) AS coeff_kpg_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk IN (8, 9, 26)
                               THEN ROUND(service_tariff * tc.value, 2)
                             ELSE 0
                        END)  AS coeff_kpg_child,

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
                         AND psc.coefficient_fk NOT IN (7)
                    LEFT JOIN provided_service_coefficient psc_curation
                      ON psc_curation.service_fk = service_id
                         AND psc_curation.coefficient_fk = 7
                    LEFT JOIN tariff_coefficient tc
                      ON tc.id_pk = psc.coefficient_fk
                WHERE ((service_term = 1
                      AND (service_group != 20 OR service_group IS NULL))
                      OR (mo_code IN ('280013', '280043')
                          AND service_group = 31)
                      )
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 2, ('count_patients',
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

                         'coeff_kskp',
                         'coeff_kskp_adult',
                         'coeff_kskp_child',

                         'coeff_kpg',
                         'coeff_kpg_adult',
                         'coeff_kpg_child',

                         'total_accepted',
                         'total_accepted_adult',
                         'total_accepted_child'
        )),