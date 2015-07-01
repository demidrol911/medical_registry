#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalRegisterRecord,
    MedicalOrganization, Gender, InsurancePolicyType, MedicalServiceTerm,
    MedicalServiceKind, MedicalServiceForm, MedicalHospitalization,
    MedicalServiceProfile, TreatmentOutcome, TreatmentResult,
    MedicalWorkerSpeciality, PaymentType, PaymentMethod, PaymentFailureCause,
    MedicalDivision, Special, MedicalService, Patient, Sanction)
from django.db.models import Sum, Max, Min
from django.db import connection, transaction
from tfoms.models import SERVICE_XML_TYPES, EXAMINATION_TYPES
from helpers import xml_writer as writer
import datetime
from math import ceil
from collections import defaultdict


def safe_str(var):
    if var:
        return var.encode('utf-8')
    else:
        return ''


def safe_int(val):
    try:
        return int(val)
    except:
        return 0


def set_precision(number, precision):
    str_number = str(number)
    return float(str_number[:str_number.index('.')+precision+1])


def get_records(register_element):
    query = """
        select DISTINCT
            provided_service.id_pk,
            medical_register_record.id as record_uid,
            patient.id as patient_uid,
            patient.last_name as patient_first_name,
            patient.first_name as patient_last_name,
            patient.middle_name as patient_middle_name,
            patient.gender_fk as patient_gender,
            patient.birthdate::VARCHAR as patient_birthdate,
            patient.agent_last_name as patient_agent_first_name,
            patient.agent_first_name as patient_agent_last_name,
            patient.agent_middle_name as patient_agent_middle_name,
            patient.agent_gender_fk as patient_agent_gender,
            patient.agent_birthdate as patient_agent_birthdate,
            patient.birthplace as patient_birthplace,
            patient.person_id_series,
            patient.person_id_number,
            (
                select issue_date
                from person_id
                where series = patient.person_id_series
                    and number = patient.person_id_number
                ORDER BY person_id.version_id_pk DESC LIMIT 1
            )::VARCHAR as person_id_issue_date,
            patient.snils as patient_snils,
            patient.okato_registration,
            patient.okato_residence,
            patient.insurance_policy_type_fk as insurance_policy_type,
            patient.insurance_policy_series as insurance_policy_series,
            patient.insurance_policy_number as insurance_policy_number,
            patient.newborn_code as newborn_code,
            patient.weight as weight,
            person.version_id_pk as person_uid,
            person_id_type.code as patient_id_type,
            provided_event.id as event_uid,
            provided_event.term_fk as event_term_code,
            medical_service_kind.code as event_kind_code,
            provided_event.form_fk as event_form_code,
            medical_service_hitech_kind.code as hitech_kind_code,
            provided_event.hitech_method_fk as hitech_method_code,
            provided_event.hospitalization_fk as event_hospitalization_code,
            (
                select code
                from provided_service
                    join medical_division
                        on medical_division.id_pk = provided_service.division_fk
                where provided_service.event_fk = provided_event.id_pk
                order by end_date DESC
                limit 1
            ) as event_division_code,
            referred.code as event_referred_organization_code,
            medical_register.organization_code as event_organization_code,
            medical_organization.name as medical_organization_name,
            medical_organization.old_code as event_department_code,
            provided_event.division_fk,
            event_profile.name as event_profile_name,
            provided_event.is_children_profile as event_is_children,
            provided_event.anamnesis_number as anamnesis_number,
            (
                select min(ps2.start_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            )::VARCHAR as event_start_date,
            (
                select max(ps2.end_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            )::VARCHAR as event_end_date,
            idc_initial.idc_code as event_initial_disease_code,
            idc_basic.name as event_basic_disease_name,

            ARRAY(select idc.idc_code
                from provided_event_concomitant_disease
                    join idc
                        on idc.id_pk = provided_event_concomitant_disease.disease_fk
                where event_fk = provided_event.id_pk) as event_concomitant_disease_code,

            ARRAY(select idc.idc_code
                from provided_event_complicated_disease
                    join idc
                        on idc.id_pk = provided_event_complicated_disease.disease_fk
                where event_fk = provided_event.id_pk) as event_complicated_disease_code,

            treatment_result.name as treatment_result_name,
            treatment_outcome.code as treatment_outcome_code,
            medical_worker_speciality.name as event_worker_speciality_name,
            provided_event.speciality_dict_version,
            provided_event.worker_code as event_worker_code,
            provided_event.payment_method_fk as event_payment_method_code,
            provided_event.special_fk as event_special_code,

            (
                case provided_event.term_fk
                when 1 THEN
                    1
                WHEN 2 THEN
                    (SELECT sum(provided_service.quantity)
                    from provided_service
                    where event_fk = provided_event.id_pk)
                WHEN 3 THEN
                    (SELECT sum(provided_service.quantity)
                    from provided_service
                    where event_fk = provided_event.id_pk)
                ELSE
                    1
                end
            ) as event_payment_units_number,

            (
                select sum(ps2.tariff)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_tariff,

            (
                select sum(ps2.invoiced_payment)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_invoiced_payment,
            (
                case
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) = 2 then 1
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) = 3 then 2
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) >= 4 then 3
                End
            ) as event_payment_type_code,
            (
                select sum(ps2.accepted_payment)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
                    and ps2.payment_type_fk in (2, 4)
            ) as event_accepted_payment,

            provided_event.examination_result_fk as examination_result_code,
            provided_event.comment as event_comment,
            provided_service.id_pk as service_pk,
            provided_service.id as service_uid,
            medical_register.organization_code as service_organization_code,
            service_department.old_code as service_department_code,
            service_division.code as service_division_code,
            service_profile.code as service_profile_code,
            provided_service.is_children_profile as service_is_children,
            provided_service.start_date::VARCHAR as service_start_date,
            provided_service.end_date::VARCHAR as service_end_date,
            service_idc_basic.idc_code as service_basic_disease_code,
            medical_service.code as service_code,
            medical_service.name as service_name,
            provided_service.quantity,
            provided_service.tariff as service_tariff,
            provided_service.invoiced_payment as service_invoiced_payment,
            payment_type.code as service_payment_type_code,
            provided_service.accepted_payment as service_accepted_payment,
            --medical_error.failure_cause_fk as service_failure_cause_code,
            --pss.underpayment as service_sanction_mek,
            service_worker_speciality.name as service_worker_speciality_name,
            provided_service.worker_code as service_worker_code,
            provided_service.comment as service_comment,
            medical_register.year, medical_register.period,
            medical_register.organization_code,
            medical_register_record.id,
            provided_event.id,
            provided_service.id,
            provided_event.id_pk as event_guid,
            provided_service.id_pk as service_guid,
            insurance_policy.type_fk as policy_type,
            insurance_policy.series as policy_series,
            insurance_policy.number as policy_number,
            insurance_policy.enp as policy_enp,
            insurance_policy.start_date::VARCHAR as policy_start_date,
            patient.id_pk as patient_guid
        from
            medical_register
            join medical_register_record
                on medical_register.id_pk = medical_register_record.register_fk
            JOIN patient
                on patient.id_pk = medical_register_record.patient_fk
            left join insurance_policy
                on patient.insurance_policy_fk = insurance_policy.version_id_pk
            left join person
                on person.version_id_pk = (
                    select version_id_pk
                    from person
                    where id = (
                        select id
                        from person
                        where version_id_pk = insurance_policy.person_fk
                    ) and is_active
                )
            LEFT join person_id_type
                on patient.person_id_type_fk = person_id_type.id_pk
            join provided_event
                on provided_event.record_fk = medical_register_record.id_pk
            join provided_service
                on provided_service.event_fk = provided_event.id_pk
            LEFT join medical_service_profile event_profile
                on event_profile.id_pk = provided_event.profile_fk
            LEFT JOIN medical_division event_division
                on event_division.id_pk = provided_event.division_fk
            left join medical_service_hitech_kind
                on provided_event.hitech_kind_fk = medical_service_hitech_kind.id_pk
            LEFT JOIN medical_organization
                ON medical_organization.id_pk = provided_event.organization_fk
            left join medical_organization referred
                on referred.id_pk = provided_event.refer_organization_fk
            left join idc idc_initial
                on idc_initial.id_pk = provided_event.initial_disease_fk
            join idc idc_basic
                on idc_basic.id_pk = provided_event.basic_disease_fk
            left join provided_event_concomitant_disease pecd
                on pecd.event_fk = provided_event.id_pk
            left join idc idc_concomitant
                on idc_concomitant.id_pk = pecd.disease_fk
            LEFT JOIN treatment_result
                on treatment_result.id_pk = provided_event.treatment_result_fk
            LEFT join treatment_outcome
                on treatment_outcome.id_pk = provided_event.treatment_outcome_fk
            LEFT JOin medical_worker_speciality
                on medical_worker_speciality.id_pk = provided_event.worker_speciality_fk
            LEFT join examination_result
                on examination_result.id_pk = provided_event.examination_result_fk
            left JOIN medical_division service_division
                on service_division.id_pk = provided_service.division_fk
            JOIN medical_organization service_department
                ON service_department.id_pk = provided_service.department_fk
            LEFT join idc service_idc_basic
                on service_idc_basic.id_pk = provided_service.basic_disease_fk
            LEFT join medical_service_profile service_profile
                on service_profile.id_pk = provided_service.profile_fk
            LEFT JOin medical_worker_speciality service_worker_speciality
                on service_worker_speciality.id_pk = provided_service.worker_speciality_fk
            JOIN medical_service
                on provided_service.code_fk = medical_service.id_pk
            JOIN payment_type
                on provided_service.payment_type_fk = payment_type.id_pk
            left join medical_service_kind
                on medical_service_kind.id_pk = provided_event.kind_fk
            --LEFT JOIN medical_error
            --    on pss.error_fk = medical_error.id_pk
        where medical_register.is_active
            and medical_register.year = %(year)s
            and medical_register.period = %(period)s
            and medical_register.organization_code = %(organization)s
        order by medical_register.year, medical_register.period,
            medical_register.organization_code,
            medical_register_record.id,
            provided_event.id,
            provided_service.id
    """
    return ProvidedService.objects.raw(query, dict(
        year=register_element[0], period=register_element[1],
        organization=register_element[2]))


