from main.models import MedicalOrganization
from report_printer_clear.utils.page import ReportPage


class RegistryCheckSumsPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,
                    COUNT(DISTINCT pt.id_pk) AS patients_count,
                    COUNT(DISTINCT ps.id_pk) AS services_count,
                    SUM(ps.tariff) AS invoiced_sum,
                    SUM(ms.uet) AS stomatology_uet,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 1
                                THEN ps.id_pk
                                END
                         ) AS hospital_count,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 2
                                AND (ms.group_fk != 28
                                    OR ms.group_fk is null
                                    )
                               THEN ps.id_pk
                               END
                        ) AS day_hospital_count,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 3
                                AND (ms.group_fk != 19
                                    OR ms.group_fk is null
                                    )
                               THEN ps.id_pk
                               END
                        ) AS policlinic_count,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 4
                               THEN ps.id_pk
                               END
                        ) AS ambulance_count,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 3
                                AND (ms.group_fk != 19
                                    OR ms.group_fk is null
                                    )
                                AND ms.reason_fk = 1
                               THEN ps.id_pk
                               END
                        ) AS policlinic_disease_count,

                    COUNT(DISTINCT CASE WHEN pe.term_fk = 3
                                AND ms.reason_fk = 5
                               THEN ps.id_pk
                               END
                        ) AS policlinic_emergency_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk = 7
                               THEN ps.id_pk
                               END
                        ) AS exam_first_phase_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk in (25, 26)
                               THEN ps.id_pk
                               END
                        ) AS exam_second_phase_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk = 9
                               THEN ps.id_pk
                               END
                        ) AS priventive_exam_adults_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk = 11
                               THEN ps.id_pk
                               END
                        ) AS priventive_exam_childrens_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk in (12, 13)
                               THEN ps.id_pk
                               END
                        ) AS exam_orphans_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk in (15, 16)
                               THEN ps.id_pk
                               END
                        ) AS periodic_exam_childrens_count,

                    COUNT(DISTINCT CASE WHEN ms.group_fk = 19
                               THEN ps.id_pk
                               END
                        ) AS stomatology_count

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
                    JOIN patient pt
                       ON pt.id_pk = mrr.patient_fk
                WHERE mr.is_active
                   AND mr.period = %(period)s
                   AND mr.year = %(year)s
                   AND mr.organization_code = %(organization)s
                   AND (ms.group_fk != 27
                        OR ms.group_fk is null
                       )
                  GROUP BY mo.id_pk
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))[0]

    def print_page(self, sheet, parameters):
        sheet.write_cell(0, 0, parameters.report_name)
        sheet.write_cell(0, 1, parameters.date_string)
        sheet.write_cell(2, 1, self.data.patients_count)
        sheet.write_cell(3, 1, self.data.services_count)
        sheet.write_cell(5, 1, self.data.hospital_count)
        sheet.write_cell(18, 1, self.data.day_hospital_count)
        sheet.write_cell(7, 1, self.data.policlinic_count)
        sheet.write_cell(8, 1, self.data.policlinic_disease_count)
        sheet.write_cell(16, 1, self.data.policlinic_emergency_count)
        sheet.write_cell(9, 1, self.data.exam_first_phase_count)
        sheet.write_cell(10, 1, self.data.exam_second_phase_count)
        sheet.write_cell(11, 1, self.data.priventive_exam_adults_count)
        sheet.write_cell(12, 1, self.data.priventive_exam_childrens_count)
        sheet.write_cell(13, 1, self.data.exam_orphans_count)
        sheet.write_cell(20, 1, self.data.ambulance_count)
        sheet.write_cell(14, 1, self.data.periodic_exam_childrens_count)
        sheet.write_cell(21, 1, self.data.stomatology_count)
        sheet.write_cell(24, 1, self.data.invoiced_sum)
        sheet.write_cell(22, 1, self.data.stomatology_uet)
