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
                      AND (service_group != 20 OR service_group IS NULL)
                      and service_code not in (
                            '098995',
                            '098996',
                            '098997',
                            '098606',
                            '098607',
                            '098608',
                            '098609',
                            '198611',
                            '198612',
                            '198613',
                            '198614',
                            '198615',
                            '198616',
                            '198617',
                            '198995',
                            '198996',
                            '198997'
                      ))
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


class AbortionVolumeExceededPage(MedicalServiceTypePage):
    """
    Отчёт включает в себя аборты сверх объёма.
    Используется для вынесения данных по абортам в отдельную колонку
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

                    COUNT(DISTINCT (patient_id, service_tariff_profile)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_quantity) AS count_days,
                    SUM(CASE WHEN is_adult
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult
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
                WHERE service_group = 45
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
        return ('0', 24, fields),


class HospitalKSGPage(MedicalServiceTypePage):
    """
    Отчёт включает в себя услуги оплачиваемы по КСГ в круглосуточном стационаре (мед реабилитацию и операции на сердце
    и коронарных сосудах)
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code in ('098995', '198995') THEN '180'
                         WHEN service_code in ('098996', '198996') THEN '181'
                         WHEN service_code in ('098997', '198997') THEN '182'
                         WHEN service_code in ('098606') THEN '300'
                         WHEN service_code in ('098607') THEN '301'
                         WHEN service_code in ('098608', '198611') THEN '302'
                         WHEN service_code in ('198613') THEN '303'
                         WHEN service_code in ('098609', '198612') THEN '304'
                         WHEN service_code in ('198614') THEN '305'
                         WHEN service_code in ('198615') THEN '306'
                         WHEN service_code in ('198616') THEN '307'
                         WHEN service_code in ('198617') THEN '308'
                    END AS group_field,

                    COUNT(DISTINCT (patient_id, service_tariff_profile)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_tariff_profile)
                                   END) AS count_patients_child,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_quantity) AS count_days,
                    SUM(CASE WHEN is_adult
                               THEN service_quantity
                        END) AS count_days_adult,
                    SUM(CASE WHEN NOT is_adult
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
                WHERE service_code in (
                    '098995', '098996', '098997',
                    '198995', '198996', '198997', '098606',
                    '098607', '098608', '098609', '198611',
                    '198612', '198613', '198614', '198615',
                    '198616', '198617'
                )
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

        return (('180', 3, fields),
                ('181', 15, fields),
                ('182', 27, fields),
                ('300', 39, fields),
                ('301', 51, fields),
                ('302', 63, fields),
                ('303', 75, fields),
                ('304', 87, fields),
                ('305', 99, fields),
                ('306', 111, fields),
                ('307', 123, fields),
                ('308', 135, fields))
