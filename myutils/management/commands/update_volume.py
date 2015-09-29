from django.core.management.base import BaseCommand
from main.models import MedicalOrganization, MedicalServiceVolume
import datetime
from medical_service_register.path import BASE_DIR
import os
import csv


class Command(BaseCommand):

    def handle(self, *args, **options):

        mapper_file_path = os.path.join(
            BASE_DIR, ur'myutils\management\commands\volume_mapper.csv')

        volume_mapper = csv.reader(open(mapper_file_path, 'r'),
                                   delimiter=';', quotechar='"')
        volume_map = {}

        for rec in volume_mapper:
            volume_map[rec[0]] = rec[1]

        volume_file_path = os.path.join(
            BASE_DIR, ur'myutils\management\commands\volume.csv')

        file_csv = csv.reader(open(volume_file_path, 'r'), delimiter=';')

        for rec in file_csv:
            name, hospital, day_hospital = rec

            src_name = name
            dst_name = volume_map.get(src_name, 'not found')

            mo = MedicalOrganization.objects.get(name__startswith=dst_name,
                                                 parent__isnull=True)

            if mo:
                MedicalServiceVolume.objects.create(
                    organization_id=mo.pk,
                    date=datetime.date(year=2015, month=9, day=1),
                    hospital=int(hospital or 0),
                    day_hospital=int(day_hospital or 0))
            else:
                print src_name
