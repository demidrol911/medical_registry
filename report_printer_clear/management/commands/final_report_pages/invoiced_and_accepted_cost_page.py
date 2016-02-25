from main.models import MedicalOrganization
from report_printer.excel_style import VALUE_STYLE
from report_printer_clear.management.commands.medical_services_types_pages.const import POSITION_REPORT
from report_printer_clear.utils.page import ReportPage
from tfoms.func import get_mo_register, calculate_capitation


class InvoicedAndAcceptedCostPage(ReportPage):

    def __init__(self):
        self.data = None
        self.capitation_data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
        self.capitation_data = None
        query = '''
                WITH mo_services AS (
                    SELECT
                        mo.id_pk AS mo_id,
                        mr.organization_code AS organization_code,
                        pe.term_fk = 1 OR (mr.organization_code IN ('280013', '280043') AND ms.group_fk = 31) AS is_hospital,
                        pe.term_fk = 2 AS is_day_hospital,
                        ((pe.term_fk = 3 AND (ms.group_fk != 19 OR ms.group_fk IS NULL)
                        AND (ps.payment_kind_fk != 2 OR ps.payment_kind_fk IS NULL)) OR pe.term_fk IS NULL) AND
                            (CASE WHEN mr.organization_code IN ('280013', '280043') AND ms.group_fk = 31 THEN False
                              ELSE True END) AS is_clinic,
                        pe.term_fk = 4 AND (ps.payment_kind_fk != 2 OR ps.payment_kind_fk IS NULL) AS is_acute_care,
                        pe.term_fk = 3 AND ms.group_fk = 19 AS is_stom,

                        ps.payment_type_fk = 2 AS is_accepted,
                        ps.payment_type_fk = 3 AS is_excluded,

                        ROUND(ps.accepted_payment, 2) AS accepted_cost,
                        ROUND(ps.provided_tariff, 2) AS excluded_cost,
                        ROUND(CASE WHEN ps.payment_type_fk = 2 THEN ps.accepted_payment
                                   WHEN ps.payment_type_fk = 3 THEN ps.provided_tariff
                              END, 2) AS invoiced_cost

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
                    WHERE mr.is_active
                       AND mr.period = %(period)s
                       AND mr.year = %(year)s
                       AND (ms.group_fk != 27 OR ms.group_fk is null)
                )
                SELECT
                    mo.id_pk,
                    organization_code,
                    COALESCE(SUM(CASE WHEN is_hospital THEN invoiced_cost END), 0) AS hospital_invoiced_cost,
                    COALESCE(SUM(CASE WHEN is_day_hospital THEN invoiced_cost END), 0) AS day_hospital_invoiced_cost,
                    COALESCE(SUM(CASE WHEN is_clinic THEN invoiced_cost END), 0) AS clinic_visit_invoiced_cost,
                    COALESCE(SUM(CASE WHEN is_acute_care THEN invoiced_cost END), 0) AS acutecare_invoiced_cost,
                    COALESCE(SUM(CASE WHEN is_stom THEN invoiced_cost END), 0) AS stom_invoiced_cost,

                    COALESCE(SUM(CASE WHEN is_excluded AND is_hospital THEN excluded_cost END), 0) AS hospital_excluded_cost,
                    COALESCE(SUM(CASE WHEN is_excluded AND is_day_hospital THEN excluded_cost END), 0) AS day_hospital_excluded_cost,
                    COALESCE(SUM(CASE WHEN is_excluded AND is_clinic THEN excluded_cost END), 0) AS clinic_visit_excluded_cost,
                    COALESCE(SUM(CASE WHEN is_excluded AND is_acute_care THEN excluded_cost END), 0) AS acutecare_excluded_cost,
                    COALESCE(SUM(CASE WHEN is_excluded AND is_stom THEN excluded_cost END), 0) AS stom_excluded_cost,

                    COALESCE(SUM(CASE WHEN is_accepted AND is_hospital THEN accepted_cost END), 0) AS hospital_accepted_cost,
                    COALESCE(SUM(CASE WHEN is_accepted AND is_day_hospital THEN accepted_cost END), 0) AS day_hospital_accepted_cost,
                    COALESCE(SUM(CASE WHEN is_accepted AND is_clinic THEN accepted_cost END), 0) AS clinic_visit_accepted_cost,
                    COALESCE(SUM(CASE WHEN is_accepted AND is_acute_care THEN accepted_cost END), 0) AS acutecare_accepted_cost,
                    COALESCE(SUM(CASE WHEN is_accepted AND is_stom THEN accepted_cost END), 0) AS stom_accepted_cost
                FROM
                   mo_services
                   JOIN medical_organization mo
                      ON mo.id_pk = mo_id
                GROUP BY mo.id_pk, organization_code
                '''

        self.data = MedicalOrganization.objects.raw(query, dict(
            year=parameters.registry_year,
            period=parameters.registry_period
        ))
        self.capitation_data = self._calc_capitation()

    def _calc_capitation(self):
        capitation_cost = {}
        for mo_code in get_mo_register():
            capitation_cost[mo_code] = {'clinic_capitation': 0, 'ambulance_capitation': 0}
            clinic_capitation = calculate_capitation(3, mo_code)
            ambulance_capitation = calculate_capitation(4, mo_code)
            if clinic_capitation[0]:
                capitation_cost[mo_code]['clinic_capitation'] = self._calc_capitation_total(clinic_capitation[1])
            if ambulance_capitation[0]:
                capitation_cost[mo_code]['ambulance_capitation'] = self._calc_capitation_total(ambulance_capitation[1])
        return capitation_cost

    def _calc_capitation_total(self, capitation):
        total = 0
        for key in capitation:
            total += capitation[key].get('accepted', 0)
        return total

    def print_page(self, sheet, parameters):
        sheet.set_style({'align': 'center'})
        sheet.write_cell(5, 1, parameters.date_string)
        sheet.set_style(VALUE_STYLE)
        for data_on_mo in self.data:
            capitation_on_mo = self.capitation_data[data_on_mo.organization_code]
            sheet.set_position(POSITION_REPORT[data_on_mo.organization_code], 2)
            sheet.write(data_on_mo.hospital_invoiced_cost, 'c')
            sheet.write(data_on_mo.day_hospital_invoiced_cost, 'c')
            sheet.write(data_on_mo.clinic_visit_invoiced_cost, 'c')
            sheet.write(capitation_on_mo['clinic_capitation'], 'c')
            sheet.write(data_on_mo.acutecare_invoiced_cost, 'c')
            sheet.write(capitation_on_mo['ambulance_capitation'], 'c')
            sheet.write(data_on_mo.stom_invoiced_cost, 'c')
            sheet.write(data_on_mo.hospital_invoiced_cost
                        + data_on_mo.day_hospital_invoiced_cost
                        + data_on_mo.clinic_visit_invoiced_cost
                        + capitation_on_mo['clinic_capitation']
                        + capitation_on_mo['ambulance_capitation']
                        + data_on_mo.stom_invoiced_cost, 'c')

            sheet.write(data_on_mo.hospital_excluded_cost, 'c')
            sheet.write(data_on_mo.day_hospital_excluded_cost, 'c')
            sheet.write(data_on_mo.clinic_visit_excluded_cost, 'c')
            sheet.write(0, 'c')
            sheet.write(data_on_mo.acutecare_excluded_cost, 'c')
            sheet.write(0, 'c')
            sheet.write(data_on_mo.stom_excluded_cost, 'c')
            sheet.write(data_on_mo.hospital_excluded_cost
                        + data_on_mo.day_hospital_excluded_cost
                        + data_on_mo.clinic_visit_excluded_cost
                        + data_on_mo.stom_excluded_cost, 'c')

            sheet.write(data_on_mo.hospital_accepted_cost, 'c')
            sheet.write(data_on_mo.day_hospital_accepted_cost, 'c')
            sheet.write(data_on_mo.clinic_visit_accepted_cost, 'c')
            sheet.write(capitation_on_mo['clinic_capitation'], 'c')
            sheet.write(data_on_mo.acutecare_accepted_cost, 'c')
            sheet.write(capitation_on_mo['ambulance_capitation'], 'c')
            sheet.write(data_on_mo.stom_accepted_cost, 'c')
            sheet.write(data_on_mo.hospital_accepted_cost
                        + data_on_mo.day_hospital_accepted_cost
                        + data_on_mo.clinic_visit_accepted_cost
                        + capitation_on_mo['clinic_capitation']
                        + capitation_on_mo['ambulance_capitation']
                        + data_on_mo.stom_accepted_cost, 'c')

