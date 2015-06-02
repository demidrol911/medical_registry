# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.db import connection
from main.models import MedicalRegister, ProvidedService, MedicalOrganization
from main.models import MedicalRegisterStatus
from django.http import HttpResponse
from django.core import serializers

from registry_import.simple_validation import PROFILES, DIVISIONS, DISEASES, CODES
from registry_import.simple_validation import queryset_to_dict
from main.funcs import safe_date_to_string, safe_float
from main.models import MedicalError

import json
import time
from datetime import datetime
from xlsxwriter.workbook import Workbook
from xlsxwriter.utility import xl_rowcol_to_cell
import base64
import StringIO


ERRORS = {rec.old_code: rec for rec in MedicalError.objects.all()}


def safe_date(string):
    if string:
        try:
            date = datetime.strptime(string, '%Y-%m-%dT%H:%M:%S').date()
        except:
            date = None
    else:
        date = None
    return date


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
                    'organization_timestamp': rec.timestamp.date().strftime(
                        '%d-%m-%Y')}

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

    print year, period, organization_code, repr(department_code)

    query = """
        select dense_rank() OVER(ORDER BY pe.id) as i,
            ps.id_pk, p.first_name, p.last_name, p.middle_name,
            to_char(p.birthdate, 'YYYY-MM-DD') as birthdate, gender.name gender,
            trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) policy,
            to_char(ps.start_date, 'YYYY-MM-DD') as "start",
            to_char(ps.end_date, 'YYYY-MM-DD') as "end",
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
                    pss.service_fk = ps.id_pk and pss.is_active
                ORDER BY me.weight desc limit 1
            ) as errors,
            array(
                select idc.idc_code
                from provided_event_concomitant_disease
                    join idc
                        on idc.id_pk = provided_event_concomitant_disease.disease_fk
                WHERE provided_event_concomitant_disease.event_fk = pe.id_pk
            ) as concomitant_disease,
            array(
                select idc.idc_code
                from provided_event_complicated_disease
                    join idc
                        on idc.id_pk = provided_event_complicated_disease.disease_fk
                WHERE provided_event_complicated_disease.event_fk = pe.id_pk
            ) as complicated_disease,
            pe.payment_units_number as uet,
            ps.profile_fk as profile_code,
            msp.name as profile_name,
            idc_pei.idc_code as initial_disease_code,
            idc_peb.idc_code as basic_disease_code,
            ps.payment_type_fk as payment_code,
            coalesce(mst.name, 'Поликлиника') as term_name,
            tr.name as result_name,
            dep.old_code as department_code
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
            left join idc idc_pei
                on idc_pei.id_pk = pe.initial_disease_fk
            left join idc idc_peb
                on idc_peb.id_pk = pe.basic_disease_fk
            left join medical_service_term mst
                on mst.id_pk = pe.term_fk
            LEFT join treatment_result tr
                on tr.id_pk = pe.treatment_result_fk

        where mr.is_active
            and mr.year = %(year)s
            and mr.period = %(period)s
            and mr.organization_code = %(organization)s
            and (%(department)s = '' or dep.old_code = %(department)s)
        order by pe.id, p.first_name, p.last_name, p.middle_name, ps.start_date, ps.end_date, ms.code
    """

    if not (year and period and organization_code):
        return HttpResponse(json.dumps({'error': 404}),
                            mimetype='application/json')

    services = ProvidedService.objects.raw(
        query, {'year': year, 'period': period,
                'organization': organization_code,
                'department': department_code})

    start = time.clock()

    services_list = [
        {'id': rec.pk, 'first_name': rec.first_name, 'last_name': rec.last_name,
         'middle_name': rec.middle_name,
         'birthdate': rec.birthdate,
         'gender': rec.gender, 'policy': rec.policy,
         'start_date': rec.start,
         'end_date': rec.end,
         'division_code': rec.dvsn_code, 'division_name': rec.dvsn_name,
         'service_code': rec.srv_code, 'service_name': rec.srv_name,
         'disease_name': rec.ds_name, 'disease_code': rec.ds_code,
         'tariff': float(rec.tariff or 0),
         'accepted': float(rec.accepted or 0) if rec.payment_code == 2 else 0,
         'quantity': float(rec.quantity or 0), 'anamnesis': rec.anamnesis,
         'worker_code': rec.wrk_code, 'event_id': rec.evt_id,
         'errors': ','.join(rec.errors) or 'нет', 'uet': float(rec.uet or 0),
         'service_comment': rec.srv_comment, 'event_comment': rec.evt_comment,
         'profile_code': rec.profile_code, 'profile_name': rec.profile_name,
         'initial_disease': rec.initial_disease_code,
         'basic_disease': rec.basic_disease_code,
         'concomitant_disease': ','.join(rec.concomitant_disease),
         'complicated_disease': ','.join(rec.complicated_disease),
         'payment_code': rec.payment_code, 'term': rec.term_name,
         'result': rec.result_name, 'department': rec.department_code,
        } for rec in list(services)]

    elapsed = time.clock() - start
    print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed // 60),
                                                          int(elapsed % 60))

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
            status = MedicalRegisterStatus.objects.get(
                name=json_data['organization_status'])
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


