#! -*- coding: utf-8 -*-
from report_printer.excel_style import VALUE_STYLE

from main.models import MedicalOrganization, MedicalService
from tfoms import func
from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_DIR, BASE_DIR
from report_printer.excel_writer import ExcelWriter
from report_printer.const import MONTH_NAME
from django.db import connection


def get_mo_statistics():
    query = """
            select
            1,
            case when T.term = 1 and (T.service_group is null or T.service_group in (1, 2,20, 32)) then 'hospital'
                  when T.service_code in ('049023', '149023') then 'gemodialis_hospital'
                  when T.service_code in ('049024', '149024') then 'peritondialis_hospital'
                  when T.term = 2 and (T.service_group is null or T.service_group in (17, 28)) then 'day_hospital'
                  when T.is_policlinic_treatment THEN 'policlinic_disease'
                  when ((T.service_group IS NULL or T.service_group = 24)
                       and ((T.term = 3 and T.service_reason in (2, 3, 8))
                            or (T.term = 3 and  T.service_reason = 1
                                   and not T.is_policlinic_treatment)))
                       or T.service_group = 4 THEN 'policlinic_priventive'
                  when T.term = 3 and T.service_reason = 5 or T.service_group = 31 THEN 'policlinic_ambulance'
                  when T.service_group = 9 and T.service_code in ('019214', '019215', '019216' ,'019217',
                                                                  '019212', '019201'
                                                                  ) then 'adult_exam'
                  when T.term = 4 THEN 'ambulance'
                  WHEN T.service_group = 29 THEN 'mrt'
                  WHEN T.service_code in ('049021', '149021') THEN 'gemodialis_policlinic'
                  WHEN T.service_code in ('049022', '149022') THEN 'peritondialis_policlinic'
                  WHEN T.service_group = 11
                       and T.service_code in ('119057', '119058', '119059',
                                              '119060', '119061', '119062',
                                              '119064', '119065', '119066',
                                              '119080', '119081', '119082',
                                              '119083', '119084', '119085',
                                              '119086', '119087', '119088',
                                              '119089', '119090', '119091') THEN 'children_exam'
                  WHEN T.service_group = 15
                       and T.service_code in ('119111', '119110', '119109',
                                              '119107', '119106', '119105',
                                              '119104', '119103', '119102',
                                              '119101', '119119', '119120') THEN 'prelim_children_exam'
                  WHEN T.service_group = 16 and T.service_code = '119151' THEN 'period_children_exam'
                  when T.service_group in (7, 25, 26, 12, 13) and T.service_code in (
                                              '019001', '019021', '019023', '019022', '019024', '019020',
                                              '019114', '019113', '019112', '019111', '019110',
                                              '019109', '019108', '019107', '019106', '019105',
                                              '019104', '019103', '019102', '119003', '119004',
                                              '119002', '119005', '119006', '119007', '119008',
                                              '119009', '119010', '119020', '119021', '119022',
                                              '119023', '119024', '119025', '119026', '119027',
                                              '119028', '119029', '119030', '119031', '119202',
                                              '119203', '119204', '119205', '119206', '119207',
                                              '119208', '119209', '119210', '119220', '119221',
                                              '119222', '119223', '119224', '119225', '119226',
                                              '119227', '119228', '119229', '119230', '119231'
                                                                                ) then 'clinical_exam'
                  when T.service_group = 19 and T.stomatology_reason = 12 then 'stom_disease'
                  when T.service_group = 19 AND (T.stomatology_reason in (13, 14, 17)
                       or T.stomatology_reason is NULL) then 'stom_ambulance'
                  ELSE T.service_code end as division_term,

            -- заявлено
            count(distinct CASE WHEN not T.is_children THEN  T.service_id END) as visit_all_adult,
            count(distinct CASE WHEN T.is_children THEN T.service_id END) AS visit_all_children,

            count(distinct CASE WHEN not T.is_children THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                       when T.service_group in (19) and T.stomatology_reason is NULL THEN NULL
                  ELSE T.event_id END END) AS treatment_all_adult,
            count(distinct CASE WHEN T.is_children  THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                       when T.service_group in (19) and T.stomatology_reason is NULL THEN NULL
                  ELSE T.event_id END END) AS treatment_all_children,

            sum(CASE WHEN not T.is_children THEN T.count_days else 0 END) AS count_days_all_adult,
            sum(CASE WHEN  T.is_children THEN T.count_days else 0 END) AS count_days_all_children,

            sum(CASE WHEN not T.is_children THEN T.uet else 0 END) AS uet_all_adult,
            sum(CASE WHEN  T.is_children THEN T.uet else 0END) AS uet_all_children,

            -- принято
            count(distinct CASE WHEN not T.is_children and T.is_accepted THEN  T.service_id END) AS visit_accept_adult,
            count(distinct CASE WHEN T.is_children and T.is_accepted THEN T.service_id END) as visit_accept_children,

            count(distinct CASE WHEN not T.is_children and T.is_accepted THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                  ELSE T.event_id END END) AS treatment_accept_adult,
            count(distinct CASE WHEN T.is_children and T.is_accepted THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                  ELSE T.event_id END END) AS treatment_accept_children,

            sum(CASE WHEN not T.is_children and T.is_accepted THEN T.count_days else 0 END) as count_days_accept_adult,
            sum(CASE WHEN  T.is_children and T.is_accepted THEN T.count_days else 0 END) As count_days_accept_children,

            sum(CASE WHEN not T.is_children and T.is_accepted THEN T.uet else 0 END) as uet_accept_adult,
            sum(CASE WHEN  T.is_children and T.is_accepted THEN T.uet else 0 END) as uet_accept_children,

            -- Исключено
            count(distinct CASE WHEN T.is_excluded THEN T.service_id END) as visit_exclude,
            count(distinct CASE WHEN T.is_excluded THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                  when T.service_group in (19) and T.stomatology_reason is NULL THEN NULL
                  ELSE T.event_id END END) as treatment_exclude,
            sum(CASE WHEN T.is_excluded THEN T.count_days else 0 END) as count_days_exclude,
            sum(CASE WHEN T.is_excluded THEN T.uet else 0 END) as uet_exclude


            from (
                select ms.code like '1%%' as is_children, ps.id_pk as service_id,
                         pe.id_pk as event_id, ps.quantity as count_days, ps.quantity*ms.uet as uet,
                         ps.payment_type_fk = 2 as is_accepted,
                         ps.payment_type_fk = 3 as is_excluded,
                         pe.term_fk as term, ms.group_fk as service_group,
                         ms.code as service_code,
                         ms.reason_fk as service_reason,
                         ms.subgroup_fk as service_subgroup,
                         mo.id_pk as organization_id,
                 (pe.term_fk = 3 and ms.reason_fk = 1 and
                    (ms.group_fk is NULL or ms.group_fk = 24)
                    and (select count(ps1.id_pk) FROM provided_service ps1
                         join medical_service ms1 on ms1.id_pk = ps1.code_fk
                         WHERE ps1.event_fk  = ps.event_fk and (ms1.group_fk is NULL or ms1.group_fk in (24, 29))
                         and ms1.reason_fk = 1
                         )>1
                    ) as is_policlinic_treatment,
                 (select distinct ms1.subgroup_fk
                    from medical_service ms1
                    where ms1.id_pk in (
                         select ps1.code_fk FROM provided_service ps1
                         where ps1.event_fk = ps.event_fk
                               and ps1.start_date=ps.start_date
                               and ps1.end_date=ps.end_date
                         and ps.payment_type_fk = ps1.payment_type_fk
                       )
                       AND ms1.subgroup_fk is NOT NULL
                       AND ms1.group_fk =19
                    ) AS stomatology_reason
                from
                    medical_register mr
                    JOIN medical_register_record mrr
                         ON mr.id_pk=mrr.register_fk
                    JOIN provided_event pe
                         ON mrr.id_pk=pe.record_fk
                    JOIN provided_service ps
                         ON ps.event_fk=pe.id_pk
                    JOIN medical_organization mo
                         ON ps.organization_fk=mo.id_pk
                    JOIN medical_service ms
                         ON ms.id_pk = ps.code_fk
                    join patient pt
                        ON pt.id_pk = mrr.patient_fk
                    where mr.is_active
                          AND mr.period= %(period)s
                          and mr.year= %(year)s
                          and (ms.group_fk != 27 or ms.group_fk is null)
            ) AS T
            group by division_term
            """

    cursor = connection.cursor()
    cursor.execute(query, dict(period=func.PERIOD, year=func.YEAR))
    return cursor.fetchall()


