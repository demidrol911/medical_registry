#! -*- coding: utf-8 -*-
from servces_by_divison_general import GeneralServicesPage
from report_printer_clear.utils.page import ReportPage


class AcceptedServicesPage(GeneralServicesPage):

    def __init__(self):
        GeneralServicesPage.__init__(self)

    def get_query(self, parameters):
        query = '''
                -- Рассчёт --
                COUNT(DISTINCT CASE WHEN S.is_adult
                                      THEN S.patient_id
                               END
                      ) AS patient_adult,
                COUNT(DISTINCT CASE WHEN S.is_child
                                      THEN S.patient_id
                               END
                      ) AS patient_child,

                COUNT(DISTINCT CASE WHEN S.is_adult AND S.is_treatment
                                      THEN S.event_id
                               END
                      ) AS treatment_adult,
                COUNT(DISTINCT CASE WHEN S.is_child AND S.is_treatment
                                      THEN S.event_id END
                      ) AS treatment_child,

                COUNT(DISTINCT CASE WHEN S.is_adult
                                      THEN (
                                          CASE WHEN T.term = 7 AND T."group" = 19
                                                    AND S.service_subgroup is NULL
                                                 THEN NULL
                                               ELSE S.service_id
                                          END
                                        )
                               END
                      ) AS service_adult,
                COUNT(DISTINCT CASE WHEN S.is_child
                                      THEN (
                                          CASE WHEN T.term= 7 AND T."group" = 19
                                                    AND S.service_subgroup is NULL
                                                 THEN NULL
                                               ELSE S.service_id
                                          END
                                        )
                               END
                      ) AS service_child,

                SUM(CASE WHEN S.is_adult
                           THEN S.service_quantity
                         ELSE 0
                    END
                    ) AS quantity_adult,
                SUM(CASE WHEN S.is_child
                           THEN S.service_quantity
                         ELSE 0
                    END
                    ) AS quantity_child,

                SUM(CASE WHEN S.is_adult
                           THEN S.service_tariff
                         ELSE 0
                    END
                    ) AS tariff_adult,
                SUM(CASE WHEN S.is_child
                           THEN S.service_tariff
                         ELSE 0
                    END
                    ) AS tariff_child,

                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,

                SUM(CASE WHEN S.is_adult
                           THEN (
                               CASE WHEN T.capitation = 0
                                      THEN 0
                                    ELSE S.service_accepted_payment
                               END
                           )
                         ELSE 0
                    END
                    ) AS accepted_payment_adult,
                SUM(CASE WHEN S.is_child
                           THEN (
                               CASE WHEN T.capitation = 0
                                      THEN 0
                                    ELSE S.service_accepted_payment
                               END
                           )
                         ELSE 0
                    END
                    ) AS accepted_payment_child
                '''

        return GeneralServicesPage.get_general_query().format(
            inner_query=query,
            joins='',
            where='S.payment_type=2' +
                  ((" AND S.department = '%s'" % parameters.department)
                   if parameters.department
                   else '')
        )

    def get_coeff_query(self, parameters):
        query = '''
                -- Рассчёт --
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,

                -- Коэффициент курации
                SUM(ROUND(CASE WHEN  S.is_adult AND psc.coefficient_fk = 7
                                     AND ((
                                        SELECT
                                            COUNT(DISTINCT psc1.id_pk)
                                        FROM provided_service_coefficient psc1
                                            JOIN tariff_coefficient tc1
                                               ON tc1.id_pk = psc1.coefficient_fk
                                        WHERE psc1.service_fk = S.service_id
                                              AND tc1.id_pk in (8, 9, 10, 11, 12)
                                     ) >= 1)
                                 THEN ROUND(0.25*S.service_tariff, 2) * (
                                                SELECT
                                                    tc1.value
                                                FROM provided_service_coefficient psc1
                                                    JOIN tariff_coefficient tc1
                                                       ON tc1.id_pk = psc1.coefficient_fk
                                                WHERE psc1.service_fk = S.service_id
                                                      AND tc1.id_pk in (8, 9, 10, 11, 12)
                                             )
                               ELSE 0
                          END, 2)
                    ) + SUM(ROUND(CASE WHEN S.is_adult AND psc.coefficient_fk = 7
                                         THEN ROUND(0.25*S.service_tariff, 2)
                                       ELSE 0
                                  END, 2)
                    ),

                SUM(ROUND(CASE WHEN  S.is_child AND psc.coefficient_fk = 7
                                     AND ((
                                        SELECT
                                            COUNT(DISTINCT psc1.id_pk)
                                        FROM provided_service_coefficient psc1
                                            JOIN tariff_coefficient tc1
                                               ON tc1.id_pk = psc1.coefficient_fk
                                        WHERE psc1.service_fk = S.service_id
                                              AND tc1.id_pk in (8, 9, 10, 11, 12)
                                     ) >= 1)
                                 THEN ROUND(0.25*S.service_tariff, 2) * (
                                                SELECT
                                                    tc1.value
                                                FROM provided_service_coefficient psc1
                                                    JOIN tariff_coefficient tc1
                                                       ON tc1.id_pk = psc1.coefficient_fk
                                                WHERE psc1.service_fk = S.service_id
                                                      AND tc1.id_pk in (8, 9, 10, 11, 12)
                                            ) ELSE 0
                                  END, 2)
                    ) + SUM(ROUND(CASE WHEN  S.is_child AND psc.coefficient_fk = 7
                                         THEN  round(0.25*S.service_tariff, 2)
                                       ELSE 0
                                  END, 2)
                    ),

                -- Коэффициент курации закончился

                -- Неотложка у зубника
                SUM(CASE WHEN S.is_adult AND tc.id_pk = 4
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 4
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                -- Мобильные бригады
                SUM(CASE WHEN S.is_adult AND tc.id_pk = 5
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 5
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                0,  0,

                SUM(CASE WHEN S.is_adult
                           THEN
                              (CASE WHEN S.organization = '280005' AND tc.id_pk = 19
                                     THEN (tc.value-1)*S.service_tariff
                                   WHEN S.organization = '280064' AND tc.id_pk = 16
                                     THEN (tc.value-1)*S.service_tariff
                                   ELSE 0
                              END)
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child
                           THEN
                              (CASE WHEN S.organization = '280005' AND tc.id_pk = 19
                                     THEN (tc.value-1)*S.service_tariff
                                   WHEN S.organization = '280064' AND tc.id_pk = 16
                                     THEN (tc.value-1)*S.service_tariff
                                   ELSE 0
                              END)
                         ELSE 0
                    END),

                SUM(CASE WHEN S.is_adult AND tc.id_pk = 17
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 17
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                SUM(CASE WHEN S.is_adult AND tc.id_pk = 18
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 18
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                -- Клинико-профильные группы
                sum(CASE WHEN S.is_adult AND tc.id_pk in (8, 9, 10, 11, 12)
                           THEN round(tc.value*S.service_tariff, 2)
                         ELSE 0
                    END),
                sum(CASE WHEN S.is_child AND tc.id_pk in (8, 9, 10, 11, 12)
                           THEN round(tc.value*S.service_tariff, 2)
                         ELSE 0
                    END),

                ---
                0,  0
                '''

        return GeneralServicesPage.get_general_query().format(
            inner_query=query,
            joins='''
                  JOIN provided_service_coefficient psc
                     ON psc.service_fk = T.service_id
                  JOIN tariff_coefficient tc
                     ON tc.id_pk = psc.coefficient_fk
                  ''',
            where='S.payment_type = 2' +
                  ((" AND S.department = '%s'" % parameters.department)
                   if parameters.department
                   else '')
        )


