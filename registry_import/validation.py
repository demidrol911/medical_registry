# -*- coding: utf-8 -*-

from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalOrganization,
    Patient, Person, InsurancePolicy, MedicalRegisterRecord, PersonIDType,
    MedicalServiceTerm, MedicalServiceKind, MedicalServiceForm, MedicalDivision,
    MedicalServiceProfile, TreatmentResult, TreatmentOutcome, Special,
    MedicalWorkerSpeciality, PaymentMethod, PaymentType, PaymentFailureCause,
    Gender, InsurancePolicyType, MedicalHospitalization, MedicalService,
    ProvidedEventConcomitantDisease, ProvidedEventComplicatedDisease,
    MedicalServiceHiTechKind, MedicalServiceHiTechMethod, ExaminationResult)

from main.funcs import safe_int, queryset_to_dict
from validator.collection import Collection
from validator.field import Field
from validator.rules import Regex, IsInList, IsLengthBetween, IsRequired
from validator.rules import IsLength

ERROR_MESSAGES = {
    'length exceeded': (u'904;Количество символов в поле не соответствует '
                        u'регламентированному.'),
    'missing value': u'902;Отсутствует обязательное значение.',
    'wrong value': u'904;Значение не соответствует справочному.',
    'wrong format': (u'904;Формат значения не соответствует '
                     u'регламентированному.'),
}

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
FAILURE_CUASES = queryset_to_dict(PaymentFailureCause.objects.all())
DISEASES = {rec.idc_code: rec for rec in IDC.objects.all() if rec.idc_code or rec.idc_code != u'НЕТ'}
DIVISIONS = queryset_to_dict(MedicalDivision.objects.all())
SPECIALS = queryset_to_dict(Special.objects.all())
CODES = queryset_to_dict(MedicalService.objects.all())
PERSON_ID_TYPES = queryset_to_dict(PersonIDType.objects.filter(is_visible=True))
HITECH_KINDS = queryset_to_dict(MedicalServiceHiTechKind.objects.all())
HITECH_METHODS = queryset_to_dict(MedicalServiceHiTechMethod.objects.all())
EXAMINATION_RESULTS = queryset_to_dict(ExaminationResult.objects.all())

ADULT_EXAMINATION_COMMENT_PATTERN = r'^F(0|1)(0|1)[0-3]{1}(0|1)$'
ADULT_PREVENTIVE_COMMENT_PATTERN = r'^F(0|1)[0-3]{1}(0|1)$'

KIND_TERM_DICT = {1: [2, 3, 21, 22, 31, 32, 4],
                  2: [1, 2, 3, 21, 22, 31, 32, 4],
                  3: [1, 11, 12, 13, 4]}


class MyCollection(Collection):
    def get_dict(self):
        results = {}
        for field in self.fields:
            results[field.title] = field.value

        return results


