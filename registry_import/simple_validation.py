# -*- coding: utf-8 -*-

from main.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalOrganization,
    Patient, Person, InsurancePolicy, MedicalRegisterRecord, PersonIDType,
    MedicalServiceTerm, MedicalServiceKind, MedicalServiceForm, MedicalDivision,
    MedicalServiceProfile, TreatmentResult, TreatmentOutcome, Special,
    MedicalWorkerSpeciality, PaymentMethod, PaymentType, PaymentFailureCause,
    Gender, InsurancePolicyType, MedicalHospitalization, MedicalService,
    ProvidedEventConcomitantDisease, ProvidedEventComplicatedDisease,
    MedicalServiceHiTechKind, MedicalServiceHiTechMethod, ExaminationResult)

from main.funcs import safe_int, queryset_to_dict
from main.data_cache import (
    GENDERS, POLICY_TYPES, DEPARTMENTS, ORGANIZATIONS, TERMS, KINDS, FORMS,
    HOSPITALIZATIONS, PROFILES, OUTCOMES, RESULTS, SPECIALITIES_NEW,
    SPECIALITIES_OLD, METHODS, TYPES, FAILURE_CUASES, DISEASES, DIVISIONS,
    SPECIALS, CODES, PERSON_ID_TYPES, HITECH_KINDS, HITECH_METHODS,
    EXAMINATION_RESULTS, ADULT_EXAMINATION_COMMENT_PATTERN)

from validator.collection import Collection
from validator.field import Field
from validator.rules import Regex, IsInList, IsLengthBetween, IsRequired
from validator.rules import IsLength
from validator import rule
from datetime import datetime
import re


ERROR_MESSAGES = {
    'length exceeded': (u'904;Количество символов в поле не соответствует '
                        u'регламентированному.'),
    'missing value': u'902;Отсутствует обязательное значение.',
    'wrong value': u'904;Значение не соответствует справочному.',
    'wrong format': (u'904;Формат значения не соответствует '
                     u'регламентированному.'),
    'is precision': u'904;Диагноз указан без подрубрики',
    'wrong exam result': u'904;Результат диспансеризации не совпадает с '
                         u'указанным в комментарии',
    'registry type mismatch': u'904;Услуга не соответсвует типу файла',
    'hitech method mismatch': u'904;Услуга не соответсвует методу ВМП',
    'expired service': u'904;Код услуги не может быть применён '
                       u'в текущем периоде',
    'children profile mismatch': u'904;Признак детского профила услуги не '
                                 u'совпадает с признаком детского профиля '
                                 u'случая',
    'kind term mismatch': u'904;Вид помощи не соответствует условиям оказания',
}


class MyCollection(Collection):
    def get_dict(self):
        results = {}
        for field in self.fields:
            results[field.title] = field.value

        return results


class IsValidDate(rule.Rule):
    def run(self, field_value):
        try:
            date = datetime.strptime(field_value, '%Y-%m-%d')
        except:
            return False

        return True


