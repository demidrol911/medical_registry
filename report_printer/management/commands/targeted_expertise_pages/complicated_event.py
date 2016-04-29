#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866


class ComplicatedEvent(FilterReportPage):

    def __init__(self):
        super(ComplicatedEvent, self).__init__()

    def get_query(self):
        query = '''
            SELECT
                mo.name AS mo_name,
                dep.old_code AS department,
                ms.code AS service_code,
                md.code AS division_code,
                md.name AS division_name,
                '' AS errors,
                trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number)) AS policy,
                p.last_name,
                p.first_name,
                p.middle_name,
                p.birthdate,
                p.gender_fk AS gender_code,
                idc.idc_code AS disease_code,
                idc.name AS disease_name,
                pe.anamnesis_number,
                ps.start_date,
                ps.end_date,
                ps.quantity,
                coalesce(ms.uet, 0) AS uet,
                ps.tariff,
                ps.accepted_payment,
                ps.comment,
                pe.hospitalization_fk AS hospitalization_code,
                pe.worker_code,
                tro.code AS outcome_code,
                tr.name AS treatment_result_name,
                concat_ws(', ', COALESCE(aa2.name, ''), COALESCE(aa1.name, ''), COALESCE(aa.name, ''),
                COALESCE(adr.street, ''), COALESCE(adr.house_number, ''),
                COALESCE(adr.extra_number, ''), COALESCE(adr.room_number)) AS address,
                CASE ps.payment_kind_fk WHEN 2 THEN 'P' ELSE 'T' END AS funding_type,

                ps.end_date - ps.start_date AS c_quantity,
                array_to_string(ARRAY(
                    SELECT DISTINCT pecd_idc.idc_code
                    FROM provided_event_concomitant_disease pecd
                        JOIN idc pecd_idc ON pecd.disease_fk = pecd_idc.id_pk
                    WHERE
                        pecd.event_fk = pe.id_pk
                ), ' ') AS concomitant_disease,

                 array_to_string(ARRAY(
                    SELECT DISTINCT pecmd_idc.idc_code
                    FROM provided_event_complicated_disease pecmd
                        JOIN idc pecmd_idc on pecmd.disease_fk = pecmd_idc.id_pk
                    WHERE
                        pecmd.event_fk = pe.id_pk
                ), ' ') AS complicated_disease
            FROM
                provided_service ps
                JOIN provided_event pe
                    ON pe.id_pk = ps.event_fk
                JOIN medical_register_record mrr
                    ON mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    ON mrr.register_fk = mr.id_pk
                JOIN medical_service ms
                    ON ms.id_pk = ps.code_fk
                JOIN medical_organization dep
                    ON dep.id_pk = ps.department_fk
                JOIN medical_organization mo
                    ON mo.code = mr.organization_code
                        and mo.parent_fk is null
                JOIN patient p
                    ON p.id_pk = mrr.patient_fk
                JOIN idc
                    ON idc.id_pk = ps.basic_disease_fk
                JOIN medical_service_term mst
                    ON mst.id_pk = pe.term_fk
                LEFT JOIN tariff_profile tp
                    ON tp.id_pk = ms.tariff_profile_fk
                LEFT JOIN medical_division md
                    ON ps.division_fk = md.id_pk
                LEFT JOIN insurance_policy i
                    ON i.version_id_pk = p.insurance_policy_fk
                LEFT JOIN person per
                    ON per.version_id_pk = (
                        SELECT version_id_pk
                        FROM person
                        WHERE id = (
                            SELECT id
                            FROM person
                            WHERE version_id_pk = i.person_fk
                        ) AND is_active
                    )
                LEFT JOIN treatment_outcome tro
                    ON tro.id_pk = pe.treatment_outcome_fk
                LEFT JOIN treatment_result tr
                    ON tr.id_pk = pe.treatment_result_fk
                LEFT JOIN address adr
                    ON adr.person_fk = per.version_id_pk and adr.type_fk = 1
                LEFT JOIN administrative_area aa
                    ON aa.id_pk = adr.administrative_area_fk
                LEFT JOIN administrative_area aa1
                    ON aa1.id_pk = aa.parent_fk
                LEFT JOIN administrative_area aa2
                    ON aa2.id_pk = aa1.parent_fk
            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND (ms.group_fk != 27 or ms.group_fk is null)
                AND ps.payment_type_fk = 2
                AND (SELECT count(distinct pecmd.id_pk) FROM provided_event_complicated_disease pecmd
                    WHERE pecmd.event_fk = pe.id_pk) != 0
            '''
        return query

    def get_dbf_struct(self):
        return {
            'path': u'C:/work/DIFFICULT_DBF',
            'order_fields': ('last_name', 'first_name', 'middle_name'),
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
            'path': u'C:/work/DIFFICULT',
            'order_fields': ('last_name', 'first_name', 'middle_name'),
            'stop_fields': ('mo_name', ),
            'titles': [
                u'', u'Подразделение', u'Фамилия', u'Имя', u'Отчество', u'ДР',
                u'Полис', u'Начало', u'Окончание', u'Отделение', u'Услуга',
                u'Номер карты', u'Код диагноза', u'Диагноз',  u'Сопутст. диагноз',  u'Диагноз осложнения',
                u'Кол-во', u'Оплачено', u'Тариф', u'Ошибки', u'УЕТ', u'Результат'
            ],
            'file_pattern': '%s'
        }

    def get_statistic_param(self):
        pass

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
        new["DS2"] = unicode_to_cp866(item['concomitant_disease'])
        new["DS3"] = unicode_to_cp866(item['complicated_disease'])
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

    def print_item_excel(self, sheet, item):
        sheet.write(item['mo_name'], 'c')
        sheet.write(item['department'], 'c')
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
        sheet.write(item['concomitant_disease'], 'c')
        sheet.write(item['complicated_disease'], 'c')
        sheet.write(item['quantity'], 'c')
        sheet.write(item['accepted_payment'], 'c')
        sheet.write(item['tariff'], 'c')
        sheet.write(item['errors'], 'c')
        sheet.write(item['uet'], 'c')
        sheet.write(item['treatment_result_name'], 'r')
