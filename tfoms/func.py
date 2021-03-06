#! -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
from django.db.models import Q
from django.db import connection
from main.models import (
    MedicalError, ProvidedService, MedicalRegister,
    ProvidedEvent,
    TariffFap, PaymentFailureCause,
    MedicalRegisterRecord, Sanction,
    MedicalOrganization, TariffCapitation,
    MedicalWorkerSpeciality, MedicalServiceProfile,
    MedicalService, MedicalDivision,
    MedicalServiceSubgroup, MedicalServiceTerm,
    TariffProfile, MedicalServiceGroup,
    MedicalServiceReason,
    ProvidedServiceCoefficient,
    TariffCoefficient,
    ProvidedEventConcomitantDisease
)
from main.funcs import dictfetchall

### Отчётный год и период
YEAR = '2016'  # str(cur_date.year)
PERIOD = '06'  # ('0%d' if PERIOD_INT < 10 else '%d') % PERIOD_INT
DATE_ATTACHMENT = datetime.strptime(
    '{year}-{period}-1'.format(year=YEAR, period=PERIOD),
    '%Y-%m-%d'
)


### Справочники

# Справочник причин отказов
FAILURE_CAUSES = {
    failure_cause.pk: {'number': failure_cause.number, 'name': failure_cause.name}
    for failure_cause in PaymentFailureCause.objects.all()
}

# Справочник ошибок
ERRORS = {
    error.pk: {
        'code': error.old_code,
        'failure_cause': error.failure_cause_id,
        'name': error.name
    }
    for error in MedicalError.objects.all()
}

# Справочник специальностей мед. работника
WORKER_SPECIALITIES = {
    worker.pk: {
        'code': worker.code,
        'name': worker.name
    }
    for worker in MedicalWorkerSpeciality.objects.all()
}

# Справочник медицинских профилей
MEDICAL_PROFILES = {
    profile.pk: {
        'code': profile.code,
        'name': profile.name
    }
    for profile in MedicalServiceProfile.objects.all()
}

# Справочник тарифных профилей
TARIFF_PROFILES = {
    profile.pk: {'name': profile.name}
    for profile in TariffProfile.objects.all()
}

# Справочник медицинских услуг
MEDICAL_SERVICES = {
    service.pk: {
        'code': service.code,
        'name': service.name
    }
    for service in MedicalService.objects.all()
}

# Справочник медицинских отделений
MEDICAL_DIVISIONS = {
    division.pk: {
        'code': division.code,
        'name': division.name
    }
    for division in MedicalDivision.objects.all()
}

# Справочник медицинских групп
MEDICAL_GROUPS = {
    group.pk: {'name': group.name}
    for group in MedicalServiceGroup.objects.all()
}

# Справочник медицинских подгрупп
MEDICAL_SUBGROUPS = {
    subgroup.pk: {'name': subgroup.name}
    for subgroup in MedicalServiceSubgroup.objects.all()
}

# Справочник условий оказания мед. помощи
MEDICAL_TERMS = {
    term.pk: {'name': term.name}
    for term in MedicalServiceTerm.objects.all()
}

# Справочник причин оказания мед. помощи
MEDICAL_REASONS = {
    reason.pk: {'name': reason.name}
    for reason in MedicalServiceReason.objects.all()
}

# Справочник типов коэффициентовы
COEFFICIENT_TYPES = {
    coefficient.pk: {'name': coefficient.name, 'value': coefficient.value}
    for coefficient in TariffCoefficient.objects.all()
}


# Информация о лечебном учреждении
def get_mo_info(mo_code, department_code=None):
    if department_code:
        mo = MedicalOrganization.objects.get(code=mo_code, old_code=department_code)
    else:
        mo = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True)
    return {'code': mo.code, 'name': mo.name, 'is_agma_cathedra': mo.is_agma_cathedra,
            'act_number': mo.act_number, 'act_head_fullname': mo.act_head_fullname,
            'act_head_position': mo.act_head_position}


# Коды больниц прикреплённых к указанной больнице
def get_partial_register(mo_code):
    return list(ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period=PERIOD,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code).\
        values_list('department__old_code', flat=True).distinct())


# Коды больниц в медицинском реестре за указанный период
def get_mo_register(status=None):
    organizations = MedicalRegister.objects.filter(year=YEAR, period=PERIOD, is_active=True, type=1)
    if status:
        organizations = organizations.filter(status__pk=status)
    return organizations.values_list('organization_code', flat=True)


# Сопутствующие диаагнозы
def get_concomitant_disease(department):
    diseases = ProvidedEventConcomitantDisease.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period=PERIOD,
        event__record__register__is_active=True,
        event__department__old_code=department
    ).values('event__id_pk', 'disease__idc_code')
    disease_list = {}
    for disease in diseases:
        if disease['event__id_pk'] not in disease_list:
            disease_list[disease['event__id_pk']] = disease['disease__idc_code']
    return disease_list


