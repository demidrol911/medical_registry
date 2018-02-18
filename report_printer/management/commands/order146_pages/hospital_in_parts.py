#! -*- coding: utf-8 -*-
from general import MedicalServiceTypeInPartPage


class HospitalInPartPage(MedicalServiceTypeInPartPage):
    """
    Лист принятых услуг по
    1. Круглосуточный стационар
    """

    def get_query(self):
        query = MedicalServiceTypeInPartPage.get_general_query() + '''
                SELECT
                    mo_code AS mo_code,
                    CASE WHEN kpg.code = 7 THEN 13
                         WHEN kpg.code = 8 THEN 19
                         WHEN kpg.code = 9 THEN 30
                         WHEN kpg.code = 10 THEN 31
                         WHEN kpg.code = 11 THEN 35
                         WHEN kpg.code = 26 THEN 34
                         ELSE kpg.code END :: VARCHAR AS group_field,

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
                JOIN ksg ON ksg.code::VARCHAR = ksg_smo AND ksg.start_date = '2017-01-01'
                     AND ksg.term_fk = service_term
                JOIN kpg ON kpg.id_pk = ksg.kpg_fk
                WHERE service_term = 1 AND (service_group IS NULL OR service_group NOT IN (20, 45, 3))
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

        if self.part_number == 1:
            return (('1', 2, fields),
                    ('2', 14, fields),
                    ('3', 26, fields),
                    ('4', 38, fields),
                    ('5', 50, fields),
                    ('6', 62, fields),
                    ('12', 74, fields),
                    ('14', 86, fields),
                    ('15', 98, fields),
                    ('16', 110, fields))
        elif self.part_number == 2:
            return (('18', 2, fields),
                    ('20', 14, fields),
                    ('21', 26, fields),
                    ('23', 38, fields),
                    ('24', 50, fields),
                    ('25', 62, fields),
                    ('28', 74, fields),
                    ('29', 86, fields),
                    ('32', 98, fields),
                    ('33', 110, fields))
        elif self.part_number == 3:
            return (('13', 2, fields),
                    ('19', 14, fields),
                    ('30', 26, fields),
                    ('31', 38, fields),
                    ('35', 50, fields),
                    ('34', 62, fields),
                    ('17', 74, fields),
                    ('22', 86, fields),
                    ('27', 98, fields),
                    ('36', 110, fields))