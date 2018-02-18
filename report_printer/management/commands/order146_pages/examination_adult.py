#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class ExamAdultFirstStagePage(MedicalServiceTypePage):
    """
    Лист принятых услуг по первому этапу диспансеризации взрослых
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN ms_final.code IN ('019021', '019022')
                           THEN '1'
                        WHEN ms_final.code IN ('019023', '019024')
                           THEN '2'
                    END ||
                    CASE WHEN service_code = '019002'
                            THEN '&interview'
                         WHEN service_code not in ('019002', '019021', '019022', '019023', '019024')
                            THEN '&other'
                         ELSE ''
                    END AS group_field,


                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN patient_id
                                   END) AS count_patients_male,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN patient_id
                                   END) AS count_patients_female,

                    COUNT(DISTINCT service_id) AS count_services,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1
                                          THEN service_id
                                   END) AS count_services_male,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2
                                          THEN service_id
                                   END) AS count_services_female,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_male,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_female,

                    SUM(CASE WHEN psc.id_pk is NOT NULL
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0 END) AS coeff1_07,
                    SUM(CASE WHEN psc.id_pk is NOT NULL AND patient_gender = 1
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0
                        END) AS coeff1_07_male,
                    SUM(CASE WHEN psc.id_pk is NOT NULL AND patient_gender = 2
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0
                        END) AS coeff1_07_female,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_male,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_female
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                      AND psc.coefficient_fk = 5
                    lEFT JOIN medical_service ms_final
                      ON ms_final.id_pk = (
                         SELECT ms1.id_pk
                         FROM provided_service ps1
                             JOIN medical_service ms1
                                ON ms1.id_pk = ps1.code_fk
                         WHERE ps1.event_fk = event_id
                               AND ms1.code in (
                                   '019021',
                                   '019023',
                                   '019022',
                                   '019024'
                               )
                      )
                WHERE service_group = 7
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields_final = ('count_patients',
                        'count_patients_male',
                        'count_patients_female',

                        'count_services',
                        'count_services_male',
                        'count_services_female',

                        'total_tariff',
                        'total_tariff_male',
                        'total_tariff_female',

                        'coeff1_07',
                        'coeff1_07_male',
                        'coeff1_07_female',

                        'total_accepted',
                        'total_accepted_male',
                        'total_accepted_female')

        return (('1', 2, fields_final),
                ('2', 17, fields_final),
                ('1&interview', 48, fields_final),
                ('2&interview', 63, fields_final),
                ('1&other', 94, fields_final),
                ('2&other', 109, fields_final))


class ExamAdultSecondStagePage(MedicalServiceTypePage):
    """
    Лист принятых услуг по второму этапу диспансеризации взрослых
    """

    def __init__(self):
        self.data = None
        self.page_number = 1

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_code AS group_field,
                    COUNT(DISTINCT patient_id) AS count_patients,
                    COUNT(DISTINCT service_id) AS count_services,
                    SUM(service_tariff) AS total_tariff
                FROM registry_services
                WHERE service_group IN (25, 26)
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_patients', 'count_services', 'total_tariff')
        return (('019102', 2, fields),
                ('019103', 5, fields),
                ('019104', 8, fields),
                ('019106', 11, fields),
                ('019107', 14, fields),
                ('019105', 17, fields),
                ('019116', 20, fields),
                ('019108', 23, fields),
                ('019109', 26, fields),
                ('019110', 29, fields),
                ('019111', 32, fields),
                ('019112', 35, fields),
                ('019113', 38, fields),
                ('019114', 41, fields),
                ('019115', 44, fields),
                ('019117', 47, fields))


class PreventiveInspectionAdultPage(MedicalServiceTypePage):
    """
    Лист принятых услуг по
    1. Профосмотр взрослых (первичный и итоговый приём)
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    '0' AS group_field,

                    COUNT(DISTINCT CASE WHEN service_code IN ('019215', '019214')
                                          THEN service_id
                                   END) AS count_services_primary,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1 AND service_code IN ('019215', '019214')
                                          THEN service_id
                                   END) AS count_services_primary_male,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2 AND service_code IN ('019215', '019214')
                                          THEN service_id
                                   END) AS count_services_primary_female,

                    COUNT(DISTINCT CASE WHEN service_code IN ('019216', '019217')
                                          THEN service_id
                                   END) AS count_services_final,
                    COUNT(DISTINCT CASE WHEN patient_gender = 1 AND service_code IN ('019216', '019217')
                                          THEN service_id
                                   END) AS count_services_final_male,
                    COUNT(DISTINCT CASE WHEN patient_gender = 2 AND service_code IN ('019216', '019217')
                                          THEN service_id
                                   END) AS count_services_final_female,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_male,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_tariff
                             ELSE 0
                        END) AS total_tariff_female,

                    SUM(CASE WHEN psc.id_pk is NOT NULL
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0 END) AS coeff1_07,
                    SUM(CASE WHEN psc.id_pk is NOT NULL AND patient_gender = 1
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0
                        END) AS coeff1_07_male,
                    SUM(CASE WHEN psc.id_pk is NOT NULL AND patient_gender = 2
                               THEN ROUND(service_tariff*0.07, 2)
                             ELSE 0
                        END) AS coeff1_07_female,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN patient_gender = 1
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_male,
                    SUM(CASE WHEN patient_gender = 2
                               THEN service_accepted
                             ELSE 0
                        END) AS total_accepted_female
                FROM registry_services
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                      AND psc.coefficient_fk = 5
                WHERE service_group = 9
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields = ('count_services_primary',
                  'count_services_primary_male',
                  'count_services_primary_female',

                  'count_services_final',
                  'count_services_final_male',
                  'count_services_final_female',

                  'total_tariff',
                  'total_tariff_male',
                  'total_tariff_female',

                  'coeff1_07',
                  'coeff1_07_male',
                  'coeff1_07_female',

                  'total_accepted',
                  'total_accepted_male',
                  'total_accepted_female')
        return ('0', 2, fields),
