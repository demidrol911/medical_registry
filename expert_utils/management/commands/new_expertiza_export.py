#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalService,
    MedicalOrganization, Address, Patient)
from django.db import connection
import os

from dbfpy import dbf


def unicode_to_cp866(string):
    return string.encode('cp866') if string else ''


def get_department_services(year, period, department_code):
    query = """

        -- Выборка услуг для выгрузки Т-файлов экспертам --
        select DISTINCT ps.id_pk,
            md.code as division_code,
            ms.code as service_code,
            case
                when p.insurance_policy_series = '' or p.insurance_policy_series is NULL THEN p.insurance_policy_number
                ELSE p.insurance_policy_series || ' ' || coalesce(p.insurance_policy_number, '')
            END as policy,
            p.last_name,
            p.first_name,
            p.middle_name,
            p.birthdate,
            p.gender_fk as gender_code,
            case
                when mr.type between 3 and 11 then pe_idc_b.idc_code
                else idc.idc_code
            END as disease,
            pecd_idc.idc_code as concomitant_disease,
            ps.start_date,
            ps.end_date,
            pe.anamnesis_number,
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
            dep.old_code,
            pe.id_pk as event_Id
        FROM provided_service ps
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            JOIN provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
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
            LEFT JOIN medical_division md
                on ps.division_fk = md.id_pk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk
            LEFT JOIN idc pe_idc_i
                on pe_idc_i.id_pk = pe.initial_disease_fk
            LEFT JOIN idc pe_idc_b
                on pe_idc_b.id_pk = pe.basic_disease_fk
            LEFT JOIN provided_event_concomitant_disease pecd
                on pecd.event_fk = pe.id_pk
            LEFT JOIN idc pecd_idc
                on pecd.disease_fk = pecd_idc.id_pk
            LEFT JOIN treatment_outcome tro
                on tro.id_pk = pe.treatment_outcome_fk
            LEFT JOIN address adr
                on adr.person_fk = per.version_id_pk and adr.type_fk = 1
            LEFT JOIN medical_organization dep
                on dep.id_pk = ps.department_fk
            LEFT JOIN administrative_area aa
                on aa.id_pk = adr.administrative_area_fk
            LEFT join administrative_area aa1
                on aa1.id_pk = aa.parent_fk
            LEFT join administrative_area aa2
                on aa2.id_pk = aa1.parent_fk
        WHERE mr.is_active
            and ps.payment_type_fk in (2, 4)
            and mr.year = %s
            and mr.period = %s
            and dep.old_code = %s
            and ms.code not like 'A%%'
        ORDER BY dep.old_code, p.last_name, p.first_name, p.middle_name, p.birthdate, ps.end_date
    """

    return list(ProvidedService.objects.raw(query, [year, period,
                                                    department_code]))

def main():
    year = '2015'
    period = '12'
    path = 'c:/work/expertiza_export/%s/%s' % (year, period)

    departments = ProvidedService.objects.filter(
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        event__record__register__organization_code='280043',
        payment_type_id__in=(2, 4),
    ).exclude(code__code__startswith='A').values_list(
        'department__old_code', flat=True).distinct('department__old_code')

    pass_departments = []

    print departments
    for department in departments:
        print department
        p = 'c:/work/expertiza_export/2015/%s/t%s.dbf' % (period, department)
        print p
        if os.path.exists(p):
            print 'ok'
            continue

        if department in pass_departments:
            continue
        if not department:
            continue

        db = dbf.Dbf('%s/t%s.dbf' % (path, department), new=True)
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
            ("IDSERV", "C", 32),
            ("IDCASE", "C", 32),
            ("ISREPEATED", "N", 2),
        )

        services = get_department_services(year, period, department)

        exclude_departments = []
        for service in services:
            new = db.newRecord()
            new["COD"] = unicode_to_cp866(service.service_code)
            new["OTD"] = service.division_code or '000'
            new["ERR_ALL"] = ''
            new["SN_POL"] = unicode_to_cp866(service.policy)
            new["FAM"] = unicode_to_cp866(service.last_name or '')
            new["IM"] = unicode_to_cp866(service.first_name or '')
            new["OT"] = unicode_to_cp866(service.middle_name or '')
            new["DR"] = service.birthdate or '1900-01-01'
            new["DS"] = unicode_to_cp866(service.disease)
            new["DS2"] = unicode_to_cp866(service.concomitant_disease)
            new["C_I"] = unicode_to_cp866(service.anamnesis_number or '')
            new["D_BEG"] = service.start_date or '1900-01-01'
            new["D_U"] = service.end_date or '1900-01-01'
            new["K_U"] = service.quantity or 0
            new["S_OPL"] = round(float(service.accepted_payment), 2)
            try:
                new["ADRES"] = unicode_to_cp866(service.address)
            except:
                new["ADRES"] = ''
            new["SPOS"] = service.funding_type
            new["GENDER"] = service.gender_code or 0
            new["OUTCOME"] = service.outcome_code or ''
            new["HOSP_TYPE"] = service.hospitalization_code or 0
            new["EMPL_NUM"] = unicode_to_cp866(service.worker_code or '')
            new["IDSERV"] = service.pk
            new["IDCASE"] = service.event_id
            new.store()
        db.close()
        print connection.queries


class Command(BaseCommand):
    help = 'export big XML'

    def handle(self, *args, **options):
        print 'Here'
        main()