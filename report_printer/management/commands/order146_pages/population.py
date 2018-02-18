#! -*- coding: utf-8 -*-
from general import MedicalServiceTypePage


class PopulationMedicalExamPage(MedicalServiceTypePage):
    """
    Лист принятых пациентов по диспансеризациям и профосмотрам
    """

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = '''
                    SELECT
                    mo.code AS mo_code, '0' AS group_field, count(distinct ip.id) AS count_patients
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
                        JOIN insurance_policy ip ON ip.version_id_pk = pt.insurance_policy_fk
                        WHERE mr.is_active
                            AND mr.year = '2015'
                            AND ps.payment_type_fk = 2
                            AND ms.group_fk = 9

                GROUP BY mo_code, group_field
                '''
        return query

    def get_output_order_fields(self):
        return ('0', 3, ('count_patients',)),