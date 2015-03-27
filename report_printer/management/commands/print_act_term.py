#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from term_fond.hospital import Command as Hospital
from term_fond.day_hospital import Command as DayHospital
from term_fond.acute_care import Command as AcuteCare
from term_fond.exam_children import Command as ExamChildren
from term_fond.exam_adult import Command as ExamAdult
from term_fond.policlinic_ambulance import Command as PoliclinicAmbulance
from term_fond.policlinic_preventive import Command as PoliclinicPreventive
from term_fond.policlinic_disease import Command as PoliclinicDisease
from term_fond.policlinic import Command as Policlinic
from term_fond.stomatology import Command as Stomatology
from report_printer.management.commands.term_fond.capitation import Command as Capitation


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
