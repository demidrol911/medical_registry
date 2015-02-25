#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from report_printer.management.commands.term_fond.func import print_act, DIVISION_ALL_1_2


### Стоматология
def stomatology():
    """
    Стоматология
    """
    title = u'Стоматология'
    pattern = 'stomatology'
    query = """
            select
            mo.code as mo,
            ms.subgroup_fk AS division,

            count(DISTINCT mrr.patient_fk) AS patient,
            count(distinct CASE WHEN ms.code ilike '0%' THEN mrr.patient_fk END) AS patinet_adult,
            count(distinct CASE WHEN ms.code ilike '1%' THEN mrr.patient_fk END) AS patinet_child,

            count(Distinct CASE WHEN ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment,
            count(distinct CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_adult,
            count(distinct CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 12 THEN ps.event_fk END) AS treatment_child,

            count(CASE WHEN ms.subgroup_fk is NOT NULL then ps.id_pk END) AS service,
            count(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_adult,
            count(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk is not null THEN ps.id_pk END) AS service_child,

            sum((SELECT sum(ps1.quantity*ms1.uet)
                      from provided_service ps1
                           join medical_service ms1 on ms1.id_pk = ps1.code_fk
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                    ) AS quantity,
            sum(CASE WHEN ms.code ilike '0%'
                      THEN (SELECT sum(ps1.quantity*ms1.uet)
                      from provided_service ps1
                           join medical_service ms1 on ms1.id_pk = ps1.code_fk
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS quantity_adult,
            sum(CASE WHEN ms.code ilike '1%'
                      THEN (SELECT sum(ps1.quantity*ms1.uet)
                      from provided_service ps1
                           join medical_service ms1 on ms1.id_pk = ps1.code_fk
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS quantity_child,

            sum((SELECT sum(ps1.tariff)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                     ) AS tariff,
             sum(CASE WHEN ms.code ilike '0%'
                      THEN (SELECT sum(ps1.tariff)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS tariff_adult,
             sum(CASE WHEN ms.code ilike '1%'
                      THEN (SELECT sum(ps1.tariff)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS tariff_child,


            sum(CASE WHEN ms.subgroup_fk = 17
                      THEN (SELECT sum(ps1.tariff*0.2)
                      from provided_service ps1
                           join provided_service_coefficient psc
                               on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END),
            sum(CASE WHEN ms.code ilike '0%' and ms.subgroup_fk = 17
                      THEN (SELECT sum(ps1.tariff*0.2)
                      from provided_service ps1
                           join provided_service_coefficient psc
                               on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END),
            sum(CASE WHEN ms.code ilike '1%' and ms.subgroup_fk = 17
                      THEN (SELECT sum(ps1.tariff*0.2)
                      from provided_service ps1
                           join provided_service_coefficient psc
                               on ps1.id_pk = psc.service_fk and psc.coefficient_fk = 4
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END),

              sum((SELECT sum(ps1.accepted_payment)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                     ) AS accepted_payment,
             sum(CASE WHEN ms.code ilike '0%'
                      THEN (SELECT sum(ps1.accepted_payment)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS accepted_payment_adult,
             sum(CASE WHEN ms.code ilike '1%'
                      THEN (SELECT sum(ps1.accepted_payment)
                      from provided_service ps1
                           where ps1.event_fk = ps.event_fk
                                 and ps1.payment_type_fk = 2
                                 and ps1.start_date = ps.start_date
                                 and ps1.end_date = ps.end_date)
                      ELSE 0 END) AS accepted_payment_child

             from medical_register mr
             JOIN medical_register_record mrr
                ON mr.id_pk=mrr.register_fk
             JOIN provided_event pe
                ON mrr.id_pk=pe.record_fk
             JOIN provided_service ps
                ON ps.event_fk=pe.id_pk
             JOIN medical_organization mo
                ON ps.organization_fk=mo.id_pk
             JOIN medical_organization dep ON ps.department_fk = dep.id_pk
             JOIN medical_service ms
                ON ms.id_pk = ps.code_fk
             where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and ps.payment_type_fk = 2
             AND ms.group_fk = 19 and ms.subgroup_fk is not null

             group by mo, division
        order by mo, division
    """

    column_position = [12, 13, 14, 17]

    column_division = {(12, 13, 14, 17): DIVISION_ALL_1_2}

    column_length = {
        (12, ): [0, 1, 2, 3, 6],
        (13, 14): [0, 2, 3, 6],
        (17, ): [0, 2, 3, 4, 5, 6]
    }

    return {
        'title': title,
        'pattern': pattern,
        'data': [{'structure': (query, column_position, column_division),
                  'column_length': column_length}, ]
    }


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            stomatology()
        ]
        for act in acts:
            print_act(year, period, act)