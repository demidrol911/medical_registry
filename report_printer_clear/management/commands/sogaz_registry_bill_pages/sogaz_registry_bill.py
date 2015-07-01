#! -*- coding: utf-8 -*-

from main.models import MedicalOrganization
from report_printer.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage


class SogazRegistryBillPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,
                    pe.id AS event_xml_id,
                    UPPER(coalesce(pt.last_name, '') || ' ' || coalesce(pt.first_name, '') ||
                          ' ' || coalesce(pt.middle_name, '')) AS patient_fullname,
                    pt.gender_fk AS patient_gender,
                    pt.birthdate AS patient_birthdate,

                    CASE WHEN pt.insurance_policy_series is NULL
                           THEN pt.insurance_policy_number
                         ELSE REPLACE(pt.insurance_policy_series, '\n', '') ||
                              ' ' || pt.insurance_policy_number
                    END AS patient_police,

                    p.birthplace AS patient_birthplace,
                    p.snils AS patient_snils,
                    pt.person_id_series || pt.person_id_number AS patient_identity_document,

                    pt.okato_registration AS patient_place_registration,
                    pt.okato_residence AS patient_place_residence,

                    idc.idc_code AS service_idc_code,
                    pe.start_date AS event_start_date,
                    pe.end_date AS event_end_date,
                    msp.code AS event_profile_code,
                    mws.code AS event_worker_speciality,
                    msk.code AS event_kind,
                    tr.code AS event_treatment_result,
                    COUNT(DISTINCT ps.id_pk) AS services_volume,
                    SUM(ps.tariff) AS tariff,
                    SUM(ps.calculated_payment) AS calculated_payment

                FROM medical_register mr
                    JOIN medical_register_record mrr
                       ON mr.id_pk = mrr.register_fk
                    JOIN provided_event pe
                       ON mrr.id_pk = pe.record_fk
                    JOIN provided_service ps
                       ON ps.event_fk = pe.id_pk
                    JOIN medical_organization mo
                       ON ps.organization_fk = mo.id_pk
                    JOIN patient pt
                       ON mrr.patient_fk = pt.id_pk
                    JOIN medical_service ms
                       ON ms.id_pk = ps.code_fk
                    LEFT JOIN medical_service_kind msk
                       ON msk.id_pk = pe.kind_fk
                    LEFT JOIN insurance_policy ip
                       ON ip.version_id_pk = pt.insurance_policy_fk
                    LEFT JOIN person p
                       ON p.version_id_pk = ip.person_fk
                    LEFT JOIN idc
                       ON pe.basic_disease_fk = idc.id_pk
                    LEFT JOIN medical_service_profile msp
                       ON msp.id_pk = pe.profile_fk
                    LEFT JOIN medical_worker_speciality mws
                       ON mws.id_pk = pe.worker_speciality_fk
                    LEFT JOIN treatment_result tr
                       ON tr.id_pk = pe.treatment_result_fk
                WHERE mr.is_active
                   AND mr.period = %(period)s
                   AND mr.year = %(year)s
                   AND mr.organization_code = %(organization)s
                   AND (ms.group_fk != 27
                        OR ms.group_fk is NULL
                       )
                GROUP BY mo.id_pk, event_xml_id, patient_fullname,
                         patient_gender, patient_birthdate,
                         patient_police, patient_birthplace,
                         patient_identity_document,
                         patient_snils,
                         patient_place_registration,
                         patient_place_residence,
                         service_idc_code, event_start_date, event_end_date,
                         event_profile_code, event_worker_speciality, event_kind,
                         event_treatment_result
                '''
        self.data = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))

    def print_page(self, sheet, parameters):
        sheet.write_cell(5, 6, parameters.report_name)
        sheet.set_position(15, 0)
        sheet.set_style(VALUE_STYLE)
        for item in self.data:
            sheet.set_style(VALUE_STYLE)
            sheet.write(item.event_xml_id, 'c')
            sheet.write(item.patient_fullname, 'c')
            sheet.write(item.patient_gender, 'c')
            sheet.write(item.patient_birthdate.strftime('%d.%m.%Y'), 'c')
            sheet.write(item.patient_birthplace, 'c')
            sheet.write(item.patient_identity_document, 'c')
            sheet.write(item.patient_place_registration, 'c')
            sheet.write(item.patient_place_residence, 'c')
            sheet.write(item.patient_snils, 'c')
            sheet.write(item.patient_police, 'c')

            sheet.write(item.event_kind, 'c')
            sheet.write(item.service_idc_code, 'c')
            sheet.write(item.event_start_date.strftime('%d.%m.%Y') + '-'
                        + item.event_end_date.strftime('%d.%m.%Y'), 'c')
            sheet.write(item.services_volume, 'c')
            sheet.write(item.event_profile_code, 'c')
            sheet.write(item.event_worker_speciality, 'c')
            sheet.write(item.tariff, 'c')
            sheet.write(item.calculated_payment, 'c')
            sheet.write(item.event_treatment_result, 'r')
        SogazRegistryBillPage.print_place_for_signature(sheet)

    @staticmethod
    def print_place_for_signature(sheet):
        sheet.set_style({})
        sheet.write('', 'r')
        sheet.write('', 'c', 1)
        sheet.write(u'Главный бухгалтер', 'c', 2)
        sheet.set_style({'bottom': 1})
        sheet.write('', 'r', 4)
        sheet.set_style({})
        sheet.write('', 'c', 4)
        sheet.write(u'(подпись, расшифровка подписи)', 'r', 4)
        sheet.write(u'М.П.', 'r', 1)
        sheet.write('', 'c', 1)
        sheet.write(u'Исполнитель', 'c', 2)
        sheet.set_style({'bottom': 1})
        sheet.write('', 'r', 4)
        sheet.set_style({})
        sheet.write('', 'c', 4)
        sheet.write(u'(подпись, расшифровка подписи)', 'r', 4)
        sheet.write('', 'c', 1)
        sheet.write(u'Дата '+'_'*50, 'c', 2)




