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


def find(rec):
    query = """
select ps.id_pk
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
    JOIN idc
        on idc.id_pk = ps.basic_disease_fk
where mr.is_active
    and (REPLACE(coalesce(p.insurance_policy_series, ''), '99', '') || coalesce(p.insurance_policy_number, '') ) = %(policy)s
    and ms.code = %(service)s
    and idc.idc_code like %(disease)s
    and (ps.end_date = %(date)s or ps.start_date = %(date)s)
    and upper(pe.anamnesis_number) = upper(%(anamnesis)s)
order by ps.end_date, mr.year, mr.period DESC
limit 1
    """
    name = rec[FIO]
    if name:
        name = name.split()
    else:
        name = [None, None, None]

    q = Q(event__record__register__is_active=True)
    q &= Q(department__old_code=rec[LPU_NUMBER])

    if len(name) > 3:
        last_name = name[0].upper()
        first_name = name[1].upper()
        middle_name = '%s %s' % (name[2].strip().upper(), name[3].strip().upper())

    elif len(name) == 0:
        last_name = None
        first_name = None
        middle_name = None

    elif len(name) == 3:
        last_name = name[0].upper()
        first_name = name[1].upper()
        middle_name = name[2].upper()

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

    if series:
        q &= Q(event__record__patient__insurance_policy_series=series)
    q &= Q(event__record__patient__insurance_policy_number=number)
    q &= Q(code__code=service_code)
    q &= Q(payment_type_id__in=(2, 4))
    """
    try:
        service = ProvidedService.objects.get(q & Q(basic_disease__idc_code__startswith=rec[DS][:3]) & (Q(start_date=rec[STARTDATE]) | Q(end_date=rec[STARTDATE])))
    except ObjectDoesNotExist:
        try:
            service = ProvidedService.objects.get(q & (Q(start_date=rec[STARTDATE]) | Q(end_date=rec[STARTDATE])))
        except ObjectDoesNotExist:
            try:
                service = ProvidedService.objects.get(q & Q(basic_disease__idc_code__startswith=rec[DS][:3]) & (Q(start_date=rec[ENDDATE]) | Q(end_date=rec[ENDDATE])))
            except ObjectDoesNotExist:
                print 'not found', rec[LPU_NUMBER], series, number, service_code, rec[DS], rec[STARTDATE], rec[ANAMNESIS_NUMBER]
                service = None
        except MultipleObjectsReturned:
            print 'multiple-2', rec[LPU_NUMBER], series, number, service_code, rec[DS], rec[STARTDATE], rec[ANAMNESIS_NUMBER]
            service = service = ProvidedService.objects.filter(q & (Q(start_date=rec[STARTDATE]) | Q(end_date=rec[STARTDATE]))).order_by('-start_date')[0]
    except MultipleObjectsReturned:
        service = ProvidedService.objects.filter(q & Q(basic_disease__idc_code__startswith=rec[DS][:3]) & (Q(start_date=rec[STARTDATE]) | Q(end_date=rec[STARTDATE]))).order_by('-start_date')[0]
        print 'multiple-1', rec[LPU_NUMBER], series, number, service_code, rec[DS], rec[STARTDATE], rec[ANAMNESIS_NUMBER]
    """
    service = list(ProvidedService.objects.raw(
        query, dict(policy=(series+number).replace(' ', ''),
                    service=service_code, disease=rec[DS][:3]+'%',
                    date=rec[STARTDATE], anamnesis=rec[ANAMNESIS_NUMBER])))

    if service:
        service = service[0]
    else:
        print 'not found', rec[LPU_NUMBER], series, number, service_code, rec[DS], rec[STARTDATE], rec[ANAMNESIS_NUMBER]
        service = None
    return service



def main():
    sanction_start_date = '2014-03-01'
    sanction_end_date = '2014-06-30'

    connect_fb = kinterbasdb.connect(
        dsn='gamma:d:/fb/expert_20.gdb', user='sysdba', password='masterkey',
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
        if float(rec[S_SN]) == 0 and float(rec[S_SNK]) == 0:
            continue

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

            if underpayment or penalty:
                try:
                    failure = PaymentFailureCause.objects.get(number=rec[NUMBER])
                except:
                    last_failure = PaymentFailureCause.objects.latest('pk')
                    PaymentFailureCause.objects.create(pk=last_failure.pk + 1,
                                                       code=last_failure.pk + 1,
                                                       number=rec[NUMBER])
                    failure = PaymentFailureCause.objects.get(number=rec[NUMBER])
                    print rec[NUMBER], failure

                Sanction.objects.create(date=sanction_date,
                            type_id=sanction_type,
                            act=sanction_act,
                            underpayment=underpayment,
                            penalty=penalty,
                            service=service,
                            failure_cause=failure)
                #print 'inserted'

        #print i, none
    connect_fb.close()


class Command(BaseCommand):
    help = 'export big XML'
    
    def handle(self, *args, **options):
        main()