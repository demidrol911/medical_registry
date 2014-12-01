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
        return str(var.encode('cp1251'))
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


def get_patients(period, start_date, end_date):
    attachment_date = '2014-%s-01' % str(int(period)+1)
    query = """
        select p1.*, medOrg.code as attachment_code
            , person_id_type.code as id_type
        from
            patient p1
            left join insurance_policy
                on p1.insurance_policy_fk = insurance_policy.version_id_pk
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
            left join attachment
                on attachment.id_pk = (
                    select max(id_pk)
                    from attachment
                    where
                        person_fk = person.version_id_pk
                        and status_fk = 1
                        and confirmation_date <= %s
                        and attachment.is_active)
            LEFT join medical_organization medOrg
                on (
                    medOrg.id_pk = attachment.medical_organization_fk
                    and medOrg.parent_fk is null
                ) or medOrg.id_pk = (
                    select parent_fk
                    from medical_organization
                    where id_pk = attachment.medical_organization_fk
                )
            LEFT join person_id_type
                on p1.person_id_type_fk = person_id_type.id_pk

        where p1.id_pk in (
            select DISTINCT medical_register_record.patient_fk
            from medical_register
            join medical_register_record
                on medical_register.id_pk = medical_register_record.register_fk
            join provided_event
                on provided_event.record_fk = medical_register_record.id_pk
            join provided_service
                on provided_service.event_fk = provided_event.id_pk
            join provided_service_sanction pss
                on provided_service.id_pk = pss.service_fk and pss.type_fk in (2, 3)
            where
                medical_register.is_active
                and pss.date between %s and %s
                --and medical_register.organization_code in ('280017', '280020',
                --                                           '280084')
            )
        """
    return Patient.objects.raw(query, [attachment_date, start_date, end_date])