def main():
    for period in ('01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'):
        year = '2013'
        print datetime.datetime.now()
        registers = MedicalRegister.objects.filter(
            is_active=True, period=period, year=year
            #organization_code__in=('280036', )

            ).values_list(
                'year',
                'period',
                'organization_code'
            ).distinct().order_by(
                'organization_code',
                'year',
                'period')

        file_regular = 'exp_cases_%s%s' % (period, year[2:])

        XML_TYPES = dict(SERVICE_XML_TYPES)
        EXAMINIATIONS = dict(EXAMINATION_TYPES)
        new_register = False

        hm_xml = writer.Xml('%s.XML' % file_regular)

        hm_xml.plain_put('<?xml version="1.0" encoding="utf-8"?>')
        hm_xml.start('EXP_CASES')

        print registers
        for index, register_element in enumerate(registers):
            records = list(get_records(register_element))
            payments_types = [rec.service_payment_type_code for rec in records]

            register = list(MedicalRegister.objects.raw(
                """
                    select id_pk,
                        (
                            select sum(ps.invoiced_payment)
                            from provided_service ps
                                join provided_event pe
                                    on pe.id_pk = ps.event_fk
                                JOIN medical_register_record mrr
                                    on mrr.id_pk = pe.record_fk
                                JOIN medical_register mr
                                    on mr.id_pk = mrr.register_fk
                            WHERE mr.is_active
                                and mr.year = mr1.year
                                and mr.period = mr1.period
                                and mr.organization_code = mr1.organization_code
                        ) as invoiced_payment_sum,
                        (
                            select sum(ps.accepted_payment)
                            from provided_service ps
                                join provided_event pe
                                    on pe.id_pk = ps.event_fk
                                JOIN medical_register_record mrr
                                    on mrr.id_pk = pe.record_fk
                                JOIN medical_register mr
                                    on mr.id_pk = mrr.register_fk
                            WHERE mr.is_active
                                and mr.year = mr1.year
                                and mr.period = mr1.period
                                and mr.organization_code = mr1.organization_code
                                and ps.payment_type_fk in (2, 4)
                        ) as accepted_payment_sum,
                        (
                            select sum(pss.underpayment)
                            from provided_service ps
                                join provided_event pe
                                    on pe.id_pk = ps.event_fk
                                JOIN medical_register_record mrr
                                    on mrr.id_pk = pe.record_fk
                                JOIN medical_register mr
                                    on mr.id_pk = mrr.register_fk
                                JOIN provided_service_sanction pss
                                    on pss.service_fk = ps.id_pk
                            WHERE mr.is_active
                                and mr.year = mr1.year
                                and mr.period = mr1.period
                                and mr.organization_code = mr1.organization_code
                                and ps.payment_type_fk in (3, 4)
                                and pss.type_fk = 1
                        ) as sanction_mek_sum,
                        (
                            select sum(pss.underpayment)
                            from provided_service ps
                                join provided_event pe
                                    on pe.id_pk = ps.event_fk
                                JOIN medical_register_record mrr
                                    on mrr.id_pk = pe.record_fk
                                JOIN medical_register mr
                                    on mr.id_pk = mrr.register_fk
                                JOIN provided_service_sanction pss
                                    on pss.service_fk = ps.id_pk
                            WHERE mr.is_active
                                and mr.year = mr1.year
                                and mr.period = mr1.period
                                and mr.organization_code = mr1.organization_code
                                and ps.payment_type_fk in (2, 4)
                                and pss.type_fk = 2
                        ) as sanction_mee_sum,
                        (
                            select sum(pss.underpayment)
                            from provided_service ps
                                join provided_event pe
                                    on pe.id_pk = ps.event_fk
                                JOIN medical_register_record mrr
                                    on mrr.id_pk = pe.record_fk
                                JOIN medical_register mr
                                    on mr.id_pk = mrr.register_fk
                                JOIN provided_service_sanction pss
                                    on pss.service_fk = ps.id_pk
                            WHERE mr.is_active
                                and mr.year = mr1.year
                                and mr.period = mr1.period
                                and mr.organization_code = mr1.organization_code
                                and ps.payment_type_fk in (2, 4)
                                and pss.type_fk = 3
                        ) as sanction_ekmp_sum
                    from medical_register mr1
                    where is_active
                        and "year" = %(year)s
                        and period = %(period)s
                        and organization_code = %(organization_code)s
                        and "type" = 1

                """,
                dict(year=register_element[0],
                period=register_element[1], organization_code=register_element[2])))[0]

            if new_register:
                #hm_xml.put('COMENTSL', safe_str(comment))
                hm_xml.end('EXP_CASE')
                #hm_xml.end('ZAP')
            comment = ''
            invoiced_payment = round(float(register.invoiced_payment_sum or 0))
            accepted_payment = round(float(register.accepted_payment_sum or 0))
            sanctions_mek = round(float(register.sanction_mek_sum or 0))
            sanctions_mee = round(float(register.sanction_mee_sum or 0))
            sanctions_ekmp = round(float(register.sanction_ekmp_sum or 0))

            if sanctions_mek < 0:
                sanctions_mek = 0

            new_register = True
            current_record = None
            current_event = None
            event_counter = 0

            #if register.type > 2:
            #    hm_xml.put('DISP', EXAMINIATIONS[register.type-2].encode('cp1251'))

            print register.organization_code, len(records)

            for i, record in enumerate(records):
                event_is_children_profile = '1' if record.event_is_children else '0'
                if record.event_payment_type_code in ('2', 2):
                    continue

                if record.record_uid != current_record:
                    if i != 0:
                        #hm_xml.put('COMENTSL', safe_str(comment))
                        hm_xml.end('EXP_CASE')
                        #hm_xml.end('ZAP')
                        event_counter = 0
                    current_record = record.record_uid

                if record.event_uid != current_event:
                    current_event = record.event_uid
                    if event_counter != 0:
                        hm_xml.end('EXP_CASE')

                    hm_xml.start('EXP_CASE')
                    patient_id = record.patient_uid

                    if record.policy_type:
                        patient_policy_type = record.policy_type
                        if record.policy_type == 3:
                            blank_series = record.policy_series
                            blank_number = record.policy_number
                            dpfs_number = record.policy_enp
                            enp_number = record.policy_enp
                        elif record.policy_type == 2:
                            blank_series = ''
                            blank_number = record.policy_number
                            dpfs_number = ''
                            enp_number = record.policy_enp
                        elif record.policy_type == 1:
                            blank_series = ''
                            blank_number = ''
                            dpfs_number = u'{0} {1}'.format(record.policy_series, record.policy_number)
                            enp_number = ''
                    else:
                        patient_policy_type = record.insurance_policy_type
                        blank_series = record.insurance_policy_series
                        blank_number = ''
                        dpfs_number = record.insurance_policy_number
                        enp_number = ''

                    hm_xml.put('PERSON_ID', record.patient_guid)
                    hm_xml.put('PERSON_GUID', safe_str(record.patient_uid))
                    last_name = safe_str(record.patient_last_name)
                    hm_xml.put('SURNAME', last_name)
                    first_name = safe_str(record.patient_first_name)
                    hm_xml.put('FIRSTNAME', first_name)
                    middle_name = safe_str(record.patient_middle_name)
                    hm_xml.put('PATRONYMIC', middle_name)
                    hm_xml.put('SEX', safe_int(record.patient_gender))
                    birthdate = record.patient_birthdate
                    if birthdate:
                        birthdate += 'T00:00:00'
                    hm_xml.put('BIRTHDATE', birthdate or '')
                    hm_xml.put('DOC_TYPE_ID', safe_int(record.patient_id_type or ''))
                    hm_xml.put('DOC_SERIES', safe_str(record.person_id_series or ''))
                    hm_xml.put('DOC_NUMBER', safe_str(record.person_id_number or ''))
                    person_id_issue_date = record.person_id_issue_date
                    if person_id_issue_date:
                        person_id_issue_date += 'T00:00:00'
                    hm_xml.put('DOC_ISSUE_DATE', safe_str(person_id_issue_date))
                    hm_xml.put('DPFS_TYPE_ID', safe_int(patient_policy_type or ''))
                    hm_xml.put('ENP_NUMBER', safe_str(enp_number or ''))
                    hm_xml.put('DPFS_NUMBER', safe_str(dpfs_number or ''))
                    hm_xml.put('DPFS_BL_SERIES', safe_str(blank_series or ''))
                    hm_xml.put('DPFS_BL_NUMBER', safe_str(blank_number or ''))
                    policy_start_date = record.policy_start_date
                    if policy_start_date:
                        policy_start_date += 'T00:00:00'
                    hm_xml.put('DPFS_ISSUE_DATE', safe_str(policy_start_date or ''))
                    hm_xml.put('SNILS', safe_str(record.patient_snils))
                    hm_xml.put('CASE_GUID', record.event_guid)
                    hm_xml.put('CASE_ADDITION_ID', '')
                    hm_xml.put('CASE_DESCRIPTION', '')
                    start_date = record.event_start_date
                    end_date = record.event_end_date
                    if start_date:
                        start_date += 'T00:00:00'
                    if end_date:
                        end_date += 'T00:00:00'
                    if start_date > end_date:
                        hm_xml.put('CASE_START', end_date)
                        hm_xml.put('CASE_END', start_date)
                    else:
                        hm_xml.put('CASE_START', start_date)
                        hm_xml.put('CASE_END', end_date)
                    hm_xml.put('CASE_CARE_TYPE', record.event_term_code or '')
                    hm_xml.put('CASE_MED_ORG', safe_str(record.medical_organization_name))
                    hm_xml.put('CASE_PROFILE', safe_str(record.event_profile_name or ''))
                    hm_xml.put('CASE_SPEC', safe_str(record.event_worker_speciality_name or ''))
                    hm_xml.put('CASE_RESULT', safe_str(record.treatment_result_name or ''))
                    event_invoiced = record.event_invoiced_payment
                    hm_xml.put('CASE_SUM', set_precision(float(event_invoiced), 2))
                    hm_xml.put('CASE_DIAGNOSE', safe_str(record.event_basic_disease_name or '')[:254])
                    hm_xml.put('CASE_PAYMENT_TYPE', record.event_payment_type_code or '')
                    if (record.event_comment or '').startswith('F'):
                        is_examination = '1'
                    else:
                        is_examination = '0'
                    hm_xml.put('IS_DISPANSERISATION', is_examination)

                    event_counter += 1

                hm_xml.start('EXP_PROVIDED_SERVICE')
                hm_xml.put('CASE_GUID', record.event_guid)
                hm_xml.put('SRV_GUID', record.service_guid)
                hm_xml.put('SRV_CODE', record.service_code or '')
                hm_xml.put('DESCRIPTION', safe_str(record.service_name or ''))
                start_date = record.service_start_date
                end_date = record.service_end_date
                if start_date:
                    start_date += 'T00:00:00'
                if end_date:
                    end_date += 'T00:00:00'
                hm_xml.put('DATE_START', start_date)
                hm_xml.put('DATE_END', end_date)
                hm_xml.put('SRV_COUNT', record.quantity or '1.00')
                hm_xml.put('SRV_SPEC', safe_str(record.service_worker_speciality_name or ''))
                hm_xml.put('DOCTOR_CODE', safe_str(record.service_worker_code or ''))
                if record.service_payment_type_code != 2:
                    accepted_payment = record.service_accepted_payment or 0
                else:
                    accepted_payment = 0
                hm_xml.put('SRV_SUM', set_precision(float(accepted_payment), 2))
                hm_xml.end('EXP_PROVIDED_SERVICE')

                comment = record.event_comment
                previous_record_uid = record.event_uid

        hm_xml.end('EXP_CASE')
        hm_xml.end('EXP_CASES')

        print datetime.datetime.now()


class Command(BaseCommand):
    help = 'export big XML'
    
    def handle(self, *args, **options):
        main()