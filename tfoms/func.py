#! -*- coding: utf-8 -*-

from datetime import datetime
from decimal import Decimal
from django.db.models import Q
from django.db import connection
from tfoms.models import (
    MedicalError, ProvidedService, MedicalRegister,
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

### Отчётный год и период
cur_date = datetime.now()

YEAR = str(cur_date.year)
PERIOD_INT = cur_date.month if cur_date.day > 25 else cur_date.month - 1
PERIOD = ('0%d' if PERIOD_INT < 10 else '%d') % PERIOD_INT
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
    return {'code': mo.code, 'name': mo.name, 'is_agma_cathedra': mo.is_agma_cathedra}


# Коды больниц прикреплённых к указанной больнице
def get_partial_register(mo_code):
    return ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period=PERIOD,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code).\
        values_list('department__old_code', flat=True).distinct()


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
    distinct pe.id_pk
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
            where mr.is_active and mr.year='{year}' and mr.period='{period}'
                  and mo.code = '{mo}'
                  AND ((ms.group_fk = 19 and ms.subgroup_fk = 12)
                         or (pe.term_fk = 3 and ms.reason_fk = 1 and
                                (ms.group_fk is NULL or ms.group_fk = 24)
                                and (select count(ps1.id_pk) FROM provided_service ps1
                                         join medical_service ms1 on ms1.id_pk = ps1.code_fk
                                         WHERE ps1.event_fk  = ps.event_fk and (ms1.group_fk is NULL or ms1.group_fk = 24))>1
                                )
                              )
    """
    cursor = connection.cursor()
    cursor.execute(query.format(year=YEAR, period=PERIOD, mo=mo_code))
    return [row[0] for row in cursor.fetchall()]

    '''
    events = ProvidedService.objects.filter(
        event__record__register__year=YEAR,
        event__record__register__period=PERIOD,
        event__record__register__is_active=True,
        event__record__register__organization_code=mo_code).\
        filter(
            Q(code__subgroup__pk=12, code__group__pk=19) |
            (Q(code__reason__pk=1, event__term__pk=3) &
             (Q(code__group__isnull=True) | Q(code__group__pk=24)))
        )
    return events.values_list('event__pk', flat=True).distinct()
    '''


### Расчёт тарифа по подушевому по поликлинике и скорой помощи c января 2015
def calculate_capitation_tariff(term, mo_code):
    tariff = TariffCapitation.objects.filter(
        term=term, organization__code=mo_code,
        start_date__lte=DATE_ATTACHMENT,
        is_children_profile=True
    )
    result = [
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],

        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],

        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],

        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],

        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0],
        [0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0,  0, 0]
    ]

    if tariff:
        if term == 3:
            population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                get_attachment_count(DATE_ATTACHMENT)
        elif term == 4:
            population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                get_ambulance_attachment_count(DATE_ATTACHMENT)
    else:
        return False, result

    print '*', population
    # Чмсленность

    result[0][1] = population[1]['men']
    result[1][1] = population[1]['fem']

    result[2][1] = population[2]['men']
    result[3][1] = population[2]['fem']

    result[4][1] = population[3]['men']
    result[5][1] = population[3]['fem']

    result[6][0] = population[4]['men']
    result[7][0] = population[4]['fem']

    result[8][0] = population[5]['men']
    result[9][0] = population[5]['fem']

    # Тариф основной

    result[0][5] = tariff.filter(age_group=1, gender=1).order_by('-start_date')[0].value
    result[1][5] = tariff.filter(age_group=1, gender=2).order_by('-start_date')[0].value

    result[2][5] = tariff.filter(age_group=2, gender=1).order_by('-start_date')[0].value
    result[3][5] = tariff.filter(age_group=2, gender=2).order_by('-start_date')[0].value

    result[4][5] = tariff.filter(age_group=3, gender=1).order_by('-start_date')[0].value
    result[5][5] = tariff.filter(age_group=3, gender=2).order_by('-start_date')[0].value

    result[6][4] = tariff.filter(age_group=4, gender=1).order_by('-start_date')[0].value
    result[7][4] = tariff.filter(age_group=4, gender=2).order_by('-start_date')[0].value

    result[8][4] = tariff.filter(age_group=5, gender=1).order_by('-start_date')[0].value
    result[9][4] = tariff.filter(age_group=5, gender=2).order_by('-start_date')[0].value

    for idx in xrange(0, 10):
        result[idx][8] = Decimal(round(result[idx][0]*result[idx][4], 2))
        result[idx][9] = Decimal(round(result[idx][1]*result[idx][5], 2))
        # Повышающий коэффициент для Магдагачей
        if mo_code == '280029' and term == 4:
            result[idx][8] *= 2
            result[idx][9] *= 2

    if term == 3:
        fap = TariffFap.objects.filter(organization__code=mo_code,
                                       start_date__lte=DATE_ATTACHMENT,
                                       is_children_profile=True)
        if fap:
            coeff = fap.order_by('-start_date')[0].value
            for idx in xrange(0, 10):
                result[idx][16] = Decimal(round(float(result[idx][8])*float(coeff-1), 2))
                result[idx][17] = Decimal(round(float(result[idx][9])*float(coeff-1), 2))

    for idx in xrange(0, 10):
        result[idx][22] = Decimal(round(result[idx][8] + result[idx][16], 2))
        result[idx][23] = Decimal(round(result[idx][9] + result[idx][17], 2))

    return True, result


### Устанавливает статус реестру
def change_register_status(mo_code, register_status):
    MedicalRegister.objects.filter(
        year=YEAR,
        period=PERIOD,
        organization_code=mo_code,
        is_active=True
    ).update(status=register_status)