from general import MedicalServiceTypePage


class StomatologyPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    (SELECT
                         DISTINCT ms1.subgroup_fk
                     FROM provided_service ps1
                        JOIN medical_service ms1
                            ON ms1.id_pk = ps1.code_fk
                     WHERE ps1.event_fk = event_id
                           AND ps1.start_date = service_start_date
                           AND ps1.end_date = service_end_date
                           AND ms1.subgroup_fk is NOT NULL) AS group_field,

                    COUNT(DISTINCT (patient_id, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN patient_id
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN patient_id
                                   END) AS count_patients_child,

                    COUNT(DISTINCT CASE WHEN service_subgroup = 12
                                          THEN event_id END) AS count_treatment,
                    COUNT(DISTINCT CASE WHEN is_adult AND service_subgroup = 12
                                          THEN event_id
                                   END) AS count_treatment_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult AND service_subgroup = 12
                                          THEN event_id
                                   END) AS count_treatment_child,

                    COUNT(DISTINCT CASE WHEN service_subgroup is NOT NULL
                                                   THEN service_id END) AS count_services,
                    COUNT(DISTINCT CASE WHEN is_adult
                                             AND service_subgroup is NOT NULL
                                          THEN service_id
                                   END) AS count_services_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                             AND service_subgroup is NOT NULL
                                          THEN service_id
                                   END) AS count_services_child,

                    SUM(service_quantity) AS total_quantity,
                    SUM(CASE WHEN is_adult
                               THEN service_quantity
                        END) AS total_quantity_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_quantity
                        END) AS total_quantity_child,

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                        END) AS total_tariff_child,

                    SUM(service_accepted) AS total_accepted,
                    SUM(CASE WHEN is_adult
                               THEN service_accepted
                        END) AS total_accepted_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_accepted
                        END) AS total_accepted_child

                FROM registry_services
                WHERE service_group = 19
                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        fields_disease = ('count_patients', 'count_patients_adult', 'count_patients_child',
                          'count_treatment', 'count_treatment_adult', 'count_treatment_child',
                          'count_services', 'count_services_adult', 'count_services_child',
                          'total_quantity', 'total_quantity_adult', 'total_quantity_child',
                          'total_tariff', 'total_tariff_adult', 'total_tariff_child')
        fields_preventive = ('count_patients', 'count_patients_adult', 'count_patients_child',
                             'count_services', 'count_services_adult', 'count_services_child',
                             'total_quantity', 'total_quantity_adult', 'total_quantity_child',
                             'total_tariff', 'total_tariff_adult', 'total_tariff_child')
        fields_ambulance = ('count_patients', 'count_patients_adult', 'count_patients_child',
                            'count_services', 'count_services_adult', 'count_services_child',
                            'total_quantity', 'total_quantity_adult', 'total_quantity_child',
                            'total_tariff', 'total_tariff_adult', 'total_tariff_child')
        return ((12, 6, fields_disease),
                (13, 21, fields_preventive),
                (14, 33, fields_preventive),
                (17, 45, fields_ambulance))