### Информация о пациентах в указанной больнице
def get_patients(mo_code):
    patients = MedicalRegisterRecord.objects.filter(
        register__year=YEAR,
        register__period=PERIOD,
        register__is_active=True,
        register__organization_code=mo_code
    ).values(
        'patient__pk',                       # Ид пациента
        'patient__insurance_policy_series',  # Серия полиса
        'patient__insurance_policy_number',  # Номер полиса
        'patient__last_name',                # Фамилия пациета
        'patient__first_name',               # Имя пациента
        'patient__middle_name',              # Отчество пациента
        'patient__birthdate',                # Дата рождения
        'patient__gender__code',
        'id'
    ).distinct()

    patients_dict = {
        patient['patient__pk']: {
            'policy_series': patient['patient__insurance_policy_series'],
            'policy_number': patient['patient__insurance_policy_number'],
            'last_name': patient['patient__last_name'],
            'first_name': patient['patient__first_name'],
            'middle_name': patient['patient__middle_name'],
            'birthdate': patient['patient__birthdate'],
            'gender_code': patient['patient__gender__code'],
            'xml_id': patient['id']
        }
        for patient in patients}
    return patients_dict


### Информация об услугах в указанной больнице
def get_services(mo_code, is_include_operation=False, department_code=None, payment_type=None,
                 payment_kind=None):
    services = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period=PERIOD,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code
    )

    if department_code:
        services = services.filter(department__old_code=department_code)

    if payment_type:
        services = services.filter(payment_type_id__in=payment_type)

    if payment_kind:
        if payment_kind == [4, ]:
            services = services.filter(payment_kind_id__in=payment_kind)
        else:
            services = services.filter(Q(payment_kind_id__isnull=True) |
                                       Q(payment_kind_id__in=payment_kind))

    if not is_include_operation:
        services = services.exclude(code__group_id=27)

    services_values = services.values(
        'id_pk',                                            # Ид услуги
        'id',                                               # Ид из xml
        'event__anamnesis_number',                          # Амбулаторная карта
        'event__term__pk',                                  # Условие оказания МП
        'worker_code',                                      # Код мед. работника
        'quantity',                                         # Количество дней (услуг)
        'comment',                                          # Комментарий
        'code__pk',                                         # Ид кода услуги
        'code__code',                                       # Код услуги
        'code__name',                                       # Название услуги
        'start_date',                                       # Дата начала услуги
        'end_date',                                         # Дата конца услуги
        'basic_disease__idc_code',                          # Основной диагноз
        'event__basic_disease__idc_code',                   # Основной диагноз случая
        'event__concomitant_disease__idc_code',             # Сопутствующий диагноз
        'code__group__id_pk',                               # Группа
        'code__subgroup__id_pk',                            # Подгруппа услуги
        'code__reason__ID',                                 # Причина
        'division__code',                                   # Код отделения
        'division__term__pk',                               # Вид отделения
        'code__division__pk',                               # Ид отделения (для поликлиники)
        'code__tariff_profile__pk',                         # Тарифный профиль (для стационара и дн. стационара)
        'profile__pk',                                      # Профиль услуги
        'is_children_profile',                              # Возрастной профиль
        'worker_speciality__pk',                            # Специалист
        'payment_type__pk',                                 # Тип оплаты
        'payment_kind__pk',                                 # Вид оплаты
        'tariff',                                           # Основной тариф
        'invoiced_payment',                                 # Поданная сумма
        'accepted_payment',                                 # Принятая сумма
        'calculated_payment',                               # Рассчётная сумма
        'provided_tariff',                                  # Снятая сумма
        'code__uet',                                        # УЕТ
        'event__pk',                                        # Ид случая
        'department__old_code',                             # Код филиала
        'event__record__patient__pk'                        # Ид патиента
    ).order_by(
        'event__record__patient__last_name',
        'event__record__patient__first_name',
        'event__pk', 'code__code'
    )

    services_list = [
        {'id': service['id_pk'],
         'xml_id': service['id'],
         'anamnesis_number': service['event__anamnesis_number'],
         'term': service['event__term__pk'],
         'worker_code': service['worker_code'],
         'quantity': float(service['quantity'] or 1),
         'comment': service['comment'],
         'code_id': service['code__pk'],
         'code': service['code__code'],
         'name': service['code__name'],
         'start_date': service['start_date'],
         'end_date': service['end_date'],
         'basic_disease': service['basic_disease__idc_code'],
         'event_basic_disease': service['event__basic_disease__idc_code'],
         'concomitant_disease': service['event__concomitant_disease__idc_code'],
         'group': service['code__group__id_pk'],
         'subgroup': service['code__subgroup__id_pk'],
         'reason': service['code__reason__ID'],
         'division_code': service['division__code'],
         'division_term': service['division__term__pk'],
         'division_id': service['code__division__pk'],
         'tariff_profile_id': service['code__tariff_profile__pk'],
         'profile': service['profile__pk'],
         'worker_speciality': service['worker_speciality__pk'],
         'payment_type': service['payment_type__pk'],
         'payment_kind': service['payment_kind__pk'],
         'tariff': service['tariff'],
         'invoiced_payment': service['invoiced_payment'],
         'accepted_payment': service['accepted_payment'],
         'calculated_payment': service['calculated_payment'] or 0,
         'provided_tariff': service['provided_tariff'] or service['tariff'],
         'uet': float(service['code__uet'] or 0) * float(service['quantity'] or 1),
         'event_id': service['event__pk'],
         'department': service['department__old_code'],
         'patient_id': service['event__record__patient__pk']}
        for service in services_values]

    return services_list


