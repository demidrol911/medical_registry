# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Q
from tfoms.models import ProvidedService, Sanction, MedicalError, \
    MedicalServiceDisease, MedicalRegister, MedicalRegisterStatus
from collections import defaultdict
from dbfpy import dbf
import os


def get_errors_dict():
    errors = MedicalError.objects.all()
    errors_dict = {}
    for rec in errors:
        errors_dict[rec.old_code] = rec.pk

    return errors_dict


def main():

    ERRORS_CODES = get_errors_dict()

    pse_dir = 'd:/work/pse'
    year, period = '2014', '05'
    files = os.listdir(pse_dir)
    departments = set([filename[1:-4] for filename in files if '.dbf' in filename])
    registers = []

    for department in departments:
        print department
        e_db = dbf.Dbf('%s/e%s.dbf' % (pse_dir, department))
        s_db = dbf.Dbf('%s/s%s.dbf' % (pse_dir, department))

        errors = defaultdict(list)

        for rec in e_db:
            if not rec.deleted or rec['c_err'] not in (None, '', 'HD', 'PA'):
                errors[rec['recid']].append(rec['c_err'])

        snyato = 0
        pofig = 0
        dobavleno = 0
        smena = 0
        kosyak = 0

        #cache = {}
        #for rec in ProvidedService.objects.filter(q):
        #    cache[rec.migration] = rec
        a = True
        for i, rec in enumerate(s_db):
            if rec.deleted:
                continue
            q = Q(event__record__register__year=year)
            q &= Q(event__record__register__period=period)
            q &= Q(department__old_code=department)
            q &= Q(event__record__register__is_active=True)

            policy = rec['sn_pol'].split()
            series = policy[0].decode('cp866')
            number = ''.join(policy[1:]).decode('cp866')
            code = str(rec['cod'])
            code = '0'*(6-len(code)) + code

            if len(number) <= 7 and series != '99':
                q &= Q(event__record__patient__insurance_policy_series=series)
            q &= Q(event__record__patient__insurance_policy_number=number)
            q &= Q(code__code=code)
            if code[:3] not in ('019', '119'):
                q &= Q(basic_disease__idc_code=rec['ds'].decode('cp866').upper())
            q &= Q(worker_code=rec['tn1'].decode('cp866'))
            q &= Q(end_date=rec['d_u'])

            provided_service = ProvidedService.objects.filter(q).order_by('id_pk')

            if not provided_service:
                print 'shit ', series, number, code, rec['ds'].decode('cp866'), rec['tn1'].decode('cp866'), rec['d_u']
                continue

            if provided_service.count() > 1:
                if a:
                    provided_service = provided_service[0]
                    a = False if a else True
                else:
                    provided_service = provided_service[1]
                    a = False if a else True
            else:
                provided_service = provided_service[0]

            error = errors.get(rec['recid'], None)
            #if error and len(error) > 1:
            #    print 'ERROR list', error
            sanction = Sanction.objects.filter(service=provided_service).order_by('-id_pk')

            if error and error[0] not in ('HD', 'H8', 'PA'):

                failure_id = ERRORS_CODES.get(error[0])
                if not failure_id:
                    print error[0]

                if sanction:
                    if sanction[0].error_id == failure_id:
                        provided_service.payment_type_id = 3
                        provided_service.save()
                        kosyak += 1

                    elif sanction[0].error_id != failure_id:
                        sanction[0].error_id = failure_id
                        provided_service.payment_type_id = 3
                        provided_service.save()
                        sanction[0].save()
                        smena += 1
                else:
                    Sanction.objects.create(
                        type_id=1, service=provided_service,
                        underpayment=provided_service.accepted_payment,
                        error_id=failure_id)
                    provided_service.payment_type_id = 3
                    provided_service.accepted_payment = 0
                    provided_service.save()
                    if failure_id == 40:
                        service_disease = MedicalServiceDisease.objects.filter(
                            service=provided_service.code,
                            disease=provided_service.basic_disease)
                        service_disease.delete()
                    dobavleno += 1
            else:
                if sanction:
                    provided_service.payment_type_id = 1
                    provided_service.save()
                    snyato += 1
                    registers.append(provided_service.event.record.register.pk)
                    if 40 in sanction.values_list('error_id', flat=True):
                        MedicalServiceDisease.objects.create(
                            service=provided_service.code,
                            disease=provided_service.basic_disease
                        )
                    sanction.delete()
                else:
                    pofig += 1
        else:
            registers_set = MedicalRegister.objects.filter(
                is_active=True, year=year, period=period,
                organization_code=provided_service.event.record.register.organization_code)
            registers_set.update(status=MedicalRegisterStatus.objects.get(pk=5))
            provided_service.event.record.register.save()

        registers_set = MedicalRegister.objects.filter(pk__in=set(registers))
        registers_set.update(status=MedicalRegisterStatus.objects.get(pk=5))
        registers_set = MedicalRegister.objects.filter(
            year=year, period=period, is_active=True,
            organization_code=provided_service.event.record.register.organization_code)
        registers_set.update(status=MedicalRegisterStatus.objects.get(pk=5))
        print provided_service.event.record.register.organization_code, department, snyato, dobavleno, smena, pofig, kosyak


class Command(BaseCommand):
    help = u'Импортим PSE'

    def handle(self, *args, **options):
        main()