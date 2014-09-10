#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Max, Q
from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister,
    IDC, MedicalOrganization, Patient,
    Person, InsurancePolicy, MedicalRegisterRecord,
    PersonIDType, MedicalServiceTerm,
    MedicalServiceKind, MedicalServiceForm,
    MedicalDivision, MedicalServiceProfile,
    TreatmentResult, TreatmentOutcome, Special,
    MedicalWorkerSpeciality, PaymentMethod,
    PaymentType, PaymentFailureCause, MedicalRegister,
    ProvidedServiceFailureCause, Sanction, MedicalService,
    ExaminationAgeBracket)
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


def is_wrong_examination_age_group(service):
    months = 13
    group = ExaminationAgeBracket.objects.get(1, months=months)


def main():
    pass

class Command(BaseCommand):
    help = 'export reports'

    def handle(self, *args, **options):
        main()
