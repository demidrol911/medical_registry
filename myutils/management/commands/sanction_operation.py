#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import ProvidedService, Sanction, SanctionStatus

FILE_NAME = 'service.csv'


def get_services_ids():
    file_services = file(FILE_NAME)
    services_ids = [
        int(services_id.replace('\n', '')
            for services_id in file_services)
    ]
    file_services.close()
    return services_ids


def insert_sanction(services_id, errors_id):
    service = ProvidedService.objects.get(id_pk=services_id)
    if service:
        service.payment_type_id = 3
        service.accepted_payment = 0
        service.provided_tariff = service.invoiced_payment
        service.save()
        sanction = Sanction.objects.get_or_create(
            type_id=1,
            service=service,
            underpayment=service.invoiced_payment,
            is_active=True,
            error_id=errors_id
        )
        SanctionStatus.objects.get_or_create(
            sanction=sanction,
            who=SanctionStatus.SANCTION_TYPE_ADDED_BY_ECONOMIST
        )
        return True
    else:
        return False


def drop_sanction(services_id):
    service = ProvidedService.objects.get(id_pk=services_id)
    if service:
        print service
        service.payment_type_id = 2
        service.accepted_payment = service.calculated_payment
        service.save()
        sanction = Sanction.objects.filter(
            type_id=1,
            service=service,
            is_active=True
        ).update(is_active=False)
        SanctionStatus.objects.get_or_create(
            sanction=sanction,
            type=SanctionStatus.SANCTION_TYPE_REMOVED_BY_ECONOMIST
        )
        return True
    else:
        return False


class Command(BaseCommand):

    def handle(self, *args, **options):
        actions_cmd = args[0]
        for services_id in get_services_ids():
            actions_result = False
            if actions_cmd == 'del':
                actions_result = drop_sanction(services_id)
            elif actions_cmd == 'insert':
                errors_id = args[1]
                actions_result = insert_sanction(services_id, errors_id)
            else:
                print u'Действие не опознано'
            if not actions_result:
                print u'Не найдена', services_id
