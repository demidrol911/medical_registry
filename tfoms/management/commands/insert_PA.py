#! -*- coding: utf-8 -*-

from datetime import datetime
from django.core.management.base import BaseCommand
from tfoms.models import ProvidedService, ProvidedServiceCoefficient, Sanction


### Проставляет ошибки PA (частичная оплата)
### Формат вызова из командной строки
### insert_PA код.больницы вид_помощи(1-стационар, 2-дневной стационар) кол-во_ошибок
class Command(BaseCommand):

    def handle(self, *args, **options):
        year = '2014'
        period = '09'

        mo_code = args[0]
        term = args[1]
        count_pa = int(args[2])

        service_pa = []

        services = ProvidedService.objects.filter(
            event__record__register__year=year,
            event__record__register__period=period,
            event__record__register__is_active=True,
            event__record__register__organization_code=mo_code,
            payment_type=2,
            code__group__isnull=True,
            tariff__gt=0,
            event__term=term
        )

        # Дата начала периода
        date_begin_period = datetime.strptime(
            '{year}-{period}-1'.format(year=year, period=period),
            '%Y-%m-%d')

        # Услуги, у которых больница проставила комментарий PA
        print u'Услуги c комментарием PA'
        services_has_comment_pa = services.filter(comment__icontains='PA',
                                                  start_date__gte=date_begin_period,
                                                  end_date__gte=date_begin_period).\
            order_by('tariff')
        for service in services_has_comment_pa[:count_pa]:
            service_pa.append(service)

        # Услуги, у которых больница не проставила комментарий PA
        if len(service_pa) < count_pa:
            print u'Услуги без комментария PA'
            services_nohas_comment_pa = services.filter(start_date__gte=date_begin_period,
                                                        end_date__gte=date_begin_period).\
                order_by('tariff')
            for service in services_nohas_comment_pa[:count_pa-len(service_pa)]:
                service_pa.append(service)

        # Остальные услуги
        if len(service_pa) < count_pa:
            print u'Остальные услуги'
            services_other = services.filter(start_date__lte=date_begin_period,
                                             end_date__lte=date_begin_period).\
                order_by('tariff')
            for service in services_other[:count_pa-len(service_pa)]:
                service_pa.append(service)

        print u'PA будет проставлено на %d услугах из %d' % (len(service_pa), count_pa)

        # Проставляем PA
        for service in service_pa:
            print service.pk, service.payment_type_id, service.tariff, \
                service.accepted_payment, service.calculated_payment, \
                service.provided_tariff, service.start_date
            service.payment_type_id = 4
            service.accepted_payment = float(service.tariff) - round(0.7*float(service.tariff), 2)
            service.calculated_payment = round(0.3*float(service.tariff), 2)
            service.provided_tariff = round(0.7*float(service.tariff), 2)
            service.save()
            ProvidedServiceCoefficient.objects.create(
                service=service, coefficient_id=6
            )
            Sanction.objects.create(
                type_id=1, service=service, underpayment=round(0.7*float(service.tariff), 3),
                error_id=75)

