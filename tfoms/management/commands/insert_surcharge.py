#! -*- coding: utf-8 -*-
import datetime
from django.core.management.base import BaseCommand
from tfoms.models import ProvidedService, Sanction


class Command(BaseCommand):

    def handle(self, *args, **options):
        #failure_cause = args[0]
        file_service = file('service.csv')
        current_data = datetime.date(year=2014, day=31, month=10)
        for id_service_str in file_service:
            id_service = int(id_service_str.replace('\n', ''))
            service = ProvidedService.objects.get(id_pk=id_service)
            if service:
                Sanction.objects.create(
                    type_id=4,
                    service=service,
                    is_active=True,
                    underpayment=service.provided_tariff,
                    date=current_data)
        file_service.close()
