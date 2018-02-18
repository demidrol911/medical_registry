#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class DayHospitalHepatitisCVirusPage(MedicalServiceTypePage):
    """
    Лист принятых услуг по гепатиту С в дневном стационаре
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN service_code IN ('098716', '198716') THEN '0'
                         WHEN service_code IN ('098717', '198717') THEN '1'
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
                    LEFT JOIN provided_service_coefficient psc
                      ON psc.service_fk = service_id
                    LEFT JOIN tariff_coefficient tc
                      ON tc.id_pk = psc.coefficient_fk
                WHERE service_group = 30
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
        return (('0', 4, fields),
                ('1', 16, fields))