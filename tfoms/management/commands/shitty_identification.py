#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Max, Q
from tfoms.models import (
    TariffBasic, ProvidedService, MedicalRegister, TariffNkd,
    ProvidedServiceCoefficient, MedicalOrganization, Sanction,
    ExaminationAgeBracket, ProvidedEvent, Patient, InsurancePolicy)
import csv
from datetime import datetime


def get_patient(fio, dr):
    query = """
        select max(patient.id_pk) as id_pk
        from patient
            join medical_register_record
                on medical_register_record.patient_fk = patient.id_pk
            JOIN medical_register
                on medical_register_record.register_fk = medical_register.id_pk
        where
            medical_register.is_active
            and medical_register.year = '2014'
            and medical_register.period = '04'
            and replace((last_name || first_name || middle_name), ' ', '') = %s
            and birthdate = %s
    """

    return Patient.objects.raw(query, [fio, dr])


def ident_by_passport_fio(patient):
    query = u"""
    select DISTINCT p2.id_pk as patient_id,
        insurance_policy.version_id_pk, operation.reason_stop_fk as stop_reason
    from patient p2
        join person_id
            on person_id.id = (
                select id from (
                    select person_id.id, stop_date
                    from person_id
                        join person
                            on person.version_id_pk = person_id.person_fk
                        join insurance_policy
                            on insurance_policy.person_fk = person.version_id_pk
                    where replace(upper(regexp_replace(person_id.series, '[ -/\\_]', '')), 'I', '1') = replace(upper(regexp_replace(p2.person_id_series, '[ -/\\_]', '')), 'I', '1')
                        and replace(upper(regexp_replace(person_id.number, '[ -/\\_]', '')), 'I', '1') = replace(upper(regexp_replace(p2.person_id_number, '[ -/\\_]', '')), 'I', '1')
                    order by insurance_policy.stop_date desc nulls first
                    limit 1
                ) as T
            ) and person_id.is_active

        JOIN person
            ON person.version_id_pk = (
                select max(version_id_pk)
                from person
                where id = (
                    select id from (
                    select DISTINCT person.id, stop_date
                    from person
                        join insurance_policy
                            on person.version_id_pk = insurance_policy.person_fk
                    where replace(last_name, 'Ё', 'Е') = replace(p2.last_name, 'Ё', 'Е')
                        and replace(first_name, 'Ё', 'Е') = replace(p2.first_name, 'Ё', 'Е')
                        and replace(middle_name, 'Ё', 'Е') = replace(p2.middle_name, 'Ё', 'Е')
                        and birthdate = p2.birthdate
                    ORDER BY stop_date DESC NULLS FIRST
                    limit 1) as T
                )
            )
        join insurance_policy
            on person.version_id_pk = insurance_policy.person_fk
                and insurance_policy.is_active
        JOIN medical_register_record
            on medical_register_record.patient_fk = p2.id_pk
        JOIN medical_register
            ON medical_register.id_pk = medical_register_record.register_fk
        left join operation
            on operation.insurance_policy_fk = insurance_policy.version_id_pk
                and operation.id_pk = (
                    select op.id_pk
                    from operation op
                        join operation_status os
                            on op.id_pk = os.operation_fk
                    where op.insurance_policy_fk = insurance_policy.version_id_pk
                        and os.timestamp = (
                            select min(timestamp)
                            from operation_status
                            where operation_status.operation_fk = op.id_pk)
                    order by timestamp desc limit 1)
    where medical_register.is_active
        and p2.id_pk = %s
    """

    return InsurancePolicy.objects.raw(query, [patient.pk])


