#! -*- coding: utf-8 -*-
from copy import deepcopy
from datetime import datetime
from main.funcs import howlong

from main.models import MedicalOrganization
from report_printer.const import MONTH_NAME
from report_printer_clear.utils.excel_style import VALUE_STYLE
from report_printer_clear.utils.page import ReportPage
from tfoms.func import FAILURE_CAUSES, ERRORS, get_mo_info


class SanctionsPage(ReportPage):
    TABLE_HEADER = [
        u'№ n/n в реестре счетов', u'№ документа ОМС',
        u'ФИО', u'Дата рождения', u'Номер карты', u'Дата лечения',
        u'Кол-во дней лечения', u'Пос/госп', u'УЕТ', u'Код услуги',
        u'Код по МКБ-10', u'Отд.', u'Профиль отделения', u'№ случая',
        u'ID_SERV', u'ID_PAC', u'Представлено к оплате',
        u'Расчетная сумма', u'Отказано в оплате'
    ]
    EXCEL_FAILURE_CAUSE_STYLE = {
        'bold': True,
        'font_color': 'red',
        'font_size': 11
    }
    EXCEL_ERROR_STYLE = {
        'bold': True,
        'font_color': 'blue',
        'font_size': 11
    }
    EXCEL_TABLE_HEADER_STYLE = {
        'bold': True,
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'font_size': 11,
        'text_wrap': True
    }

    def __init__(self):
        self.data = None
        self.page_number = 1

    @howlong
    def calculate(self, parameters):
        self.data = None
        query = '''
                SELECT
                    mo.id_pk,
                    pfc.number AS failure_cause_number,
                    me.failure_cause_fk AS failure_cause_id,
                    me.id_pk AS error_id,
                    ps.id as service_xml_id,
                    CASE WHEN pt.insurance_policy_series is null
                           THEN pt.insurance_policy_number
                         ELSE REPLACE(pt.insurance_policy_series, '\n', '') ||
                              ' ' || pt.insurance_policy_number
                    END as patient_police,
                    UPPER(coalesce(pt.last_name, '') || ' ' || coalesce(pt.first_name, '') ||
                          ' ' || coalesce(pt.middle_name, '')) AS patient_fullname,
                    pt.birthdate AS patient_birthdate,
                    pe.anamnesis_number AS service_anamnesis_number,
                    ps.end_date AS service_end_date,
                    CASE WHEN ps.quantity = 0
                              or ps.quantity is null
                           THEN 1
                         ELSE ps.quantity
                    END AS service_quantity,
                    (CASE WHEN ps.quantity = 0
                               or ps.quantity is null
                            THEN 1
                          ELSE ps.quantity
                     END) * COALESCE(ms.uet, 0) AS service_uet,
                    ms.code AS service_code,
                    idc.idc_code AS service_basic_disease,
                    ms.name AS service_name,
                    CASE WHEN pe.term_fk in (1, 2)
                           THEN ps.profile_fk
                         ELSE ps.worker_speciality_fk
                         END AS service_profile_or_worker_speciality,
                    pe.id_pk AS event_id,
                    pt.id AS patient_xml_id,
                    ps.tariff AS service_tariff,
                    ps.calculated_payment As service_calculated_payment,
                    CASE WHEN ps.payment_kind_fk = 2
                           THEN 'Подуш.'
                    END AS capitation_string,
                    ps.provided_tariff AS service_provided_tariff


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
                    JOIN medical_organization dep
                       ON dep.id_pk = ps.department_fk
                    LEFT JOIN idc
                       ON ps.basic_disease_fk = idc.id_pk
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
                   AND dep.old_code = ANY(%(department)s)
                ORDER BY failure_cause_number ASC, error_id ASC,
                patient_fullname, event_id, service_code
                '''

        self.data = MedicalOrganization.objects.raw(
            query,
            dict(
                period=parameters.registry_period,
                year=parameters.registry_year,
                organization=parameters.organization_code,
                department=parameters.departments
            ))

    def print_page(self, sheet, parameters):
        zero_sum = {
            'days': 0,
            'hosp': 0,
            'uet': 0,
            'tariff': 0,
            'calculated_payment': 0,
            'provided_tariff': 0
        }
        current_failure_cause = 0
        current_error = 0
        total_amount_of_error = deepcopy(zero_sum)
        total_amount = deepcopy(zero_sum)
        mo_info = get_mo_info(parameters.organization_code)

        sheet.set_style({'align': 'center'})
        current_date = datetime.now()
        sheet.write_rich_text(3, 0, {'bold': True}, u'Акт ',
                              u'№ ',
                              {'underline': True}, mo_info['act_number'],
                              u' от _.%s.%s г.' % (current_date.month if current_date.month > 9
                                                   else '0'+str(current_date.month),
                              current_date.year), {'align': 'center'})
        sheet.set_style({'bold': True, 'underline': True, 'align': 'center'})
        sheet.write_cell(4, 0, u'медико-экономического контроля счета за %s'
                               % MONTH_NAME[parameters.registry_period])
        sheet.set_style({'align': 'center'})
        sheet.write_rich_text(6, 0, u'в медицинской организации: ',
                              {'bold': True}, parameters.report_name,
                              {'align': 'center'})
        sheet.set_position(10, 0)
        for item in self.data:
            if current_failure_cause != item.failure_cause_id:
                SanctionsPage.print_total_amount_of_error(sheet, current_error, total_amount_of_error)
                sheet.set_style(SanctionsPage.EXCEL_FAILURE_CAUSE_STYLE)
                sheet.write(FAILURE_CAUSES[item.failure_cause_id]['number'] +
                            ' ' + FAILURE_CAUSES[item.failure_cause_id]['name'], 'r')
                current_failure_cause = item.failure_cause_id
                current_error = 0
                total_amount = SanctionsPage.add_sum(total_amount, total_amount_of_error)
                total_amount_of_error = deepcopy(zero_sum)

            if current_error != item.error_id:
                SanctionsPage.print_total_amount_of_error(sheet, current_error, total_amount_of_error)
                sheet.set_style(SanctionsPage.EXCEL_ERROR_STYLE)
                sheet.write(ERRORS[item.error_id]['code'] +
                            ' ' + ERRORS[item.error_id]['name'], 'r')
                SanctionsPage.print_table_header(sheet)
                current_error = item.error_id
                total_amount = SanctionsPage.add_sum(total_amount, total_amount_of_error)
                total_amount_of_error = deepcopy(zero_sum)

            sheet.set_style(VALUE_STYLE)
            sheet.write(item.service_xml_id, 'c')
            sheet.write(item.patient_police, 'c')
            sheet.write(item.patient_fullname, 'c')
            sheet.write(item.patient_birthdate.strftime('%d.%m.%Y'), 'c')
            sheet.write(item.service_anamnesis_number, 'c')
            sheet.write(item.service_end_date.strftime('%d.%m.%Y'), 'c')
            sheet.write(item.service_quantity, 'c')
            sheet.write(1, 'c')
            sheet.write(item.service_uet, 'c')
            sheet.write(item.service_code, 'c')
            sheet.write(item.service_basic_disease, 'c')
            sheet.write(item.service_name, 'c')
            sheet.write(item.service_profile_or_worker_speciality, 'c')
            sheet.write(item.event_id, 'c')
            sheet.write(item.service_xml_id, 'c')
            sheet.write(item.patient_xml_id, 'c')
            sheet.write(item.service_tariff, 'c')
            sheet.write(item.service_calculated_payment, 'c')
            sheet.write(item.capitation_string
                        if item.capitation_string == u'Подуш.'
                        else item.service_provided_tariff, 'r')

            total_amount_of_error['days'] += item.service_quantity
            total_amount_of_error['hosp'] += 1
            total_amount_of_error['uet'] += item.service_uet
            total_amount_of_error['tariff'] += item.service_tariff
            total_amount_of_error['calculated_payment'] += item.service_calculated_payment or 0
            total_amount_of_error['provided_tariff'] += 0 \
                if item.capitation_string == u'Подуш.' \
                else item.service_provided_tariff

        if self.data:
            total_amount = SanctionsPage.add_sum(total_amount, total_amount_of_error)
            SanctionsPage.print_total_amount_of_error(sheet, current_error, total_amount_of_error)
            sheet.set_style(VALUE_STYLE)
            sheet.write(u'Итого по ошибкам', 'c')
            SanctionsPage.print_sum(sheet, total_amount)

        sheet.hide_column('M:M')
        sheet.hide_column('O:P')
        sheet.hide_column('P:P')

        sheet.set_style({})
        sheet.write('', 'r')
        sheet.write('', 'r')
        SanctionsPage.print_place_for_signature(sheet, mo_info)

    @staticmethod
    def add_sum(sum_src, sum_dst):
        for key in sum_src:
            sum_src[key] += sum_dst[key]
        return sum_src

    @staticmethod
    def print_total_amount_of_error(sheet, error_id, sum_src):
        if error_id != 0:
            sheet.write(u'Итого по ошибке '+ERRORS[error_id]['code'], 'c')
            SanctionsPage.print_sum(sheet, sum_src)
            sheet.set_style({})
            sheet.write('', 'r')
            sheet.write('', 'r')

    @staticmethod
    def print_sum(sheet, sum_src):
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write(sum_src['days'], 'c')
        sheet.write(sum_src['hosp'], 'c')
        sheet.write(sum_src['uet'], 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write('', 'c')
        sheet.write(sum_src['tariff'], 'c')
        sheet.write(sum_src['calculated_payment'], 'c')
        sheet.write(sum_src['provided_tariff'], 'c')

    @staticmethod
    def print_table_header(sheet):
        sheet.set_style(SanctionsPage.EXCEL_TABLE_HEADER_STYLE)
        for title in SanctionsPage.TABLE_HEADER:
            sheet.write(title, 'c')
        sheet.set_style({})
        sheet.write('', 'r')

    @staticmethod
    def print_place_for_signature(sheet, mo_info):
        sheet.set_style({})
        sheet.write('', 'r')
        sheet.write(u'Исполнитель', 'c')
        sheet.set_style({'bottom': 1})
        sheet.write('', 'c', 3)
        sheet.set_style({})
        sheet.write(u'подпись', 'c')
        sheet.write('()', 'c')

        sheet.write('', 'r')
        sheet.write('', 'r')
        sheet.write('', 'r')
        sheet.write(u'Руководитель страховой медицинской организации', 'r')
        sheet.write('', 'r')
        sheet.write('', 'c')
        sheet.set_style({'bottom': 1})
        sheet.write('', 'c', 3)
        sheet.set_style({})
        sheet.write(u'подпись', 'c')
        sheet.write(u'(Е.Л. Дьячкова)', 'r')

        sheet.write('', 'r')
        sheet.write(u'МП', 'r')

        sheet.write('', 'r')
        sheet.write('', 'r')
        sheet.write(u'Должность, подпись руководителя '
                    u'медицинской организации, ознакомившегося с Актом', 'r')
        sheet.write('', 'r')
        sheet.write('', 'c')
        sheet.set_style({'bottom': 1})
        sheet.write('', 'c', 3)
        sheet.set_style({})
        sheet.write(u'подпись', 'c')
        last_name, first_name, middle_name = mo_info['act_head_fullname'].split(' ')
        sheet.write(u'(%s.%s. %s)' % (first_name[0], middle_name[0], last_name), 'r')

        sheet.write('', 'r')
        sheet.write(u'МП', 'r')
        sheet.write('', 'r')
        sheet.write('', 'r', 2)
        sheet.write(u'Дата       '+'_'*30, 'c')




