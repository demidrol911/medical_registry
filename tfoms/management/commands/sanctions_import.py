# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import (
    ProvidedService, MedicalRegister, IDC, MedicalService, MedicalOrganization,
    Sanction, PaymentFailureCause, MedicalError)
from django.db.models import Q
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
import datetime
import csv
import kinterbasdb
import sanction_query


FIO, DR, KMU, S_OPL, S_SN, STARTDATE, ENDDATE, NUMBER, PERIOD_USL, CODE_MO,\
S_POL, K_U, DS, TN1, SUM_USL, FFOMS, TFOMS, S_PPP, S_SNK, SNILS, SANK_TYPE,\
DOC_NUMBER, STATUS, S_SNT, S_SNF, SANCTION_DATE,\
ANAMNESIS_NUMBER, LPU_NUMBER = range(0, 28)

sanction_start_date = '2014-12-01'
sanction_end_date = '2014-12-31'
z = csv.writer(open('d:/work/duplicates_%s.csv' % sanction_start_date, 'wb'), delimiter=';')


def find(rec):
    old_service_query = """
        select DISTINCT ps.id_pk, ps.end_date, mr.year, mr.period
        from provided_service ps
            join medical_service ms
                On ps.code_fk = ms.id_pk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record
                on pe.record_fk = medical_register_record.id_pk
            join medical_register mr
                on medical_register_record.register_fk = mr.id_pk
            JOIN patient p
                on p.id_pk = medical_register_record.patient_fk
            JOIN medical_organization department
                on department.id_pk = ps.department_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk or idc.id_pk = pe.basic_disease_fk
            LEFT JOIN idc idc1
                on idc1.id_pk = pe.initial_disease_fk
            LEFT JOIN idc idc2
                on idc2.id_pk = pe.basic_disease_fk
        where mr.is_active
            and (((REPLACE(coalesce(p.insurance_policy_series, ''), '99', '') || coalesce(p.insurance_policy_number, '') ) = %(policy)s)
            or (upper(p.last_name || ' ' || p.first_name || ' ' || p.middle_name ) = upper(%(person)s)))
            and ms.code = %(service)s
            and (((ms.group_fk not in (7, 9, 11, 12, 13, 15, 16, 25, 26) or ms.group_fk is null)
            and (idc.idc_code like %(disease)s or idc1.idc_code like %(disease)s or idc2.idc_code like %(disease)s))
            or (ms.group_fk in (7, 9, 11, 12, 13, 15, 16, 25, 26)
            and (ps.basic_disease_fk is null or
            (idc.idc_code like %(disease)s or idc1.idc_code like %(disease)s or idc2.idc_code like %(disease)s))))
            and (
                (ps.start_date = %(start_date)s or ps.end_date = %(start_date)s)
                or (ps.start_date = %(end_date)s or ps.end_date = %(end_date)s)
            )
            and (upper(pe.anamnesis_number) = upper(%(anamnesis)s) or upper(%(anamnesis)s) = '')
            and (department.old_code = %(department)s or mr.organization_code = %(organization_code)s)
            --%(organization_code)s
            and ps.payment_type_fk in (2, 4)
        order by ps.end_date, mr.year, mr.period DESC
        --limit 1
    """

    new_service_query = """
        select DISTINCT ps.id_pk, ps.end_date, mr.year, mr.period
        from provided_service ps
            join medical_service ms
                On ps.code_fk = ms.id_pk
            join provided_event pe
                on ps.event_fk = pe.id_pk
            join medical_register_record
                on pe.record_fk = medical_register_record.id_pk
            join medical_register mr
                on medical_register_record.register_fk = mr.id_pk
            JOIN patient p
                on p.id_pk = medical_register_record.patient_fk
            JOIN medical_organization department
                on department.id_pk = ps.department_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk or idc.id_pk = pe.basic_disease_fk
            LEFT JOIN idc idc1
                on idc1.id_pk = pe.initial_disease_fk
            LEFT JOIN idc idc2
                on idc2.id_pk = pe.basic_disease_fk
        where mr.is_active
            and (((REPLACE(coalesce(p.insurance_policy_series, ''), '99', '') || coalesce(p.insurance_policy_number, '') ) = %(policy)s)
            or (upper(p.last_name || ' ' || p.first_name || ' ' || p.middle_name ) = upper(%(person)s)))
            and ms.code = %(service)s
            and (((ms.group_fk not in (7, 9, 11, 12, 13, 15, 16, 25, 26) or ms.group_fk is null)
            and (idc.idc_code like %(disease)s or idc1.idc_code like %(disease)s or idc2.idc_code like %(disease)s))
            or (ms.group_fk in (7, 9, 11, 12, 13, 15, 16, 25, 26)
            and (ps.basic_disease_fk is null or
            (idc.idc_code like %(disease)s or idc1.idc_code like %(disease)s or idc2.idc_code like %(disease)s))))
            and (ps.end_date = %(end_date)s or ps.start_date = %(start_date)s)
            -- %(start_date)s
            --and (upper(pe.anamnesis_number) = upper(%(anamnesis)s) or upper(%(anamnesis)s) = '')
            and (department.old_code = %(department)s or mr.organization_code = %(organization_code)s)
            and ps.payment_type_fk in (2, 4)
            --and
        order by ps.end_date, mr.year, mr.period DESC
        --limit 1
    """

    policy = rec[S_POL].split() if rec[S_POL] else None
    if policy:
        if len(policy) >= 2:
            series = policy[0]
            number = ' '.join(policy[1:])
        else:
            series = ''
            number = policy[0]
    else:
        series = ''
        number = ''

    service_length = len(rec[KMU])
    if service_length < 6:
        service_code = '0' * (6-service_length) + rec[KMU]
    else:
        service_code = rec[KMU]

    if rec[ENDDATE] < datetime.datetime.strptime('2014-01-01', "%Y-%m-%d").date():
        query = old_service_query
    else:
        query = new_service_query

    service = list(ProvidedService.objects.raw(
        query, dict(policy=(series+number).replace(' ', ''),
                    person=rec[FIO],
                    service=service_code, disease=rec[DS][:3]+'%',
                    start_date=rec[STARTDATE], end_date=rec[ENDDATE],
                    anamnesis=rec[ANAMNESIS_NUMBER] or '',
                    department=rec[LPU_NUMBER],
                    organization_code=rec[CODE_MO])))
    if service:
        service = service[0]
    else:
        service = None

    return service