def ident_by_snils_io(patient):
    query = u"""
    select DISTINCT p2.id_pk as patient_id,
        insurance_policy.version_id_pk, operation.reason_stop_fk as stop_reason
    from patient p2
        JOIN person
            ON person.version_id_pk = (
                select max(version_id_pk)
                from person
                where id = (
                    select id from (
                    select DISTINCT person.id, start_date, stop_date
                    from person
                        join insurance_policy
                            on person.version_id_pk = insurance_policy.person_fk
                    where replace(first_name, 'Ё', 'Е') = replace(p2.first_name, 'Ё', 'Е')
                        and replace(middle_name, 'Ё', 'Е') = replace(p2.middle_name, 'Ё', 'Е')
                        and birthdate = p2.birthdate
                        and regexp_replace(person.snils, '[ -/\\_]', '') = regexp_replace(p2.snils, '[ -/\\_]', '')
                    ORDER BY start_date, stop_date DESC
                    limit 1) as T
                )
            )
        join insurance_policy
            on person.version_id_pk = insurance_policy.person_fk
                and insurance_policy.is_active
        left join operation
            on operation.insurance_policy_fk = insurance_policy.version_id_pk
                and operation.id_pk = (
                    select op.id_pk
                    from operation op
                        join operation_status os
                            on op.id_pk = os.operation_fk
                    where op.insurance_policy_fk = insurance_policy.version_id_pk
                        and os.timestamp = (
                            select min(timestamp)
                            from operation_status
                            where operation_status.operation_fk = op.id_pk)
                    order by timestamp desc limit 1)
        JOIN medical_register_record
            on medical_register_record.patient_fk = p2.id_pk
        JOIN medical_register
            ON medical_register.id_pk = medical_register_record.register_fk
    where medical_register.is_active
        and p2.id_pk = %s
    """

    return InsurancePolicy.objects.raw(query, [patient.pk])


def ident_by_policy_fio(patient):
    query = """
            select version_id_pk, operation.reason_stop_fk as stop_reason
            from insurance_policy
            left join operation
                on operation.insurance_policy_fk = insurance_policy.version_id_pk
                    and operation.id_pk = (
                        select op.id_pk
                        from operation op
                            join operation_status os
                                on op.id_pk = os.operation_fk
                        where op.insurance_policy_fk = insurance_policy.version_id_pk
                            and os.timestamp = (
                                select min(timestamp)
                                from operation_status
                                where operation_status.operation_fk = op.id_pk)
                        order by timestamp desc limit 1)
            where insurance_policy.id = (
                select insurance_policy.id
                from patient p2
                    JOIN insurance_policy
                        on version_id_pk = (
                            CASE
                            when char_length(p2.insurance_policy_number) <= 8 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        series = p2.insurance_policy_series
                                        and number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                ))
                            when char_length(p2.insurance_policy_number) = 9 THEN
                                (select max(version_id_pk) from insurance_policy where id = (
                                    select id from insurance_policy where
                                        number = p2.insurance_policy_number
                                    order by stop_date DESC NULLS FIRST
                                    LIMIT 1
                                ))
                            when char_length(p2.insurance_policy_number) = 16 THEN
                               (select max(version_id_pk) from insurance_policy where id = (
                                    select insurance_policy.id from insurance_policy
                                        join person
                                            on insurance_policy.person_fk = person.version_id_pk
                                                and (
                                                    (person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name
                                                        and person.birthdate = p2.birthdate)
                                                    or

                                                    ((

                                                        (person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name)
                                                        or (person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        ) or (person.last_name = p2.last_name
                                                        and person.middle_name = p2.middle_name)
                                                    ) and person.birthdate = p2.birthdate)
                                                    or (
                                                        person.last_name = p2.last_name
                                                        and person.first_name = p2.first_name
                                                        and person.middle_name = p2.middle_name
                                                    )
                                                )

                                    where
                                        enp = p2.insurance_policy_number
                                    order by stop_date desc NULLS FIRST
                                    LIMIT 1
                                ))
                            else
                                NULL
                            end
                        )
                    join person
                        on insurance_policy.person_fk = person.version_id_pk
                            and (
                                (
                                    (
                                        p2.first_name = person.first_name
                                        or p2.middle_name = person.middle_name
                                        or p2.last_name = person.last_name
                                    ) and p2.birthdate = person.birthdate
                                ) or (
                                    p2.first_name = person.first_name
                                    and p2.middle_name = person.middle_name
                                ) or (p2.snils = person.snils)
                            )
                where p2.id_pk = %s
                order by insurance_policy.version_id_pk DESC
                limit 1
            ) and is_active
    """

    return InsurancePolicy.objects.raw(query, [patient.pk])


