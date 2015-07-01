# -*- coding: utf-8 -*-

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


class IsValidDate(rule.Rule):
    def run(self, field_value):
        try:
            date = datetime.strptime(field_value, '%Y-%m-%d')
        except:
            return False

        return True


class SpecifiedDisease(rule.Rule):
    def run(self, field_value):
        disease = DISEASES.get(field_value)

        if disease and disease.is_precision:
            return False

        return True


def set_error(code, field='', parent='', record_uid='',
              event_uid='', service_uid='', comment=''):
    return {'code': code, 'field': field, 'parent': parent,
            'record_uid': record_uid, 'event_uid': event_uid,
            'service_uid': service_uid, 'comment': comment}


def handle_errors(errors=[], parent='', record_uid='',
                  event_uid='', service_uid=''):
    errors_list = []
    for field in errors:
        for e in errors[field]:
            error_code, error_message = e.split(';')
            errors_list.append(set_error(
                code=error_code, field=field, parent=parent,
                record_uid=record_uid, event_uid=event_uid,
                service_uid=service_uid, comment=error_message)
            )
    return errors_list


class PersonValidator(object):
    registry = {}
    invoice = {}

    raw_person = {}
    raw_policy = {}
    raw_record = {}
    raw_event = {}
    raw_service = {}
    raw_concomitant_disease = {}
    raw_complicated_disease = {}

    clean_person = {}
    clean_policy = {}
    clean_record = {}
    clean_event = {}
    clean_service = {}
    clean_concomitant_disease = {}
    clean_complicated_disease = {}

    _person_validator = {}
    _policy_validator = {}
    _record_validator = {}
    _event_validator = {}
    _service_validator = {}
    _concomitant_disease_validator = {}
    _complicated_disease_validator = {}


    def set_registry(self, item):
        self.registry = item

    def set_invoice(self, item):
        self.invoice = item

    def set_person(self, item):
        self.raw_person = item
        self._person_validator = self._get_person_validator(item)
        self.clean_person = self._get_cleaned_data(self._person_validator)

    def set_policy(self, item):
        self.raw_policy = item
        self._policy_validator = self._get_policy_validator(item)
        self.clean_policy = self._get_cleaned_data(self._policy_validator)

    def set_record(self, item):
        self.raw_record = item
        self._record_validator = self._get_record_validator(item)
        self.clean_record = self._get_cleaned_data(self._record_validator)

    def _get_cleaned_data(self, validator):
        cleaned_data = {}

        for field in validator.fields:
            cleaned_data[field.title] = field.value

        return cleaned_data

    def _get_person_validator(self, item):
        collection = Collection().append([
            Field('pk', item['pk']),
            Field('ID_PAC', item['ID_PAC'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsLengthBetween(1, 36,
                                error=ERROR_MESSAGES['length exceeded']),
            ]),
            Field('FAM', item['FAM'] or '').append([
                IsLengthBetween(0, 40, error=ERROR_MESSAGES['length exceeded']),
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
        collection.run()

        return collection

    def _get_policy_validator(self, item):
        collection = Collection().append([
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

        if self.registry.type == 1:
            collection.append(
                Field('NOVOR', item['NOVOR'] or '').append([
                    Regex('(0)|([12]\d{2}\d{2}\d{2}[0-9][0-9]?)',
                          error=ERROR_MESSAGES['wrong format'],
                          pass_on_blank=True)
                ]), )

        collection.run()

        return collection

    def _get_record_validator(self, item):
        collection = Collection().append([
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

        collection.run()

        return collection

    def _get_event_validator(self, item):
        division = (item['PODR'] or '')[:3]
        if division:
            if len(division) < 3:
                division = ('0'*(3-len(division))) + division

        collection = Collection().append([
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
                IsInList(DISEASES, error=ERROR_MESSAGES['wrong value'], pass_on_blank=True),
                SpecifiedDisease(error=ERROR_MESSAGES['is precision'], pass_on_blank=True)
            ]),
            Field('IDSP', item['IDSP'] or '').append([
                IsRequired(error=ERROR_MESSAGES['missing value']),
                IsInList(METHODS, error=ERROR_MESSAGES['wrong value']),
            ]),
            Field('ED_COL', item['ED_COL'] or ''),
        ])

        if self.registry.type in (1, 2):
            collection.append([
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
                    SpecifiedDisease(error=ERROR_MESSAGES['is precision'], pass_on_blank=True)
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

        if self.registry.type == 2:
            collection.append([
                Field('VID_HMP', item['VID_HMP'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    IsInList(HITECH_KINDS, error=ERROR_MESSAGES['wrong value']),
                ]),
                Field('METOD_HMP', item['METOD_HMP'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    IsInList(HITECH_METHODS, error=ERROR_MESSAGES['wrong value']),
                ]),
            ])

        if self.registry.type in [3, 4, 6, 7]:
            collection.append([
                Field('P_OTK', item['P_OTK'] or '').append([
                    IsInList(['0', '1'], error=ERROR_MESSAGES['wrong value'])
                ]),
            ])

        if self.registry.type in list(range(3, 11)):
            collection.append([
                Field('RSLT_D', item['RSLT_D'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    IsInList(EXAMINATION_RESULTS,
                             error=ERROR_MESSAGES['wrong value']),
                ])
            ])

        if self.registry.type in (3, 4):
            collection.append([
                Field('COMENTSL', item['COMENTSL'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    Regex(ADULT_EXAMINATION_COMMENT_PATTERN,
                          error=ERROR_MESSAGES['wrong format']),
                ])
            ])

        if self.registry.type == 5:
            collection.append([
                Field('COMENTSL', item['COMENTSL'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    Regex(r'^F(0|1)[0-3]{1}(0|1)$',
                          error=ERROR_MESSAGES['wrong format']),
                ])
            ])

        if self.registry.type in (6, 7, 8, 9, 10):
            collection.append([
                Field('COMENTSL', item['COMENTSL'] or '').append([
                    IsRequired(error=ERROR_MESSAGES['missing value']),
                    Regex(r'^F(0|1)[0-9]{1}$',
                          error=ERROR_MESSAGES['wrong format']),
                ])
            ])

        collection.run()

        return collection

    def _get_person_errors(self):
        handle_errors(self._validator_object, parent='PERS',
                      record_uid=self.clean_record.get('uid', ''),
                      event_uid='',
                      service_uid='')

    def handle_errors(errors=[], parent='', record_uid='',
                      event_uid='', service_uid=''):
        errors_list = []
        for field in errors:
            for e in errors[field]:
                error_code, error_message = e.split(';')
                errors_list.append(set_error(
                    code=error_code, field=field, parent=parent,
                    record_uid=record_uid, event_uid=event_uid,
                    service_uid=service_uid, comment=error_message)
                )
        return errors_list

    def _get_complicated_disease_validator(self, item):
        collection = Collection()

        if self.registry.type in (1, 2):
            collection.append([
                Field('DS3', item or '').append([
                    IsInList(DISEASES, error=ERROR_MESSAGES['wrong value'],
                             pass_on_blank=True),
                    SpecifiedDisease(error=ERROR_MESSAGES['is precision'],
                                     pass_on_blank=True)
                ])
            ])
        collection.run()

        return collection

    def _get_concomitant_disease_validator(self, item):
        collection = Collection()

        if self.registry.type in (1, 2):
            collection.append([
                Field('DS2', item or '').append([
                    IsInList(DISEASES, error=ERROR_MESSAGES['wrong value'],
                             pass_on_blank=True),
                    SpecifiedDisease(error=ERROR_MESSAGES['is precision'],
                                     pass_on_blank=True)
                ])
            ])
        collection.run()

        return collection

    def _get_event_special_validator(self, item):
        collection = Collection()

        collection.append([
            Field('OS_SLUCH', item['OS_SLUCH'] or '').append([
                IsInList(SPECIALS, error=ERROR_MESSAGES('wrong value'),
                         pass_on_blank=True)
            ])
        ])
        collection.run()

        return collection

    def _get_service_validation(self, item):
        division = (item['PODR'] or '')[:3]
        if division:
            if len(division) < 3:
                division = ('0'*(3-len(division))) + division

        collection = Collection().append([
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
                SpecifiedDisease(error=ERROR_MESSAGES['is precision'])
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

        if self.registry.type in (1, 2):
            collection.append([
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
        collection.run()

        return collection

    def _is_service_registry_corresponding(self):
        self.clean_service['service = CODES.get(field_value)

        if field_value and field_value.startswith('A'):
            return True

        if registry_type == 1 and \
                service.group_id in list(range(6, 17)) + [20, 25, 26]:
            return False
        elif registry_type == 2 and \
                service.group_id != 20:
            return False
        elif registry_type in list(range(3, 11)) and \
                service.group_id not in list(range(6, 17) + [25, 26]):
            return False

        return True


    def is_event_kind_corresponds_term(kind, term):
        if not kind:
            return True

        if not term:
            return True

        kinds = KIND_TERM_DICT.get(term, [])

        if not kinds or not term:
            return True

        if kind in kinds:
            return True

        return False


    def is_examination_result_matching_comment(examination_result, event_comment):
        if not examination_result:
            return True

        if not event_comment:
            return True

        pattern = re.compile(ADULT_EXAMINATION_COMMENT_PATTERN)
        matching = pattern.match(event_comment)
        result = EXAMINATION_HEALTH_GROUP_EQUALITY[examination_result]

        if examination_result in ['1', '2', '3', '4', '5', '31', '32']:
            if matching.group('health_group') != result and matching.group('second_level') != '0':
                return False

        elif examination_result in ['11', '12', '13', '14', '15']:
            if matching.group('health_group') != result and matching.group('second_level') != '1':
                return False

        return True


    def is_service_code_matching_hitech_method(code, method):
        if code.startswith('A'):
            return True

        if safe_int(code[-3:]) != safe_int(method):
            return False

        return True


    def is_service_children_profile_matching_event_children_profile(
            service_children_profile, event_children_profile):
        if service_children_profile is None and event_children_profile is None:
            return True

        if event_children_profile != service_children_profile:

            return False

        return True


    def is_expired_service(code, event_end_date):
        try:
            event_date = datetime.strptime(event_end_date, '%Y-%m-%d').date()
        except:
            return False

        control_date = datetime.strptime('2015-04-01', '%Y-%m-%d').date()

        if code in OLD_ADULT_EXAMINATION and event_date >= control_date:
            return False

    if code in NEW_ADULT_EXAMINATION \
            and event_date < control_date:
        return False

    return True