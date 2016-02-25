from general import MedicalServiceTypePage


class AcuteCarePage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_group AS group_field,
                    COUNT(DISTINCT (patient_id, service_subgroup, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_subgroup)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_subgroup)
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
                WHERE service_term = 4 OR service_group != 43
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients', 'count_patients_adult', 'count_patients_child',
                  'count_services', 'count_services_adult', 'count_services_child',
                  'total_tariff', 'total_tariff_adult', 'total_tariff_child')
        return ((34, 5, fields),
                (33, 14, fields),
                (35, 23, fields),
                (36, 32, fields))


class ThrombolysisAcuteCarePage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_group AS group_field,
                    COUNT(DISTINCT (patient_id, service_subgroup, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_subgroup)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_subgroup)
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
                WHERE service_term = 4 AND service_group = 43
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients', 'count_patients_adult', 'count_patients_child',
                  'count_services', 'count_services_adult', 'count_services_child',
                  'total_tariff', 'total_tariff_adult', 'total_tariff_child')
        return (43, 3, fields),


