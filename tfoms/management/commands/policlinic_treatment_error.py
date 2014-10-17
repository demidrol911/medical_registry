#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import MedicalOrganization


class Command(BaseCommand):
    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        mo_code = args[2]
        failure_cause = args[3]
        mo_obj = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True)
        treatment = mo_obj.get_policlinic_treatment_error(year, period, failure_cause)
        print u'Все: ', treatment.all
        print u'Взрослые: ', treatment.adult
        print u'Дети: ', treatment.children
