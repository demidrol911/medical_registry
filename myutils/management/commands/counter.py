from django.core.management.base import BaseCommand
from main.models import MedicalOrganization, MedicalServiceVolume
import datetime
from medical_service_register.path import BASE_DIR
import os
import csv
from django.db.models import F
import codecs


class Command(BaseCommand):

    def handle(self, *args, **options):
        mo_group = {}
        file_csv = open('35.csv')
        for row in file_csv:
            data = row.replace('\n', '')
            if data:
                if data not in mo_group:
                    mo_group[data] = 0
                mo_group[data] += 1
        for mo in mo_group:
            mo_name = MedicalOrganization.objects.get(code=mo, parent__isnull=True).name
            print '\''+mo+'\',', '\''+mo_name+'\',', mo_group[mo]