def get_person_patient_validation(item, registry_type=1):
    patient = MyCollection().append([
        Field('pk', item['pk']),
        Field('uid', item['ID_PAC'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 36,
                            error=ERROR_MESSAGES['length exceeded']),
        ]),
        Field('last_name', item['FAM'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'], ),
        ]),
        Field('first_name', item['IM'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('middle_name', item['OT'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('birthdate', item['DR'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['wrong format'],),
        ]),
        Field('gender', item['W'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(GENDERS, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('agent_last_name', item['FAM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_first_name', item['IM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_middle_name', item['OT_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_birthdate', item['DR_P'] or '').append([
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['length exceeded'],
                  pass_on_blank=True),
        ]),
        Field('agent_gender', item['W_P'] or '').append([
            IsInList(GENDERS, error=ERROR_MESSAGES['wrong value'],
                     pass_on_blank=True),
        ]),
        Field('person_id_type', item['DOCTYPE'] or '').append([
        IsInList(list(PERSON_ID_TYPES) + [0, ],
                 error=ERROR_MESSAGES['wrong value'],
                 pass_on_blank=True),
        ]),
        Field('person_id_series', item['DOCSER'] or '').append([
            IsLengthBetween(1, 10,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('person_id_number', item['DOCNUM'] or '').append([
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        #Field('snils', item['SNILS'] or '').append([
        #    IsLength(14, error=u'904,Неверное количество символов.', pass_on_blank=True)
    ])
    patient.run()
    return patient


def get_policy_patient_validation(item, registry_type=1):
    policy = MyCollection().append([
        Field('insurance_policy_type', item['VPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(['1', '2', '3'],
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('insurance_policy_series', item['SPOLIS'] or '').append([
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('insurance_policy_number', item['NPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'], )
        ]),
    ])
    if registry_type == 1:
        policy.append(
            Field('newborn_code', item['NOVOR'] or '').append([
                Regex('(0)|([12]\d{2}\d{2}\d{2}[1-99])',
                      error=ERROR_MESSAGES['wrong format'],
                      pass_on_blank=True)
            ]), )
    policy.run()

    return policy


def get_record_validation(item):
    record = MyCollection().append([
        Field('pk', item['pk']),
        Field('uid', item['N_ZAP']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 8,
                            error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('is_corrected', item['PR_NOV']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLength(1, error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('register_id', item['registry_pk']),
    ])
    record.run()
    return record


def get_event_validation(item, registry_type=1):
    event = MyCollection().append([
        Field('uid', item['IDCASE']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 11,
                            error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('kind', item['VID_POM']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(KINDS), error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('organization', item['LPU']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(ORGANIZATIONS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('department', item['LPU_1']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(DEPARTMENTS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('anamnesis_number', item['NHISTORY']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 50, error=ERROR_MESSAGES['wrong format']),
        ]),

    ])

    if registry_type in (1, 2):
        event.append([
            Field('term', item['USL_OK']).append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(TERMS), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('form', item['FOR_POM']).append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(FORMS), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('refer_organization', item['NPR_MO']).append([
                IsInList(list(ORGANIZATIONS),
                         error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('hospitalization', item['EXTR']).append([
                IsInList(list(ORGANIZATIONS),
                         error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('division', item['PODR']).append([
                IsInList(list(DIVISIONS), error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('profile', item['PROFIL']).append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(PROFILES), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('is_children_profile', item['DET']).append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(['0', '1']), error=ERROR_MESSAGES['wrong value']),
            ]),

        ])

    if registry_type in range(3, 4, 6, 7):
        event.append([
            Field('examination_rejection', item['P_OTK']).append([
                IsInList(['0', '1'], error=ERROR_MESSAGES['wrong value'])
            ]),
        ])

    """
        if self.term in KIND_TERM_DICT and self.kind not in KIND_TERM_DICT[self.term]:
            errors.append((True, '904', 'SLUCH', 'VIDPOM', record_id, self.id, 0,
                           u'Вид медицинской помощи не соответствует условиям оказания'))

        if not self.start_date:
            errors.append((True, '904', 'SLUCH', 'DATE_1', record_id, self.id, 0,
                           u'Отсутствует дата начала лечения'))

        if not self.end_date:
            errors.append((True, '904', 'SLUCH', 'DATE_2', record_id, self.id, 0,
                           u'Отсутствует дата конца лечения'))

        initial_disease = DISEASES.get(self.initial_disease, None)
        if not initial_disease and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'DS0', record_id, self.id, 0,
                           u'Недопустимый код первичного диагноза'))

        if initial_disease and initial_disease.is_precision and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DS0', record_id, self.id, 0,
                           u'Первичный диагноз указан без подрубрики!'))

        basic_disease = DISEASES.get(self.basic_disease, None)
        if not basic_disease:
            errors.append((True, '902', 'SLUCH', 'DS1', record_id, self.id, 0,
                           u'Недопустимый код основного диагноза'))

        if basic_disease and basic_disease.is_precision:
            errors.append((True, '904', 'SLUCH', 'DS1', record_id, self.id, 0,
                           u'Основной диагноз указан без подрубрики!'))

        if safe_int(self.treatment_result) not in RESULTS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'RSLT', record_id, self.id, 0,
                           u'Недопустимый код результата обращения'))

        if safe_int(self.treatment_outcome) not in OUTCOMES and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'ISHOD', record_id, self.id, 0,
                           u'Недопустимый код исхода заболевания'))

        if self.speciality_dict_version == 'V015' and \
              self.worker_speciality not in SPECIALITIES_NEW and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'PRVS', record_id, self.id, 0,
                           u'Недопустимый код специальности врача'))

        if (not self.speciality_dict_version or self.speciality_dict_version == 'V004')\
                and self.worker_speciality not in SPECIALITIES_OLD and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'PRVS', record_id, self.id, 0,
                           u'Недопустимый код специальности врача'))

        if not self.worker_code and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'IDDOKT', record_id, self.id, 0,
                           u'Отсутствует код врача'))

        for special in self.special or []:
            if safe_int(special) not in SPECIALS:
                errors.append((True, '902', 'SLUCH', 'OS_SLUCH', record_id, self.id, 0,
                               u'Недопустимый код особого случая'))

        if safe_int(self.payment_method) not in METHODS:
            errors.append((True, '902', 'SLUCH', 'IDSP', record_id, self.id, 0,
                           u'Недопустимый код способа оплаты'))

        if self.record.register.type == 2 and \
                self.hitech_kind not in HITECH_KINDS:
            errors.append((True, '904', 'SLUCH', 'VID_HMP', record_id, self.id, 0,
                           u'Недопустимый код вида ВМП'))

        if self.record.register.type == 2:
            if self.hitech_method not in HITECH_METHODS:
                errors.append((True, '904', 'SLUCH', 'METHOD_HMP',
                               record_id, self.id, 0,
                               u'Недопустимый код метода ВМП'))

        if self.record.register.type in list(range(3, 11)):
            if self.examination_result not in EXAMINATION_RESULTS:
                errors.append((True, '904', 'SLUCH', 'RSLT_D', record_id,
                               self.id, 0,
                               u'Недопустимый код результата диспансеризации'))
        a = re.compile(ADULT_EXAMINATION_COMMENT_PATTERN)
        if self.record.register.type in [3, 4] and a.match(self.comment or ''):

            if self.examination_result in [1, 2, 3, 4, 5] and \
                    str(self.comment)[3] != str(self.examination_result)[-1]:
                errors.append((True, '904', 'SLUCH', 'RSLT_D', record_id,
                               self.id, 0,
                               u'Неверный код результата диспансеризации'))

            if self.examination_result in [11, 12, 13] and \
                    str(self.comment)[2:4] != str(self.examination_result)[-2:]:
                errors.append((True, '904', 'SLUCH', 'RSLT_D', record_id,
                               self.id, 0,
                               u'Неверный код результата диспансеризации'))
                #print repr(self.comment), repr(self.examination_result)

        elif self.record.register.type in [3, 4] and not a.match(self.comment or ''):
            errors.append((True, '902', 'SLUCH', 'COMENTSL', record_id,
                           self.id, 0,
                           u'Отсутствует или неверный формат обязательного комментария'))

        b = re.compile(ADULT_PREVENTIVE_COMMENT_PATTERN)
        if self.record.register.type in [5, ] and not b.match(self.comment or ''):
            errors.append((True, '902', 'SLUCH', 'COMENTSL', record_id,
                           self.id, 0,
                           u'Отсутствует или неверный формат обязательного комментария'))

    """
