#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from hospital import Command as Hospital
from day_hospital import Command as DayHospital
from acute_care import Command as AcuteCare
from exam_children import Command as ExamChildren
from exam_adult import Command as ExamAdult
from policlinic_ambulance import Command as PoliclinicAmbulance
from policlinic_preventive import Command as PoliclinicPreventive
from policlinic_disease import Command as PoliclinicDisease
from policlinic import Command as Policlinic
from stomatology import Command as Stomatology
from capitation import Command as Capitation


class Command(BaseCommand):

    def handle(self, *args, **options):
        acts = [
            Hospital(),
            DayHospital(),
            AcuteCare(),
            ExamChildren(),
            ExamAdult(),
            PoliclinicAmbulance(),
            PoliclinicPreventive(),
            PoliclinicDisease(),
            Policlinic(),
            Stomatology(),
            Capitation(),
        ]
        for act in acts:
            act.handle(*args, **options)
            print '='*79
