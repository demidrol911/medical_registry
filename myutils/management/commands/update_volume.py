from django.core.management.base import BaseCommand
from main.models import MedicalOrganization, MedicalServiceVolume
import datetime
from medical_service_register.path import BASE_DIR
import os


class Command(BaseCommand):

    def handle(self, *args, **options):
        volume_mapper = open(os.path.join(BASE_DIR,
                                          ur'myutils\management\commands\volume_mapper.csv'))
        volume_map = {}
        for line in volume_mapper:
            data = line.replace('\n', '').decode('utf8').split(';')
            volume_map[data[0]] = data[1]
        volume_mapper.close()
        file_csv = open(os.path.join(BASE_DIR,
                                     ur'myutils\management\commands\volume.csv'))
        for line in file_csv:
            name, hospital, day_hospital = line.replace('\n', '').split(';')
            src_name = name.decode('utf8')
            dst_name = volume_map.get(src_name, 'not found')
            mo = MedicalOrganization.objects.filter(name__startswith=dst_name, parent__isnull=True)
            if mo:
                MedicalServiceVolume.objects.create(organization_id=mo[0].pk,
                                                    date=datetime.date(year=2015, month=6, day=1),
                                                    hospital=int(hospital), day_hospital=int(day_hospital))
            else:
                print src_name

        file_csv.close()
