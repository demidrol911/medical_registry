# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.db import connection
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


def get_registers_json(request):
    cursor = connection.cursor()
    year = request.GET.get('year', None)
    period = request.GET.get('period', None)

    query = """
        select DISTINCT mr.year, mr.period, mr.organization_code, org.name, dep.old_code, dep.name, mrs.name
        from provided_event pe
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            LEFT JOIN medical_organization org
                on org.code = mr.organization_code and org.parent_fk is null
            JOIN medical_organization dep
                on dep.id_pk = pe.department_fk
            JOIN medical_register_status mrs
                on mrs.id_pk = mr.status_fk
        where mr.is_active
            and mr.year = %s
            and mr.period = %s
        order by mr.year, mr.period, mr.organization_code, dep.old_code
    """

    query_max_period = """
        select max(format('%s-%s', year, period))
        from medical_register
        where is_active
    """
    if not (year and period):
        cursor.execute(query_max_period)
        year, period = cursor.fetchone()[0].split('-')

    cursor.execute(query, [year, period])
    records = cursor.fetchall()

    registries_codes = []

    registries = []

    for ind, rec in enumerate(records):
        if rec[2] in registries_codes:
            registry_children = {'year': rec[0], 'period': rec[1],
                                 'name': rec[5], 'code': rec[4], 'status': '',
                                 'leaf': True}
            registry_parent['children'].append(registry_children)
        else:
            registries_codes.append(rec[2])
            if ind != 0:
                registries.append(registry_parent)
            registry_children = {'year': rec[0], 'period': rec[1],
                                 'name': rec[5], 'code': rec[4], 'status': '',
                                 'leaf': True}
            registry_parent = {'year': rec[0], 'period': rec[1],
                               'name': rec[3] or rec[5], 'code': rec[2], 'status': rec[6],
                               'children': [registry_children]}

    registries.append(registry_parent)

    registries_json = json.dumps(registries)

    return HttpResponse(registries_json, mimetype='application/json')


def get_services_json(request):
    year=request.GET.get('year', None)
    period=request.GET.get('period', None)
    organization_code=request.GET.get('organization', None),
    department_code=request.GET.get('department', None)

    query = """
        select ps.id_pk, p.first_name, p.last_name, p.middle_name,
            p.birthdate, gender.name gender_name,
            trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) policy,
            ps.end_date, md.code as division_code, md.name as division_name,
            ms.code service_code, ms.name service_name, pe.anamnesis_number,
            idc.idc_code disease_code, idc.name disease_name,
            ps.quantity, ps.accepted_payment, ps.worker_code,
            pe.id as event_id,
            ARRAY(
                select me.old_code
                from provided_service_sanction pss
                    join medical_error me
                        on me.id_pk = pss.error_fk
                WHERE
                    pss.service_fk = ps.id_pk
                ORDER BY me.weight DESC
            ) as errors
        from provided_service ps
            JOIN provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN medical_organization dep
                on dep.id_pk = pe.department_fk
            JOIN medical_register_status mrs
                on mrs.id_pk = mr.status_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN gender
                on gender.id_pk = p.gender_fk
            LEFT JOIN medical_division md
                on md.id_pk = ps.division_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk

        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (dep.old_code = %(department)s or %(department)s is null)
        order by p.first_name, p.last_name, p.middle_name, ps.end_date, ms.code
    """

    if not (year and period and organization_code):
        return HttpResponse(json.dumps({'error': 404}),
                            mimetype='application/json')

    services = list(ProvidedService.objects.raw(
        query, {'year': year, 'period': period,
                'organization': organization_code,
                'department': department_code}))

    total_services = len(services)
    services_list = []

    for rec in services:
        try:
            birthdate = rec.birthdate.strftime('%Y-%m-%d')
        except:
            birthdate = None

        try:
            end_date = rec.end_date.strftime('%Y-%m-%d')
        except:
            end_date = None

        if rec.payment_type_id in (2, 4):
            accepted_payment = float(rec.accepted_payment or 0)
        else:
            accepted_payment = 0


        service = {'id': rec.pk, 'first_name': rec.first_name,
                   'last_name': rec.last_name, 'middle_name': rec.middle_name,
                   'birthdate': birthdate,
                   'gender': rec.gender_name,
                   'policy': rec.policy,
                   'end_date': end_date,
                   'division_code': rec.division_code,
                   'division_name': rec.division_name,
                   'service_code': rec.service_code,
                   'service_name': rec.service_name,
                   'disease_name': rec.disease_name,
                   'disease_code': rec.disease_code,
                   'accepted_payment': accepted_payment,
                   'quantity': float(rec.quantity or 0),
                   'anamnesis_number': rec.anamnesis_number,
                   'worker_code': rec.worker_code,
                   'event_id': rec.event_id,
                   'errors': ','.join(rec.errors),
                   'full_name': '%s %s %s' % (rec.first_name, rec.last_name,
                                              rec.middle_name),
        }

        services_list.append(service)

    return HttpResponse(json.dumps({'totalCount': total_services,
                                    'services': services_list}),
                        mimetype='application/json')





