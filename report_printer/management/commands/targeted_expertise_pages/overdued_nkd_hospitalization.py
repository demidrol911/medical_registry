#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866


class OverduedNkdHospitalization(FilterReportPage):

    def __init__(self):
        super(OverduedNkdHospitalization, self).__init__()

    def get_query(self):
        query = '''
        select *,
            case when nkd <= 1 then 100
            else round(T.c_quantity / T.nkd * 100, 0)
            END
        from (
            select DISTINCT
                COALESCE(
                        (
                            select tariff_nkd.value
                            from tariff_nkd
                            where start_date = (
                                select max(start_date)
                                from tariff_nkd
                                where start_date <= greatest('2016-01-01'::DATE, ps.end_date)
                                    and start_date >= '2016-01-01'::DATE
                                    and profile_fk = ms.tariff_profile_fk
                                    and is_children_profile = ps.is_children_profile
                                    and "level" = dep.level
                            ) and profile_fk = ms.tariff_profile_fk
                                and is_children_profile = ps.is_children_profile
                                and (( pe.term_fk = 1 and "level" = dep.level)
                                    or (pe.term_fk = 2)
                                )
                            order by start_date DESC
                            limit 1
                        ), 1
                ) as nkd,
                mo.name AS mo_name,
                dep.old_code as department,
                mst.name AS term_name,
                ms.code as service_code,
                md.code as division_code,
                tp.name AS profile_name,
                '' as errors,
                trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number)) as policy,
                p.last_name,
                p.first_name,
                p.middle_name,
                p.birthdate,
                p.gender_fk as gender_code,
                idc.idc_code as basic_disease_code,
                array_to_string(ARRAY(
                    SELECT DISTINCT pecd_idc.idc_code
                    FROM provided_event_concomitant_disease pecd
                        JOIN idc pecd_idc ON pecd.disease_fk = pecd_idc.id_pk
                    WHERE
                        pecd.event_fk = pe.id_pk
                ), ' ')  as concomitant_disease,
                pe.anamnesis_number,
                ps.start_date,
                ps.end_date,
                ps.quantity,
                ps.accepted_payment AS accepted,
                ps.comment,
                pe.hospitalization_fk as hospitalization_code,
                pe.worker_code,
                tro.code as outcome_code,
                concat_ws(', ', COALESCE(aa2.name, ''), Coalesce(aa1.name, ''), COALESCE(aa.name, ''),
                coalesce(adr.street, ''), coalesce(adr.house_number, ''),
                COALESCE(adr.extra_number, ''), coalesce(adr.room_number)) as address,
                case ps.payment_kind_fk when 2 then 'P' else 'T' END as funding_type,
                ps.quantity as c_quantity,
                pe.term_fk AS event_term,
                ps.id_pk AS service_id,
                mr.organization_code AS organization_code,
                pe.id AS event_mo_id
            from
                provided_service ps
                join provided_event pe
                    on pe.id_pk = ps.event_fk
                join medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                join medical_register mr
                    on mrr.register_fk = mr.id_pk
                JOIN medical_service ms
                    on ms.id_pk = ps.code_fk
                JOIN medical_organization dep
                    on dep.id_pk = ps.department_fk
                join medical_organization mo
                    on mo.code = mr.organization_code
                        and mo.parent_fk is null
                join patient p
                    on p.id_pk = mrr.patient_fk
                JOIN idc
                    on idc.id_pk = ps.basic_disease_fk
                JOIN medical_service_term mst
                    on mst.id_pk = pe.term_fk
                LEFT JOIN tariff_profile tp
                    on tp.id_pk = ms.tariff_profile_fk
                LEFT JOIN medical_division md
                    on ps.division_fk = md.id_pk
                LEFT JOIN insurance_policy i
                    on i.version_id_pk = p.insurance_policy_fk
                LEFT JOIN person per
                    on per.version_id_pk = (
                        select version_id_pk
                        from person
                        where id = (
                            select id
                            from person
                            where version_id_pk = i.person_fk
                        ) and is_active
                    )
                LEFT JOIN treatment_outcome tro
                    on tro.id_pk = pe.treatment_outcome_fk
                LEFT JOIN address adr
                    on adr.person_fk = per.version_id_pk and adr.type_fk = 1
                LEFT JOIN administrative_area aa
                    on aa.id_pk = adr.administrative_area_fk
                LEFT join administrative_area aa1
                    on aa1.id_pk = aa.parent_fk
                LEFT join administrative_area aa2
                    on aa2.id_pk = aa1.parent_fk
            where mr.is_active
                and mr.year = %(year)s
                and mr.period = %(period)s
                and pe.term_fk in (1, 2)
                and ps.tariff > 0
                and ps.payment_type_fk = 2
                and (ps.comment not like '1%%' or ps.comment is null or ps.comment = '')
                and idc.idc_code not like 'O04%%'
                and (ms.group_fk is null or ms.group_fk <> 17)
        ) as T
        where
            case when nkd <= 1 then 100
            else round(T.c_quantity / T.nkd * 100, 0)
            END >= 150
            or
            case when nkd <= 1 then 100
            else round(T.c_quantity / T.nkd * 100, 0)
            END <= 50
        '''
        return query

    def get_dbf_struct(self):
        return {
            'path': u'C:/work/OVERDUED_NKD_DBF',
            'order_fields': ('term_name', 'last_name', 'first_name', 'middle_name'),
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
                ("DS2", "C", 6),
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
                ("OUTCOME", "C", 3),
            ),
            'file_pattern': 't%s'
            }

    def get_excel_struct(self):
        return {
            'path': u'C:/work/OVERDUED_NKD',
            'order_fields': ('last_name', 'first_name', 'middle_name'),
            'stop_fields': ('mo_name', 'term_name'),
            'titles': [
                u'', u'Подразделение', u'Условия',
                u'Фамилия', u'Имя', u'Отчество', u'ДР', u'Код диагноза',
                u'Услуга', u'Профиль', u'Оплачено',
                u'Начало услуги', u'Окончание услуги',
                u'Средняя прод-сть', u'Факт. прод-сть',
                u'Процент', u''
            ],
            'file_pattern': '%s %s'
        }

    def get_statistic_param(self):
        return {
            'group_by': ['mo_name', 'event_term'], 'field': 'service_id'
        }

    def print_item_dbf(self, db, item):
        new = db.newRecord()
        new["COD"] = unicode_to_cp866(item['service_code'])
        new["OTD"] = item.get('division_code', '000')
        new["ERR_ALL"] = ''
        new["SN_POL"] = unicode_to_cp866(item['policy'])
        new["FAM"] = unicode_to_cp866(item.get('last_name', ''))
        new["IM"] = unicode_to_cp866(item.get('first_name', ''))
        new["OT"] = unicode_to_cp866(item.get('middle_name', ''))
        new["DR"] = item.get('birthdate', '1900-01-01')
        new["DS"] = unicode_to_cp866(item['basic_disease_code'])
        new["DS2"] = unicode_to_cp866(item['concomitant_disease'])
        new["C_I"] = unicode_to_cp866(item.get('anamnesis_number', ''))
        new["D_BEG"] = item.get('start_date', '1900-01-01')
        new["D_U"] = item.get('end_date', '1900-01-01')
        new["K_U"] = item.get('quantity', 0)
        new["S_OPL"] = round(float(item.get('accepted', 0)), 2)
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
        sheet.write(item['department'], 'c')
        sheet.write(item['term_name'], 'c')
        sheet.write(item['last_name'], 'c')
        sheet.write(item['first_name'], 'c')
        sheet.write(item['middle_name'], 'c')
        sheet.write(item['birthdate'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['basic_disease_code'], 'c')
        sheet.write(item['service_code'], 'c')
        sheet.write(item['profile_name'], 'c')
        sheet.write(item['accepted'], 'c')
        sheet.write(item['start_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['end_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['nkd'], 'c')
        sheet.write(item['quantity'], 'c')
        sheet.write(item['event_mo_id'], 'r')