def main():
    MO, FIO, DR, ENDDATE, DS = 2, 3, 4, 7, 8
    cs = csv.reader(open('d:/work/id_smo.csv', 'rb'), delimiter='|')
    #cr = csv.writer(open('d:/work/checked.csv', 'wb'), delimiter='|')

    cr = csv.writer(open('d:/work/checked_for_mo.csv', 'wb'), delimiter='|')

    total_errors = 0

    report_dict = {}

    for index, rec in enumerate(cs):
        if index == 0:
            continue
        fio = rec[FIO].decode('utf-8').replace(' ', '')
        birthdate = datetime.strptime(rec[DR], '%d.%m.%Y').date()
        patient = list(get_patient(fio, birthdate))[0]
        person_tuple = [rec[MO], patient.last_name.encode('utf-8'), patient.first_name.encode('utf-8'),
                        patient.middle_name.encode('utf-8'), patient.birthdate, patient.snils or '',
                        (patient.insurance_policy_series or '').encode('utf-8'),
                        (patient.insurance_policy_number or '').encode('utf-8'),
                        (patient.person_id_series or '').encode('utf-8'),
                        (patient.person_id_number or '').encode('utf-8'),
                        rec[ENDDATE], rec[DS]]
        weight = False
        policy1 = list(ident_by_policy_fio(patient))
        policy2 = list(ident_by_passport_fio(patient))
        policy3 = list(ident_by_snils_io(patient))
        policy4 = not bool(patient.insurance_policy_number.startswith('0177'))

        if not (policy1 or policy2 or policy3 or policy4):
            total_errors += 1

        print patient.last_name, patient.first_name, patient.middle_name, patient.birthdate,

        policy5 = True
        policy6 = True

        if policy1:
            print policy1[0].series, policy1[0].number, policy1[0].enp
            if policy1[0].stop_date and policy1[0].stop_date < datetime.strptime('2011-01-01', '%Y-%m-%d').date() or policy1[0].stop_reason in (1, 3, 4):
                policy5 = False
                total_errors += 1
            if len(patient.insurance_policy_number) == 16 and policy1[0].type_id == 1:
                total_errors += 1
                policy6 = False
        elif policy2:
            print policy2[0].series, policy2[0].number, policy2[0].enp
            if policy2[0].stop_date and policy2[0].stop_date < datetime.strptime('2011-01-01', '%Y-%m-%d').date() or policy2[0].stop_reason in (1, 3, 4):
                policy5 = False
                total_errors += 1
            if len(patient.insurance_policy_number) == 16 and policy2[0].type_id == 1:
                total_errors += 1
                policy6 = False
        elif policy3:
            print policy3[0].series, policy3[0].number, policy3[0].enp
            if policy3[0].stop_date and policy3[0].stop_date < datetime.strptime('2011-01-01', '%Y-%m-%d').date() or policy3[0].stop_reason in (1, 3, 4):
                policy5 = False
                total_errors += 1
            if len(patient.insurance_policy_number) == 16 and policy3[0].type_id == 1:
                total_errors += 1
                policy6 = False

        else:
            print
        if rec[MO] in report_dict:
            if not (policy1 or policy2 or policy3):
                report_dict[rec[MO]]['failed'] += 1
            else:
                if not policy4:
                    report_dict[rec[MO]]['vs'] += 1
                if not policy5:
                    report_dict[rec[MO]]['closed'] += 1
                if not policy6:
                    report_dict[rec[MO]]['enp'] += 1
                if policy4 and policy5 and policy6:
                    report_dict[rec[MO]]['zhopa'] += 1
        else:
            report_dict[rec[MO]] = {'failed': 0, 'vs': 0, 'closed': 0, 'enp': 0,
                                    'zhopa': 0}
        #cr.writerow(person_tuple + [bool(policy1), bool(policy2), bool(policy3), bool(policy4), policy5, policy6])

    print total_errors

    for rec in report_dict:
        cr.writerow([MedicalOrganization.objects.get(parent=None,
                                                     code=rec).name.encode('cp1251')])
        cr.writerow([report_dict[rec]['failed'], report_dict[rec]['vs'], report_dict[rec]['closed'], report_dict[rec]['enp'], report_dict[rec]['zhopa']])


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()