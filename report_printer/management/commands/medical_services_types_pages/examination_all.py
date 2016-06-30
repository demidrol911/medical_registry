#! -*- coding: utf-8 -*-

from general import MedicalServiceTypePage


class ExaminationAllPage(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = '''
             WITH registry_services AS (
                    SELECT
                        pt.gender_fk AS patient_gender,
                        pe.term_fk AS service_term,
                        ms.tariff_profile_fk AS service_tariff_profile,
                        ms.reason_fk AS service_reason,
                        ms.division_fk AS service_division,
                        ms.group_fk AS service_group,
                        ms.subgroup_fk AS service_subgroup,
                        ms.code ILIKE '0%%' AS is_adult,
                        ms.code AS service_code,
                        ms.examination_primary,

                        CASE WHEN ms.group_fk = 19
                               THEN ms.uet * ps.quantity
                             ELSE ps.quantity
                        END AS service_quantity,

                        CASE WHEN (pe.term_fk = 3 AND ps.payment_kind_fk = 2) OR pe.term_fk = 4
                               THEN True
                             ELSE False
                        END AS is_capitation,

                        ps.id_pk AS service_id,
                        pe.id_pk AS event_id,
                        ROUND(ps.tariff, 2) AS service_tariff,
                        ROUND(ps.accepted_payment, 2) AS service_accepted,
                        ROUND(ps.calculated_payment, 2) AS service_calculated,
                        ROUND(ps.invoiced_payment, 2) AS service_invoiced,
                        mr.organization_code AS mo_code,
                        pt.id_pk AS patient_id,
                        ps.start_date AS service_start_date,
                        ps.end_date AS service_end_date,
                        pe.end_date AS event_end_date,
                        pe.division_fk AS event_division_id,

                        CASE WHEN pe.term_fk = 3
                              AND ms.reason_fk = 1
                              AND (ms.group_fk = 24 OR ms.group_fk IS NULL)
                              AND (SELECT
                                  COUNT(DISTINCT inner_ps.id_pk)
                                  FROM provided_service inner_ps
                                  JOIN medical_service inner_ms
                                     ON inner_ms.id_pk = inner_ps.code_fk
                                  WHERE
                                 inner_ps.event_fk = pe.id_pk
                                 AND (inner_ms.group_fk is NULL
                                      OR inner_ms.group_fk in (24))
                                 AND inner_ms.reason_fk = 1
                               )=1 THEN 'поликлиника разовые'
                        WHEN (pe.term_fk = 3
                                    AND ms.reason_fk IN (2, 3, 8)
                                    AND (ms.group_fk = 24 OR ms.group_fk IS NULL))
                                    OR (ms.group_fk = 9 AND ms.code IN ('019214', '019215', '019216', '019217'))
                                    OR ms.group_fk = 4 THEN 'поликлиника'
                                 WHEN  ms.group_fk = 7 THEN 'диспансеризация 1 этап'
                                 WHEN  ms.group_fk IN (25, 26) THEN  'диспансеризация 2 этап'
                                 WHEN  ms.group_fk = 12 and (ms.examination_primary = True or ms.subgroup_fk = 9) THEN 'в трудной жизненной ситуации'
                                 when  ms.group_fk = 13 and (ms.examination_primary = True or ms.subgroup_fk = 10) THEN 'без попечения родителей'
                                 when  ms.group_fk = 16 and ms.examination_primary = True THEN 'периодический'
                                 when  ms.group_fk = 15 and (ms.examination_primary = True or ms.subgroup_fk = 11) THEN 'предварительный'
                                 when  ms.group_fk = 11 and (ms.examination_primary = True or ms.subgroup_fk = 8) THEN 'профилактический'
                        END AS group_label

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
                        JOIN patient pt
                           ON pt.id_pk = mrr.patient_fk
                        WHERE mr.is_active
                            AND mr.period = %(period)s
                            AND mr.year = %(year)s
                            and ps.payment_type_fk = 2
                            AND (ms.group_fk != 27 OR ms.group_fk is NULL)
                )
                SELECT
                    mo_code AS mo_code,

                    '0' AS group_field,

                    count(distinct CASE WHEN  group_label = 'поликлиника разовые'  THEN patient_id END)  +
                    count(distinct CASE WHEN group_label = 'поликлиника' THEN patient_id  END) +
                    count(distinct CASE WHEN  group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'диспансеризация 2 этап' THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'в трудной жизненной ситуации' THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'без попечения родителей' THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'периодический' THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'предварительный' THEN patient_id END) +
                    count(distinct CASE WHEN group_label = 'профилактический' THEN patient_id END) AS count_patients,

                    count(distinct CASE WHEN is_adult and group_label = 'поликлиника разовые'  THEN patient_id END) +
                    count(distinct CASE WHEN  is_adult and group_label = 'поликлиника' THEN  patient_id END) +
                    count(distinct CASE WHEN  is_adult and group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'диспансеризация 2 этап' THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'в трудной жизненной ситуации' THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'без попечения родителей' THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'периодический' THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'предварительный' THEN patient_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'профилактический' THEN patient_id END) AS count_patients_adult,


                    count(distinct CASE WHEN not is_adult and group_label = 'поликлиника разовые'  THEN patient_id END) +
                    count(distinct CASE WHEN not is_adult and group_label = 'поликлиника' THEN  patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'диспансеризация 2 этап' THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'в трудной жизненной ситуации' THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'без попечения родителей' THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'периодический' THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'предварительный' THEN patient_id END) +
                    count(distinct CASE WHEN NOT is_adult and group_label = 'профилактический' THEN patient_id END) AS count_patients_child,


                    count(distinct CASE WHEN  group_label = 'поликлиника разовые'  THEN service_id END)  +
                    count(distinct CASE WHEN group_label = 'поликлиника' THEN service_id END) +
                    count(distinct CASE WHEN  group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'диспансеризация 2 этап' THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'в трудной жизненной ситуации' THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'без попечения родителей' THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'периодический' THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'предварительный' THEN service_id END) +
                    count(distinct CASE WHEN group_label = 'профилактический' THEN service_id END) AS count_services,


                    count(distinct CASE WHEN  is_adult and group_label = 'поликлиника разовые'  THEN service_id END)  +
                    count(distinct CASE WHEN is_adult and group_label = 'поликлиника' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'диспансеризация 2 этап' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'в трудной жизненной ситуации' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'без попечения родителей' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'периодический' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'предварительный' THEN service_id END) +
                    count(distinct CASE WHEN is_adult and group_label = 'профилактический' THEN service_id END)
                    as count_services_adult,


                    count(distinct CASE WHEN not is_adult and group_label = 'поликлиника разовые'  THEN service_id END)  +
                    count(distinct CASE WHEN not  is_adult and group_label = 'поликлиника' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and  group_label = 'диспансеризация 1 этап'
                                                  and service_code in ('019021', '019023', '019022', '019024', '019002') THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'диспансеризация 2 этап' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'в трудной жизненной ситуации' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'без попечения родителей' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'периодический' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'предварительный' THEN service_id END) +
                    count(distinct CASE WHEN not  is_adult and group_label = 'профилактический' THEN service_id END)
                    AS count_services_child,

                    SUM(CASE WHEN is_capitation THEN 0 ELSE service_invoiced END) AS total_invoiced,
                    SUM(CASE WHEN is_adult THEN (CASE WHEN is_capitation THEN 0 ELSE service_invoiced END) ELSE 0 END) AS total_invoiced_adult,
                    SUM(CASE WHEN not is_adult THEN (CASE WHEN is_capitation THEN 0 ELSE service_invoiced END) ELSE 0 END) AS total_invoiced_child


                FROM registry_services
                where group_label is not null

                GROUP BY mo_code
                order by mo_code
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 2, ('count_patients',
                         'count_patients_adult',
                         'count_patients_child',

                         'count_services',
                         'count_services_adult',
                         'count_services_child',

                         'total_invoiced',
                         'total_invoiced_adult',
                         'total_invoiced_child')),

