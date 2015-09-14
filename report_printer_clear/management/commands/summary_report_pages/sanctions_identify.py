from main.funcs import howlong
from main.models import MedicalOrganization
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage


class SanctionsIdentifyPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 3

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,

                    COUNT(DISTINCT T.patient_id) AS count_patients,

                    COUNT(DISTINCT CASE WHEN T.is_hospital
                                          THEN T.service_id
                                   END
                         ) AS hospital_services,
                    SUM(CASE WHEN T.is_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS hospital_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_day_hospital
                                          THEN T.service_id
                                   END
                         ) AS day_hospital_services,
                    SUM(CASE WHEN T.is_day_hospital
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS day_hospital_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_policlinic
                                          THEN T.service_id
                                   END
                          ) AS policlinic_services,
                    SUM(CASE WHEN T.is_policlinic
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS policlinic_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_ambulance
                                          THEN T.service_id
                                   END
                          ) AS ambulance_services,
                    SUM(CASE WHEN T.is_ambulance
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS ambulance_provided_tariff,


                    COUNT(DISTINCT CASE WHEN T.is_stomatology
                                          THEN T.service_id
                                        END
                          ) AS stomatology_services,
                    SUM(CASE WHEN T.is_stomatology
                               THEN T.provided_tariff
                             ELSE 0
                        END
                        ) AS stomatology_provided_tariff,


                    COUNT(DISTINCT T.service_id) AS total_services,
                    SUM(T.provided_tariff) AS total_provided_tariff

                FROM (
                   SELECT
                       mo.id_pk AS organization_id,
                       ps.id_pk AS service_id,
                       pe.id_pk AS event_id,
                       ps.department_fk AS service_department,
                       pt.id_pk AS patient_id,
                       ps.tariff AS tariff,

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
                       END AS provided_tariff

                       FROM medical_register mr
                           JOIN medical_register_record mrr
                              ON mr.id_pk = mrr.register_fk
                           JOIN provided_event pe
                              ON mrr.id_pk = pe.record_fk
                           JOIN provided_service ps
                              ON ps.event_fk = pe.id_pk
                           JOIN medical_organization mo
                              ON ps.organization_fk = mo.id_pk
                           JOIN medical_organization dep
                              ON dep.id_pk = ps.department_fk
                           JOIN medical_service ms
                              ON ms.id_pk = ps.code_fk
                           JOIN patient pt
                              ON pt.id_pk = mrr.patient_fk
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
                       WHERE mr.is_active
                          AND mr.period = %(period)s
                          AND mr.year = %(year)s
                          AND mr.organization_code = %(organization)s
                          AND dep.old_code = ANY(%(department)s)
                          AND pss.is_active
                          AND pss.type_fk = 1
                          AND me.old_code = 'PK'
                          AND ps.payment_type_fk = 3
                          AND (ms.group_fk != 27
                               OR ms.group_fk is null
                              )
                         ) AS T
                   JOIN medical_organization mo
                      ON mo.id_pk = T.organization_id
                   GROUP BY mo.id_pk
                '''

        self.data = MedicalOrganization.objects.raw(
            query,
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code,
                department=parameters.departments
            ))
        if list(self.data):
            self.data = self.data[0]
        else:
            self.data = None

    def print_page(self, sheet, parameters):
        sheet.set_style({})
        sheet.write_cell(2, 0, parameters.report_name)
        sheet.write_cell(2, 5, parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        sheet.set_position(6, 0)
        if self.data:
            item = self.data
            sheet.write(item.count_patients, 'c')
            sheet.write(item.hospital_services, 'c')
            sheet.write(item.hospital_provided_tariff, 'c')

            sheet.write(item.day_hospital_services, 'c')
            sheet.write(item.day_hospital_provided_tariff, 'c')

            sheet.write(item.policlinic_services, 'c')
            sheet.write(item.policlinic_provided_tariff, 'c')

            sheet.write(item.ambulance_services, 'c')
            sheet.write(item.ambulance_provided_tariff, 'c')

            sheet.write(item.stomatology_services, 'c')
            sheet.write(item.stomatology_provided_tariff, 'c')

            sheet.write(item.total_services, 'c')
            sheet.write(item.total_provided_tariff, 'r')
