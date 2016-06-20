#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866
from medical_service_register.path import DEVELOP_OKS_ONMK, DEVELOP_OKS_ONMK_DBF, \
    PRODUCTION_OKS_ONMK, PRODUCTION_OKS_ONMK_DBF


class OksOnmkPage(FilterReportPage):

    def __init__(self):
        super(OksOnmkPage, self).__init__()

    def get_query(self):
        query = '''
            SELECT
                row_number() OVER (PARTITION BY mo.name
                      ORDER BY dep.old_code, p.last_name, p.first_name, p.middle_name) AS n_number,
                mo.name AS mo_name,
                p.last_name,
                p.first_name,
                p.middle_name,
                p.birthdate,
                trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''),
                                          coalesce(p.insurance_policy_number, ''))) AS policy,
                ps.start_date,
                ps.end_date,
                p.gender_fk AS gender_code,
                md.code AS division_code,
                md.name AS division_name,
                ms.code AS service_code,
                pe.anamnesis_number,
                idc.idc_code AS disease_code,
                idc.name AS disease_name,
                ps.quantity,
                (CASE ps.payment_type_fk WHEN 2 THEN ps.accepted_payment ELSE 0 END),
                ps.tariff,
                ps.accepted_payment,
                (CASE ps.payment_type_fk WHEN 2 THEN '' ELSE array_to_string(ARRAY(
                    SELECT DISTINCT me.old_code
                    FROM provided_service_sanction pss
                        JOIN medical_error me
                            ON me.id_pk = pss.error_fk
                    WHERE
                        pss.service_fk = ps.id_pk AND pss.is_active
                        AND pss.type_fk = 1
                ), ' ') END ) AS errors,
                CASE ms.group_fk WHEN 19 THEN ms.uet ELSE 0 END AS uet,
                CASE ps.payment_kind_fk WHEN 2 THEN 'P' ELSE 'T' END AS funding_type,
                tro.code AS outcome_code,
                pe.hospitalization_fk AS hospitalization_code,
                pe.worker_code,
                dep.old_code AS department,
                ps.id_pk AS service_id
            FROM provided_service ps
                JOIN provided_event pe
                    ON ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    ON mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    ON mr.id_pk = mrr.register_fk
                JOIN medical_organization dep
                    ON dep.id_pk = ps.department_fk
                JOIN medical_register_status mrs
                    ON mrs.id_pk = mr.status_fk
                JOIN patient p
                    ON p.id_pk = mrr.patient_fk
                LEFT JOIN medical_division md
                    ON md.id_pk = ps.division_fk
                LEFT JOIN medical_service_profile msp
                    ON msp.id_pk = ps.profile_fk
                JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                LEFT JOIN idc
                    ON idc.id_pk = ps.basic_disease_fk
                LEFT JOIN medical_service_term mst
                    ON mst.id_pk = pe.term_fk
                LEFT JOIN treatment_result tr
                    ON tr.id_pk = pe.treatment_result_fk
                LEFT JOIN treatment_outcome tro
                    ON tro.id_pk = pe.treatment_outcome_fk
                JOIN medical_organization mo
                    ON mo.code = mr.organization_code and mo.parent_fk is null

                LEFT JOIN idc idc1
                    ON idc1.id_pk = pe.initial_disease_fk
                LEFT JOIN idc idc2
                    ON idc2.id_pk = pe.basic_disease_fk

            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND mr.organization_code NOT IN ('280075', '280001', '280026', '280003', '280027',  '280084')
                AND (idc.idc_code IN (
                    'I20.0', 'I21.9', 'I22.0', 'I22.1', 'I22.8', 'I22.9', 'I23.8', 'I26.0', 'I26.9',
                    'G45.8', 'G45.9',
                    'I61.8', 'I61.9', 'I62.0', 'I62.1', 'I62.9',
                    'I63.8', 'I63.9', 'I64.0'
            ) OR idc.idc_code BETWEEN 'I21.0' AND 'I21.4' OR idc.idc_code BETWEEN 'I23.0' AND 'I23.6' OR idc.idc_code BETWEEN 'G46.0' AND 'G46.8' OR idc.idc_code BETWEEN 'I60.0' AND 'I60.9'
            OR idc.idc_code BETWEEN 'I61.0' AND 'I61.6' OR idc.idc_code BETWEEN 'I63.0' AND 'I63.6' OR idc.idc_code BETWEEN 'G45.0' AND 'G45.4')
                AND (ms.group_fk NOT IN (1, 2) OR ms.group_fk IS NULL)
                AND pe.term_fk IN (1)
                AND (md.name NOT ILIKE '%%РСЦ%%' AND md.name NOT ILIKE '%%ПСО%%')
                AND ps.payment_type_fk = 2
                AND ms.code LIKE '_98%%'
            '''
        return query

    def get_dbf_struct(self):
        return {
            'dev_path': DEVELOP_OKS_ONMK_DBF,
            'prod_path': PRODUCTION_OKS_ONMK_DBF,
            'order_fields': ('last_name', 'first_name', 'middle_name', 'birthdate'),
            'stop_fields': ('department', ),
            'titles': (
                ("COD", "C", 15),
                ("OTD", "C", 3),
                ("ERR_ALL", "C", 8),
                ("SN_POL", "C", 25),
                ("FAM", "C", 20),
                ("IM", "C", 20),
                ("OT", "C", 25),
                ("DR", "D"),
                ("DS", "C", 6),
                ("DS2", "C", 255),
                ("DS3", "C", 255),
                ("C_I", "C", 16),
                ("D_BEG", "D"),
                ("D_U", "D"),
                ("K_U", "N", 4),
                ("F_DOP_R", "N", 10, 2),
                ("T_DOP_R", "N", 10, 2),
                ("S_OPL", "N", 10, 2),
                ("ADRES", "C", 80),
                ("SPOS", "C", 2),
                ("GENDER", "C", 1),
                ("EMPL_NUM", "C", 16),
                ("HOSP_TYPE", "N", 2),
                ("OUTCOME", "C", 3),),
            'file_pattern': 't%s'
            }

    def get_excel_struct(self):
        return {
            'dev_path': DEVELOP_OKS_ONMK,
            'prod_path': PRODUCTION_OKS_ONMK,
            'order_fields': ('department', 'last_name', 'first_name', 'middle_name', 'birthdate'),
            'stop_fields': ('mo_name', ),
            'titles': [
                u'', u'№ п/п', u'Фамилия', u'Имя', u'Отчество', u'ДР',
                u'Полис', u'Начало', u'Окончание', u'Отделение',
                u'Услуга', u'Номер карты', u'Код диагноза',
                u'Диагноз', u'Кол-во', u'Оплачено', u'Тариф',
                u'Ошибки', u'УЕТ', u'Подразделение', u''
            ],
            'file_pattern': '%s'
        }

    def get_statistic_param(self):
        return {
            'group_by': ['mo_name'], 'field': 'service_id'
        }

    def print_item_dbf(self, db, item):
        new = db.newRecord()
        new["COD"] = unicode_to_cp866(item['service_code'])
        new["OTD"] = item.get('division_code', '000')
        new["ERR_ALL"] = item.get('errors', '')
        new["SN_POL"] = unicode_to_cp866(item['policy'])
        new["FAM"] = unicode_to_cp866(item.get('last_name', ''))
        new["IM"] = unicode_to_cp866(item.get('first_name', ''))
        new["OT"] = unicode_to_cp866(item.get('middle_name', ''))
        new["DR"] = item.get('birthdate', '1900-01-01')
        new["DS"] = unicode_to_cp866(item['disease_code'])
        new["C_I"] = unicode_to_cp866(item.get('anamnesis_number', ''))
        new["D_BEG"] = item.get('start_date', '1900-01-01')
        new["D_U"] = item.get('end_date', '1900-01-01')
        new["K_U"] = item.get('quantity', 0)
        new["S_OPL"] = round(float(item.get('accepted_payment', 0)), 2)
        try:
            new["ADRES"] = unicode_to_cp866(item.get('address', ''))
        except:
            new["ADRES"] = ''
        new["SPOS"] = item['funding_type']
        new["GENDER"] = item['gender_code'] or 0
        new["OUTCOME"] = item['outcome_code'] or ''
        new["HOSP_TYPE"] = item['hospitalization_code'] or 0
        new["EMPL_NUM"] = unicode_to_cp866(item['worker_code'] or '')
        new.store()

    def print_item_excel(self, sheet, item):
        sheet.write(item['mo_name'], 'c')
        sheet.write(item['n_number'], 'c')
        sheet.write(item['last_name'], 'c')
        sheet.write(item['first_name'], 'c')
        sheet.write(item['middle_name'], 'c')
        sheet.write(item['birthdate'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['policy'], 'c')
        sheet.write(item['start_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['end_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['division_name'], 'c')
        sheet.write(item['service_code'], 'c')
        sheet.write(item['anamnesis_number'], 'c')
        sheet.write(item['disease_code'], 'c')
        sheet.write(item['disease_name'], 'c')
        sheet.write(item['quantity'], 'c')
        sheet.write(item['accepted_payment'], 'c')
        sheet.write(item['tariff'], 'c')
        sheet.write(item['errors'], 'c')
        sheet.write(item['uet'], 'c')
        sheet.write(item['department'], 'r')
