# -*- coding: utf-8 -*-

from funcs import queryset_to_dict

from main.models import (
    IDC, MedicalOrganization,
    PersonIDType,
    MedicalServiceTerm, MedicalServiceKind, MedicalServiceForm, MedicalDivision,
    MedicalServiceProfile, TreatmentResult, TreatmentOutcome, Special,
    MedicalWorkerSpeciality, PaymentMethod, PaymentType, PaymentFailureCause,
    Gender, InsurancePolicyType, MedicalHospitalization, MedicalService,
    MedicalServiceHiTechKind, MedicalServiceHiTechMethod, ExaminationResult, KSG,
    MedicalError, TariffProfile, MedicalServiceGroup, MedicalServiceSubgroup,
    MedicalServiceReason, TariffCoefficient
)


GENDERS = queryset_to_dict(Gender.objects.all())
POLICY_TYPES = queryset_to_dict(InsurancePolicyType.objects.all())
DEPARTMENTS = {rec.old_code: rec for rec in MedicalOrganization.objects.all()}
ORGANIZATIONS = queryset_to_dict(MedicalOrganization.objects.filter(parent=None))
TERMS = queryset_to_dict(MedicalServiceTerm.objects.all())
KINDS = queryset_to_dict(MedicalServiceKind.objects.all())
FORMS = queryset_to_dict(MedicalServiceForm.objects.all())
HOSPITALIZATIONS = queryset_to_dict(MedicalHospitalization.objects.all())
PROFILES = queryset_to_dict(MedicalServiceProfile.objects.filter(is_active=True))
OUTCOMES = queryset_to_dict(TreatmentOutcome.objects.all())
RESULTS = queryset_to_dict(TreatmentResult.objects.all())
SPECIALITIES_OLD = queryset_to_dict(MedicalWorkerSpeciality.objects.filter(
    is_active=False
))
SPECIALITIES_NEW = queryset_to_dict(MedicalWorkerSpeciality.objects.filter(
    is_active=True
))
METHODS = queryset_to_dict(PaymentMethod.objects.all())
TYPES = queryset_to_dict(PaymentType.objects.all())
FAILURE_CAUSES = queryset_to_dict(PaymentFailureCause.objects.all())
DISEASES = {rec.idc_code: rec for rec in IDC.objects.all() if rec.idc_code or rec.idc_code != u'НЕТ'}
DIVISIONS = queryset_to_dict(MedicalDivision.objects.all())
SPECIALS = queryset_to_dict(Special.objects.all())
CODES = queryset_to_dict(MedicalService.objects.all())
PERSON_ID_TYPES = queryset_to_dict(PersonIDType.objects.all())
HITECH_KINDS = queryset_to_dict(MedicalServiceHiTechKind.objects.filter(is_active=True))
HITECH_METHODS = queryset_to_dict(MedicalServiceHiTechMethod.objects.filter(is_active=True))
EXAMINATION_RESULTS = queryset_to_dict(ExaminationResult.objects.all())
HOSPITAL_KSGS = queryset_to_dict(KSG.objects.filter(start_date='2016-01-01', term=1))
DAY_HOSPITAL_KSGS = queryset_to_dict(KSG.objects.filter(start_date='2016-01-01', term=2))

ERRORS = {error.pk: {'code': error.old_code, 'failure_cause': error.failure_cause_id, 'name': error.name}
          for error in MedicalError.objects.all()}
TARIFF_PROFILES = {profile.pk: {'name': profile.name} for profile in TariffProfile.objects.all()}
MEDICAL_GROUPS = {group.pk: {'name': group.name} for group in MedicalServiceGroup.objects.all()}
MEDICAL_SUBGROUPS = {subgroup.pk: {'name': subgroup.name} for subgroup in MedicalServiceSubgroup.objects.all()}
MEDICAL_REASONS = {reason.pk: {'name': reason.name} for reason in MedicalServiceReason.objects.all()}
COEFFICIENT_TYPES = {coefficient.pk: {'name': coefficient.name, 'value': coefficient.value}
                     for coefficient in TariffCoefficient.objects.all()}
FAILURES = {
    failure_cause.pk: {'number': failure_cause.number, 'name': failure_cause.name}
    for failure_cause in PaymentFailureCause.objects.all()
}


KIND_TERM_DICT = {'1': ['2', '3', '21', '22', '31', '32', '4'],
                  '2': ['1', '2', '3', '21', '22', '31', '32', '4'],
                  '3': ['1', '11', '12', '13', '4'],
                  '4': ['1', '2', '3', '4', '11', '12', '21', '22', '31', '32']}

EXAMINATION_HEALTH_GROUP_EQUALITY = {
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '11': '1',
    '12': '2',
    '13': '3',
    '14': u'3а',
    '15': u'3б',
    '31': u'3а',
    '32': u'3б'}

ADULT_EXAMINATION_COMMENT_PATTERN = ur'^F(?P<student>[01])(?P<second_level>[01])(?P<veteran>[01])(?P<health_group>[123][абАБ]?)$'
ADULT_PREVENTIVE_COMMENT_PATTERN = r'^F(0|1)[0-3]{1}(0|1)$'

OLD_ADULT_EXAMINATION = ('019015', '019020', '019001', '019017', '19015', '19020', '19001', '19017')
NEW_ADULT_EXAMINATION = ('019025', '019026', '019027', '019028', '19025', '19026', '19027', '19028')

MONTH_NAME = {
    '01': u'Январь', '02': u'февраль',
    '03': u'Март', '04': u'Апрель', '05': u'Май',
    '06': u'Июнь', '07': u'Июль', '08': u'Август',
    '09': u'Сентябрь', '10': u'Октябрь', '11': u'Ноябрь',
    '12': u'Декабрь'
}
