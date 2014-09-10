# -*- coding: utf-8 -*-

from django.shortcuts import render
from tfoms.models import MedicalRegister, ProvidedService, MedicalOrganization
from forms import PeriodFastSearchForm, RegisterSearchForm, RegisterStatusForm
from django.db.models import Q
from django.http import HttpResponse
from django.utils import simplejson
from django.core import serializers


def index(request):
    return render(request, 'base.html', {})


def periods_list(request):
    registers_years = MedicalRegister.objects.filter(is_active=True)\
                                             .values_list('year', flat=True)\
                                             .distinct()
    periods_dict = {}
    print sorted(map(lambda x: int(x), registers_years), key=int)
    for year in sorted(map(lambda x: int(x), registers_years), key=int):
        periods = MedicalRegister.objects.filter(is_active=True, year=year)\
                                         .values_list('period', flat=True)\
                                         .distinct().order_by('period')
        periods_dict[year] = periods

    return render(request, 'periods_list.html', {'periods_dict': periods_dict},
                  content_type='application/xml')