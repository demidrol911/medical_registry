from general import MedicalServiceTypePage


class PeriodicMedicalExamPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_code AS group_field,
                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT service_id) AS count_services,
                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN psc.id_pk is not NULL
                               THEN ROUND(service_tariff * 0.07, 2)
                        END) AS coeff1_07,
                    SUM(service_accepted) AS total_accepted
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                      AND psc.coefficient_fk = 5
                WHERE service_group = 16
                      AND service_code = '119151'
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('119151', 3, ('count_patients',
                              'count_services',
                              'total_tariff',
                              'coeff1_07',
                              'total_accepted')),


class PrelimMedicalExamPrimaryPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_code AS group_field,
                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT service_id) AS count_services,
                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN psc.id_pk is not NULL
                               THEN ROUND(service_tariff * 0.07, 2)
                        END) AS coeff1_07,
                    SUM(service_accepted) AS total_accepted
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                      AND psc.coefficient_fk = 5
                WHERE service_group = 15
                      AND service_code IN (
                           '119101',
                           '119119',
                           '119120'
                         )
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients',
                  'count_services',
                  'total_tariff',
                  'coeff1_07',
                  'total_accepted')
        return (('119101', 3, fields),
                ('119119', 9, fields),
                ('119120', 15, fields))


class PrelimMedicalExamSpecPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,
                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT service_id) AS count_services
                FROM registry_services
                WHERE service_group = 15
                      AND service_subgroup = 11
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 26, ('count_patients', 'count_services')),


class PreventMedicalExamPrimaryPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code IN ('119080','119081') THEN '1'
                         WHEN service_code IN ('119082','119083') THEN '2'
                         WHEN service_code IN ('119084','119085') THEN '3'
                         WHEN service_code IN ('119086','119087') THEN '4'
                         WHEN service_code IN ('119088','119089') THEN '5'
                         WHEN service_code IN ('119090','119091') THEN '6'
                    END AS group_field,

                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN patient_id
                                   END) AS count_patients_female,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN patient_id
                                   END) AS count_patients_male,

                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN service_id
                                   END) AS count_services_female,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN service_id
                                   END) AS count_services_male,

                    SUM(CASE WHEN patient_gender = 2
                               THEN service_tariff
                        END) AS total_tariff_female,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_tariff
                        END) AS total_tariff_male,

                    SUM(CASE WHEN patient_gender = 2 AND psc.id_pk is NOT NULL
                               THEN ROUND(service_tariff * 0.07, 2)
                        END) AS coeff1_07_female,
                    SUM(CASE WHEN patient_gender = 1 AND psc.id_pk is NOT NULL
                               THEN ROUND(service_tariff * 0.07, 2)
                        END)  AS coeff1_07_male,

                    SUM(CASE WHEN patient_gender = 2
                               THEN service_accepted
                        END) AS total_accepted_female,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_accepted
                        END) AS total_accepted_male

                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                      AND psc.coefficient_fk = 5
                WHERE service_group = 11
                      AND service_code IN (
                         '119080','119081',
                         '119082','119083',
                         '119084','119085',
                         '119086','119087',
                         '119088','119089',
                         '119090','119091'
                      )
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients_female', 'count_patients_male',
                  'count_services_female', 'count_services_male',
                  'total_tariff_female', 'total_tariff_male',
                  'coeff1_07_female', 'coeff1_07_male',
                  'total_accepted_female', 'total_accepted_male')
        return (('1', 4, fields),
                ('2', 16, fields),
                ('3', 28, fields),
                ('4', 40, fields),
                ('5', 52, fields),
                ('6', 64, fields))


class PreventMedicalExamSpecPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN patient_id
                                   END) AS count_patients_female,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN patient_id
                                   END) AS count_patients_male,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN service_id
                                   END) AS count_services_female,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN service_id
                                   END) AS count_services_male

                FROM registry_services
                WHERE service_group = 11
                      AND service_subgroup = 8
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 91, ('count_patients',
                          'count_patients_female',
                          'count_patients_male',
                          'count_services',
                          'count_services_female',
                          'count_services_male')),