def main():
    connect_fb = kinterbasdb.connect(
        dsn='s01-2800-1c01:d:/fb/expert_20.gdb', user='sysdba', password='masterkey',
        charset='win1251')
    cursor_fb = connect_fb.cursor()

    n = csv.writer(open('d:/work/none_%s.csv' % sanction_start_date, 'wb'), delimiter=';')

    n.writerow((
        'FIO', 'DR', 'KMU', 'S_OPL', 'S_SN', 'STARTDATE', 'ENDDATE', 'NUMBER',
        'PERIOD_USL', 'CODE_MO', 'S_POL', 'K_U', 'DS', 'TN1', 'SUM_USL',
        'FFOMS', 'TFOMS', 'S_PPP', 'S_SNK', 'SNILS', 'SANK_TYPE', 'DOC_NUMBER',
        'STATUS', 'S_SNT', 'S_SNF', 'SANCTION_DATE', 'ANAMNESIS_NUMBER', 'LPU')
    )

    Sanction.objects.filter(date__gte=sanction_start_date,
                            date__lte=sanction_end_date,
                            type__in=(2, 3)).delete()

    cursor_fb.execute(sanction_query.q, (sanction_start_date,
                                         sanction_end_date))
    data = cursor_fb.fetchall()

    none = 0
    print len(data)

    for i, rec in enumerate(data):
        if i % 1000 == 0:
            print i

        service = find(rec)

        if not service:
            w = []

            for r in rec:
                if isinstance(r, unicode):
                    w.append(r.encode('utf-8'))
                else:
                    w.append(r)

            none += 1

            n.writerow(w)
        else:
            sanction_date = datetime.datetime.strptime(
                rec[SANCTION_DATE], '%d.%m.%Y')
            sanction_act = rec[DOC_NUMBER]

            if rec[SANK_TYPE] in (6, 17):
                sanction_type = 2
            elif rec[SANK_TYPE] in (5, 7, 19):
                sanction_type = 3
            else:
                raise ValueError("Unknown sanctions type!")

            underpayment = rec[S_SN]
            penalty = rec[S_SNK]

            try:
                failure = PaymentFailureCause.objects.get(number=rec[NUMBER])
            except:
                last_failure = PaymentFailureCause.objects.latest('pk')
                PaymentFailureCause.objects.create(pk=last_failure.pk + 1,
                                                   code=last_failure.pk + 1,
                                                   number=rec[NUMBER])
                failure = PaymentFailureCause.objects.get(number=rec[NUMBER])
                print rec[NUMBER], failure

            Sanction.objects.create(
                date=sanction_date, type_id=sanction_type, act=sanction_act,
                underpayment=underpayment, penalty=penalty, service=service,
                failure_cause=failure)

    print i

    connect_fb.close()


class Command(BaseCommand):
    help = 'export big XML'
    
    def handle(self, *args, **options):
        main()