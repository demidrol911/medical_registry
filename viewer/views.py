# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.db import connection
from main.models import MedicalRegister, ProvidedService, MedicalOrganization
from main.models import MedicalRegisterStatus
from django.http import HttpResponse
from django.core import serializers

import json
import time

from registry_import.validation import PROFILES, DIVISIONS, DISEASES, CODES
from registry_import.validation import queryset_to_dict

from main.models import MedicalError

ERRORS = {rec.old_code: rec for rec in MedicalError.objects.all()}


def index(request):
    return render(request, 'viewer/index.html', {})


def get_periods_json(request):
    registers_years = MedicalRegister.objects.filter(is_active=True) \
        .values_list('year', flat=True) \
        .order_by('-year').distinct()
    periods_list = []

    for year in registers_years:
        parent = {'name': year, 'children': []}
        periods = MedicalRegister.objects.filter(is_active=True, year=year) \
            .values_list('period', flat=True) \
            .distinct().order_by('period')

        parent['children'] = [{'name': period, 'leaf': True} for period in
                              periods]

        periods_list.append(parent)

    periods = json.dumps(periods_list)

    return HttpResponse(periods,
                        mimetype='application/json')


def get_organization_registers_json(request):
    cursor = connection.cursor()
    year = request.GET.get('year', None)
    period = request.GET.get('period', None)

    query_max_period = """
        select max(format('%s-%s', year, period))
        from medical_register
        where is_active
    """

    extra_query_mo_name = ('select name from medical_organization where '
                           'code = medical_register.organization_code '
                           'and parent_fk is null')

    if not (year and period):
        cursor.execute(query_max_period)
        year, period = cursor.fetchone()[0].split('-')

    records = MedicalRegister.objects.select_related('status').filter(
        year=year, period=period, is_active=True, type=1).extra(
        select={'organization_name': extra_query_mo_name})

    registries = []

    for rec in records:
        registry = {'year': rec.year, 'period': rec.period,
                    'organization_name': rec.organization_name,
                    'organization_code': rec.organization_code,
                    'organization_status': rec.status.name,
                    'organization_timestamp': rec.timestamp.date().strftime('%d-%m-%Y')}

        registries.append(registry)

    registries_json = json.dumps({'root': registries})

    return HttpResponse(registries_json, mimetype='application/json')