def get_service_divisions_json(request):
    divisions = []

    for rec in DIVISIONS:
        divisions.append({'code': rec, 'name': u'{0} - {1}'.format(rec, DIVISIONS[rec].name)})

    return HttpResponse(json.dumps({'divisions': divisions}),
                        mimetype='application/json')


def get_service_profiles_json(request):
    profiles = []

    for rec in PROFILES:
        profiles.append({'code': rec, 'name': u'{0}'.format(PROFILES[rec].name)})

    return HttpResponse(json.dumps({'profiles': profiles}),
                        mimetype='application/json')


def get_excel_export(request):
    base_query = """
        select ps.id_pk,
            row_number() OVER () as rnum,
            p.first_name, p.last_name, p.middle_name,
            to_char(p.birthdate, 'DD-MM-YYYY') as birthdate,
            trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) policy,
            to_char(ps.start_date, 'DD-MM-YYYY') as "start",
            to_char(ps.end_date, 'DD-MM-YYYY') as "end",
            md.name as dvsn_name,
            ms.code srv_code,
            pe.anamnesis_number as anamnesis,
            idc.idc_code ds_code,
            ps.quantity,
            ps.accepted_payment as accepted,
            pe.id as evt_id,
            ps.tariff,
            ARRAY(
                select DISTINCT me.old_code
                from provided_service_sanction pss
                    join medical_error me
                        on me.id_pk = pss.error_fk
                WHERE
                    pss.service_fk = ps.id_pk and pss.is_active
                    and pss.type_fk = 1
            ) as errors,
            case ms.group_fk when 19 then ms.uet else 0 end as uet,
            dep.old_code as department_code
        from provided_service ps
            JOIN provided_event pe
                on ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                on mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                on mr.id_pk = mrr.register_fk
            JOIN medical_organization dep
                on dep.id_pk = ps.department_fk
            JOIN medical_register_status mrs
                on mrs.id_pk = mr.status_fk
            JOIN patient p
                on p.id_pk = mrr.patient_fk
            LEFT JOIN medical_division md
                on md.id_pk = ps.division_fk
            LEFT JOIN medical_service_profile msp
                on msp.id_pk = ps.profile_fk
            JOIN medical_service ms
                on ms.id_pk = ps.code_fk
            LEFT JOIN idc
                on idc.id_pk = ps.basic_disease_fk
            left join medical_service_term mst
                on mst.id_pk = pe.term_fk
            LEFT join treatment_result tr
                on tr.id_pk = pe.treatment_result_fk
            LEFT join provided_service_sanction pss
                on pss.service_fk = ps.id_pk and pss.is_active and pss.type_fk = 1
            LEFT JOIN medical_error me
                on me.id_pk = pss.error_fk
        where mr.is_active
    """
    organization_code = request.POST.get('organization_code')
    year = request.POST.get('year', None)
    period = request.POST.get('period', None)
    department_code = request.POST.get('department_code', None)
    policy = request.POST.get('policy')
    last_name = request.POST.get('last_name')
    first_name = request.POST.get('first_name')
    middle_name = request.POST.get('middle_name')
    birthdate = request.POST.get('birthdate')
    term = request.POST.get('term')
    disease_1 = request.POST.get('disease_1')
    disease_2 = request.POST.get('disease_2')
    service_1 = request.POST.get('service_1')
    service_2 = request.POST.get('service_2')
    start_date_1 = request.POST.get('start_date_1')
    start_date_2 = request.POST.get('start_date_2')
    end_date_1 = request.POST.get('end_date_1')
    end_date_2 = request.POST.get('end_date_2')
    division_code = request.POST.get('division_code')
    profile = request.POST.get('profile')
    errors = request.POST.get('errors')
    args = {}

    if organization_code:
        base_query += 'and mr.organization_code = %(organization_code)s\n'
        args['organization_code'] = organization_code

    if year:
        base_query += 'and mr.year = %(year)s\n'
        args['year'] = year

    if period:
        base_query += 'and mr.period = %(period)s\n'
        args['period'] = period

    if department_code:
        base_query += 'and dep.old_code = %(department_code)s\n'
        args['department_code'] = department_code

    if policy:
        base_query += "and trim(BOTH ' ' from format('%%s %%s', coalesce(p.insurance_policy_series, ''), coalesce(p.insurance_policy_number, ''))) ilike %(policy)s\n"
        args['policy'] = '%%%s%%' % policy

    if last_name:
        base_query += 'and p.last_name ilike %(last_name)s\n'
        args['last_name'] = '%s%%' % last_name

    if first_name:
        base_query += 'and p.first_name ilike %(first_name)s\n'
        args['first_name'] = '%s%%' % first_name

    if middle_name:
        base_query += 'and p.middle_name ilike %(middle_name)s\n'
        args['middle_name'] = '%s%%' % middle_name

    if birthdate:
        _birthdate = safe_date(birthdate)

        if _birthdate:
            base_query += 'and p.birthdate = %(birthdate)s\n'
            args['birthdate'] = _birthdate

    if term:
        base_query += 'and mst.name = %(term)s\n'
        args['term'] = term

    if disease_1 and disease_2:
        base_query += 'and idc.idc_code between upper(%(disease_1)s) and upper(%(disease_2)s)'
        args['disease_1'] = disease_1
        args['disease_2'] = disease_2
    elif disease_1:
        base_query += 'and idc.idc_code ilike %(disease)s\n'
        args['disease'] = '%%%s%%' % disease_1

    if service_1 and service_2:
        base_query += 'and ms.code between upper(%(service_1)s) and upper(%(service_2)s)'
        args['service_1'] = service_1
        args['service_2'] = service_2
    elif service_1:
        base_query += 'and ms.code ilike %(service)s'
        args['service'] = '%%%s%%' % service_1

    if start_date_1 and start_date_2:
        _start_date_1 = safe_date(start_date_1)
        _start_date_2 = safe_date(start_date_2)

        if _start_date_1 and _start_date_2:
            base_query += 'and ps.start_date between %(start_date_1)s and %(start_date_2)s\n'
            args['start_date_1'] = _start_date_1
            args['start_date_2'] = _start_date_2
    elif start_date_1:
        _start_date_1 = safe_date(start_date_1)

        if _start_date_1:
            base_query += 'and ps.start_date = %(start_date)s\n'
            args['start_date'] = _start_date_1

    if end_date_1 and end_date_2:
        _end_date_1 = safe_date(end_date_1)
        _end_date_2 = safe_date(end_date_2)

        if _end_date_1 and _end_date_2:
            base_query += 'and ps.start_date between %(end_date_1)s and %(end_date_2)s\n'
            args['end_date_1'] = _end_date_1
            args['end_date_2'] = _end_date_2
    elif end_date_1:
        _end_date_1 = safe_date(end_date_1)

        if _end_date_1:
            base_query += 'and ps.end_date = %(end_date)s\n'
            args['end_date'] = _end_date_1

    if division_code:
        base_query += 'and md.code = %(division_code)s\n'
        args['division_code'] = division_code

    if profile:
        base_query += 'and upper(msp.name) = upper(%(profile)s)'
        args['profile'] = profile

    if errors and errors != u'нет':
        _errors = errors.split(',')
        base_query += 'and me.old_code = any(%(errors)s)'
        args['errors'] = _errors

    services = list(ProvidedService.objects.raw(base_query, args))

    output = StringIO.StringIO()

    book = Workbook(output)
    sheet = book.add_worksheet('test')
    sheet.write(0, 0, u'ВЫПИСКА ИЗ РЕЕСТРА ПАЦИЕНТА')
    sheet.write(1, 0, u'За оказанные медицинские услуги по территориальной программе ОМС')

    if organization_code:
        try:
            organization = MedicalOrganization.objects.get(code=organization_code, parent_id=None)
        except:
            organization = None

    registry = None
    if organization_code and year and period:
        try:
            registry = MedicalRegister.objects.get(
                type=1, year=year, period=period,
                organization_code=organization_code)
        except:
            registry = None

    sheet.write(3, 0, u'Наименование МО:')
    sheet.write(4, 0, u'Дата проверки:')

    if organization:
        sheet.write(3, 2, organization.name)
    if registry:
        print registry.timestamp.date()
        sheet.write(4, 2, str(registry.timestamp.date() or ''))

    headers = [u'№ п/п', u'Фамилия', u'Имя', u'Отчество', u'Номер карты',
               u'Ош.', u'ЛПУ', u'МКБ-9', u'Дата поступ.', u'Дата выписки',
               u'Код услуги', u'Кол дн.', u'Дата рождения', u'Номер полиса',
               u'Адрес', u'Отделение', u'УЕТ', u'Тариф',  u'Оплачено']

    headers_widths = [10, 20, 20, 20, 10,
                      10, 10, 10, 10, 10,
                      10, 10, 10, 30,
                      10, 30, 10, 10, 10]

    header_format = book.add_format({'text_wrap': True, 'border': 1,
                                     'align': 'center', 'valign': 'vcenter'})

    for i, rec in enumerate(headers):
        sheet.set_column(i, i, headers_widths[i])
        sheet.write(6, i, rec, header_format)

    regular_format = book.add_format({'border': 1})

    for j, rec in enumerate(services):
        i = 7 + j
        sheet.write(i, 0, rec.rnum, regular_format)
        sheet.write(i, 1, rec.last_name, regular_format)
        sheet.write(i, 2, rec.first_name, regular_format)
        sheet.write(i, 3, rec.middle_name, regular_format)
        sheet.write(i, 4, rec.anamnesis, regular_format)
        sheet.write(i, 5, ','.join(rec.errors), regular_format)
        sheet.write(i, 6, rec.department_code, regular_format)
        sheet.write(i, 7, rec.ds_code, regular_format)
        sheet.write(i, 8, rec.start, regular_format)
        sheet.write(i, 9, rec.end, regular_format)
        sheet.write(i, 10, rec.srv_code, regular_format)
        sheet.write(i, 11, rec.quantity, regular_format)
        sheet.write(i, 12, rec.birthdate, regular_format)
        sheet.write(i, 13, rec.policy, regular_format)
        sheet.write(i, 14, '', regular_format)
        sheet.write(i, 15, rec.dvsn_name, regular_format)
        sheet.write(i, 16, safe_float(rec.uet), regular_format)
        sheet.write(i, 17, safe_float(rec.tariff), regular_format)
        sheet.write(i, 18, safe_float(rec.accepted), regular_format)
    #xl_rowcol_to_cell

    regular_format_bold = book.add_format({'border': 1, 'bold': True})

    sheet.write(i+1, 15, u'Итого:', regular_format_bold)
    s_cell = xl_rowcol_to_cell(7, 16)
    e_cell = xl_rowcol_to_cell(i, 16)
    sheet.write_formula(i+1, 16, '=SUM({0}:{1})'.format(s_cell, e_cell), regular_format_bold)
    s_cell = xl_rowcol_to_cell(7, 17)
    e_cell = xl_rowcol_to_cell(i, 17)
    sheet.write_formula(i+1, 17, '=SUM({0}:{1})'.format(s_cell, e_cell), regular_format_bold)
    s_cell = xl_rowcol_to_cell(7, 18)
    e_cell = xl_rowcol_to_cell(i, 18)
    sheet.write_formula(i+1, 18, '=SUM({0}:{1})'.format(s_cell, e_cell), regular_format_bold)

    book.close()

    output.seek(0)

    response = HttpResponse(base64.b64encode(
        output.read()),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = "attachment; filename=test.xlsx"

    return response
