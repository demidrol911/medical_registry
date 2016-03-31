#! -*- coding: utf-8 -*-

import psycopg2
import os
import datetime
from dbfpy import dbf

pg_conn_string = "host='10.28.10.7' dbname='dms' user='dms' password='iThaeMaiD5'"
connect_pg = psycopg2.connect(pg_conn_string)
cursor_pg = connect_pg.cursor()


def unicode_to_cp866(string):
    return string.decode('utf-8').encode('cp866') if string else ''


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


def get_services(year, period):
    query = """
        select DISTINCT
            dep.old_code as department,
            ms.code as service_code,
            md.code as division_code,
            '' as errors,
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
            ps.quantity,
            ps.accepted_payment,
            ps.comment,
            pe.hospitalization_fk as hospitalization_code,
            pe.worker_code,
            tro.code as outcome_code,
            concat_ws(', ', COALESCE(aa2.name, ''), Coalesce(aa1.name, ''), COALESCE(aa.name, ''),
            coalesce(adr.street, ''), coalesce(adr.house_number, ''),
            COALESCE(adr.extra_number, ''), coalesce(adr.room_number)) as address,
            case ps.payment_kind_fk when 2 then 'P' else 'T' END as funding_type,

            ps.end_date - ps.start_date as c_quantity
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
            --JOIN provided_service_sanction pss
            --    on ps.id_pk = pss.service_fk and pss.type_fk in (2, 3)
        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and pe.term_fk in (1, 2)
            and pe.treatment_result_fk in (5, 6, 15, 16)
            and ps.payment_type_fk = 2
            and ms.code not like 'A%%'
        ORDER BY dep.old_code, p.last_name, p.first_name, p.middle_name
    """
    cursor_pg.execute(query, {'year': year, 'period': period})
    result = dictfetchall(cursor_pg)

    return result


def main():
    year = '2016'
    period = '02'

    path = 'c:/work/DEAD_RESULT_DBF/'
    services = get_services(year, period)

    current_department = None
    db = None
    current_term_name = None
    stored_services_id = []

    for service in services:
        print repr(service['last_name'])
        if service['department'] != current_department:
            current_department = service['department']

            stored_services_id = []

            if db:
                db.close()

            db = dbf.Dbf('%s/t%s.dbf' % (path, current_department), new=True)
            db.addField(
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
            )

        new = db.newRecord()
        new["COD"] = unicode_to_cp866(service['service_code'])
        new["OTD"] = service.get('division_code', '000')
        new["ERR_ALL"] = ''
        new["SN_POL"] = unicode_to_cp866(service['policy'])
        new["FAM"] = unicode_to_cp866(service.get('last_name', ''))
        new["IM"] = unicode_to_cp866(service.get('first_name', ''))
        new["OT"] = unicode_to_cp866(service.get('middle_name', ''))
        new["DR"] = service.get('birthdate', '1900-01-01')
        new["DS"] = unicode_to_cp866(service['disease'])
        new["DS2"] = unicode_to_cp866(service['concomitant_disease'])
        new["C_I"] = unicode_to_cp866(service.get('anamnesis_number', ''))
        new["D_BEG"] = service.get('start_date', '1900-01-01')
        new["D_U"] = service.get('end_date', '1900-01-01')
        new["K_U"] = service.get('quantity', 0)
        new["S_OPL"] = round(float(service.get('accepted_payment', 0)), 2)
        try:
            new["ADRES"] = unicode_to_cp866(service.get('address', ''))
        except:
            new["ADRES"] = ''
        new["SPOS"] = service['funding_type']
        new["GENDER"] = service['gender_code'] or 0
        new["OUTCOME"] = service['outcome_code'] or ''
        new["HOSP_TYPE"] = service['hospitalization_code'] or 0
        new["EMPL_NUM"] = unicode_to_cp866(service['worker_code'] or '')
        new.store()

    db.close()

main()