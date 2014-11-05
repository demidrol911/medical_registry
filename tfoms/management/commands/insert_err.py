#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import ProvidedService, Sanction


### Проставляет указанную ошибку на услугах, ид которых содержатся в файле service.csv
### Формат вызова insert_err код_ошибки
class Command(BaseCommand):

    def handle(self, *args, **options):
        failure_cause = args[0]
        file_service = file('service.csv')
        for id_service_str in file_service:
            id_service = int(id_service_str.replace('\n', ''))
            service = ProvidedService.objects.get(id_pk=id_service)
            if service:
                print service
                service.payment_type_id = 3
                service.accepted_payment = 0
                service.provided_tariff = service.invoiced_payment
                service.save()
                Sanction.objects.create(
                    type_id=1, service=service, underpayment=service.invoiced_payment,
                    error_id=failure_cause)
        file_service.close()
