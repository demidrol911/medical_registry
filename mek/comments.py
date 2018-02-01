# -*- coding: utf-8 -*-

from django.db import connection, transaction


def comment_not_active_policy(register_element):
    query = """
          update provided_service_sanction set comment = 'полис погашен ' || to_char(T.stop_date, 'YYYY-MM-DD')
          from (
                select
                    pss.id_pk, u_pol.stop_date
                    from medical_register mr
                    JOIN medical_register_record mrr
                          ON mr.id_pk=mrr.register_fk
                    JOIN provided_event pe
                          ON mrr.id_pk=pe.record_fk
                    JOIN provided_service ps
                          ON ps.event_fk=pe.id_pk
                    join patient p ON p.id_pk = mrr.patient_fk
                    join uploading_policy u_pol ON u_pol.id_pk = p.insurance_policy_fk and ps.start_date > u_pol.stop_date
                    join provided_service_sanction pss ON pss.service_fk = ps.id_pk and pss.error_fk = 54
                    where mr.is_active
                          and mr.year = %s
                          and mr.period = %s
                          and mr.organization_code = %s
                          and ps.payment_type_fk = 3

                ) AS T
          where T.id_pk = provided_service_sanction.id_pk
    """
    cursor = connection.cursor()
    cursor.execute(query, [register_element['year'],
                           register_element['period'],
                           register_element['organization_code']])
    transaction.commit()

    cursor.close()