### Информация об ошибках в указанной больнице
def get_sanctions(mo_code):
    sanctions = Sanction.objects.filter(
        service__event__record__register__year=YEAR,
        service__event__record__register__period=PERIOD,
        service__event__record__register__is_active=True,
        service__event__record__register__organization_code=mo_code,
        is_active=True,
        service__payment_type__in=[3, 4],
        type_id=1,
    )

    sanctions_list = sanctions.values(
        'id_pk',                                       # Ид санкции
        'error__pk',                                   # Ид ошибки
        'service__pk'                                  # Ид услуги
    ).order_by('-service__pk', '-error__weight').distinct()

    sanctions_dict = {}
    for sanction in sanctions_list:
        if sanction['service__pk'] not in sanctions_dict.keys():
            sanctions_dict[sanction['service__pk']] = []
        sanctions_dict[sanction['service__pk']].\
            append({'id': sanction['id_pk'], 'error': sanction['error__pk']})

    return sanctions_dict


def get_coefficients(mo_code):
    coefficients = ProvidedServiceCoefficient.objects.filter(
        service__event__record__register__year=YEAR,
        service__event__record__register__period=PERIOD,
        service__event__record__register__is_active=True,
        service__event__record__register__organization_code=mo_code
    )

    coefficients_list = coefficients.values(
        'service__pk', 'coefficient__pk'
    ).distinct()
    coefficients_dict = {}
    for coefficient in coefficients_list:
        if coefficient['service__pk'] not in coefficients_dict:
            coefficients_dict[coefficient['service__pk']] = []
        coefficients_dict[coefficient['service__pk']].append(coefficient['coefficient__pk'])

    return coefficients_dict


### Ид случаев, по которым рассчитывается подушевое
def get_capitation_events(mo_code):
    mo_obj = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True)
    return mo_obj.get_capitation_events(YEAR, PERIOD, DATE_ATTACHMENT)


### Ид случаев, по которым рассчитыватся обращения
def get_treatment_events(mo_code):
    query = """
    select
    distinct pe.id_pk as event_id
    from medical_register mr
        JOIN medical_register_record mrr
            ON mr.id_pk=mrr.register_fk
        JOIN provided_event pe
            ON mrr.id_pk=pe.record_fk
        JOIN provided_service ps
            ON ps.event_fk=pe.id_pk
        JOIN medical_organization mo
            ON ps.organization_fk=mo.id_pk
        JOIN medical_service ms
            ON ms.id_pk = ps.code_fk
        JOIN patient pt
            ON pt.id_pk = mrr.patient_fk
        left join medical_division msd
            on msd.id_pk = pe.division_fk
        where mr.is_active
           and mr.year=%(year)s
           and mr.period=%(period)s
           and mo.code=%(mo)s
           AND (
             (ms.group_fk = 19 and ms.subgroup_fk = 12)
              or (pe.term_fk = 3 and ms.reason_fk = 1 and
                  (ms.group_fk is NULL or ms.group_fk = 24)
                    and (
                      select count(ps1.id_pk)
                      FROM provided_service ps1
                      join medical_service ms1 on ms1.id_pk = ps1.code_fk
                      WHERE ps1.event_fk  = ps.event_fk
                            and (ms1.group_fk is NULL or ms1.group_fk = 24)
                            and ms1.reason_fk = 1
                      )>1
                    )
                  )
    """
    cursor = connection.cursor()
    cursor.execute(query, dict(year=YEAR, period=PERIOD, mo=mo_code))
    return [row[0] for row in cursor.fetchall()]


