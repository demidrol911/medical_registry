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
from validator.collection import Collection
from validator.field import Field
from validator.rules import Regex, IsInList, IsLengthBetween, IsRequired
from validator.rules import IsLength
from validator import rule
from datetime import datetime

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
PERSON_ID_TYPES = queryset_to_dict(PersonIDType.objects.all())
HITECH_KINDS = queryset_to_dict(MedicalServiceHiTechKind.objects.all())
HITECH_METHODS = queryset_to_dict(MedicalServiceHiTechMethod.objects.all())
EXAMINATION_RESULTS = queryset_to_dict(ExaminationResult.objects.all())

ADULT_EXAMINATION_COMMENT_PATTERN = r'^F(0|1)(0|1)[0-3]{1}(0|1)$'
ADULT_PREVENTIVE_COMMENT_PATTERN = r'^F(0|1)[0-3]{1}(0|1)$'

KIND_TERM_DICT = {'1': ['2', '3', '21', '22', '31', '32', '4'],
                  '2': ['1', '2', '3', '21', '22', '31', '32', '4'],
                  '3': ['1', '11', '12', '13', '4'],
                  '4': ['1', '2', '3', '4', '11', '12', '21', '22', '31', '32']
}

NEW_EXAMINATION_CHILDREN_HARD_LIFE = (
    '119020', '119021', '119022', '119023', '119024',
    '119025', '119026', '119027', '119028', '119029',
    '119030', '119031'
)

OLD_EXAMINATION_CHILDREN_HARD_LIFE = ('119001', )

NEW_EXAMINATION_CHILDREN_ADOPTED = (
    '119220', '119221', '119222', '119223', '119224',
    '119225', '119226', '119227', '119228', '119229',
    '119230', '119231'
)

OLD_EXAMINATION_CHILDREN_ADOPTED = ('119001', )

NEW_EXAMINATION_CHILDREN_PREVENTIVE = (
    '119080', '119081', '119082', '119083', '119084',
    '119085', '119086', '119087', '119088', '119089',
    '119090', '119091'
)

OLD_EXAMINATION_CHILDREN_PREVENTIVE = (
    '119051', '119052', '119053', '119054',
    '119055', '119056'
)

NEW_EXAMINATION_ADULT_PREVENTIVE = (
    '019214', '019215', '019216', '019217'
)

OLD_EXAMINATION_ADULT_PREVENTIVE = ('019201', )


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


class DiseaseHasPrecision(rule.Rule):
    def run(self, field_value):
        disease = DISEASES.get(field_value, None)

        if disease and disease.is_precision:
            return False

        return True


