#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import ProvidedService, Sanction, SanctionStatus, ProvidedServiceCoefficient
from datetime import datetime

FILE_NAME = 'service.csv'


def get_services_ids():
    file_services = file(FILE_NAME)
    services_ids = [
        int(services_id.replace('\n', '')
            for services_id in file_services)
    ]
    file_services.close()
    return services_ids


def calculate_cost(services_id, value):
    coefficients = ProvidedServiceCoefficient.objects.filter(
        service=services_id
    ).values('coefficient__pk', 'coefficient_value').distinct()
    result = value
    for coefficient in coefficients:
        coef_calc = coefficient['coefficient_value'] - 1
        if coef_calc < 0:
            result -= round(result * coef_calc, 2)
        else:
            result += round(result * coef_calc, 2)
    return result


def insert_coefficient(services_id, coefficients_id):
    service = ProvidedService.objects.get(id_pk=services_id)
    if service:
        ProvidedServiceCoefficient.objects.get_or_create(
            service=service,
            error_id=coefficients_id
        )
        if service.payment_type == 2:
            service.accepted_payment = calculate_cost(services_id, service.tariff)
            service.calculated_payment = calculate_cost(services_id, service.tariff)
            service.provided_tariff = calculate_cost(services_id, service.tariff)
        elif service.payment_type == 3:
            service.calculated_payment = calculate_cost(services_id, service.tariff)
            service.provided_tariff = service.invoiced_payment
        service.save()
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
            created_at=datetime.now(),
            who=WHO_STATUS
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
