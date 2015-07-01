from general import MedicalServiceTypePage


class ExamChildrenDifficultSituationPrimaryPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code IN ('119020','119021') THEN '1'
                         WHEN service_code IN ('119022','119023') THEN '2'
                         WHEN service_code IN ('119024','119025') THEN '3'
                         WHEN service_code IN ('119026','119027') THEN '4'
                         WHEN service_code IN ('119028','119029') THEN '5'
                         WHEN service_code IN ('119030','119031') THEN '6'
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
                WHERE service_group = 12
                      AND service_code IN (
                          '119020','119021',
                          '119022','119023',
                          '119024','119025',
                          '119026','119027',
                          '119028','119029',
                          '119030','119031'
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


class ExamChildrenDifficultSituationSpecPage(MedicalServiceTypePage):

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
                WHERE service_group = 12
                      AND service_subgroup = 9
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 90, ('count_patients',
                          'count_patients_female',
                          'count_patients_male',
                          'count_services',
                          'count_services_female',
                          'count_services_male')),


class ExamChildrenWithoutCarePrimaryPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code IN ('119220', '119221') THEN '1'
                         WHEN service_code IN ('119222', '119223') THEN '2'
                         WHEN service_code IN ('119224', '119225') THEN '3'
                         WHEN service_code IN ('119226', '119227') THEN '4'
                         WHEN service_code IN ('119228', '119229') THEN '5'
                         WHEN service_code IN ('119230', '119231') THEN '6'
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
                WHERE service_group = 13
                      AND service_code IN (
                         '119220', '119221',
                         '119222', '119223',
                         '119224', '119225',
                         '119226', '119227',
                         '119228', '119229',
                         '119230', '119231'
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


class ExamChildrenWithoutCareSpecPage(MedicalServiceTypePage):

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
                WHERE service_group = 13
                      AND service_subgroup = 10
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 90, ('count_patients',
                          'count_patients_female',
                          'count_patients_male',
                          'count_services',
                          'count_services_female',
                          'count_services_male')),


