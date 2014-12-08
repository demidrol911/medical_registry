# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.core import serializers
from tfoms.models import MedicalRegister, ProvidedService, MedicalOrganization
from forms import PeriodFastSearchForm, RegisterSearchForm, RegisterStatusForm
from django.db.models import Q
from django.http import HttpResponse
from django.core import serializers

import json


def index(request):
    return render(request, 'viewer/index.html', {})


def get_periods_json(request):
    registers_years = MedicalRegister.objects.filter(is_active=True)\
                                             .values_list('year', flat=True)\
                                             .order_by('-year').distinct()
    periods_list = []

    for year in registers_years:
        parent = {'name': year, 'children': []}
        periods = MedicalRegister.objects.filter(is_active=True, year=year)\
                                         .values_list('period', flat=True)\
                                         .distinct().order_by('period')

        parent['children'] = [{'name': period, 'leaf': True} for period in periods]

        periods_list.append(parent)

    periods = json.dumps(periods_list)

    return HttpResponse(periods,
                        mimetype='application/json')