def get_department_registers_json(request):
    cursor = connection.cursor()
    year = request.GET.get('year', None)
    period = request.GET.get('period', None)

    query = """
        select DISTINCT mr.year, mr.period, mr.organization_code,
            org.name organization_name,
            dep.old_code department_code,
            dep.name department_name,
            mrs.name status,
            mr.timestamp
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
            and mr.type = 1
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

    registries = []

    for rec in records:
        registry = {'year': rec[0], 'period': rec[1],
                    'organization_name': rec[3],
                    'department_name': rec[5], 'department_code': rec[4],
                    'department_status': rec[6], 'organization_code': rec[2],
                    'department_timestamp': rec[7].date().strftime('%d-%m-%Y')}
        registries.append(registry)

    registries_json = json.dumps({'root': registries})

    return HttpResponse(registries_json, mimetype='application/json')


def get_services_json(request):
    year = request.GET.get('year', None)
    period = request.GET.get('period', None)
    organization_code = request.GET.get('organization', None),
    department_code = request.GET.get('department', None)

    print year, period, organization_code, department_code

    query = """
        select ps.id_pk, p.first_name, p.last_name, p.middle_name,
            p.birthdate, gender.name gender,
            trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) policy,
            ps.start_date as "start",
            ps.end_date as "end",
            md.code as dvsn_code,
            md.name as dvsn_name,
            ms.code srv_code,
            ms.name srv_name,
            pe.anamnesis_number as anamnesis,
            idc.idc_code ds_code,
            idc.name ds_name,
            ps.quantity,
            ps.accepted_payment as accepted,
            ps.worker_code as wrk_code,
            pe.id as evt_id,
            pe.comment as evt_comment,
            ps.comment as srv_comment,
            ps.tariff,
            ARRAY(
                select me.old_code
                from provided_service_sanction pss
                    join medical_error me
                        on me.id_pk = pss.error_fk
                WHERE
                    pss.service_fk = ps.id_pk
                ORDER BY me.weight DESC
            ) as errors,
            pe.payment_units_number as uet,
            ps.profile_fk as profile_code,
            msp.name as profile_name
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
            LEFT JOIN medical_service_profile msp
                on msp.id_pk = ps.profile_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk

        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (dep.old_code = %(department)s or %(department)s is null)
        order by pe.id, p.first_name, p.last_name, p.middle_name, ps.end_date, ms.code
    """

    if not (year and period and organization_code):
        return HttpResponse(json.dumps({'error': 404}),
                            mimetype='application/json')

    services = ProvidedService.objects.raw(
            query, {'year': year, 'period': period,
            'organization': organization_code,
            'department': department_code})

    print 'Ok! Sending...'

    services_list = []
    """
    for i, rec in enumerate(services):
        try:
            birthdate = rec.birthdate.strftime('%Y-%m-%d')
        except:
            birthdate = None

        try:
            end_date = rec.end.strftime('%Y-%m-%d')
        except:
            end_date = None

        try:
            start_date = rec.start.strftime('%Y-%m-%d')
        except:
            start_date = None

        if rec.payment_type_id in (2, 4):
            accepted_payment = float(rec.accepted_payment or 0)
        else:
            accepted_payment = 0

        tariff = float(rec.tariff or 0)

        service = {'id': rec.pk, 'first_name': rec.first_name,
                   'last_name': rec.last_name, 'middle_name': rec.middle_name,
                   'birthdate': birthdate,
                   'gender': rec.gender,
                   'policy': rec.policy,
                   'start': start_date,
                   'end': end_date,
                   'div_code': rec.dvsn_code,
                   #'div_n': rec.dvsn_name,
                   'srv_code': rec.srv_code,
                   #'srv_n': rec.srv_name,
                   #'ds_n': rec.ds_name,
                   'ds_code': rec.ds_code,
                   'tariff': tariff,
                   'accepted': accepted_payment,
                   'quantity': float(rec.quantity or 0),
                   'anamnesis': rec.anamnesis,
                   'wrk_code': rec.wrk_code,
                   'event_id': rec.evt_id,
                   'errors': ','.join(rec.errors) or 'нет',
                   'uet': float(rec.uet or 0),
                   'srv_comment': rec.srv_comment,
                   'evt_comment': rec.evt_comment,
                   'profile': rec.profile_code,
                   #'prof_n': rec.profile_name
        }

        services_list.append(service)
    print 'Ok! Serialized, fire to client'
    """
    start = time.clock()
    services_list = [{'id': rec.pk, 'first_name': rec.first_name,
                   'last_name': rec.last_name, 'middle_name': rec.middle_name,
                   'birthdate': rec.birthdate.strftime('%Y-%m-%d'),
                   'gender': rec.gender,
                   'policy': rec.policy,
                   'start': rec.birthdate.strftime('%Y-%m-%d'),
                   'end': rec.birthdate.strftime('%Y-%m-%d'),
                   'div_code': rec.dvsn_code,
                   'div_n': rec.dvsn_name,
                   'srv_code': rec.srv_code,
                   'srv_n': rec.srv_name,
                   'ds_n': rec.ds_name,
                   'ds_code': rec.ds_code,
                   'tariff': float(rec.tariff or 0),
                   'accepted': float(rec.accepted or 0),
                   'quantity': float(rec.quantity or 0),
                   'anamnesis': rec.anamnesis,
                   'wrk_code': rec.wrk_code,
                   'event_id': rec.evt_id,
                   'errors': ','.join(rec.errors) or 'нет',
                   'uet': float(rec.uet or 0),
                   'srv_comment': rec.srv_comment,
                   'evt_comment': rec.evt_comment,
                   'profile': rec.profile_code,
                   'prof_n': rec.profile_name
        } for rec in list(services)]
    elapsed = time.clock() - start
    print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed//60), int(elapsed % 60))

    start = time.clock()

    dump = json.dumps(services_list)

    return HttpResponse(dump,
                        mimetype='application/json')


def get_registry_status_json(request):
    statuses = []
    for rec in MedicalRegisterStatus.objects.all():
        statuses.append({'id': rec.pk, 'name': rec.name})

    return HttpResponse(json.dumps({'root': statuses}),
                        mimetype='application/json')


def update_organization_registry_status(request):

    if request.is_ajax() and request.method == 'POST':
        body = request.body

        json_data = json.loads(body)

        try:
            status = MedicalRegisterStatus.objects.get(name=json_data['organization_status'])
        except:
            print 'non status'
            return HttpResponse(json.dumps({'error': u'Нет такого статуса'}),
                                mimetype='application/json')
        registries = MedicalRegister.objects.filter(
            is_active=True, year=json_data['year'], period=json_data['period'],
            organization_code=json_data['organization_code'])
        print registries
        registries.update(status=status)

    return HttpResponse(json.dumps({'success': '1'}),
                        mimetype='application/json')


def get_additional_info_json(request):
    info = {}

    profile = request.GET.get('profile', None)
    division = request.GET.get('division', None)
    service = request.GET.get('service', None)
    disease = request.GET.get('disease', None)
    errors = request.GET.get('errors', None)

    profile_obj = PROFILES.get(profile)
    info['profile'] = profile_obj.name if profile_obj else None

    division_obj = DIVISIONS.get(division)
    info['division'] = division_obj.name if division_obj else None

    service_obj = CODES.get(service)
    info['service'] = service_obj.name if service_obj else None

    disease_obj = DISEASES.get(disease)
    info['disease'] = disease_obj.name if disease_obj else None

    errors_names = []

    if errors and errors != u'нет':

        for error in errors.split(','):
            error_obj = ERRORS.get(error, None)

            errors_names.append(error_obj.name if error_obj else '')

    info['errors'] = '; '.join(errors_names)

    return HttpResponse(json.dumps({'info': info}), mimetype='application/json')