def get_records(register_element, start_date, end_date):
    query = """
        select DISTINCT
            provided_service.id_pk,
            medical_register_record.id as record_uid,
            patient.id as patient_uid,
            patient.last_name as patient_first_name,
            patient.first_name as patient_last_name,
            patient.middle_name as patient_middle_name,
            patient.gender_fk as patient_gender,
            patient.birthdate as patient_birthdate,
            patient.agent_last_name as patient_agent_first_name,
            patient.agent_first_name as patient_agent_last_name,
            patient.agent_middle_name as patient_agent_middle_name,
            patient.agent_gender_fk as patient_agent_gender,
            patient.agent_birthdate as patient_agent_birthdate,
            patient.birthplace as patient_birthplace,
            patient.person_id_series,
            patient.person_id_number,
            patient.snils as patient_snils,
            patient.okato_registration,
            patient.okato_residence,
            patient.insurance_policy_type_fk as insurance_policy_type,
            patient.insurance_policy_series as insurance_policy_series,
            patient.insurance_policy_number as insurance_policy_number,
            patient.newborn_code as newborn_code,
            patient.weight as weight,
            medOrg.code as attachment_code,
            person_id_type.code as patient_id_type,
            provided_event.id as event_uid,
            provided_event.term_fk as event_term_code,
            provided_event.kind_fk as event_kind_code,
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
            medical_organization.old_code as event_department_code,
            provided_event.division_fk,
            event_profile.code as event_profile_code,
            provided_event.is_children_profile as event_is_children,
            provided_event.anamnesis_number as anamnesis_number,
            (
                select min(ps2.start_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_start_date,
            (
                select max(ps2.end_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_end_date,
            idc_initial.idc_code as event_initial_disease_code,
            idc_basic.idc_code as event_basic_disease_code,
                idc_basic.idc_code as event_basic_disease_code,

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

            treatment_result.code as treatment_result_code,
            treatment_outcome.code as treatment_outcome_code,
            medical_worker_speciality.code as event_worker_speciality_code,
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
            (
                select sum(provided_service_sanction.underpayment)
                from provided_service ps2
                    join provided_service_sanction
                        on provided_service_sanction.service_fk = ps2.id_pk
                            and provided_service_sanction.id_pk = (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                            )
                            and ps2.payment_type_fk in (3, 4)
                where ps2.event_fk = provided_event.id_pk
                    and provided_service_sanction.type_fk = 1
            ) as event_sanctions_mek_sum,
            (
                select sum(case provided_service_sanction.underpayment - ps2.accepted_payment between -0.02 and 0.02
                        when true then ps2.accepted_payment
                        else provided_service_sanction.underpayment
                        end) + sum(provided_service_sanction.penalty)
                from provided_service ps2
                    join provided_service_sanction
                        on provided_service_sanction.service_fk = ps2.id_pk
                            and ps2.payment_type_fk in (2, 4)
                where ps2.event_fk = provided_event.id_pk
                    and provided_service_sanction.type_fk in (2, 3)
                    and provided_service_sanction.date between %(start_date)s and %(end_date)s
            ) as event_sanctions_mee_ekmp_sum,

            ARRAY(SELECT ROW(ps2.id
                    , case provided_service_sanction.underpayment - ps2.accepted_payment between -0.02 and 0.02
                        when true then ps2.accepted_payment
                        else provided_service_sanction.underpayment
                        end
                    , provided_service_sanction.penalty
                    , provided_service_sanction.type_fk
                    , provided_service_sanction.failure_cause_fk
                    , ''
                    , 1
                    , ps2.accepted_payment
                    , provided_service_sanction.id_pk
                    , provided_service_sanction.date)
                from provided_service ps2
                    join provided_service_sanction
                        on provided_service_sanction.service_fk = ps2.id_pk
                            and ps2.payment_type_fk in (2, 4)
                where ps2.event_fk = provided_event.id_pk
                    and provided_service_sanction.type_fk in (2, 3, 4)
                    and provided_service_sanction.date between %(start_date)s and %(end_date)s
            ) as event_sanctions_mee_ekmp,

            provided_event.examination_result_fk as examination_result_code,
            provided_event.comment as event_comment,
            provided_service.id_pk as service_pk,
            provided_service.id as service_uid,
            medical_register.organization_code as service_organization_code,
            service_department.old_code as service_department_code,
            service_division.code as service_division_code,
            service_profile.code as service_profile_code,
            provided_service.is_children_profile as service_is_children,
            provided_service.start_date as service_start_date,
            provided_service.end_date as service_end_date,
            service_idc_basic.idc_code as service_basic_disease_code,
            medical_service.code as service_code,
            provided_service.quantity,
            provided_service.tariff as service_tariff,
            provided_service.invoiced_payment as service_invoiced_payment,
            payment_type.code as service_payment_type_code,
            provided_service.accepted_payment as service_accepted_payment,
            --medical_error.failure_cause_fk as service_failure_cause_code,
            --pss.underpayment as service_sanction_mek,
            service_worker_speciality.code as service_worker_speciality_code,
            provided_service.worker_code as service_worker_code,
            provided_service.comment as service_comment,
            medical_register.year, medical_register.period,
            medical_register.organization_code,
            medical_register_record.id,
            provided_event.id,
            provided_service.id
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
            left join attachment
                on attachment.id_pk = (
                    select max(id_pk)
                    from attachment
                    where
                        person_fk = person.version_id_pk
                        and status_fk = 1
                        and confirmation_date <= (medical_register.year || '-' || medical_register.period || '-' || '01')::DATE
                        and attachment.is_active)
            LEFT join medical_organization medOrg
                on (
                    medOrg.id_pk = attachment.medical_organization_fk
                    and medOrg.parent_fk is null
                ) or medOrg.id_pk = (
                    select parent_fk
                    from medical_organization
                    where id_pk = attachment.medical_organization_fk
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

            JOIN medical_organization
                ON medical_organization.id_pk = provided_event.department_fk
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
            JOIN provided_service_sanction pss2
                on pss2.id_pk = (
                    select max(id_pk)
                    from provided_service_sanction
                    where service_fk = provided_service.id_pk
                        and type_fk in (2, 3, 4)
                        and date between %(start_date)s and %(end_date)s
                )
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
        start_date=start_date, end_date=end_date,
        year=register_element[0], period=register_element[1],
        organization=register_element[2]))


def main():
    sanction_start_date = '2014-08-01'
    sanction_end_date = '2014-08-31'
    period = '10'

    print datetime.datetime.now()
    registers = Sanction.objects.filter(
        service__event__record__register__is_active=True,
        date__gte=sanction_start_date,
        date__lte=sanction_end_date
        ).values_list(
            'service__event__record__register__year',
            'service__event__record__register__period',
            'service__event__record__register__organization_code'
        ).distinct().order_by(
            'service__event__record__register__organization_code',
            'service__event__record__register__year',
            'service__event__record__register__period')

    file_regular = 'HX28002T28_14%s1' % period
    file_patients = 'LX28002T28_14%s1' % period

    lm_xml = writer.Xml('%s.xml' % file_patients)
    lm_xml.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
    lm_xml.start('PERS_LIST')
    lm_xml.start('ZGLV')
    lm_xml.put('VERSION', '2.1')
    lm_xml.put('DATA', '18.%s.2014' % period)
    lm_xml.put('FILENAME', file_patients)
    lm_xml.put('FILENAME1', file_regular)
    lm_xml.end('ZGLV')

    XML_TYPES = dict(SERVICE_XML_TYPES)
    EXAMINIATIONS = dict(EXAMINATION_TYPES)
    new_register = False

    hm_xml = writer.Xml('%s.XML' % file_regular)

    hm_xml.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
    hm_xml.start('ZL_LIST')

    hm_xml.start('ZGLV')
    hm_xml.put('VERSION', '2.1')
    hm_xml.put('DATA', '18.%s.2014' % period)
    hm_xml.put('FILENAME', file_regular)
    hm_xml.end('ZGLV')
    print registers
    for index, register_element in enumerate(registers):
        records = list(get_records(register_element, sanction_start_date, sanction_end_date))
        payments_types = [rec.service_payment_type_code for rec in records]

        if set(payments_types) == set((2, )):
            continue

        if not records:
            continue
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
            hm_xml.put('COMENTSL', safe_str(comment))
            hm_xml.end('SLUCH')
            hm_xml.end('ZAP')
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
        hm_xml.start('SCHET')
        hm_xml.put('CODE', index+1)
        hm_xml.put('CODE_MO', register.organization_code)
        hm_xml.put('YEAR', register.year)
        hm_xml.put('MONTH', register.period)
        hm_xml.put('NSCHET', index+1)
        hm_xml.put('DSCHET', register.invoice_date.strftime("%Y-%m-%d"))
        hm_xml.put('PLAT', '28002')
        hm_xml.put('SUMMAV', invoiced_payment)
        hm_xml.put('COMENTS', safe_str(register.invoice_comment))
        hm_xml.put('SUMMAP', accepted_payment)
        hm_xml.put('SANK_MEK', sanctions_mek)
        hm_xml.put('SANK_MEE', sanctions_mee)
        hm_xml.put('SANK_EKMP', sanctions_ekmp)
        #if register.type > 2:
        #    hm_xml.put('DISP', EXAMINIATIONS[register.type-2].encode('cp1251'))
        hm_xml.end('SCHET')

        print register.organization_code, len(records)

        for i, record in enumerate(records):
            event_is_children_profile = '1' if record.event_is_children else '0'
            if record.event_payment_type_code in ('2', 2):
                continue

            if record.record_uid != current_record:
                if i != 0:
                    hm_xml.put('COMENTSL', safe_str(comment))
                    hm_xml.end('SLUCH')
                    hm_xml.end('ZAP')
                    event_counter = 0
                current_record = record.record_uid

                patient_id = record.patient_uid
                patient_policy_type = record.insurance_policy_type
                patient_policy_series = record.insurance_policy_series
                patient_policy_number = record.insurance_policy_number
                patient_is_newborn = record.newborn_code if record.newborn_code else '0'

                lm_xml.start('PERS')
                lm_xml.put('ID_PAC', safe_str(record.patient_uid))
                last_name = safe_str(record.patient_last_name)
                lm_xml.put('FAM', last_name)
                first_name = safe_str(record.patient_first_name)
                lm_xml.put('IM', first_name)
                middle_name = safe_str(record.patient_middle_name)
                lm_xml.put('OT', middle_name or u'НЕТ'.encode('cp1251'))
                lm_xml.put('W', safe_int(record.patient_gender))
                birthdate = record.patient_birthdate
                if not birthdate:
                    birthdate = ''
                lm_xml.put('DR', birthdate)
                lm_xml.put('FAM_P', safe_str(record.patient_agent_last_name))
                lm_xml.put('IM_P', safe_str(record.patient_agent_first_name))
                lm_xml.put('OT_P', safe_str(record.patient_agent_middle_name))
                lm_xml.put('W_P', safe_int(record.patient_agent_gender))
                birthdate = record.patient_agent_birthdate
                if not birthdate:
                    birthdate = ''
                lm_xml.put('DR_P', birthdate)
                lm_xml.put('MR', safe_str(record.patient_birthplace))
                lm_xml.put('DOCTYPE', safe_int(record.patient_id_type))
                lm_xml.put('DOCSER', safe_str(record.person_id_series))
                lm_xml.put('DOCNUM', safe_str(record.person_id_number))
                lm_xml.put('SNILS', safe_str(record.patient_snils))
                lm_xml.put('OKATOG', safe_str(record.okato_registration))
                lm_xml.put('OKATOP', safe_str(record.okato_residence))
                attachment_code = record.attachment_code
                lm_xml.put('COMENTP', attachment_code or '')
                lm_xml.end('PERS')

                hm_xml.start('ZAP')
                hm_xml.put('N_ZAP', record.record_uid)
                hm_xml.put('PR_NOV', '0')
                hm_xml.start('PACIENT')
                hm_xml.put('ID_PAC', safe_str(patient_id))
                hm_xml.put('VPOLIS', safe_int(patient_policy_type))
                hm_xml.put('SPOLIS', safe_str(patient_policy_series))
                hm_xml.put('NPOLIS', safe_str(patient_policy_number))
                hm_xml.put('ST_OKATO', '')
                hm_xml.put('SMO', '28002')
                hm_xml.put('SMO_OGRN', '1022800508488')
                hm_xml.put('SMO_OK', '10000')
                hm_xml.put('SMO_NAM', u'ОАО "МСК "ДАЛЬМЕДСТРАХ"'.encode('cp1251'))
                hm_xml.put('NOVOR', patient_is_newborn)
                hm_xml.put('VNOV_D', record.weight or '')
                hm_xml.end('PACIENT')

            if record.event_uid != current_event:
                current_event = record.event_uid
                if event_counter != 0:
                    hm_xml.put('COMENTSL', safe_str(comment))
                    hm_xml.end('SLUCH')

                hm_xml.start('SLUCH')
                hm_xml.put('IDCASE', record.event_uid)
                hm_xml.put('USL_OK', record.event_term_code or '')
                hm_xml.put('VIDPOM', record.event_kind_code or '')
                hm_xml.put('FOR_POM', record.event_form_code or '')
                hm_xml.put('VID_HMP', record.hitech_kind_code or '')
                hm_xml.put('METOD_HMP', record.hitech_method_code or '')
                hm_xml.put('NPR_MO', record.event_referred_organization_code or '')
                hm_xml.put('EXTR', record.event_hospitalization_code or '')
                hm_xml.put('LPU', record.event_organization_code or '')
                hm_xml.put('LPU_1', record.event_department_code or '')
                hm_xml.put('PODR', record.event_division_code or '')
                hm_xml.put('PROFIL', record.event_profile_code or '')
                hm_xml.put('DET', event_is_children_profile)
                hm_xml.put('NHISTORY', record.anamnesis_number.encode('cp1251'))
                start_date = record.event_start_date
                end_date = record.event_end_date

                if start_date > end_date:
                    hm_xml.put('DATE_1', end_date)
                    hm_xml.put('DATE_2', start_date)
                else:
                    hm_xml.put('DATE_1', start_date)
                    hm_xml.put('DATE_2', end_date)
                hm_xml.put('DS0', (record.event_initial_disease_code or '').encode('cp1251'))
                hm_xml.put('DS1', (record.event_basic_disease_code or '').encode('cp1251'))
                for rec in record.event_concomitant_disease_code:
                    hm_xml.put('DS2', rec or '')
                for rec in record.event_complicated_disease_code:
                    hm_xml.put('DS3', rec or '')
                hm_xml.put('VNOV_M', record.weight or '')
                hm_xml.put('CODE_MES1', '')
                hm_xml.put('CODE_MES2', '')
                hm_xml.put('RSLT', record.treatment_result_code or '')
                hm_xml.put('ISHOD', record.treatment_outcome_code or '')
                hm_xml.put('PRVS', record.event_worker_speciality_code or '')
                hm_xml.put('VERS_SPEC', record.speciality_dict_version or '')
                hm_xml.put('IDDOKT', (record.event_worker_code or '').encode('cp1251'))
                hm_xml.put('OS_SLUCH', record.event_special_code or '')
                hm_xml.put('RSLT_D', record.examination_result_code or '')
                hm_xml.put('IDSP', record.event_payment_method_code or '')
                hm_xml.put('ED_COL', record.event_payment_units_number or 0)
                hm_xml.put('TARIF', round(float(record.event_tariff or 0), 2))
                hm_xml.put('SUMV', set_precision(float(record.event_invoiced_payment or 0), 2))
                hm_xml.put('OPLATA', record.event_payment_type_code or '')

                hm_xml.put('SUMP', set_precision(float(record.event_accepted_payment or 0), 2))
                hm_xml.put('SANK_IT', set_precision(float(record.event_sanctions_mee_ekmp_sum or 0), 2))
                #s = record.event_sanctions_mek[1:-1].replace('"', '').replace("(", '').replace('),', ';').replace(')', '')
                s2 = record.event_sanctions_mee_ekmp[1:-1].replace('"', '').replace("(", '').replace('),', ';').replace(')', '')
                """
                if s:
                    sanctions = s.split(';')

                    for rec in sanctions:
                        sanc_rec = rec.split(',')
                        hm_xml.start('SANK')
                        hm_xml.put('S_CODE', sanc_rec[0])
                        hm_xml.put('S_SUM', set_precision(float(sanc_rec[1] or 0), 2))
                        hm_xml.put('S_TIP', sanc_rec[2])
                        hm_xml.put('S_OSN', sanc_rec[3] or '')
                        hm_xml.put('S_COM', '')
                        hm_xml.put('S_IST', sanc_rec[5])
                        hm_xml.end('SANK')
                """
                if s2:
                    sanctions = s2.split(';')

                    for rec in sanctions:
                        sanc_rec = rec.split(',')
                        hm_xml.start('SANK')
                        hm_xml.put('S_CODE', sanc_rec[0])
                        hm_xml.put('S_SUM', set_precision(float(sanc_rec[1] or 0), 2))
                        hm_xml.put('S_ORG', set_precision(float(sanc_rec[2] or 0), 2))
                        hm_xml.put('S_TIP', sanc_rec[3])
                        hm_xml.put('S_OSN', sanc_rec[4])
                        hm_xml.put('S_COM', '')
                        hm_xml.put('S_IST', sanc_rec[6])
                        #hm_xml.put('PKEY', sanc_rec[8])
                        #hm_xml.put('SDATE', sanc_rec[9])
                        hm_xml.end('SANK')
                event_counter += 1

                service_is_children_profile = '1' if record.service_is_children else '0'
            hm_xml.start('USL')
            hm_xml.put('IDSERV', record.service_uid)
            hm_xml.put('LPU', record.service_organization_code)
            hm_xml.put('LPU_1', record.service_department_code or '')
            hm_xml.put('PODR', record.service_division_code or '')
            hm_xml.put('PROFIL', record.service_profile_code or '')
            hm_xml.put('VID_VME', '')
            hm_xml.put('DET', service_is_children_profile)
            start_date = record.service_start_date
            end_date = record.service_end_date

            if start_date > end_date:
                hm_xml.put('DATE_IN', end_date)
                hm_xml.put('DATE_OUT', start_date)
            else:
                hm_xml.put('DATE_IN', start_date)
                hm_xml.put('DATE_OUT', end_date)
            hm_xml.put('DS', (record.service_basic_disease_code or '').encode('cp1251'))
            hm_xml.put('CODE_USL', record.service_code or '')
            hm_xml.put('KOL_USL', record.quantity or '')
            hm_xml.put('TARIF', round(float(record.service_tariff or 0), 2) or 0)
            if record.service_payment_type_code != 2:
                accepted_payment = record.service_accepted_payment or 0
            else:
                accepted_payment = 0
            hm_xml.put('SUMV_USL', set_precision(float(accepted_payment), 2))
            hm_xml.put('PRVS', record.service_worker_speciality_code or '')
            hm_xml.put('CODE_MD', (record.service_worker_code or '').encode('cp1251'))
            hm_xml.put('COMENTU', record.service_comment or '')
            hm_xml.end('USL')

            comment = record.event_comment
            previous_record_uid = record.event_uid

    hm_xml.put('COMENTSL', safe_str(record.event_comment))
    hm_xml.end('SLUCH')
    hm_xml.end('ZAP')
    hm_xml.end('ZL_LIST')
    lm_xml.end('PERS_LIST')

    print datetime.datetime.now()


class Command(BaseCommand):
    help = 'export big XML'
    
    def handle(self, *args, **options):
        main()