def get_mo_error_statistics():
    query = """
            select
            1,
            case when T.term = 1 and (T.service_group is null or T.service_group in (1, 2, 20, 32)) then 'hospital'
                  when T.service_code in ('049023', '149023') then 'gemodialis_hospital'
                  when T.service_code in ('049024', '149024') then 'peritondialis_hospital'
                  when T.term = 2 and (T.service_group is null or T.service_group in (17, 28)) then 'day_hospital'
                  when T.is_policlinic_treatment THEN 'policlinic_disease'
                  when ((T.service_group IS NULL or T.service_group = 24)
                       and ((T.term = 3 and T.service_reason in (2, 3, 8))
                            or (T.term = 3 and  T.service_reason = 1
                                   and not T.is_policlinic_treatment)))
                       or T.service_group = 4 THEN 'policlinic_priventive'
                  when T.term = 3 and T.service_reason = 5 or T.service_group = 31 THEN 'policlinic_ambulance'
                  when T.service_group = 9 and T.service_code in ('019214', '019215', '019216' ,'019217',
                                                                  '019212', '019201'
                                                                  ) then 'adult_exam'
                  when T.term = 4 THEN 'ambulance'
                  WHEN T.service_group = 29 THEN 'mrt'
                  WHEN T.service_code in ('049021', '149021') THEN 'gemodialis_policlinic'
                  WHEN T.service_code in ('049022', '149022') THEN 'peritondialis_policlinic'
                  WHEN T.service_group = 11
                       and T.service_code in ('119057', '119058', '119059',
                                              '119060', '119061', '119062',
                                              '119064', '119065', '119066',
                                              '119080', '119081', '119082',
                                              '119083', '119084', '119085',
                                              '119086', '119087', '119088',
                                              '119089', '119090', '119091') THEN 'children_exam'
                  WHEN T.service_group = 15
                       and T.service_code in ('119111', '119110', '119109',
                                              '119107', '119106', '119105',
                                              '119104', '119103', '119102',
                                              '119101', '119119', '119120') THEN 'prelim_children_exam'
                  WHEN T.service_group = 16 and T.service_code = '119151' THEN 'period_children_exam'
                  when T.service_group in (7, 25, 26, 12, 13) and T.service_code in (
                                              '019001', '019021', '019023', '019022', '019024', '019020',
                                              '019114', '019113', '019112', '019111', '019110',
                                              '019109', '019108', '019107', '019106', '019105',
                                              '019104', '019103', '019102', '119003', '119004',
                                              '119002', '119005', '119006', '119007', '119008',
                                              '119009', '119010', '119020', '119021', '119022',
                                              '119023', '119024', '119025', '119026', '119027',
                                              '119028', '119029', '119030', '119031', '119202',
                                              '119203', '119204', '119205', '119206', '119207',
                                              '119208', '119209', '119210', '119220', '119221',
                                              '119222', '119223', '119224', '119225', '119226',
                                              '119227', '119228', '119229', '119230', '119231'
                                                                                ) then 'clinical_exam'
                  when T.service_group = 19 and T.stomatology_reason = 12 then 'stom_disease'
                  when T.service_group = 19 AND (T.stomatology_reason in (13, 14, 17)
                       or T.stomatology_reason is NULL) then 'stom_ambulance'
                  ELSE T.service_code end as division_term,

            CASE WHEN T.error in (145, 128) THEN 55
                 WHEN T.error = 127 THEN 133
                 ELSE T.error END as failure_cause,

            -- Исключено
            count(distinct CASE WHEN T.is_excluded THEN T.service_id END) as visit_exclude,
            count(distinct CASE WHEN T.is_excluded THEN
                  case when T.service_group in (25, 26) THEN T.service_id
                  when T.service_group in (19) and T.stomatology_reason is NULL THEN NULL
                  when T.service_group in (19) and T.service_subgroup is NULL THEN NULL
                  ELSE T.event_id END END) as treatment_exclude,
            sum(CASE WHEN T.is_excluded THEN T.count_days else 0 END) as count_days_exclude,
            sum(CASE WHEN T.is_excluded THEN T.uet else 0 END) as uet_exclude

            from (
                select ms.code like '1%%' as is_children, ps.id_pk as service_id,
                     pe.id_pk as event_id, ps.quantity as count_days, ps.quantity*ms.uet as uet,
                     ps.payment_type_fk = 2 as is_accepted,
                     ps.payment_type_fk = 3 as is_excluded,
                     pe.term_fk as term, ms.group_fk as service_group,
                     ms.code as service_code,
                     ms.reason_fk as service_reason,
                     ms.subgroup_fk as service_subgroup,
                     mo.id_pk as organization_id,
                     me.failure_cause_fk as error,
                     (pe.term_fk = 3 and ms.reason_fk = 1 and
                        (ms.group_fk is NULL or ms.group_fk = 24)
                        and (select count(ps1.id_pk) FROM provided_service ps1
                             join medical_service ms1 on ms1.id_pk = ps1.code_fk
                             WHERE ps1.event_fk  = ps.event_fk and (ms1.group_fk is NULL or ms1.group_fk in (24, 29))
                             and ms1.reason_fk = 1
                             )>1
                        ) as is_policlinic_treatment,
                     (select distinct ms1.subgroup_fk from medical_service ms1
                      where ms1.id_pk in (
                             select ps1.code_fk FROM provided_service ps1
                                    join provided_service_sanction pss1
                                        on ps1.id_pk = pss1.service_fk
                                    join medical_error me1
                                        on pss1.error_fk = me1.id_pk
                                           and me1.weight = (
                                              select max(weight) from medical_error
                                              where id_pk in (
                                                 select pss2.error_fk from provided_service_sanction pss2
                                                 where pss2.is_active and service_fk = ps1.id_pk)
                                              )

                             where
                             ps1.event_fk = ps.event_fk
                             and ps1.start_date=ps.start_date
                             and ps1.end_date=ps.end_date
                             and ps1.payment_type_fk = ps.payment_type_fk
                             and pss1.is_active
                             --and me1.failure_cause_fk = me.failure_cause_fk
                         )
                         AND ms1.subgroup_fk is NOT NULL
                         AND ms1.group_fk =19
                        ) AS stomatology_reason
                from medical_register mr
                    JOIN medical_register_record mrr
                         ON mr.id_pk=mrr.register_fk
                    JOIN provided_event pe
                         ON mrr.id_pk=pe.record_fk
                    JOIN provided_service ps
                         ON ps.event_fk=pe.id_pk
                    JOIN medical_organization mo
                         ON ps.organization_fk=mo.id_pk
                    JOIN medical_service ms
                         ON ms.id_pk = ps.code_fk
                    join patient pt
                         ON pt.id_pk = mrr.patient_fk
                    join provided_service_sanction pss
                         on ps.id_pk = pss.service_fk
                    join medical_error me
                         on pss.error_fk = me.id_pk
                            and me.weight = (
                                select max(weight) from medical_error
                                where id_pk in (
                                    select pss1.error_fk from provided_service_sanction pss1
                                    where pss1.is_active and pss1.service_fk = ps.id_pk
                                )
                            )

                        where mr.is_active
                        AND mr.period= %(period)s
                        and mr.year= %(year)s
                        and ps.payment_type_fk = 3
                        and pss.is_active
                        and (ms.group_fk != 27 or ms.group_fk is null)
            ) AS T
            group by division_term, failure_cause
            order by division_term, failure_cause
            """
    #
    cursor = connection.cursor()
    cursor.execute(query, dict(period=func.PERIOD, year=func.YEAR))
    return cursor.fetchall()


