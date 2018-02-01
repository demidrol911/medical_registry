from django.db import connection, transaction


def update_wrong_accepted_payment(register_element):
    query = """
        update provided_service set accepted_payment = T.tariff
        from (
        select
            ps.id_pk AS service_id, ps.tariff
            from medical_register mr
            JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
            where mr.is_active
                  AND mr.year = %(year)s
                  AND mr.period = %(period)s
                  AND mr.organization_code = %(organization)s
                  and ps.payment_type_fk = 2
                  and pe.term_fk in (1, 2)
                  and ps.tariff != ps.accepted_payment
                  and abs(ps.tariff - ps.accepted_payment) <= 0.01
              ) AS T
              where T.service_id = id_pk
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


def update_wrong_invoiced_payment(register_element):
    query = """
        update provided_service set invoiced_payment = T.accepted_payment
        from (
        select
            ps.id_pk AS service_id, ps.accepted_payment
            from medical_register mr
            JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
            where mr.is_active
                  AND mr.year = %(year)s
                  AND mr.period = %(period)s
                  AND mr.organization_code = %(organization)s
                  and ps.payment_type_fk = 2
                  and pe.term_fk in (1, 2)
                  and ps.invoiced_payment != ps.accepted_payment
                  and abs(ps.invoiced_payment - ps.accepted_payment) <= 0.01
              ) AS T
              where T.service_id = id_pk
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


def update_accepted_payment_non_payment_services(register_element):
    query = """
        update provided_service set accepted_payment = 0
        where id_pk in (
        select
            ps.id_pk AS service_id
            from medical_register mr
            JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
            JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
            where mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
                AND mr.organization_code = %(organization)s
                and ps.payment_type_fk = 3
        )
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()


def update_payment_type_services_operations(register_element):
    query = """
           update provided_service set payment_type_fk = 2
           where id_pk in (
           select ps1.id_pk
           from (
           select

                pe.id_pk AS event_id,
                count(CASE WHEN ms.group_fk = 27 and ps.payment_type_fk = 3 THEN ps.id_pk END) AS op_count,
                count(CASE WHEN ps.accepted_payment > 0 and ps.payment_type_fk = 2 THEN ps.id_pk END) tariff_count
                from medical_register mr
                JOIN medical_register_record mrr
                  ON mr.id_pk=mrr.register_fk
                JOIN provided_event pe
                  ON mrr.id_pk=pe.record_fk
                JOIN provided_service ps
                  ON ps.event_fk=pe.id_pk
                JOIN medical_organization mo
                  ON mo.id_pk = ps.organization_fk
                join medical_service ms ON ms.id_pk = ps.code_fk
                where mr.is_active
                    AND mr.year = %(year)s
                    AND mr.period = %(period)s
                    AND mr.organization_code = %(organization)s
                    and pe.term_fk in (1, 2)
                    group by 1
           ) AS T
           join provided_service ps1 ON ps1.event_fk = T.event_id and ps1.payment_type_fk = 3
           join medical_service ms1 ON ms1.id_pk = ps1.code_fk and ms1.group_fk = 27
           join provided_service_sanction pss ON pss.service_fk = ps1.id_pk
           where T.op_count > 0 and T.tariff_count > 0
           order by ps1.id_pk)
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(
        year=register_element['year'], period=register_element['period'],
        organization=register_element['organization_code']))

    transaction.commit()
    cursor.close()