from django.db.models import Sum, Count, Q
from tfoms import func
from tfoms.models import ProvidedService, Sanction

CAPITATION_CRITERIA = Q(payment_kind=1) & ~Q(event__term=4)
HOSPITAL_CRITERIA = Q(event__term=1)
DAY_HOSPITAL_CRITERIA = Q(event__term=2)
POLICLINIC_CRITERIA = (Q(event__term=3) | Q(event__term__isnull=True))
AMBULANCE_CRITERIA = Q(event__term=4)

ACCEPTED_CRITERIA = Q(payment_type=2)
SANCTION_CRITERIA = Q(payment_type=3)


def get_services(year, period, mo_code):
    return ProvidedService.objects.filter(
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code
    ).exclude(code__group=27)


def get_service_pa(services):
    services_pk = services.filter(SANCTION_CRITERIA).values_list('pk', flat=True)
    sanctions = Sanction.objects.filter(service__in=services_pk, error=75).values_list('service__pk', flat=True)
    return sanctions


def calculated_capitation(services, term):
    mo_code = services[0].event.record.register.organization_code
    sum_capitation = 0
    if term == 3:
        capitation_policlinic = func.calculate_capitation_tariff(3, mo_code=mo_code)
        for group in capitation_policlinic[1]:
            sum_capitation += group[27] + group[26]
    if term == 4:
        capitation_ambulance = func.calculate_capitation_tariff(4, mo_code=mo_code)
        for group in capitation_ambulance[1]:
            sum_capitation += group[27] + group[26]
    return sum_capitation


def calculated_money(services, condition, field, is_calculate_capitation=False):
    sum_value = services.filter(condition).aggregate(sum_value=Sum(field))['sum_value'] or 0
    if is_calculate_capitation:
        return sum_value + calculated_capitation(services, 3) + calculated_capitation(services, 4)
    else:
        return sum_value


def calculated_services(services, condition):
    return services.filter(condition).aggregate(
        count_value=Count('id_pk')
    )['count_value']
