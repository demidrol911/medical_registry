# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from tfoms.models import Patient, MedicalRegister, Person, InsurancePolicy
from tfoms.models import MedicalRegisterRecord, MedicalOrganization

from lxml import etree
import re
import os


def main():
    policy_types = {1: u'полис старого образца',
                    2: u'временное свидетельство',
                    3: u'полис нового образца',
                    None: u'тип не указан'}

    year = '2014'
    period = '04'

    f_dir = 'd:/work/non_identified_errors_reports/'

    registers = MedicalRegister.objects.filter(is_active=True, period=period,
                                               organization_code='280059',
                                               year=year)

    for register in registers:
        name = MedicalOrganization.objects.get(code=register.organization_code,
                                               parent=None).name.replace('"', '')

        fi_name = u'%s%s ошибки идентификации.txt' % (f_dir, name)
        fi = open(fi_name, 'wb')
        patients_pk = MedicalRegisterRecord.objects.filter(
            register=register).values_list('patient_id', flat=True).distinct()
        non_identified = Patient.objects.filter(insurance_policy=None,
                                                pk__in=patients_pk
        ).order_by('last_name', 'first_name', 'middle_name', 'birthdate')
        for patient in non_identified:
            active_person = None
            active_policy_by_person = None
            person_string = None
            policy_string = None

            person_id = Person.objects.filter(last_name=patient.last_name,
                                              first_name=patient.first_name,
                                              middle_name=patient.middle_name,
                                              birthdate=patient.birthdate) \
                .order_by('-version')
            person_id = person_id[0].id if person_id else None
            if patient.insurance_policy_number:
                number_len = len(patient.insurance_policy_number)
            else:
                number_len = 0
            policy_type = patient.insurance_policy_type_id
            if number_len <= 7:
                policy_id = InsurancePolicy.objects.filter(
                    series=patient.insurance_policy_series,
                    number=patient.insurance_policy_number).order_by(
                    '-version')
            elif 7 < number_len < 12:
                policy_id = InsurancePolicy.objects.filter(
                    number=patient.insurance_policy_number).order_by(
                    '-version')
            elif number_len == 16:
                policy_id = InsurancePolicy.objects.filter(
                    enp=patient.insurance_policy_number, is_active=True).order_by(
                    '-version')
            else:
                policy_id = None

            if person_id:
                active_person_by_person = Person.objects.get(
                    id=person_id, is_active=True)

                active_policy_by_person = InsurancePolicy.objects.get(
                    is_active=True, person=active_person_by_person)

                person_string = u'по ФИО найден: %s %s %s %s, %s - %s %s выдан %s;'.replace('  ', '').replace(' 99 ', '') % (
                    active_person_by_person.last_name or '',
                    active_person_by_person.first_name or '',
                    active_person_by_person.middle_name or '',
                    active_person_by_person.birthdate or '',
                    policy_types[active_policy_by_person.type_id],
                    '' if active_policy_by_person.type_id == 3 else active_policy_by_person.series or '',
                    active_policy_by_person.enp if active_policy_by_person.type_id == 3 else active_policy_by_person.number or '',
                    active_policy_by_person.start_date, )

            if policy_id:
                active_policy_by_policy = InsurancePolicy.objects.get(
                    id=policy_id[0].id, is_active=True)

                active_person_by_policy = Person.objects.get(
                    id=active_policy_by_policy.person.id, is_active=True)

                policy_string = u'по полису найден: %s %s %s %s, %s - %s %s выдан %s'.replace('  ', '').replace(' 99 ', '') % (
                    active_person_by_policy.last_name or '',
                    active_person_by_policy.first_name or '',
                    active_person_by_policy.middle_name or '',
                    active_person_by_policy.birthdate or '',
                    policy_types[active_policy_by_policy.type_id],
                    '' if active_policy_by_policy.type_id == 3 else active_policy_by_policy.series or '',
                    active_policy_by_policy.enp if active_policy_by_policy.type_id == 3 else active_policy_by_policy.number or '',
                    active_policy_by_policy.start_date, )

            provided_string = u'подано: %s %s %s %s, %s - %s %s;' % (
                patient.last_name or '',
                patient.first_name or '',
                patient.middle_name or '',
                patient.birthdate or '',
                policy_types[patient.insurance_policy_type_id],
                patient.insurance_policy_series or '',
                patient.insurance_policy_number or '', )

            print provided_string
            fi.write(provided_string.encode('cp1251')+'\n')
            if person_id:
                print person_string
                fi.write(person_string.encode('cp1251')+'\n')
            if policy_id:
                print policy_string
                fi.write(policy_string.encode('cp1251')+'\n')
            else:
                print u'поданный полис в базе ОАО Дальмедстрах не найден'.encode('cp1251')
                fi.write(u'поданный полис в базе ОАО Дальмедстрах не найден\n'.encode('cp1251'))
            fi.write('\n')
        fi.close()

class Command(BaseCommand):
    help = 'export big XML'

    def handle(self, *args, **options):
        main()