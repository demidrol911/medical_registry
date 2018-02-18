#! -*- coding: utf-8 -*-
from general import MedicalServiceTypeInPartPage


class DayHospitalPrimaryInPartPage(MedicalServiceTypeInPartPage):
    """
    Лист принятых услуг по
    1. Первичная состоит из на дому (все профили) + при поликлинике (только терапевт и педиатр)
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
                JOIN medical_division md
                      ON md.id_pk = event_division_id
                WHERE service_term = 2 AND (service_group IS NULL OR service_group <> 28)
                AND (md.term_fk = 12 OR md.term_fk = 11 and service_tariff_profile IN (42, 40))
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
            return (('2', 2, fields),
                    ('3', 14, fields),
                    ('4', 26, fields),
                    ('5', 38, fields),
                    ('6', 50, fields),
                    ('12', 62, fields),
                    ('14', 74, fields),
                    ('15', 86, fields),
                    ('16', 98, fields),
                    ('18', 110, fields))
        elif self.part_number == 2:
            return (('20', 2, fields),
                    ('21', 14, fields),
                    ('23', 26, fields),
                    ('24', 38, fields),
                    ('25', 50, fields),
                    ('28', 62, fields),
                    ('29', 74, fields),
                    ('32', 86, fields),
                    ('33', 98, fields),
                    ('36', 110, fields))
        elif self.part_number == 3:
            return (('13', 2, fields),
                    ('19', 14, fields),
                    ('30', 26, fields),
                    ('31', 38, fields),
                    ('35', 50, fields),
                    ('34', 62, fields),
                    ('17', 74, fields),
                    ('22', 86, fields),
                    ('27', 98, fields))


class DayHospitalSpecialInPartPage(MedicalServiceTypeInPartPage):
    """
    Лист принятых услуг по
    1. Специализированная состоит из при поликлинике (все профили кроме терапевта и педиатра)
    + при стационаре (все профили)
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
                JOIN medical_division md
                      ON md.id_pk = event_division_id
                WHERE service_term = 2 AND (service_group IS NULL OR service_group <> 28)
                     AND (md.term_fk = 10 OR md.term_fk = 11 and service_tariff_profile NOT IN (42, 40))
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
            return (('2', 2, fields),
                    ('3', 14, fields),
                    ('4', 26, fields),
                    ('5', 38, fields),
                    ('6', 50, fields),
                    ('12', 62, fields),
                    ('14', 74, fields),
                    ('15', 86, fields),
                    ('16', 98, fields),
                    ('18', 110, fields))

        elif self.part_number == 2:
            return (('20', 2, fields),
                    ('21', 14, fields),
                    ('23', 26, fields),
                    ('24', 38, fields),
                    ('25', 50, fields),
                    ('28', 62, fields),
                    ('29', 74, fields),
                    ('32', 86, fields),
                    ('33', 98, fields),
                    ('36', 110, fields))
        elif self.part_number == 3:
            return (('13', 2, fields),
                    ('19', 14, fields),
                    ('30', 26, fields),
                    ('31', 38, fields),
                    ('35', 50, fields),
                    ('34', 62, fields),
                    ('17', 74, fields),
                    ('22', 86, fields),
                    ('27', 98, fields))