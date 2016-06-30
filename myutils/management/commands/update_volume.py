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

        mapper_file_path = os.path.join(
            BASE_DIR, ur'myutils\management\commands\volume_mapper.csv')

        volume_mapper = csv.reader(open(mapper_file_path),
                                   delimiter=';', quotechar='"')
        volume_map = {}

        for rec in volume_mapper:
            volume_map[rec[0]] = rec[1]

        volume_file_path = os.path.join(
            BASE_DIR, ur'myutils\management\commands\volume.csv')

        file_csv = csv.reader(open(volume_file_path), delimiter=';')

        for i, rec in enumerate(file_csv):
            name, hospital, day_hospital = rec

            src_name = name
            dst_name = volume_map.get(src_name, 'not found')

            print src_name.decode('utf-8'), dst_name.decode('utf-8')
            mo = MedicalOrganization.objects.get(name__startswith=dst_name,
                                                 parent__isnull=True)

            if mo:
                '''
                MedicalServiceVolume.objects.filter(organization=mo.pk, date=datetime.date(year=2015, month=12, day=1)).\
                    update(day_hospital=F('day_hospital')+day_hospital, hospital=F('hospital')+hospital)
                '''
                MedicalServiceVolume.objects.create(
                    organization_id=mo.pk,
                    date=datetime.date(year=2016, month=6, day=1),
                    hospital=int(hospital or 0),
                    day_hospital=int(day_hospital or 0))
            else:
                print '*', i, src_name, dst_name
