#! -*- coding: utf-8 -*-
from report_printer.libs.page import FilterReportPage
from main.funcs import unicode_to_cp866
from report_printer.management.commands.targeted_expertise_pages.dead_result_patient import DeadResultPatient
from medical_service_register.path import DEVELOP_AMB_DEAD_PATIENT, DEVELOP_AMB_DEAD_PATIENT_DBF, \
    PRODUCTION_AMB_DEAD_PATIENT, PRODUCTION_AMB_DEAD_PATIENT_DBF


class AmbulanceDeadPatient(DeadResultPatient):
    """
    Выборка летальных случаев по скорой помощи
    по диагнозу
    """

    def __init__(self):
        super(AmbulanceDeadPatient, self).__init__()

    def get_query(self):
        query = '''
        SELECT DISTINCT
            mo.name AS mo_name,
            mr.period AS period,
            dep.old_code AS department,
            ms.code AS service_code,
            md.code AS division_code,
            md.name AS division_name,
            (CASE ps.payment_type_fk WHEN 2 THEN '' ELSE array_to_string(ARRAY(
                SELECT DISTINCT me.old_code
                FROM provided_service_sanction pss
                    JOIN medical_error me
                        ON me.id_pk = pss.error_fk
                WHERE
                    pss.service_fk = ps.id_pk AND pss.is_active
                    AND pss.type_fk = 1
            ), ' ') END ) AS errors,
            trim(format('%%s %%s', p.insurance_policy_series, p.insurance_policy_number)) AS policy,
            p.last_name AS last_name,
            p.first_name AS first_name,
            p.middle_name AS middle_name,
            p.birthdate AS birthdate,
            p.gender_fk AS gender_code,
            idc.idc_code AS basic_disease_code,
            idc.name AS basic_disease_name,
            array_to_string(ARRAY(
                    SELECT DISTINCT pecd_idc.idc_code
                    FROM provided_event_concomitant_disease pecd
                        JOIN idc pecd_idc ON pecd.disease_fk = pecd_idc.id_pk
                    WHERE
                        pecd.event_fk = pe.id_pk
                ), ' ') AS concomitant_disease,
            pe.anamnesis_number AS anamnesis_number,
            ps.start_date AS start_date,
            ps.end_date AS end_date,
            ps.quantity AS quantity,
            (CASE ps.payment_type_fk WHEN 2 THEN ps.accepted_payment ELSE 0 END) AS accepted_payment,
            ps.tariff AS tariff,
            ps.comment,
            pe.hospitalization_fk AS hospitalization_code,
            pe.worker_code,
            tro.code AS outcome_code,
            tr.name AS treatment_result_name,
            CASE WHEN aa2.name IS NULL AND aa1.name IS NULL AND aa.name IS NULL
                          AND adr.street IS NULL AND adr.house_number IS NULL
                          AND adr.extra_number IS NULL AND adr.room_number IS NULL THEN up.address
                     ELSE concat_ws(', ', COALESCE(aa2.name, ''), COALESCE(aa1.name, ''),
                               COALESCE(aa.name, ''), COALESCE(adr.street, ''),
                               COALESCE(adr.house_number, ''), COALESCE(adr.extra_number, ''),
                               COALESCE(adr.room_number))
                END AS address,
            CASE ps.payment_kind_fk WHEN 2 THEN 'P' ELSE 'T' END AS funding_type,
            COALESCE(ms.uet, 0) AS uet,
            pe.id_pk AS event_id,
            pe.term_fk AS event_term,
            mr.organization_code AS organization_code,
            pe.id AS event_mo_id
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
            LEFT join treatment_result tr
                ON tr.id_pk = pe.treatment_result_fk
            LEFT JOIN address adr
                ON adr.person_fk = per.version_id_pk AND adr.type_fk = 1
            LEFT JOIN administrative_area aa
                ON aa.id_pk = adr.administrative_area_fk
            LEFT join administrative_area aa1
                ON aa1.id_pk = aa.parent_fk
            LEFT join administrative_area aa2
                ON aa2.id_pk = aa1.parent_fk
            LEFT JOIN uploading_person up ON up.id_pk = (
               SELECT MAX(id_pk)
               FROM uploading_person
               WHERE person_unique_id = p.person_unique_id
            )
        WHERE mr.is_active
            AND mr.year = %(year)s
            AND mr.period = %(period)s
            AND pe.term_fk = 4
            AND (idc.name ILIKE '%%смерт%%' OR idc.name ILIKE '%%остан%%' OR idc.name ILIKE '%%летал%%') and idc.idc_code not in ('I46.0', 'K02.3', 'T75.1', 'P95')
            AND ps.payment_type_fk = 2
            AND ms.code NOT LIKE 'A%%'
        '''
        return query

    def get_dbf_struct(self):
        return {
            'dev_path': DEVELOP_AMB_DEAD_PATIENT_DBF,
            'prod_path': PRODUCTION_AMB_DEAD_PATIENT_DBF,
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
        return {
            'dev_path': DEVELOP_AMB_DEAD_PATIENT,
            'prod_path': PRODUCTION_AMB_DEAD_PATIENT,
            'order_fields': ('last_name', 'first_name', 'middle_name'),
            'stop_fields': ('mo_name', ),
            'titles': [
                u'', u'Подразделение', u'Фамилия', u'Имя', u'Отчество', u'ДР',
                u'Полис', u'Начало', u'Окончание', u'Отделение', u'Услуга',
                u'Номер карты', u'Код диагноза', u'Диагноз', u'Кол-во',
                u'Оплачено', u'Тариф', u'Ошибки', u'УЕТ', u'Результат', u'IDCASE'
            ],
            'file_pattern': '%s'
        }