class IsCorrespondsToRegistryType(rule.Rule):
    def __init__(self, registry_type, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsCorrespondsToRegistryType, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.registry_type = registry_type

    def run(self, field_value):
        service = CODES.get(field_value)
        if self.register_type == 1 and \
                service.group_id in list(range(6, 17)) + [20]:
            return False
        elif self.register_type == 2 and \
                service.group_id != 20:
            return False
        elif self.register_type in list(range(3, 11)) \
                and service.group_id not in list(range(6, 17) + [25, 26]):
            return False

        return True


class IsServiceKindCorrespondsToTerm(rule.Rule):
    def __init__(self, term, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsServiceKindCorrespondsToTerm, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.term = term

    def run(self, field_value):
        kinds = KIND_TERM_DICT.get(self.term, [])

        if not kinds or not self.term:
            return True

        if field_value in kinds:
            return True

        return False


class IsResultedExaminationComment(rule.Rule):
    def __init__(self, examination_result, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsResultedExaminationComment, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.examination_result = examination_result
        self.strip = kwargs.get('strip', False)

    def run(self, field_value):
        if self.examination_result in ['1', '2', '3', '4', '5']:
            if field_value[3] != str(self.examination_result)[-1]:
                return False

        elif self.examination_result in [11, 12, 13]:
            if str(field_value)[2:4] != str(self.examination_result)[-2:]:
                return False

        return True


class IsCorrespondsToHitechMethod(rule.Rule):
    def __init__(self, hitech_method, registry_type, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsCorrespondsToHitechMethod, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.hitech_method = hitech_method
        self.registry_type = registry_type
        self.strip = kwargs.get('strip', False)

    def run(self, field_value):
        if self.registry_type == 2:
            if safe_int(field_value[-3:]) != safe_int(self.hitech_method):
                return False

        return True


class IsMatchedToEvent(rule.Rule):
    def __init__(self, event_is_children_profile, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsMatchedToEvent, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.event_is_children_profile = event_is_children_profile
        self.strip = kwargs.get('strip', False)

    def run(self, field_value):
        if self.event_is_children_profile != field_value:
            return False

        return True


class IsExpiredService(rule.Rule):
    def __init__(self, event_end_date, **kwargs):
        if not kwargs.get('error', None):
            kwargs['error'] = "???"
        super(IsExpiredService, self).__init__(
            kwargs.get('error', None), kwargs.get('pass_on_blank', False))
        self.event_end_date = event_end_date
        self.strip = kwargs.get('strip', False)

    def run(self, field_value):
        try:
            event_date = datetime.strptime(self.event_end_date, '%Y-%m-%d').date()
        except:
            return False

        control_date = datetime.strptime('2014-07-01', '%Y-%m-%d').date()

        if field_value in (OLD_EXAMINATION_CHILDREN_ADOPTED +
                OLD_EXAMINATION_CHILDREN_HARD_LIFE +
                OLD_EXAMINATION_CHILDREN_PREVENTIVE) \
                and event_date > control_date:
            return False

        if field_value in (NEW_EXAMINATION_ADULT_PREVENTIVE + \
                NEW_EXAMINATION_CHILDREN_ADOPTED +
                NEW_EXAMINATION_CHILDREN_HARD_LIFE +
                NEW_EXAMINATION_CHILDREN_PREVENTIVE) \
                and event_date < control_date:
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
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'], ),
        ]),
        Field('IM', item['IM'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('OT', item['OT'] or '').append([
            IsLengthBetween(1, 40,
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
                Regex('(0)|([12]\d{2}\d{2}\d{2}[1-99])',
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
            IsServiceKindCorrespondsToTerm(item['USL_OK'], error=ERROR_MESSAGES['kind term mismatch'])
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
            DiseaseHasPrecision(error=ERROR_MESSAGES['is precision'],
                                pass_on_blank=True),
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
                DiseaseHasPrecision(error=ERROR_MESSAGES['is precision'],
                                    pass_on_blank=True),
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
                Regex(r'^F(0|1)(0|1)[0-3]{1}(0|1)$',
                      error=ERROR_MESSAGES['wrong format']),
                IsResultedExaminationComment(
                    item['RSLT_D'],
                    error=ERROR_MESSAGES['wrong exam result'])
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

def get_complicated_disease_validation(item, registry_type=1):
    disease = MyCollection()

    if registry_type in (1, 2):
        disease.append([
            Field('DS3', item or '').append([
                IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
                DiseaseHasPrecision(error=ERROR_MESSAGES['is precision'],
                                    pass_on_blank=True)
            ])
        ])
    disease.run()

    return disease


def get_concomitant_disease_validation(item, registry_type=1):
    disease = MyCollection()

    disease.append([
        Field('DS2', item or '').append([
            IsInList(DISEASES, error=ERROR_MESSAGES['wrong value']),
            DiseaseHasPrecision(error=ERROR_MESSAGES['is precision'],
                                pass_on_blank=True)
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
            DiseaseHasPrecision(error=ERROR_MESSAGES['is precision'],
                                pass_on_blank=True),
        ]),
        Field('CODE_MD', item['CODE_MD'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 25, error=ERROR_MESSAGES['length exceeded'])
        ]),
        Field('CODE_USL', item['CODE_USL'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(CODES, error=ERROR_MESSAGES['wrong value']),
            IsCorrespondsToRegistryType(
                registry_type,
                error=ERROR_MESSAGES['registry type mismatch']),
            IsExpiredService(event['DATE_2'],
                             error=ERROR_MESSAGES['expired service']),
            IsCorrespondsToHitechMethod(
                event.get('METOD_HMP', ''), registry_type,
                error=ERROR_MESSAGES['hitech method mismatch']),
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
                IsMatchedToEvent(
                    event['DET'],
                    error=ERROR_MESSAGES['children profile mismatch'])
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
