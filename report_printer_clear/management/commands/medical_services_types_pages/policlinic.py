from general import MedicalServiceTypePage


class PoliclinicCapitationVisitOtherPurposesPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_division AS group_field,
                    COUNT(DISTINCT (patient_id, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN patient_id
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN patient_id
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
                      AND service_reason = 8
                      AND is_capitation
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
        return ((509, 5, fields),
                (500, 14, fields),
                (501, 23, fields))


class PoliclinicCapitationTreatmentDiseasePage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    service_division AS group_field,
                    COUNT(DISTINCT (patient_id, is_adult)) AS count_patients,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN patient_id
                                   END) AS count_patients_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN patient_id
                                   END) AS count_patients_child,

                    COUNT(DISTINCT event_id) AS count_treatments,
                    COUNT(DISTINCT CASE WHEN is_adult
                                          THEN event_id
                                   END) AS count_treatments_adult,
                    COUNT(DISTINCT CASE WHEN NOT is_adult
                                          THEN event_id
                                   END) AS count_treatments_child,

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
                      AND is_capitation
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

                  'total_tariff',
                  'total_tariff_adult',
                  'total_tariff_child')

        return ((399, 2, fields),
                (401, 14, fields),
                (403, 26, fields))



