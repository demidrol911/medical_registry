from report_printer_clear.management.commands.medical_services_types_pages.general import MedicalServiceTypePage


class DayHospitalHome(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_tariff_profile IN (42, 40, 41) THEN '0'
                         ELSE '1'
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

                    SUM(service_tariff) AS total_tariff,
                    SUM(CASE WHEN is_adult
                               THEN service_tariff
                        END) AS total_tariff_adult,
                    SUM(CASE WHEN NOT is_adult
                               THEN service_tariff
                        END) AS total_tariff_child,

                    SUM(CASE WHEN psc.coefficient_fk = 18
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_4,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk = 18
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_4_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk = 18
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_4_child,

                    SUM(CASE WHEN psc.coefficient_fk = 16
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_2,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk = 16
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_2_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk = 16
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_2_child,

                    SUM(CASE WHEN psc.coefficient_fk = 17
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_1,
                    SUM(CASE WHEN is_adult AND psc.coefficient_fk = 17
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_1_adult,
                    SUM(CASE WHEN NOT is_adult AND psc.coefficient_fk = 17
                               THEN ROUND(service_tariff * (tc.value - 1), 2)
                             ELSE 0
                        END) AS coeff1_1_child,

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
                    LEFT JOIN tariff_coefficient tc
                      ON tc.id_pk = psc.coefficient_fk
                    JOIN medical_division md
                      ON md.id_pk = event_division_id
                WHERE service_term = 2 AND service_group IS NULL
                      AND md.term_fk = 12
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

                  'total_tariff',
                  'total_tariff_adult',
                  'total_tariff_child',

                  'coeff1_4',
                  'coeff1_4_adult',
                  'coeff1_4_child',

                  'coeff1_2',
                  'coeff1_2_adult',
                  'coeff1_2_child',

                  'coeff1_1',
                  'coeff1_1_adult',
                  'coeff1_1_child',

                  'total_accepted',
                  'total_accepted_adult',
                  'total_accepted_child')
        return (('0', 2, fields),
                ('1', 26, fields))