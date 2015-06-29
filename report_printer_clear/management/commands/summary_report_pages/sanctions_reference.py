#! -*- coding: utf-8 -*-
from main.funcs import howlong
from main.models import MedicalOrganization
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage
from tfoms.func import FAILURE_CAUSES


class SanctionsReferencePage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 2

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,
                    T.failure_cause_id,
                    T.failure_cause_number,

                    COUNT(DISTINCT CASE WHEN T.is_hospital
                                          THEN T.service_id
                                   END
                         ) AS hospital_services,
                    0 AS hospital_treatments,
                    SUM(CASE WHEN T.is_hospital
                               THEN T.tariff
                             ELSE 0
                        END
                        ) AS hospital_tariff,
                    SUM(CASE WHEN T.is_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS hospital_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_day_hospital
                                          THEN T.service_id
                                   END
                         ) AS day_hospital_services,
                    0 AS day_hospital_treatments,
                    SUM(CASE WHEN T.is_day_hospital
                               THEN T.tariff
                             ELSE 0
                        END
                        ) AS day_hospital_tariff,
                    SUM(CASE WHEN T.is_day_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS day_hospital_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_policlinic
                                          THEN T.service_id
                                   END
                          ) AS policlinic_services,
                    COUNT(DISTINCT CASE WHEN T.is_policlinic
                                             AND T.is_treatment
                                          THEN T.event_id
                                   END
                          ) AS policlinic_treatments,
                    SUM(CASE WHEN T.is_policlinic
                               THEN T.tariff
                             ELSE 0
                        END
                        ) AS policlinic_tariff,
                    SUM(CASE WHEN T.is_policlinic
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS policlinic_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_ambulance
                                          THEN T.service_id
                                   END
                          ) AS ambulance_services,
                    0 AS ambulance_treatments,
                    SUM(CASE WHEN T.is_ambulance
                               THEN T.tariff
                             ELSE 0
                        END
                        ) AS ambulance_tariff,
                    SUM(CASE WHEN T.is_ambulance
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS ambulance_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_stomatology
                                          THEN T.service_id
                                        END
                          ) AS stomatology_services,
                    COUNT(DISTINCT CASE WHEN T.is_stomatology
                                             AND T.is_treatment
                                          THEN T.event_id
                                   END
                          ) AS stomatology_treatments,
                    SUM(CASE WHEN T.is_stomatology
                               THEN T.uet
                             ELSE 0
                        END
                        ) AS stomatology_uet,
                    SUM(CASE WHEN T.is_stomatology
                               THEN T.tariff
                             ELSE 0
                        END
                        ) AS stomatology_tariff,
                    SUM(CASE WHEN T.is_stomatology
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS stomatology_provided_tariff,


                    COUNT(DISTINCT T.service_id) AS total_services,
                    COUNT(DISTINCT CASE WHEN T.is_treatment
                                          THEN T.event_id
                                   END
                          ) AS total_treatments,
                    SUM(T.tariff) AS total_tariff,
                    SUM(T.provided_tariff) AS total_provided_tariff

                FROM (
                   SELECT
                       mo.id_pk AS organization_id,
                       ps.id_pk AS service_id,
                       pe.id_pk AS event_id,
                       ps.department_fk AS service_department,
                       ps.tariff AS tariff,
                       pfc.number AS failure_cause_number,
                       me.failure_cause_fk AS failure_cause_id,

                       pe.term_fk = 1 AS is_hospital,
                       pe.term_fk = 2 AS is_day_hospital,

                       (pe.term_fk = 3
                        OR pe.term_fk is null
                        ) AND
                       (ms.group_fk != 19
                        OR ms.group_fk is null) AS is_policlinic,

                       pe.term_fk = 4 AS is_ambulance,
                       ms.group_fk = 19 AS is_stomatology,

                       CASE WHEN ps.payment_kind_fk = 2
                              THEN 0 ELSE provided_tariff
                       END AS provided_tariff,
                       (CASE WHEN ps.quantity = 0 or ps.quantity is null
                               THEN 1
                             ELSE ps.quantity
                        END) *
                        COALESCE(ms.uet, 0) AS uet,

                       (ms.group_fk = 19 AND ms.subgroup_fk = 12)
                        OR (pe.term_fk = 3 AND ms.reason_fk = 1 AND
                           (ms.group_fk is NULL OR ms.group_fk = 24)
                            AND (
                                  SELECT
                                      COUNT(DISTINCT ps1.id_pk)
                                  FROM provided_service ps1
                                  JOIN medical_service ms1
                                     ON ms1.id_pk = ps1.code_fk
                                  WHERE ps1.event_fk  = ps.event_fk
                                        AND (ms1.group_fk is NULL OR ms1.group_fk = 24)
                                        AND ms1.reason_fk = 1
                                )>1
                        ) AS is_treatment


                       FROM medical_register mr
                           JOIN medical_register_record mrr
                              ON mr.id_pk = mrr.register_fk
                           JOIN provided_event pe
                              ON mrr.id_pk = pe.record_fk
                           JOIN provided_service ps
                              ON ps.event_fk = pe.id_pk
                           JOIN medical_organization mo
                              ON ps.organization_fk = mo.id_pk
                           JOIN medical_service ms
                              ON ms.id_pk = ps.code_fk
                           JOIN provided_service_sanction pss
                              ON pss.service_fk = ps.id_pk
                                 AND pss.is_active
                                 AND pss.type_fk = 1
                                 AND pss.error_fk = (
                                     SELECT inner_me.id_pk
                                     FROM medical_error inner_me
                                         JOIN provided_service_sanction inner_pss
                                            ON inner_me.id_pk = inner_pss.error_fk
                                               AND inner_pss.service_fk = ps.id_pk

                                     WHERE inner_pss.is_active
                                         AND inner_pss.type_fk = 1
                                     ORDER BY inner_me.weight DESC
                                     LIMIT 1
                                )
                           JOIN medical_error me
                              ON me.id_pk = pss.error_fk
                           JOIN payment_failure_cause pfc
                              ON pfc.id_pk = me.failure_cause_fk
                       WHERE mr.is_active
                          AND mr.period = %(period)s
                          AND mr.year = %(year)s
                          AND mr.organization_code = %(organization)s
                          AND pss.is_active
                          AND pss.type_fk = 1
                          AND ps.payment_type_fk = 3
                          AND (ms.group_fk != 27
                               OR ms.group_fk is null
                              )
                         ) AS T
                   JOIN medical_organization mo
                      ON mo.id_pk = T.organization_id
                   JOIN medical_organization dep
                      ON dep.id_pk = T.service_department

                '''

        self.data = MedicalOrganization.objects.raw(
            query + ((" WHERE dep.old_code = '%s'" % parameters.department)
                     if parameters.department
                     else '')
            + '''
              GROUP BY mo.id_pk, T.failure_cause_id, T.failure_cause_number
              ORDER BY T.failure_cause_number ASC
              ''',
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code
            ))

    def print_page(self, sheet, parameters):
        sheet.set_style({})
        sheet.write_cell(2, 0, parameters.report_name)
        sheet.write_cell(2, 5, parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        sheet.set_position(6, 0)
        for item in self.data:
            sheet.write(FAILURE_CAUSES[item.failure_cause_id]['number'], 'c')
            sheet.write(FAILURE_CAUSES[item.failure_cause_id]['name'], 'c')
            sheet.write(item.hospital_services, 'c')
            sheet.write(item.hospital_treatments, 'c')
            sheet.write(item.hospital_tariff, 'c')
            sheet.write(item.hospital_provided_tariff, 'c')

            sheet.write(item.day_hospital_services, 'c')
            sheet.write(item.day_hospital_treatments, 'c')
            sheet.write(item.day_hospital_tariff, 'c')
            sheet.write(item.day_hospital_provided_tariff, 'c')

            sheet.write(item.policlinic_services, 'c')
            sheet.write(item.policlinic_treatments, 'c')
            sheet.write(item.policlinic_tariff, 'c')
            sheet.write(item.policlinic_provided_tariff, 'c')

            sheet.write(item.ambulance_services, 'c')
            sheet.write(item.ambulance_treatments, 'c')
            sheet.write(item.ambulance_tariff, 'c')
            sheet.write(item.ambulance_provided_tariff, 'c')

            sheet.write(item.stomatology_services, 'c')
            sheet.write(item.stomatology_treatments, 'c')
            sheet.write(item.stomatology_uet, 'c')
            sheet.write(item.stomatology_tariff, 'c')
            sheet.write(item.stomatology_provided_tariff, 'c')

            sheet.write(item.total_services, 'c')
            sheet.write(item.total_treatments, 'c')
            sheet.write(item.total_tariff, 'c')
            sheet.write(item.total_provided_tariff, 'r')
