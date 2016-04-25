#! -*- coding: utf-8 -*-
from main.funcs import howlong
from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization
from tfoms.func import get_mo_info


class SogazMekGeneralPage(ReportPage):

    def __init__(self):
        self.data = None
        self.page_number = 5

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = SogazMekGeneralPage.get_query_statistics()
        stat_obj = MedicalOrganization.objects.raw(query, dict(
            period=parameters.registry_period,
            year=parameters.registry_year,
            organization=parameters.organization_code
        ))[0]
        self.data = dict()
        self.data['count_invoiced'] = stat_obj.count_invoiced
        self.data['sum_invoiced'] = stat_obj.sum_invoiced + \
            parameters.policlinic_capitation_total + \
            parameters.ambulance_capitation_total
        self.data['count_sanction'] = stat_obj.count_sanction
        self.data['sum_sanction'] = stat_obj.sum_sanction
        self.data['sum_sanction_total'] = self.data['sum_sanction']
        self.data['sum_sanction_other_mo'] = 0
        self.data['sum_sanction_repeat_mek'] = 0
        self.data['sum_accepted'] = stat_obj.sum_accepted + \
            parameters.policlinic_capitation_total + \
            parameters.ambulance_capitation_total + parameters.fluorography_total

        self.data['no_nl'] = stat_obj.no_nl
        self.data['no_su'] = stat_obj.no_su

    @staticmethod
    def get_query_statistics():
        query = '''
                SELECT
                    mo.id_pk,

                    -- Поданные услуги --
                    COUNT(DISTINCT T.service_id) AS count_invoiced,

                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                               THEN T.accepted_payment
                             ELSE 0 END
                        ) +
                    SUM(CASE WHEN T.is_not_paid AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) AS sum_invoiced, -- сумма предъявленная рассчётная

                    COUNT(DISTINCT CASE WHEN T.is_not_paid
                                          THEN T.service_id
                                   END) AS count_sanction,
                    SUM(CASE WHEN T.is_not_paid
                                  AND T.is_tariff
                               THEN T.provided_tariff
                             ELSE 0
                        END) as sum_sanction, -- сумма снятая рассчётная

                    SUM(CASE WHEN T.is_paid AND T.is_tariff
                               THEN T.accepted_payment
                             ELSE 0
                        END) as sum_accepted, -- сумма принятая рассчётная

                    -- Наличие ошибок
                    COUNT(DISTINCT CASE WHEN T.error_id in (57, 58, 59, 63)
                                          THEN T.service_id
                                   END
                          ) = 0 AS no_nl,

                    COUNT(DISTINCT CASE WHEN T.error_id = 61
                                          THEN T.service_id
                                   END
                          ) = 0 AS no_su

                FROM (
                    SELECT
                        pe.id_pk AS event_id,
                        ps.id_pk AS service_id,
                        mo.id_pk AS organization,
                        ps.payment_type_fk = 3 AS is_not_paid,
                        ps.payment_type_fk = 2 AS is_paid,
                        ps.tariff AS tariff,
                        ps.accepted_payment AS accepted_payment,
                        ps.provided_tariff AS provided_tariff,
                        pss.error_fk AS error_id,

                        ps.payment_kind_fk in (1, 3) AS is_tariff,

                        (
                           SELECT
                               MAX(ms1.subgroup_fk)
                           FROM provided_service ps1
                               JOIN medical_service ms1
                                  ON ps1.code_fk = ms1.id_pk
                           WHERE ps1.event_fk = ps.event_fk
                                 AND ms1.group_fk = 19
                        ) is NULL AND ms.group_fk = 19
                          OR (ms.group_fk = 7 AND ms.subgroup_fk = 5) AS is_not_count

                    FROM medical_register mr
                        JOIN medical_register_record mrr
                           ON mr.id_pk = mrr.register_fk
                        JOIN provided_event pe
                           ON mrr.id_pk = pe.record_fk
                        JOIN provided_service ps
                           ON ps.event_fk = pe.id_pk
                        JOIN medical_organization mo
                           ON mo.id_pk = ps.organization_fk
                        JOIN medical_service ms
                           ON ms.id_pk = ps.code_fk
                        LEFT JOIN provided_service_sanction pss
                           ON pss.service_fk = ps.id_pk AND pss.error_fk = (
                                    SELECT
                                        pss1.error_fk
                                    FROM provided_service_sanction pss1
                                        JOIN medical_error me1
                                           ON me1.id_pk = pss1.error_fk
                                    WHERE pss1.is_active
                                          AND pss1.service_fk = ps.id_pk
                                    ORDER BY me1.weight desc LIMIT 1
                              )
                        WHERE mr.is_active
                              AND mr.period = %(period)s
                              AND mr.year = %(year)s
                              AND mr.organization_code = %(organization)s
                              AND ((pss.id_pk is not NULL AND pss.is_active) OR pss.id_pk is NULL)
                              AND (ms.group_fk != 27 or ms.group_fk is NULL)
                    ) AS T
                JOIN medical_organization mo
                    ON T.organization = mo.id_pk
                GROUP BY mo.id_pk
                '''
        return query

    def print_page(self, sheet, parameters):
        mo_info = get_mo_info(parameters.organization_code)
        sheet.set_style({'valign': 'center', 'align': 'center', 'text_wrap': True})
        sheet.write_cell(3, 2, u'за %s' % parameters.date_string)
        sheet.set_style({'bold': True, 'align': 'center'})
        sheet.write_cell(4, 2, mo_info['act_number'])
        sheet.set_style({'valign': 'center', 'align': 'center', 'text_wrap': True, 'bold': True})
        sheet.write_cell(5, 0, parameters.report_name)
        sheet.write_cell(5, 5, parameters.organization_code)
        sheet.set_style({})
        sheet.write_cell(10, 5, self.data['count_invoiced'])
        sheet.write_cell(11, 5, self.data['sum_invoiced'])
        if self.data['no_su']:
            sheet.write_cell(14, 0, u'Тарифы, указанные в реестре оказанной '
                                    u'медицинской помощи, соответствуют '
                                    u'утвержденным тарифам,')
        if self.data['no_nl']:
            sheet.write_cell(15, 0, u'Виды и профили оказанной '
                                    u'медицинской помощи соответствуют '
                                    u'лицензии медицинского учреждения')
        sheet.write_cell(19, 5, self.data['count_sanction'])
        sheet.write_cell(20, 5, self.data['sum_sanction'])
        sheet.write_cell(24, 2, self.data['sum_sanction_total'])
        sheet.write_cell(26, 2, self.data['sum_sanction_other_mo'])
        sheet.write_cell(29, 2, self.data['sum_sanction_repeat_mek'])
        sheet.write_cell(31, 5, self.data['sum_accepted'])
        last_name, first_name, middle_name = mo_info['act_head_fullname'].split(' ')
        sheet.set_style({'align': 'center'})
        sheet.write_cell(42, 0, u'%s.%s. %s' % (first_name[0], middle_name[0], last_name))
