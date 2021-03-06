#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866
from medical_service_register.path import DEVELOP_REPAID_BY_DEATH, DEVELOP_REPAID_BY_DEATH_DBF, \
    PRODUCTION_REPAID_BY_DEATH,  PRODUCTION_REPAID_BY_DEATH_DBF


class RepaidByDeath(FilterReportPage):
    """
    Выборка умерших застрахованных с услугами, которые им были оказаны за год
    """

    def __init__(self):
        super(RepaidByDeath, self).__init__()

    def get_query(self):
        query = '''
             WITH dates AS (
                select format('%%s-%%s-01', %(year)s, %(period)s)::DATE AS start_date
                    ),
             dead_people AS (

        select
        up.person_unique_id AS person_unique_id,
        up.last_name as fam,
        up.first_name as im,
        up.middle_name as ot,
        up.birthdate as birth_date,
        up.deathdate as death_date,
        up.address AS address,
        att_org.name AS last_attachment_mo,
        'new_base' AS data_base_name
        from uploading_person up
        join uploading_policy u_pol ON u_pol.uploading_person_fk = up.id_pk
        left join uploading_attachment ua ON ua.id_pk = (
           select ua1.id_pk from uploading_attachment ua1 where ua1.id = up.id
           order by start_date desc
           limit 1
        )
        left join medical_organization att_org ON att_org.id_pk = ua.organization_fk
        where u_pol.processing_stop_file_date between (select start_date from dates) and (select start_date from dates) + INTERVAL '1 months' - INTERVAL '1 days' and u_pol.stop_reason = 1
              and (
                select count(distinct p.person_unique_id)
                from provided_service ps
                    JOIN medical_service ms
                    on ms.id_pk = ps.code_fk
                    join provided_event pe
                    on ps.event_fk = pe.id_pk
                    JOIN medical_register_record mrr
                    on mrr.id_pk = pe.record_fk
                    JOIN medical_register mr
                    on mr.id_pk = mrr.register_fk
                    JOIN patient p
                    on p.id_pk = mrr.patient_fk
                    JOIN idc ON idc.id_pk = ps.basic_disease_fk
                WHERE  mr.is_active
                    and format('%%s-%%s-01', mr.year, mr.period)::DATE <= (select start_date from dates)
                    and format('%%s-%%s-01', mr.year, mr.period)::DATE >= (select start_date from dates) - interval '12 months'
                    AND ((pe.term_fk IN (1, 2) AND pe.treatment_result_fk IN (5, 6, 15, 16))
                    or (pe.term_fk = 4 AND (idc.name ILIKE '%%смерт%%' OR idc.name ILIKE '%%остан%%' OR idc.name ILIKE '%%летал%%') and idc.idc_code not in ('I46.0', 'K02.3', 'T75.1')))
                    AND ps.payment_type_fk = 2
                    and p.person_unique_id = up.person_unique_id
                ) = 0
        )
        select  ps.id_pk,
            p.person_unique_id,
            dp.last_attachment_mo AS last_attachment_mo,
            dp.fam AS person_lastname,
            dp.im AS person_firstname,
            dp.ot AS person_middlename,
            dp.birth_date AS person_birthdate,
            dp.death_date AS person_deathdate,
            trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) AS patient_policy,
            mr.period as period,
            mr.organization_code AS organization_code,
            ms.code AS service_code,
            ps.start_date as service_startdate,
            ps.end_date as service_enddate,
            md.name as service_division,
            pe.anamnesis_number AS anamnesis_number,
            idc.idc_code AS basic_disease,
            idc.name AS basic_disease_name,
            ps.quantity AS service_quantity,
            (case ps.payment_type_fk when 2 then ps.accepted_payment else 0 end) AS accepted_payment,
            ps.tariff AS tariff,
            (case ps.payment_type_fk WHEN 2 THEN '' ELSE array_to_string(ARRAY(
                select DISTINCT me.old_code
                from provided_service_sanction pss
                join medical_error me
                    on me.id_pk = pss.error_fk
                WHERE
                pss.service_fk = ps.id_pk and pss.is_active
                and pss.type_fk = 1
            ), ' ') END ) AS errors,
            case when ms.group_fk = 19 and ms.subgroup_fk is null then ms.uet else 0 end as uet,
            dep.old_code AS department,
            dep.name AS department_name,
            mo.name AS mo_name,
            tr.name AS treatment_result,
            case ps.payment_kind_fk when 2 then 'P' else 'T' END as funding_type,
            p.gender_fk as gender_code,
            tro.code as outcome_code,
            coalesce(pe.hospitalization_fk, 0) as hospitalization_code,
            pe.worker_code
            from
            provided_service ps
            JOIN provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN medical_organization dep
                on dep.id_pk = ps.department_fk
            JOIN medical_register_status mrs
                on mrs.id_pk = mr.status_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN medical_division md
                on md.id_pk = ps.division_fk
            LEFT JOIN medical_service_profile msp
                on msp.id_pk = ps.profile_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk
            left join medical_service_term mst
                on mst.id_pk = pe.term_fk
            LEFT join treatment_result tr
                on tr.id_pk = pe.treatment_result_fk

            LEFT JOIN treatment_outcome tro
                on tro.id_pk = pe.treatment_outcome_fk

            JOIN medical_organization mo
                on mo.code = mr.organization_code and mo.parent_fk is null

            LEFT JOIN idc idc1
                on idc1.id_pk = pe.initial_disease_fk
            LEFT JOIN idc idc2
                on idc2.id_pk = pe.basic_disease_fk

            JOIN dead_people dp ON dp.person_unique_id = p.person_unique_id
            where mr.is_active
                  and pe.term_fk = 3 and (ms.group_fk is null or ms.group_fk in (24, 44, 29, 41))
                  and format('%%s-%%s-01', mr.year, mr.period)::DATE < (select start_date from dates)
                  and format('%%s-%%s-01', mr.year, mr.period)::DATE >= (select start_date from dates) - interval '12 months'
                  order by p.person_unique_id, ps.start_date DESC
            '''
        return query

    def prepare_data(self, data):
        """
        Отрезает лишние экспертизы
        """
        check_repeated = {}
        for item in data:
            unique_hash = item['person_unique_id']
            if unique_hash not in check_repeated:
                check_repeated[unique_hash] = item
            else:
                saved_value = check_repeated[unique_hash]
                if saved_value['service_startdate'] < item['service_startdate'] and item['tariff'] > 0:
                    check_repeated[unique_hash] = item

        valid_data = []
        for unique_hash in check_repeated:
            valid_data.append(check_repeated[unique_hash])
        return valid_data

    def get_dbf_struct(self):
        return {
            'dev_path': DEVELOP_REPAID_BY_DEATH_DBF,
            'prod_path': PRODUCTION_REPAID_BY_DEATH_DBF,
            'order_fields': ('person_lastname', 'person_firstname', 'person_middlename', 'person_birthdate'),
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
                ("OUTCOME", "C", 3),),
            'file_pattern': 't%s'
        }

    def get_excel_struct(self):
        if self.prepare_data_mode:
            return {
                'dev_path': DEVELOP_REPAID_BY_DEATH,
                'prod_path': PRODUCTION_REPAID_BY_DEATH,
                'order_fields': ('person_lastname', 'person_firstname', 'person_middlename', 'person_birthdate'),
                'stop_fields': ('last_attachment_mo', ),
                'titles': [
                    u'Фамилия', u'Имя', u'Отчество',
                    u'Дата рождения', u'Дата смерти', u'Полис',
                    u'Код услуги',
                    u'Отделение', u'Номер карты', u'Диагноз',
                    u'Наименование диагноза'
                ],
                'file_pattern': '%s'
            }
        else:
            return {
                'dev_path': DEVELOP_REPAID_BY_DEATH,
                'prod_path': PRODUCTION_REPAID_BY_DEATH,
                'order_fields': ('person_lastname', 'person_firstname', 'person_middlename', 'person_birthdate'),
                'stop_fields': ('last_attachment_mo', ),
                'titles': [
                    u'Фамилия', u'Имя', u'Отчество',
                    u'Дата рождения', u'Дата смерти', u'Полис',
                    u'Прикрепление', u'Период лечения',
                    u'Код услуги', u'Дата начала', u'Дата окончания',
                    u'Отделение', u'Номер карты', u'Диагноз',
                    u'Наименование диагноза', u'Койко-дней', u'Принято к оплате',
                    u'Тариф', u'Ошибки', u'УЕТ', u'ЛПУ',
                    u'ЛПУ наименование', u'Результат обращения'
                ],
                'file_pattern': '%s'
            }

    def get_statistic_param(self):
        pass

    def print_item_dbf(self, db, item):
        new = db.newRecord()
        new["COD"] = unicode_to_cp866(item['service_code'])
        new["OTD"] = item.get('division_code', '000')
        new["ERR_ALL"] = ''
        new["SN_POL"] = unicode_to_cp866(item['patient_policy'])
        new["FAM"] = unicode_to_cp866(item.get('person_lastname', ''))
        new["IM"] = unicode_to_cp866(item.get('person_firstname', ''))
        new["OT"] = unicode_to_cp866(item.get('person_middlename', ''))
        new["DR"] = item.get('person_birthdate', '1900-01-01')
        new["DS"] = unicode_to_cp866(item['basic_disease'])
        new["C_I"] = unicode_to_cp866(item.get('anamnesis_number', ''))
        new["D_BEG"] = item.get('service_startdate', '1900-01-01')
        new["D_U"] = item.get('service_enddate', '1900-01-01')
        new["K_U"] = item.get('service_quantity', 0)
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
        if self.prepare_data_mode:
            sheet.write(item['person_lastname'], 'c')
            sheet.write(item['person_firstname'], 'c')
            sheet.write(item['person_middlename'], 'c')
            sheet.write(item['person_birthdate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['person_deathdate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['patient_policy'], 'c')
            sheet.write(item['service_code'], 'c')
            sheet.write(item['service_division'], 'c')
            sheet.write(item['anamnesis_number'], 'c')
            sheet.write(item['basic_disease'], 'c')
            sheet.write(item['basic_disease_name'], 'r')
        else:
            sheet.write(item['person_lastname'], 'c')
            sheet.write(item['person_firstname'], 'c')
            sheet.write(item['person_middlename'], 'c')
            sheet.write(item['person_birthdate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['person_deathdate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['patient_policy'], 'c')
            sheet.write(item['last_attachment_mo'], 'c')
            sheet.write(item['period'], 'c')
            sheet.write(item['service_code'], 'c')
            sheet.write(item['service_startdate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['service_enddate'].strftime('%d.%m.%Y'), 'c')
            sheet.write(item['service_division'], 'c')
            sheet.write(item['anamnesis_number'], 'c')
            sheet.write(item['basic_disease'], 'c')
            sheet.write(item['basic_disease_name'], 'c')
            sheet.write(item['service_quantity'], 'c')
            sheet.write(item['accepted_payment'], 'c')
            sheet.write(item['tariff'], 'c')
            sheet.write(item['errors'], 'c')
            sheet.write(item['uet'], 'c')
            sheet.write(item['department'], 'c')
            sheet.write(item['department_name'], 'c')
            sheet.write(item['treatment_result'], 'r')
