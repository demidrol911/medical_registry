#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db.models import Max, Q
from tfoms.models import (
    TariffBasic, ProvidedService, MedicalRegister, TariffNkd,
    ProvidedServiceCoefficient,MedicalOrganization, Sanction,
    ExaminationAgeBracket, ProvidedEvent, Patient, InsurancePolicy,
    ProvidedService)
import csv
from datetime import datetime

MO, LAST_NAME, FIRST_NAME, MIDDLE_NAME, BIRTHDATE = 0, 1, 2, 3, 4
END_DATE, DISEASE = 10, 11


def get_service(record):
    service = ProvidedService.objects.filter(
        event__record__register__is_active=True,
        event__record__register__year='2014',
        event__record__register__period__in=('05', '06'),
        event__record__patient__last_name=record[LAST_NAME],
        event__record__patient__first_name=record[FIRST_NAME],
        event__record__patient__middle_name=record[MIDDLE_NAME],
        event__record__patient__birthdate=record[BIRTHDATE],
        end_date=datetime.strptime(record[END_DATE], '%d.%m.%y').date(),
        basic_disease__idc_code=record[DISEASE],
        payment_type_id__in=(2, 4)
    )

    return service


def main():
    cs = csv.reader(open('d:/work/for_check.csv', 'rb'), delimiter=';')
    total = 0
    accepted = 0

    for index, rec in enumerate(cs):
        total += 1
        print rec[END_DATE], rec[DISEASE]
        for r in get_service(rec):
            accepted += 1
            print r.event.record.register.period, r.payment_type_id

    print total, accepted


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()