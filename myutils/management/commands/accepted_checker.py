#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from main.models import MedicalService, IDC, KSG, TariffProfile, KPG, MedicalServiceHiTechMethod, ProvidedService, PaymentFailureCause, Sanction
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        new_service_query = """
        select DISTINCT ps.id_pk, upper(format('%%s %%s %%s', p.last_name, p.first_name, p.middle_name)) AS fio, ps.start_date, ps.end_date, ms.code AS service_code, ms.name AS service_name, idc.idc_code, mr.period
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
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk or idc.id_pk = pe.basic_disease_fk
        where mr.is_active
           AND
           (((REPLACE(coalesce(p.insurance_policy_series, ''), '99', '') || coalesce(p.insurance_policy_number, '') ) = %(policy)s)
                or (upper(format('%%s %%s %%s', p.last_name, p.first_name, p.middle_name)) = upper(%(person)s)))
            --and ps.end_date = %(end_date)s
            and p.birthdate = %(birth_date)s
            --and pe.term_fk = 2
            and ps.payment_type_fk = 2
            --and idc.idc_code = %(disease)s
            and mr.year in ('2016')
            and mr.organization_code = '280029'
        """
        file_with_codes = open('mo_data.csv')

        #Картамышева Елена Александровна;58ТОДНСТ;2753430889000182;10.06.1965;31.03.2016;9;I20.8
        for i, row in enumerate(file_with_codes):
            data = row.replace('\n', '').split(';')
            fio = data[0]
            anamnesis_number = data[1]
            policy = data[2].replace(' ', '')

            bd = data[3].split('.')
            birth_date = '%s-%s-%s' % (bd[2], bd[1], bd[0])

            ed = data[4].split('.')
            end_date = '%s-%s-%s' % (ed[2], ed[1], ed[0])

            disease = data[6]

            services = list(ProvidedService.objects.raw(
                new_service_query, dict(person=fio, policy=policy,
                                        birth_date=birth_date,
                                        end_date=end_date, disease=disease)))

            if services:
                print i, u'Найдено', fio.decode('utf-8'), len(services)
                for s in services:
                    print s.fio, s.start_date, s.end_date, s.service_code, s.service_name, s.idc_code, s.period
            else:
                print i, u'НЕ НАЙДЕНО', fio.decode('utf-8')

            print '*'*80
                #print i, u'Не найдено', fio.decode('utf-8')

        file_with_codes.close()