def get_person_patient_validation(item, registry_type=1):
    patient = MyCollection().append([
        Field('pk', item['pk']),
        Field('ID_PAC', item['ID_PAC'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 36,
                            error=ERROR_MESSAGES['length exceeded']),
        ]),
        Field('FAM', item['FAM'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'], ),
        ]),
        Field('IM', item['IM'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('OT', item['OT'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('DR', item['DR'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['wrong format'],),
        ]),
        Field('W', item['W'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(GENDERS, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('FAM_P', item['FAM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('IM_P', item['IM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('OT_P', item['OT_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('DR_P', item['DR_P'] or '').append([
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['length exceeded'],
                  pass_on_blank=True),
        ]),
        Field('W_P', item['W_P'] or '').append([
            IsInList(GENDERS, error=ERROR_MESSAGES['wrong value'],
                     pass_on_blank=True),
        ]),
        Field('DOCTYPE', item['DOCTYPE'] or '').append([
        IsInList(list(PERSON_ID_TYPES) + ['0'],
                 error=ERROR_MESSAGES['wrong value'],
                 pass_on_blank=True),
        ]),
        Field('DOCSER', item['DOCSER'] or '').append([
            IsLengthBetween(1, 10,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('DOCNUM', item['DOCNUM'] or '').append([
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('VNOV_D', item['VNOV_D'] or '').append([
            IsLengthBetween(1, 4, error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ])
        #Field('snils', item['SNILS'] or '').append([
        #    IsLength(14, error=u'904,Неверное количество символов.', pass_on_blank=True)
    ])
    patient.run()
    return patient


def get_policy_patient_validation(item, registry_type=1):
    policy = MyCollection().append([
        Field('VPOLIS', item['VPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(['1', '2', '3'],
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('SPOLIS', item['SPOLIS'] or '').append([
            IsLengthBetween(1, 10,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('NPOLIS', item['NPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'], )
        ]),
    ])
    if registry_type == 1:
        policy.append(
            Field('NOVOR', item['NOVOR'] or '').append([
                Regex('(0)|([12]\d{2}\d{2}\d{2}[0-9][0-9]?)',
                      error=ERROR_MESSAGES['wrong format'],
                      pass_on_blank=True)
            ]), )
    policy.run()

    return policy


def get_record_validation(item):
    record = MyCollection().append([
        Field('pk', item['pk']),
        Field('N_ZAP', item['N_ZAP']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 8,
                            error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('PR_NOV', item['PR_NOV']).append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLength(1, error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('register_id', item['registry_pk']),
    ])
    record.run()
    return record


def get_event_validation(item, registry_type=1):
    division = (item['PODR'] or '')[:3]
    if division:
        if len(division) < 3:
            division = ('0'*(3-len(division))) + division

    event = MyCollection().append([
        Field('IDCASE', item['IDCASE'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 11,
                            error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('VIDPOM', item['VIDPOM'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(KINDS), error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('LPU', item['LPU'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(ORGANIZATIONS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('LPU_1', item['LPU_1'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(DEPARTMENTS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('NHISTORY', item['NHISTORY'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 50, error=ERROR_MESSAGES['wrong format']),
        ]),
        Field('DATE_1', item['DATE_1'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsValidDate(error=ERROR_MESSAGES['wrong format'])
        ]),
        Field('DATE_2', item['DATE_2'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsValidDate(error=ERROR_MESSAGES['wrong format'])
        ]),
        Field('DS1', item['DS1'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('IDSP', item['IDSP'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(METHODS, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('ED_COL', item['ED_COL'] or ''),
    ])

    if registry_type in (1, 2):
        event.append([
            Field('USL_OK', item['USL_OK'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(TERMS), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('FOR_POM', item['FOR_POM'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(FORMS), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('NPR_MO', item['NPR_MO'] or '').append([
                IsInList(list(ORGANIZATIONS),
                         error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('EXTR', item['EXTR'] or '').append([
                IsInList(list(HOSPITALIZATIONS) + ['0'],
                         error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('PODR', division).append([
                IsInList(list(DIVISIONS), error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('PROFIL', item['PROFIL'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(PROFILES), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('DET', item['DET'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(['0', '1']), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('DS0', item['DS0'] or '').append([
                IsInList(DISEASES, error=ERROR_MESSAGES['wrong value'], pass_on_blank=True),
            ]),
            Field('RSLT', item['RSLT'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(RESULTS, error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('ISHOD', item['ISHOD'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(OUTCOMES, error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('PRVS', item['PRVS'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(SPECIALITIES_NEW, error=ERROR_MESSAGES['wrong value'])
            ]),
            Field('IDDOKT', item['IDDOKT'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsLengthBetween(1, 25, error=ERROR_MESSAGES['wrong format']),
            ]),

        ])

    if registry_type == 2:
        event.append([
            Field('VID_HMP', item['VID_HMP'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(HITECH_KINDS, error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('METOD_HMP', item['METOD_HMP'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(HITECH_METHODS, error=ERROR_MESSAGES['wrong value']),
            ]),
        ])

    if registry_type in [3, 4, 6, 7]:
        event.append([
            Field('P_OTK', item['P_OTK'] or '').append([
                IsInList(['0', '1'], error=ERROR_MESSAGES['wrong value'])
            ]),
        ])

    if registry_type in list(range(3, 11)):
        event.append([
            Field('RSLT_D', item['RSLT_D'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(EXAMINATION_RESULTS,
                         error=ERROR_MESSAGES['wrong value']),
            ])
        ])

    if registry_type in (3, 4):
        event.append([
            Field('COMENTSL', item['COMENTSL'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                Regex(ADULT_EXAMINATION_COMMENT_PATTERN,
                      error=ERROR_MESSAGES['wrong format']),
            ])
        ])

    if registry_type == 5:
        event.append([
            Field('COMENTSL', item['COMENTSL'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                Regex(r'^F(0|1)[0-3]{1}(0|1)$',
                      error=ERROR_MESSAGES['wrong format']),
            ])
        ])

    if registry_type in (6, 7, 8, 9, 10):
        event.append([
            Field('COMENTSL', item['COMENTSL'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                Regex(r'^F(0|1)[0-9]{1}$',
                      error=ERROR_MESSAGES['wrong format']),
            ])
        ])

    event.run()

    return event

def get_complicated_disease_validation(item, organization, registry_type=1):
    disease = MyCollection()

    if registry_type in (1, 2):
        disease.append([
            Field('DS3', item or '').append([
                IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
            ])
        ])
    disease.run()

    return disease


def get_concomitant_disease_validation(item, organization, registry_type=1):
    disease = MyCollection()

    disease.append([
        Field('DS2', item or '').append([
            IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
        ])
    ])
    disease.run()

    return disease


def get_event_special_validation(item, registry_type=1):
    special = MyCollection()

    special.append([
        Field('OS_SLUCH', item['OS_SLUCH'] or '').append([
            IsInList(SPECIALS, error=ERROR_MESSAGES('wrong value'),
                     pass_on_blank=True)
        ])
    ])
    special.run()

    return special


def get_service_validation(item, registry_type=1, event={}):
    division = (item['PODR'] or '')[:3]
    if division:
        if len(division) < 3:
            division = ('0'*(3-len(division))) + division

    service = MyCollection().append([
        Field('IDSERV', item['IDSERV'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 36, error=ERROR_MESSAGES['wrong format']),
        ]),
        Field('LPU', item['LPU'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(ORGANIZATIONS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('LPU_1', item['LPU_1'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(list(DEPARTMENTS),
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('DATE_IN', item['DATE_IN'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsValidDate(error=ERROR_MESSAGES['wrong format'])
        ]),
        Field('DATE_OUT', item['DATE_OUT'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsValidDate(error=ERROR_MESSAGES['wrong format'])
        ]),
        Field('DS', item['DS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('CODE_MD', item['CODE_MD'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 25, error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('CODE_USL', item['CODE_USL'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(CODES, error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('KOL_USL', item['KOL_USL'] or ''),
        Field('TARIF', item['TARIF'] or ''),
        Field('SUMV_USL', item['SUMV_USL'] or ''),
        Field('COMENTU', item['COMENTU'] or ''),
    ])

    if registry_type in (1, 2):
        service.append([
            Field('PODR', division).append([
                IsInList(list(DIVISIONS), error=ERROR_MESSAGES['wrong value'],
                         pass_on_blank=True),
            ]),
            Field('PROFIL', item['PROFIL'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(PROFILES), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('DET', item['DET'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(list(['0', '1']), error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('PRVS', item['PRVS'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(SPECIALITIES_NEW, error=ERROR_MESSAGES['wrong value'])
            ]),
        ])

    return service

(
  "if self.event.term in (1, 2) and service.tariff_profile_id and service.tariff_profile_id != 999:\n"
 "    event_term = CODES.get(self.code, 0).tariff_profile.term_id\n"
 "    if not ((self.event.term == 1 and event_term == 1) \n"
 "            or (self.event.term == 2 and event_term in (2, 10, 11, 12))):\n"
 "        errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,\n"
 "                       self.event.id, self.id,\n"
 "                       u'Услуга не оказывается в текущих условиях'))\n")
