#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866


class DoubledDisease(FilterReportPage):

    def __init__(self):
        super(DoubledDisease, self).__init__()

    def get_query(self):
        query = '''
            with all_data as (
                select DISTINCT pe.id_pk event_1, min(T.event_id) event_2
                FROM provided_service ps
                    join provided_event pe
                        on pe.id_pk = ps.event_fk
                    JOIN medical_register_record mrr
                        on mrr.id_pk = pe.record_fk
                    JOIN medical_register mr
                        on mr.id_pk = mrr.register_fk
                    JOIN patient p
                        on p.id_pk = mrr.patient_fk
                    JOIN insurance_policy ip
                        on ip.version_id_pk = p.insurance_policy_fk
                    JOIN (
                        select pe1.id_pk as event_id, mr1.organization_code,
                            ip1.id, pe1.term_fk, ps1.basic_disease_fk, ps1.code_fk,
                            pe1.start_date as event_start_date,
                            pe1.end_date as event_end_date, ps1.id_pk as service_id,
                            ps1.department_fk AS department_id,
                            format('%%s-%%s-01', mr1.year, mr1.period)::DATE AS checking_period
                        FROM provided_service ps1
                            join provided_event pe1
                                on pe1.id_pk = ps1.event_fk
                            JOIN medical_register_record mrr1
                                on mrr1.id_pk = pe1.record_fk
                            JOIN medical_register mr1
                                on mr1.id_pk = mrr1.register_fk
                            JOIN patient p1
                                on p1.id_pk = mrr1.patient_fk
                            JOIN insurance_policy ip1
                                on ip1.version_id_pk = p1.insurance_policy_fk
                        WHERE mr1.is_active
                            and format('%%s-%%s-01', mr1.year, mr1.period)::DATE <= format('%%s-%%s-01', %(year)s, %(period)s)::DATE
                            and format('%%s-%%s-01', mr1.year, mr1.period)::DATE >= format('%%s-%%s-01', %(year)s, %(period)s)::DATE - interval '9 months'
                            and (pe1.term_fk in (1,2,4)
                                or (
                                    (pe1.term_fk = 3 and
                                        (select count(ps2.id_pk)
                                        FROM provided_service ps2
                                            join medical_service ms2 on ms2.id_pk = ps2.code_fk
                                        WHERE ps2.event_fk = ps1.event_fk
                                            and (ms2.group_fk is NULL or ms2.group_fk = 24)
                                            and ms2.reason_fk = 1
                                        ) > 1
                                    )
                                )
                            )
                            and ps1.payment_type_fk in (2)
                            and ps1.tariff > 0

                        ) as T on T.id = ip.id and mr.organization_code = T.organization_code and T.term_fk = pe.term_fk
                            and ps.basic_disease_fk = T.basic_disease_fk and T.event_id <> pe.id_pk
                            and ps.id_pk <> T.service_id
                WHERE mr.is_active
                    and mr.year = %(year)s
                    and mr.period = %(period)s
                    AND ps.payment_type_fk = 2
                    and (( pe.term_fk in (1, 2) and ps.code_fk = T.code_fk
                          and format('%%s-%%s-01', mr.year, mr.period)::DATE <> checking_period
                          and (pe.end_date - event_start_date between 0 and 89 or pe.end_date - T.event_end_date between 0 and 89 or pe.start_date - T.event_start_date between 0 and 89 or pe.start_date - T.event_end_date  between 0 and 89))
                        or (pe.term_fk = 4 and ps.code_fk = T.code_fk and age(pe.end_date, T.event_end_date) = '0 days')
                        or (pe.term_fk = 4 and T.term_fk = 4 and (age(pe.end_date, T.event_end_date) BETWEEN '0 days' AND '1 days' OR age(T.event_end_date, pe.end_date) BETWEEN '0 days' AND '1 days'))
                        or (pe.term_fk = 3 and ps.code_fk = T.code_fk
                            and format('%%s-%%s-01', mr.year, mr.period)::DATE <> checking_period
                            and (age(pe.end_date, T.event_start_date) between '1 days' and '29 days' or age(pe.start_date, T.event_end_date) between '1 days' and '29 days'))
                    )
                    and ps.tariff > 0
                    and (pe.term_fk in (1, 2, 4)
                        or (
                            (pe.term_fk = 3 and
                                (select count(ps2.id_pk)
                                FROM provided_service ps2
                                    join medical_service ms2 on ms2.id_pk = ps2.code_fk
                                WHERE ps2.event_fk = ps.event_fk
                                    and (ms2.group_fk is NULL or ms2.group_fk = 24)
                                    and ms2.reason_fk = 1
                                ) > 1
                            )
                        )
                    )
                group by 1
        )

        select all_data.event_1 as event_id,
            mo.name as mo_name,
            case when pe.term_fk in (1, 2) then 'Стационар, днев. стационар' when pe.term_fk = 3 Then 'Поликлиника' when pe.term_fk = 4 Then 'Скорая помощь' END as term_name,
            dep.old_code as department,
            mr.organization_code,
            ms.code as service_code,
            md.code as division_code,
            trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number)) as policy,
            p.last_name,
            p.first_name,
            p.middle_name,
            p.birthdate,
            p.gender_fk as gender_code,
            idc.idc_code as disease,
            pecd_idc.idc_code as concomitant_disease,
            pe.anamnesis_number,
            ps.start_date,
            ps.end_date,
            pe.start_date AS event_start_date,
            pe.end_date AS event_end_date,
            ps.quantity,
            ps.accepted_payment,
            ps.comment,
            COALESCE(pe.hospitalization_fk, 0) as hospitalization_code,
            pe.worker_code,
            tro.code as outcome_code,
            concat_ws(', ', COALESCE(aa2.name, ''), Coalesce(aa1.name, ''), COALESCE(aa.name, ''),
            coalesce(adr.street, ''), coalesce(adr.house_number, ''),
            COALESCE(adr.extra_number, ''), coalesce(adr.room_number)) as address,
            case ps.payment_kind_fk when 2 then 'P' else 'T' END as funding_type,
            mr.period,
            ps.id_pk as service_id,
            pe.term_fk AS event_term,
            0 as sort
        from all_data
            join provided_event pe
                on pe.id_pk = all_data.event_1
            JOIN provided_service ps
                on ps.event_fk = pe.id_pk
            LEFT JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk
            JOIN insurance_policy ip
                on ip.version_id_pk = p.insurance_policy_fk
            JOIN medical_organization mo
                on mo.code = mr.organization_code and mo.parent_fk is null
            JOIN medical_organization dep
                on dep.id_pk = ps.department_fk
            LEFT JOIN medical_division md
                on ps.division_fk = md.id_pk
            LEFT JOIN provided_event_concomitant_disease pecd
                on pecd.event_fk = pe.id_pk
            LEFT JOIN idc pecd_idc
                on pecd.disease_fk = pecd_idc.id_pk
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
        WHERE ms.code not like 'A%%'

        union

        select all_data.event_2 as event_id,
            mo.name as mo_name,
            case when pe.term_fk in (1, 2) then 'Стационар, днев. стационар' when pe.term_fk = 3 Then 'Поликлиника' when pe.term_fk = 4 Then 'Скорая помощь' END as term_name,
            dep.old_code as department,
            mr.organization_code,
            ms.code as service_code,
            md.code as division_code,
            trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number)) as policy,
            p.last_name,
            p.first_name,
            p.middle_name,
            p.birthdate,
            p.gender_fk as gender_code,
            idc.idc_code as disease,
            pecd_idc.idc_code as concomitant_disease,
            pe.anamnesis_number,
            ps.start_date,
            ps.end_date,
            pe.start_date AS event_start_date,
            pe.end_date AS event_end_date,
            ps.quantity,
            ps.accepted_payment,
            ps.comment,
            COALESCE(pe.hospitalization_fk, 0) as hospitalization_code,
            pe.worker_code,
            tro.code as outcome_code,
            concat_ws(', ', COALESCE(aa2.name, ''), Coalesce(aa1.name, ''), COALESCE(aa.name, ''),
            coalesce(adr.street, ''), coalesce(adr.house_number, ''),
            COALESCE(adr.extra_number, ''), coalesce(adr.room_number)) as address,
            case ps.payment_kind_fk when 2 then 'P' else 'T' END as funding_type,
            mr.period,
            ps.id_pk as service_id,
            pe.term_fk AS event_term,
            1 as sort
        from all_data
            join provided_event pe
                on pe.id_pk = all_data.event_2 and pe.id_pk NOT IN (SELECT DISTINCT event_1 from all_data)
            JOIN provided_service ps
                on ps.event_fk = pe.id_pk
            LEFT JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk
            JOIN insurance_policy ip
                on ip.version_id_pk = p.insurance_policy_fk
            JOIN medical_organization mo
                on mo.code = mr.organization_code and mo.parent_fk is null
            JOIN medical_organization dep
                on dep.id_pk = ps.department_fk
            LEFT JOIN medical_division md
                on ps.division_fk = md.id_pk
            LEFT JOIN provided_event_concomitant_disease pecd
                on pecd.event_fk = pe.id_pk
            LEFT JOIN idc pecd_idc
                on pecd.disease_fk = pecd_idc.id_pk
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
        WHERE ms.code not like 'A%%'
        '''
        return query

    def get_dbf_struct(self):
        return {
            'path': u'C:/work/REPEATED_DBF',
            'order_fields': ('last_name', 'first_name', 'middle_name', 'birthdate', 'sort'),
            'stop_fields': ('department', 'term_name'),
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
                ("IDCASE", "C", 16),
                ("IDSERV", "C", 16),
                ("ISREPEATED", "N", 2),
            ),
            'file_pattern': 't%s - %s'
            }

    def get_excel_struct(self):
        return {
            'path': u'C:/work/REPEATED',
            'order_fields': ('last_name', 'first_name', 'middle_name', 'birthdate', 'sort'),
            'stop_fields': ('mo_name', 'term_name'),
            'titles': [
                u'МО', u'Подразделение', u'Условия', u'Фамилия', u'Имя', u'Отчество',
                u'ДР',  u'Услуга', u'Код диагноза', u'Оплачено',
                u'Начало услуги', u'Окончание услуги', u'Начало случая',
                u'Окончание случая', u'Повтор', u'Период'
            ],
            'file_pattern': '%s %s'
        }

    def get_statistic_param(self):
        return {'group_by': ['mo_name', 'event_term'], 'field': 'event_id', 'filter': 'sort == 0'}

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
        new["DS"] = unicode_to_cp866(item['disease'])
        new["DS2"] = unicode_to_cp866(item['concomitant_disease'])
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
        new["IDCASE"] = item['event_id'] or ''
        new["IDSERV"] = item['service_id'] or ''
        new["ISREPEATED"] = int(not bool(item.get('sort')))
        new.store()

    def print_item_excel(self, sheet, item):
        sheet.write(item['mo_name'], 'c')
        sheet.write(item['department'], 'c')
        sheet.write(item['term_name'], 'c')
        sheet.write(item['last_name'], 'c')
        sheet.write(item['first_name'], 'c')
        sheet.write(item['middle_name'], 'c')
        sheet.write(item['birthdate'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['service_code'], 'c')
        sheet.write(item['disease'], 'c')
        sheet.write(item['accepted_payment'], 'c')
        sheet.write(item['start_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['end_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['event_start_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['event_end_date'].strftime('%d.%m.%Y'), 'c')
        sheet.write(item['sort'], 'c')
        sheet.write(item['period'], 'r')
