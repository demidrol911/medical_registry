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

service_query = """
        select ps.id_pk,
        case when p.insurance_policy_series is null or replace(p.insurance_policy_series, ' ', '') = '' then '99'
        else p.insurance_policy_series end || coalesce(p.insurance_policy_number, '') ||
        coalesce(ms.code, '') || coalesce(idc.idc_code, '') ||
        coalesce(ps.worker_code, '') || coalesce(ps.end_date, '1900-01-01') ||
        coalesce(pe.anamnesis_number, '') as scache
    from provided_service ps
        join provided_event pe
            on ps.event_fk = pe.id_pk
        join medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN patient p
            on p.id_pk = mrr.patient_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
        join medical_service ms
            on ms.id_pk = ps.code_fk
        LEFT JOIN idc
            on idc.id_pk = ps.basic_disease_fk
        JOIN medical_organization department
            on department.id_pk = ps.department_fk
    where mr.is_active
        and mr.year = %s
        and mr.period = %s
        and department.old_code = %s
    """

mo_query = """
    select DISTINCT mr.id_pk, mr.organization_code
    from provided_service ps
        join provided_event pe
            on ps.event_fk = pe.id_pk
        join medical_register_record mrr
            on mrr.id_pk = pe.record_fk
        JOIN medical_register mr
            on mr.id_pk = mrr.register_fk
        JOIN medical_organization department
            on department.id_pk = ps.department_fk
    where mr.is_active
        and mr.year = %s
        and mr.period = %s
        and department.old_code = %s
    """


def main():
    ERRORS_CODES = get_errors_dict()

    pse_dir = 'c:/work/pse'
    year, period = '2014', '10'
    files = os.listdir(pse_dir)
    departments = set([filename[1:-4] for filename in files if '.dbf' in filename])
    registers = []
    mo = []
    file_not_found = file('not_found.csv', 'w')
    for department in departments:
        file_not_found.write(' '+department+'\n')
        print department

        mo_res = MedicalRegister.objects.raw(mo_query,
                                             [year, period, department])

        for mo_rec in mo_res:
            mo.append(mo_rec.organization_code)

        e_db = dbf.Dbf('%s/e%s.dbf' % (pse_dir, department))
        s_db = dbf.Dbf('%s/s%s.dbf' % (pse_dir, department))

        errors = defaultdict(list)

        for rec in e_db:
            if rec['c_err'] != 'HD':
                errors[rec['recid']].append(rec['c_err'])

        services = ProvidedService.objects.raw(service_query,
                                               [year, period, department])

        service_cache = {}

        for rec in services:
            service_cache[rec.scache] = rec.pk

        #print service_cache
        snyato = 0
        pofig = 0
        dobavleno = 0
        smena = 0
        kosyak = 0

        not_found_service = []
        for i, rec in enumerate(s_db):
            if rec.deleted:
                continue

            code = str(rec['cod'])
            code = '0'*(6-len(code)) + code

            cache = ((rec['sn_pol'].replace(' ', '') or '') + (code or '') + (rec['ds'] or '') + (rec['tn1'] or '') + (str(rec['d_u']) or '1900-01-01') + (rec['c_i'] or '')).decode('cp866')
            provided_service_pk = service_cache.get(cache, None)

            if not provided_service_pk:
                not_found_service.append(cache)
                print cache

            pse_error_set = set(errors.get(rec['recid'], [])) - set([None])

            error_set = set(Sanction.objects.filter(service_id=provided_service_pk) \
                                            .values_list('error__old_code', flat=True)) - set([None])

            to_delete = error_set - pse_error_set
            to_insert = pse_error_set - error_set

            if to_delete:
                print 'delete', to_delete, error_set, pse_error_set, 'rec_id', rec['recid']
                Sanction.objects.filter(service_id=provided_service_pk,
                                        error__old_code__in=to_delete).delete()
                print len(to_delete), len(error_set), to_delete, error_set
                if len(to_delete) == len(error_set):
                    print 'NULLed'
                    ProvidedService.objects.filter(pk=provided_service_pk) \
                                           .update(payment_type=None)

            if to_insert:
                print 'insert', to_insert
                try:
                    service = ProvidedService.objects.get(pk=provided_service_pk)
                except:
                    print provided_service_pk, rec['recid']
                    break
                underpayment = service.accepted_payment
                service.accepted_payment = 0
                service.payment_type_id = 3
                service.save()

                for err_rec in to_insert:
                    Sanction.objects.create(
                        service=service, type_id=1, underpayment=underpayment,
                        error_id=ERRORS_CODES.get(err_rec, None))
        #print not_found_service
        for s in not_found_service:
            file_not_found.write(s.encode('cp866')+'\n')
    print set(mo)
    file_not_found.close()
    MedicalRegister.objects.filter(is_active=True, year=year, period=period,
                                   organization_code__in=set(mo)) \
                           .update(status=5)


class Command(BaseCommand):
    help = u'Импортим PSE'

    def handle(self, *args, **options):
        main()