def calculate_capitation(term, mo_code):
    """
    Новая функция для рассчета тарифа по подушевому
    """
    tariff = TariffCapitation.objects.filter(
        term=term, organization__code=mo_code,
        start_date__lte=DATE_ATTACHMENT,
        start_date__gte='2016-01-01',
        is_children_profile=True
    )
    result = {'adult': {}, 'child': {}}

    if tariff:
        if term == 3:
            population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                get_attachment_count(DATE_ATTACHMENT)
        elif term == 4:
            population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                get_ambulance_attachment_count(DATE_ATTACHMENT)
    else:
        return False, result

    # Чмсленность
    result['adult']['population'] = population[4]['men'] + population[4]['fem'] + \
        population[5]['men'] + population[5]['fem']

    result['child']['population'] = population[1]['men'] + population[1]['fem'] + \
        population[2]['men'] + population[2]['fem'] + \
        population[3]['men'] + population[3]['fem']

    result['adult']['basic_tariff'] = tariff.order_by('-start_date')[0].value
    result['child']['basic_tariff'] = tariff.order_by('-start_date')[0].value

    for key in result:
        result[key]['tariff'] = Decimal(round(result[key]['population']*result[key]['basic_tariff'], 2))

    for key in result:
        result[key]['coeff'] = 0

    for key in result:
        result[key]['accepted'] = Decimal(round(result[key]['tariff'] + result[key].get('coeff', 0), 2))

    return True, result


def calculate_fluorography(mo_code):
    if mo_code == '280085':
        query = """
            select count(distinct case when age(f.start_date, f.birthdate) >= '18 years' THEN f.insurance_policy_fk END) AS adult_population,
                  count(distinct case when age(f.start_date, f.birthdate) < '18 years' THEN f.insurance_policy_fk END) AS child_population
                from fluorography f
                join medical_organization mo ON mo.code = f.attachment_code and mo.parent_fk is null
                where mo.code <> '280085'
                      and date = format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE
            """
    else:
        query = """
            select count(distinct case when age(f.start_date, f.birthdate) >= '18 years' THEN f.insurance_policy_fk END) AS adult_population,
                 count(distinct case when age(f.start_date, f.birthdate) < '18 years' THEN f.insurance_policy_fk END) AS child_population
                from fluorography f
                join medical_organization mo ON mo.code = f.attachment_code and mo.parent_fk is null
                where mo.code = %(organization_code)s
                      and date = format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE
            """
    cursor = connection.cursor()
    cursor.execute(query, dict(organization_code=mo_code, year=YEAR, period=PERIOD))
    data = dictfetchall(cursor)
    result = {'adult': {}, 'child': {}}
    if data[0]['adult_population'] or data[0]['child_population']:
        result['adult']['population'] = data[0]['adult_population']
        result['child']['population'] = data[0]['child_population']

        result['adult']['basic_tariff'] = 140 if mo_code == '280085' else -140
        result['child']['basic_tariff'] = 140 if mo_code == '280085' else -140

        for key in result:
            result[key]['tariff'] = Decimal(round(result[key]['population']*result[key]['basic_tariff'], 2))

        for key in result:
            result[key]['coeff'] = 0

        for key in result:
            result[key]['accepted'] = result[key]['tariff']

        return True, result
    else:
        return False, {}


# Устанавливает статус реестру
def change_register_status(mo_code, status):
    MedicalRegister.objects.filter(
        year=YEAR,
        period=PERIOD,
        organization_code=mo_code,
        is_active=True
    ).update(status=status)
    if status == 8:
        MedicalRegister.objects.filter(
            year=YEAR,
            period=PERIOD,
            organization_code=mo_code,
            is_active=True).update(pse_export_date=datetime.now())


def get_mo_code(status):
    organizations = MedicalRegister.objects.filter(
        year=YEAR,
        period=PERIOD,
        is_active=True,
        type=1,
        status__pk=status
    )
    if organizations:
        organization_code = organizations[0].organization_code
    else:
        organization_code = ''
    return organization_code


def get_mo_name(mo_code, department=None):
    if department:
        return MedicalOrganization.objects.get(old_code=department).name
    return MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).name


def get_mo_map():
    query = """
        SELECT DISTINCT dep.old_code AS dep_code, mo.code AS mo_code
        FROM provided_service ps
            JOIN provided_event pe
                ON ps.event_fk = pe.id_pk
            JOIN medical_register_record mrr
                ON mrr.id_pk = pe.record_fk
            JOIN medical_register mr
                ON mr.id_pk = mrr.register_fk
            JOIN medical_organization mo
                ON mo.id_pk = ps.organization_fk
            JOIN medical_organization dep
                ON dep.id_pk = ps.department_fk
        WHERE mr.is_active
            AND mr.year = %(year)s
            AND mr.period = %(period)s
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(year=YEAR, period=PERIOD))
    mo_map = {item['dep_code']: item['mo_code'] for item in dictfetchall(cursor)}
    cursor.close()
    return mo_map