class InvoicedServicesPage(GeneralServicesPage):

    def __init__(self):
        GeneralServicesPage.__init__(self)

    def get_query(self, parameters):
        query = '''
                -- Рассчёт --
                COUNT(DISTINCT CASE WHEN S.is_adult
                                      THEN S.patient_id
                               END
                      ) AS patient_adult,
                COUNT(DISTINCT CASE WHEN S.is_child
                                      THEN S.patient_id
                               END
                      ) AS patient_child,

                COUNT(DISTINCT CASE WHEN S.is_adult AND S.is_treatment
                                      THEN S.event_id
                               END
                      ) AS treatment_adult,
                COUNT(DISTINCT CASE WHEN S.is_child AND S.is_treatment
                                      THEN S.event_id END
                      ) AS treatment_child,

                COUNT(DISTINCT CASE WHEN S.is_adult
                                      THEN (
                                          CASE WHEN T.term = 7 AND T."group" = 19
                                                    AND S.service_subgroup is NULL
                                                 THEN NULL
                                               ELSE S.service_id
                                          END
                                        )
                               END
                      ) AS service_adult,
                COUNT(DISTINCT CASE WHEN S.is_child
                                      THEN (
                                          CASE WHEN T.term= 7 AND T."group" = 19
                                                    AND S.service_subgroup is NULL
                                                 THEN NULL
                                               ELSE S.service_id
                                          END
                                        )
                               END
                      ) AS service_child,

                SUM(CASE WHEN S.is_adult
                           THEN S.service_quantity
                         ELSE 0
                    END
                    ) AS quantity_adult,
                SUM(CASE WHEN S.is_child
                           THEN S.service_quantity
                         ELSE 0
                    END
                    ) AS quantity_child,

                SUM(CASE WHEN S.is_adult
                           THEN S.service_tariff
                         ELSE 0
                    END
                    ) AS tariff_adult,
                SUM(CASE WHEN S.is_child
                           THEN S.service_tariff
                         ELSE 0
                    END
                    ) AS tariff_child,

                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,

                SUM(CASE WHEN S.is_adult
                           THEN (
                                   CASE WHEN T.capitation = 0
                                          THEN 0
                                        ELSE (
                                             CASE WHEN S.payment_type = 2
                                                    THEN S.service_accepted_payment
                                                  WHEN S.payment_type = 3
                                                    THEN S.service_provided_tariff
                                                  WHEN S.payment_type = 4
                                                    THEN S.service_accepted_payment + S.service_provided_tariff
                                             END
                                        )
                                   END
                               )
                         ELSE 0
                    END) AS accepted_payment_adult,
                SUM(CASE WHEN S.is_child
                           THEN (
                                   CASE WHEN T.capitation = 0
                                          THEN 0
                                        ELSE (
                                             CASE WHEN S.payment_type = 2
                                                    THEN S.service_accepted_payment
                                                  WHEN S.payment_type = 3
                                                    THEN S.service_provided_tariff
                                                  WHEN S.payment_type = 4
                                                    THEN S.service_accepted_payment + S.service_provided_tariff
                                             END
                                        )
                                   END
                               )
                         ELSE 0
                    END) AS accepted_payment_child
                '''

        return GeneralServicesPage.get_general_query().format(
            inner_query=query,
            joins='',
            where='True'
        )

    def get_coeff_query(self, parameters):
        query = '''
                -- Рассчёт --
                0,  0,
                0,  0,
                0,  0,
                0,  0,
                0,  0,

                -- Коэффициент курации
                SUM(ROUND(CASE WHEN  S.is_adult AND psc.coefficient_fk = 7
                                     AND ((
                                        SELECT
                                            COUNT(DISTINCT psc1.id_pk)
                                        FROM provided_service_coefficient psc1
                                            JOIN tariff_coefficient tc1
                                               ON tc1.id_pk = psc1.coefficient_fk
                                        WHERE psc1.service_fk = S.service_id
                                              AND tc1.id_pk in (8, 9, 10, 11, 12)
                                     ) >= 1)
                                 THEN ROUND(0.25*S.service_tariff, 2) * (
                                                SELECT
                                                    tc1.value
                                                FROM provided_service_coefficient psc1
                                                    JOIN tariff_coefficient tc1
                                                       ON tc1.id_pk = psc1.coefficient_fk
                                                WHERE psc1.service_fk = S.service_id
                                                      AND tc1.id_pk in (8, 9, 10, 11, 12)
                                             )
                               ELSE 0
                          END, 2)
                    ) + SUM(ROUND(CASE WHEN S.is_adult AND psc.coefficient_fk = 7
                                         THEN ROUND(0.25*S.service_tariff, 2)
                                       ELSE 0
                                  END, 2)
                    ),

                SUM(ROUND(CASE WHEN  S.is_child AND psc.coefficient_fk = 7
                                     AND ((
                                        SELECT
                                            COUNT(DISTINCT psc1.id_pk)
                                        FROM provided_service_coefficient psc1
                                            JOIN tariff_coefficient tc1
                                               ON tc1.id_pk = psc1.coefficient_fk
                                        WHERE psc1.service_fk = S.service_id
                                              AND tc1.id_pk in (8, 9, 10, 11, 12)
                                     ) >= 1)
                                 THEN ROUND(0.25*S.service_tariff, 2) * (
                                                SELECT
                                                    tc1.value
                                                FROM provided_service_coefficient psc1
                                                    JOIN tariff_coefficient tc1
                                                       ON tc1.id_pk = psc1.coefficient_fk
                                                WHERE psc1.service_fk = S.service_id
                                                      AND tc1.id_pk in (8, 9, 10, 11, 12)
                                            ) ELSE 0
                                  END, 2)
                    ) + SUM(ROUND(CASE WHEN  S.is_child AND psc.coefficient_fk = 7
                                         THEN  round(0.25*S.service_tariff, 2)
                                       ELSE 0
                                  END, 2)
                    ),

                -- Коэффициент курации закончился

                -- Неотложка у зубника
                SUM(CASE WHEN S.is_adult AND tc.id_pk = 4
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 4
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                -- Мобильные бригады
                SUM(CASE WHEN S.is_adult AND tc.id_pk = 5
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 5
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                0,  0,

                SUM(CASE WHEN S.is_adult
                           THEN
                              (CASE WHEN S.organization = '280005' AND tc.id_pk = 19
                                     THEN (tc.value-1)*S.service_tariff
                                   WHEN S.organization = '280064' AND tc.id_pk = 16
                                     THEN (tc.value-1)*S.service_tariff
                                   ELSE 0
                              END)
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child
                           THEN
                              (CASE WHEN S.organization = '280005' AND tc.id_pk = 19
                                     THEN (tc.value-1)*S.service_tariff
                                   WHEN S.organization = '280064' AND tc.id_pk = 16
                                     THEN (tc.value-1)*S.service_tariff
                                   ELSE 0
                              END)
                         ELSE 0
                    END),

                SUM(CASE WHEN S.is_adult AND tc.id_pk = 17
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 17
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                SUM(CASE WHEN S.is_adult AND tc.id_pk = 18
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),
                SUM(CASE WHEN S.is_child AND tc.id_pk = 18
                           THEN (tc.value-1)*S.service_tariff
                         ELSE 0
                    END),

                -- Клинико-профильные группы
                sum(CASE WHEN S.is_adult AND tc.id_pk in (8, 9, 10, 11, 12)
                           THEN round(tc.value*S.service_tariff, 2)
                         ELSE 0
                    END),
                sum(CASE WHEN S.is_child AND tc.id_pk in (8, 9, 10, 11, 12)
                           THEN round(tc.value*S.service_tariff, 2)
                         ELSE 0
                    END),

                ---
                0,  0
                '''

        return GeneralServicesPage.get_general_query().format(
            inner_query=query,
            joins='''
                  JOIN provided_service_coefficient psc
                     ON psc.service_fk = T.service_id
                  JOIN tariff_coefficient tc
                     ON tc.id_pk = psc.coefficient_fk
                  ''',
            where='True'
        )


class NotAcceptedServicesPage(ReportPage):
    def __init__(self):
        self.data = ''
        self.page_number = 0

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        pass