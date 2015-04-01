import datetime
from main.models import ProvidedService


def date_correct(date, id_service=None, date_field=None):
    new_date = date
    if date.year < 1900:
        new_date = datetime.date(1900, date.month, date.day)
        if id_service and date_field:
            service = ProvidedService.objects.get(id_pk=id_service)
            if date_field == 'start_date':
                service.start_date = new_date
            if date_field == 'end_date':
                service.end_date = new_date
            print u'Change date', date, service.id_pk
            service.save()
    return new_date
