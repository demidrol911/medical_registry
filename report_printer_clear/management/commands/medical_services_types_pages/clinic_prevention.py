from general import MedicalServiceTypePage


class ClinicPreventionPrimary(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code IN ('001038', '101038') THEN '0'
                         WHEN service_code IN ('001039', '101039') THEN '1'
                    END AS group_field,

                    COUNT(DISTINCT (patient_id, service_code, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN (patient_id, service_code)
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN (patient_id, service_code)
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
                      AND service_group = 4
                      AND NOT is_capitation
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

        return (('0', 47, fields),
                ('1', 56, fields))


class ClinicPreventionSpec(MedicalServiceTypePage):

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
                      AND service_reason IN (2)
                      AND (service_group = 24 OR service_group IS NULL)
                      AND NOT is_capitation
                      AND service_division NOT IN (399, 401, 403)
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


class ClinicPreventionAll(MedicalServiceTypePage):

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
                      AND service_reason IN (2)
                      AND (service_group = 24 OR service_group IS NULL)
                      AND NOT is_capitation
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


class ProphylacticExaminationAdult(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,
                    COUNT(DISTINCT CASE WHEN service_code in ('019214', '019215')
                                          THEN service_id
                                    END) AS count_primary_services,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1 AND service_code IN ('019214', '019215')
                                          THEN service_id
                                   END) AS count_primary_services_men,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2 AND service_code IN ('019214', '019215')
                                          THEN service_id
                                   END) AS count_primary_services_fem,

                    COUNT(DISTINCT CASE WHEN service_code in ('019216', '019217')
                                          THEN service_id
                                    END) AS count_final_services,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1 AND service_code IN ('019216', '019217')
                                          THEN service_id
                                   END) AS count_final_services_men,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2 AND service_code IN ('019216', '019217')
                                          THEN service_id
                                   END) AS count_final_services_fem,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_men,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_fem,

                    SUM(ROUND(CASE WHEN psc.id_pk IS NOT NULL
                                     THEN (tc.value-1)*service_tariff
                                   ELSE 0
                              END, 2)) AS total_coeff1_07,
                    SUM(ROUND(CASE WHEN psc.id_pk IS NOT NULL AND patient_gender = 1
                                     THEN (tc.value-1)*service_tariff
                                   ELSE 0
                              END, 2)) AS total_coeff1_07_men,
                    SUM(ROUND(CASE WHEN psc.id_pk IS NOT NULL AND patient_gender = 2
                                     THEN (tc.value-1)*service_tariff
                                   ELSE 0
                              END, 2)) AS total_coeff1_07_fem,

                    SUM(service_tariff) AS total_accepted,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_men,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_fem

                FROM registry_services
                LEFT JOIN provided_service_coefficient psc
                   ON psc.service_fk = service_id AND psc.coefficient_fk = 5
                LEFT JOIN tariff_coefficient tc
                   ON tc.id_pk = psc.coefficient_fk
                WHERE service_group = 9
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_primary_services',
                  'count_primary_services_men',
                  'count_primary_services_fem',

                  'count_final_services',
                  'count_final_services_men',
                  'count_final_services_fem',

                  'total_tariff',
                  'total_tariff_men',
                  'total_tariff_fem',

                  'total_coeff1_07',
                  'total_coeff1_07_men',
                  'total_coeff1_07_fem',

                  'total_accepted',
                  'total_accepted_men',
                  'total_accepted_fem')

        return ('0', 15, fields),