class Command(BaseCommand):

    def handle(self, *args, **options):
        VISIT = 1
        TREATMENT = 2
        COUNT_DAYS = 3
        UET = 4
        template = BASE_DIR + r'\templates\excel_pattern\defect.xls'
        target_dir = REESTR_DIR
        rules = {
            'hospital': [(1, VISIT)],
            'gemodialis_hospital': [(2, TREATMENT), (3, COUNT_DAYS)],
            'peritondialis_hospital': [(4, TREATMENT), (5, COUNT_DAYS)],
            'day_hospital': [(6, VISIT), (7, COUNT_DAYS)],
            'policlinic_disease': [(8, VISIT), (9, TREATMENT)],
            'policlinic_priventive': [(10, TREATMENT)],
            'policlinic_ambulance': [(11, VISIT)],
            'adult_exam': [(12, TREATMENT), (13, VISIT)],
            'ambulance': [(14, VISIT)],
            'mrt': [(15, VISIT)],
            'gemodialis_policlinic': [(16, TREATMENT), (17, COUNT_DAYS)],
            'peritondialis_policlinic': [(18, TREATMENT), (19, COUNT_DAYS)],
            'children_exam': [(20, TREATMENT), (21, VISIT)],
            'prelim_children_exam': [(22, TREATMENT), (23, VISIT)],
            'period_children_exam': [(24, TREATMENT)],
            'clinical_exam': [(25, TREATMENT), (26, VISIT)],
            'stom_disease': [(27, TREATMENT), (28, UET)],
            'stom_ambulance': [(29, TREATMENT), (30, UET)]
        }

        error_sequence = [
            50, 51, 52, 53, 54, 55,
            133, 56, 57, 58, 59, 60, 61,
            62, 63, 64, 65, 66, 67, 68,
            69, 70, 71, 72, 73, 74, 75
        ]

        target = target_dir % (func.YEAR, func.PERIOD) + ur'\дефекты\%s_дефекты' % \
            u'общий'
        print target
        with ExcelWriter(target, template=template) as act_book:
            act_book.set_sheet(0)
            act_book.write_cella(0, 3, u'Сводная справка  по  дефектам  за %s %s г.'
                                       % (MONTH_NAME[func.PERIOD], func.YEAR))
            act_book.write_cella(3, 0, u'Общий')
            act_book.set_style(VALUE_STYLE)
            stat_obj = get_mo_statistics()
            ignore_services = {}
            for data in stat_obj:
                print len(data)
                division_term = data[1]
                if division_term not in rules:
                    if division_term not in ignore_services:
                        ignore_services[division_term] = [0, 0, 0, 0]
                    ignore_services[division_term][0] = data[18]
                    ignore_services[division_term][2] = data[21]
                for cell, field_group in rules.get(division_term, []):
                    act_book.set_cursor(4+cell, 2)
                    if field_group == VISIT:
                        act_book.write_cell(data[2], 'c')
                        act_book.write_cell(data[3], 'c')
                        act_book.write_cell(data[10], 'c')
                        act_book.write_cell(data[11], 'c')
                        act_book.write_cell(data[18], 'c')
                    elif field_group == TREATMENT:
                        act_book.write_cell(data[4], 'c')
                        act_book.write_cell(data[5], 'c')
                        act_book.write_cell(data[12], 'c')
                        act_book.write_cell(data[13], 'c')
                        act_book.write_cell(data[19], 'c')
                    elif field_group == COUNT_DAYS:
                        act_book.write_cell(data[6], 'c')
                        act_book.write_cell(data[7], 'c')
                        act_book.write_cell(data[14], 'c')
                        act_book.write_cell(data[15], 'c')
                        act_book.write_cell(data[20], 'c')
                    elif field_group == UET:
                        act_book.write_cell(data[8], 'c')
                        act_book.write_cell(data[9], 'c')
                        act_book.write_cell(data[16], 'c')
                        act_book.write_cell(data[17], 'c')
                        act_book.write_cell(data[21], 'c')
            error_stat_obj = get_mo_error_statistics()
            for data in error_stat_obj:
                division_term = data[1]
                error = data[2]
                index = error_sequence.index(error)
                if division_term not in rules:
                    if division_term not in ignore_services:
                        ignore_services[division_term] = [0, 0, 0, 0]
                    ignore_services[division_term][1] = data[3]
                    ignore_services[division_term][3] = data[4]
                for cell, field_group in rules.get(division_term, []):
                    act_book.set_cursor(4+cell, 7+index)
                    if field_group == VISIT:
                        act_book.write_cell(data[3], 'c')
                    elif field_group == TREATMENT:
                        act_book.write_cell(data[4], 'c')
                    elif field_group == COUNT_DAYS:
                        act_book.write_cell(data[5], 'c')
                    elif field_group == UET:
                        act_book.write_cell(data[6], 'c')
            act_book.set_sheet(1)
            act_book.set_cursor(1, 0)
            for service in ignore_services:
                act_book.write_cell(service, 'c')
                act_book.write_cell(MedicalService.objects.get(code=service).name, 'c')
                group = ''
                if MedicalService.objects.filter(code=service, group__isnull=False):
                    group = MedicalService.objects.get(code=service).group.name
                act_book.write_cell(group, 'c')
                act_book.write_cell(ignore_services[service][0], 'c')
                act_book.write_cell(ignore_services[service][1], 'c')
                act_book.write_cell(ignore_services[service][2], 'c')
                act_book.write_cell(ignore_services[service][3], 'r')