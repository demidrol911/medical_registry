#! -*- coding: utf-8 -*-
from valid import _length, _pattern, validate, _required, _in, _isdate
from main.data_cache import GENDERS, PERSON_ID_TYPES, KINDS, ORGANIZATIONS, DEPARTMENTS, DISEASES, \
    METHODS, CODES, SPECIALS, \
    TERMS, FORMS, HOSPITALIZATIONS, DIVISIONS, PROFILES, RESULTS, OUTCOMES, SPECIALITIES_NEW, HITECH_KINDS, \
    HITECH_METHODS, EXAMINATION_RESULTS, ADULT_EXAMINATION_COMMENT_PATTERN, KIND_TERM_DICT, \
    OLD_ADULT_EXAMINATION, NEW_ADULT_EXAMINATION, EXAMINATION_HEALTH_GROUP_EQUALITY, HOSPITAL_KSGS, DAY_HOSPITAL_KSGS

import re
from datetime import datetime
from main.funcs import safe_int
from main.models import MedicalServiceVolume


def set_error(code, field='', parent='', record_uid='',
              event_uid='', service_uid='', comment=''):
    return {'code': code, 'field': field, 'parent': parent,
            'record_uid': record_uid, 'event_uid': event_uid,
            'service_uid': service_uid, 'comment': comment}


def handle_errors(errors=[], parent='', record_uid='',
                  event_uid='', service_uid=''):
    errors_list = []
    for field, field_errors in errors.iteritems():
        for e in field_errors:
            error_code, error_message = e.split(';')
            errors_list.append(set_error(
                code=error_code, field=field, parent=parent,
                record_uid=record_uid, event_uid=event_uid,
                service_uid=service_uid, comment=error_message)
            )
    return errors_list


class RegistryValidator:
    """
    Валидатор, осуществляющий начальную проверку полей
    xml реестра
    """
    def __init__(self, registry_type):
        self.registry_type = registry_type
        self.current_patient = None
        self.current_record = None
        self.previous_record = None
        self.current_event = None
        self.current_service = None

        self.patient_unique = {'ID_PAC': []}
        self.record_unique = {'N_ZAP': []}
        self.event_unique = {'IDCASE': []}
        self.service_unique = {'IDSERV': []}

        self.divisions_check_list = []
        self.reasons_check_list = []
        self.groups_check_list = []

        # Правила валидации для пациента
        self.patient_valid = {
            'ID_PAC': [_required, _length(1, 36)],
            'FAM': _length(0, 40, pass_on_blank=True),
            'IM': _length(0, 40, pass_on_blank=True),
            'OT': _length(0, 40, pass_on_blank=True),
            'DR': [_required, _pattern('\d{4}-\d{2}-\d{2}')],
            'W': [_required, _in(GENDERS)],
            'FAM_P': _length(1, 40, pass_on_blank=True),
            'IM_P': _length(1, 40, pass_on_blank=True),
            'OT_P': _length(1, 40, pass_on_blank=True),
            'DR_P': _pattern('\d{4}-\d{2}-\d{2}', pass_on_blank=True),
            'W_P': _in(GENDERS, pass_on_blank=True),
            'DOCTYPE': _in(list(PERSON_ID_TYPES) + ['0'], pass_on_blank=True),
            'DOCSER': _length(1, 10, pass_on_blank=True),
            'DOCNUM': _length(1, 20, pass_on_blank=True),
            'VNOV_D': _length(1, 4, pass_on_blank=True),
        }

        # 'SNILS': _length(14, pass_on_blank=True)

        # Правила валидации для полиса
        self.policy_valid = {
            'VPOLIS': [_required, _in(['1', '2', '3'])],
            'SPOLIS': _length(1, 10, pass_on_blank=True),
            'NPOLIS': [_required, _length(1, 20)],
        }
        if registry_type == 1:
            self.policy_valid['NOVOR'] = _pattern('(0)|([12]\d{2}\d{2}\d{2}[0-9][0-9]?)', pass_on_blank=True)

        # Правила валидации для записи
        self.record_valid = {
            'N_ZAP': [_required, _length(1, 8)],
            'PR_NOV': [_required, _length(1)],
            'PACIENT': _required
        }

        # Правила валидации для случая
        self.event_valid = {
            'IDCASE': [_required, _length(1, 11)],
            'VIDPOM': [_required, _in(list(KINDS))],
            'LPU': [_required, _in(list(ORGANIZATIONS))],
            'LPU_1': [_required, _in(list(DEPARTMENTS))],
            'NHISTORY': [_required, _length(1, 50)],
            'DATE_1': [_required, _isdate()],
            'DATE_2': [_required, _isdate()],
            'OS_SLUCH': _in(SPECIALS, pass_on_blank=True),
            'DS0': _in(DISEASES),
            'DS1': [_required, _in(DISEASES)],
            'DS2': _in(DISEASES),
            'DS3': _in(DISEASES),
            'IDSP': [_required, _in(METHODS)],
            'USL': _required
        }
        if registry_type in (1, 2):
            self.event_valid['USL_OK'] = [_required, _in(list(TERMS))]
            self.event_valid['FOR_POM'] = [_required, _in(list(FORMS))]
            self.event_valid['NPR_MO'] = _in(list(ORGANIZATIONS), pass_on_blank=True)
            self.event_valid['EXTR'] = _in(list(HOSPITALIZATIONS) + ['0'], pass_on_blank=True)
            self.event_valid['PODR'] = _in(list(DIVISIONS), pass_on_blank=True)
            self.event_valid['PROFIL'] = [_required, _in(list(PROFILES))]
            self.event_valid['DET'] = [_required, _in(['0', '1'])]
            self.event_valid['DS0'] = _in(DISEASES, pass_on_blank=True)
            self.event_valid['RSLT'] = [_required, _in(RESULTS)]
            self.event_valid['ISHOD'] = [_required, _in(OUTCOMES)]
            self.event_valid['PRVS'] = [_required, _in(SPECIALITIES_NEW)]
            self.event_valid['IDDOKT'] = [_required, _length(1, 25)]

        if registry_type == 2:
            self.event_valid['VID_HMP'] = [_required, _in(HITECH_KINDS)]
            self.event_valid['METOD_HMP'] = [_required, _in(HITECH_METHODS)]
        if registry_type in [3, 4, 6, 7]:
            self.event_valid['P_OTK'] = _in(['0', '1'])
        if registry_type in list(range(3, 11)):
            self.event_valid['RSLT_D'] = [_required, _in(EXAMINATION_RESULTS)]
        if registry_type in (3, 4):
            self.event_valid['COMENTSL'] = [_required, _pattern(ADULT_EXAMINATION_COMMENT_PATTERN)]
        if registry_type == 5:
            self.event_valid['COMENTSL'] = [_required, _pattern(r'^F(0|1)[0-3]{1}(0|1)$')]
        if registry_type in (6, 7, 8, 9, 10):
            self.event_valid['COMENTSL'] = [_required, _pattern(r'^F(0|1)[0-9]{1}$')]

        # Правила валидации для услуги
        self.service_valid = {
            'IDSERV': [_required, _length(1, 36)],
            'LPU': [_required, _in(list(ORGANIZATIONS))],
            'LPU_1': [_required, _in(list(DEPARTMENTS))],
            'DATE_IN': [_required, _isdate()],
            'DATE_OUT': [_required, _isdate()],
            'DS': _in(DISEASES, pass_on_blank=True),
            'CODE_MD': [_required, _length(1, 25)],
            'CODE_USL': [_required, _in(CODES)]
        }
        if registry_type in (1, 2):
            self.service_valid['DS'] = [_required, _in(DISEASES)]
            self.service_valid['PODR'] = _in(list(DIVISIONS), pass_on_blank=True)
            self.service_valid['PROFIL'] = [_required, _in(list(PROFILES))]
            self.service_valid['DET'] = [_required, _in(['0', '1'])]
            self.service_valid['PRVS'] = [_required, _in(SPECIALITIES_NEW)]

    def validate_patient(self, patient):
        self.current_patient = patient
        errors = validate(self.patient_valid, patient)

        # Проверка на уникальность значений
        if patient['ID_PAC'] in self.patient_unique['ID_PAC']:
            errors['ID_PAC'] = [u'904;Значение не является уникальным']
        self.patient_unique['ID_PAC'].append(patient['ID_PAC'])

        return errors

    def validate_record(self, record):
        self.current_record = record
        errors = validate(self.record_valid, record)

        # Проверка на уникальность значений
        if record['N_ZAP'] in self.record_unique['N_ZAP']:
            errors['N_ZAP'] = [u'904;Значение не является уникальным']
        self.record_unique['N_ZAP'].append(record['N_ZAP'])
        return handle_errors(errors, parent='ZAP', record_uid=record['N_ZAP'])

    def validate_patient_policy(self, patient_policy):
        return handle_errors(validate(self.policy_valid, patient_policy),
                             parent='PACIENT', record_uid=self.current_record['N_ZAP'])

    def validate_event(self, event):
        h_errors = []

        if self.current_event:
            if len(set(self.divisions_check_list)) > 1:
                h_errors += handle_errors({'SLUCH': [u'904;В законченном случае обнаружены услуги с разными '
                                                     u'отделениями поликлиники.']},
                                          parent='ZAP', record_uid=self.previous_record['N_ZAP'],
                                          event_uid=self.current_event['IDCASE'])

            if 19 not in self.groups_check_list and len(set(self.reasons_check_list)) > 1:
                h_errors += handle_errors({'SLUCH': [u'904;В законченном случае обнаружены поликлинические услуги '
                                                     u'с разной целью обращения/посещения.']},
                                          parent='ZAP', record_uid=self.previous_record['N_ZAP'],
                                          event_uid=self.current_event['IDCASE'])

            if 19 in self.groups_check_list and len(set(self.groups_check_list)) > 1:
                h_errors += handle_errors({'SLUCH': [u'904;В законченном стоматологическом случае '
                                                     u'обнаружены услуги не относящиеся к стоматологии.']},
                                          parent='ZAP', record_uid=self.previous_record['N_ZAP'],
                                          event_uid=self.current_event['IDCASE'])

        self.previous_record = self.current_record

        self.current_event = event
        self.divisions_check_list = []
        self.reasons_check_list = []
        self.groups_check_list = []
        errors = validate(self.event_valid, event)

        # Проверка на уникальность значений
        if event['IDCASE'] in self.event_unique['IDCASE']:
            errors['IDCASE'] = [u'904;Значение не является уникальным']
        self.event_unique['IDCASE'].append(event['IDCASE'])

        h_errors += handle_errors(errors, parent='SLUCH', record_uid=self.current_record['N_ZAP'],
                                  event_uid=event['IDCASE'])

        # Проверка на соостветствие вида помощи усуловию оказания
        if not CheckFunction.is_event_kind_corresponds_term(event.get('VIDPOM', None), event.get('USL_OK', None)):
            h_errors += handle_errors({'SLUCH': [u'904;Указанный вид помощи не может быть оказанным в текущих условиях']},
                                      parent='ZAP', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        # Проверка на соостветствие результата диспансеризации комментарию
        if self.registry_type in (3, 4) and not CheckFunction.is_examination_result_matching_comment(
                event.get('RSLT_D'), event.get('COMENTSL')):
            h_errors += handle_errors(
                    {'RSLT_D': [u'904;Указанный код результата диспансеризации не совпадает с указанным комментарием']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        # Проверка КСГ
        if event.get('USL_OK', '') in ['1', '2'] and not event.get('KSG_MO', None):
            h_errors += handle_errors(
                    {'KSG_MO': [u'902;Отсутствует обязательное значение.']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        if (event.get('USL_OK', '') == '1' and event.get('KSG_MO', None) not in HOSPITAL_KSGS) \
                or (event.get('USL_OK', '') == '2' and event.get('KSG_MO', None) not in DAY_HOSPITAL_KSGS):
            h_errors += handle_errors(
                    {'KSG_MO': [u'904;Значение не соответствует справочному.']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        # Проверка наличия уточнения в диагнозах
        if event['LPU'] != '280043':
            if not CheckFunction.is_disease_has_precision(event.get('DS0', None)):
                h_errors += handle_errors(
                    {'DS0': [u'904;Диагноз указан без уточняющей подрубрики']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

            if not CheckFunction.is_disease_has_precision(event.get('DS1', None)):
                h_errors += handle_errors(
                    {'DS1': [u'904;Диагноз указан без уточняющей подрубрики']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

            concomitants = event.get('DS2', [])
            if type(concomitants) != list:
                concomitants = [concomitants]
            for disease in concomitants:
                if not CheckFunction.is_disease_has_precision(disease):
                    h_errors += handle_errors(
                        {'DS2': [u'904;Диагноз указан без уточняющей подрубрики']},
                        parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

            complicateds = event.get('DS3', [])
            if type(complicateds) != list:
                complicateds = [complicateds]
            for disease in complicateds:
                if not CheckFunction.is_disease_has_precision(disease):
                    h_errors += handle_errors(
                        {'DS3': [u'904;Диагноз указан без уточняющей подрубрики']},
                        parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        return h_errors

    def validate_service(self, service):
        self.current_service = service
        errors = validate(self.service_valid, service)

        # Проверка на уникальность значений
        if service['IDSERV'] in self.service_unique['IDSERV']:
            errors['IDSERV'] = [u'904;Значение не является уникальным']
        self.service_unique['IDSERV'].append(service['IDSERV'])

        h_errors = handle_errors(errors, parent='USL', record_uid=self.current_record['N_ZAP'],
                                 event_uid=self.current_event['IDCASE'],
                                 service_uid=service['IDSERV'])

        # Проверка на соответсвтие кода услуги типу файла
        if not CheckFunction.is_service_corresponds_registry_type(service['CODE_USL'], self.registry_type):
            h_errors += handle_errors({'CODE_USL': [u'904;Услуга не соответсвует типу файла']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверка на соответствие кода услуги периоду
        if not CheckFunction.is_expired_service(service['CODE_USL'], self.current_event['DATE_2']):
            h_errors += handle_errors({'CODE_USL': [u'904;Код услуги не может быть применён в текущем периоде']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверка на соответствие кода услуги методу ВМП
        if self.registry_type == 2 and not CheckFunction.is_service_code_matching_hitech_method(
                service['CODE_USL'], self.current_event['METOD_HMP']):
            h_errors += handle_errors({'CODE_USL': [u'904;Код услуги не соответствует методу ВМП']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверка наличия уточнения в диагнозах
        if self.current_event['LPU'] != '280043' \
                and not CheckFunction.is_disease_has_precision(service.get('DS', None)):
            h_errors += handle_errors({'DS': [u'904;Диагноз указан без уточняющей подрубрики']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверка на соответствие признака детского профиля услуги признаку детского профиля случая
        if self.registry_type in (1, 2) and \
                not CheckFunction.is_service_children_profile_matching_event_children_profile(
                    service.get('DET'),
                    self.current_event.get('DET')):
            h_errors += handle_errors({'CODE_USL': [u'904;Признак детского профиля случая '
                                                    u'не совпадает с признаком детского профиля услуги']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверка на соответствие даты начала случая по диспансеризации с датой опроса
        if service['CODE_USL'] in ('019002', '19002') and service['DATE_IN'] != self.current_event['DATE_1']:
            h_errors += handle_errors({'DATE_1': [u'904;Дата начала случая диспансеризации не совпадает '
                                                  u'с датой начала услуги анкетирования']},
                                      parent='SLUCH', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid='')

        # Проверка на соответствие даты окончания случая по диспансеризации дате итогового приёма терапевта
        if service['CODE_USL'] in ('019021', '019023', '019022', '019024', '19021', '19023', '19022', '19024',) \
                and service['DATE_OUT'] != self.current_event['DATE_2']:
            h_errors += handle_errors({'DATE_2': [u'904;Дата окончания случая диспансеризации не совпадает с '
                                                  u'датой окончания услуги приёма терапевта']},
                                      parent='SLUCH', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid='')

        # Проверка на соответствие кода услуги условиям оказания
        # Посещение в неотложной форме в приемном отделении стационара
        if self.current_event.get('USL_OK', '') in ('1', '2') \
                and service.get('CODE_USL', '') in ('056066', '56066', '156066', '56066'):
            h_errors += handle_errors({'DATE_2': [u'904;Услуга не может оказываться в текущих условиях']},
                                      parent='SLUCH', record_uid=self.current_record['N_ZAP'],
                                      event_uid=self.current_event['IDCASE'],
                                      service_uid=service['IDSERV'])

        # Проверки на целостность случаев по поликлинике
        code_obj = CODES[service['CODE_USL']]
        if self.current_event.get('USL_OK', '') == '3' and not service['CODE_USL'].startswith('A'):
            if code_obj.division_id:
                self.divisions_check_list.append(code_obj.division_id)
            if code_obj.reason_id:
                self.reasons_check_list.append(code_obj.reason_id)
            self.groups_check_list.append(code_obj.group_id)

        return h_errors


class CheckFunction:
    # Логические функции, использующиеся в сложных проверках

    def __init__(self):
        pass

    @staticmethod
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

    @staticmethod
    def is_examination_result_matching_comment(examination_result, event_comment):
        if not examination_result:
            return True
        if not event_comment:
            return True
        pattern = re.compile(ADULT_EXAMINATION_COMMENT_PATTERN)
        matching = pattern.match(event_comment)
        result = EXAMINATION_HEALTH_GROUP_EQUALITY[examination_result]
        if not matching:
            return True
        if examination_result in ['1', '2', '3', '4', '5', '31', '32']:
            if matching.group('health_group') != result and matching.group('second_level') != '0':
                return False
        elif examination_result in ['11', '12', '13', '14', '15']:
            if matching.group('health_group') != result and matching.group('second_level') != '1':
                return False
        return True

    @staticmethod
    def is_service_corresponds_registry_type(field_value, registry_type):
        service = CODES.get(field_value)
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

    @staticmethod
    def is_expired_service(code, event_end_date):
        try:
            event_date = datetime.strptime(event_end_date, '%Y-%m-%d').date()
        except:
            return False
        control_date = datetime.strptime('2015-06-01', '%Y-%m-%d').date()
        if code in OLD_ADULT_EXAMINATION and event_date >= control_date:
            return False
        if code in NEW_ADULT_EXAMINATION \
                and event_date < control_date:
            return False
        return True

    @staticmethod
    def is_service_code_matching_hitech_method(code, method):
        if code.startswith('A'):
            return True
        if safe_int(code[-3:]) != safe_int(method):
            return False
        return True

    @staticmethod
    def is_service_children_profile_matching_event_children_profile(service_children_profile, event_children_profile):
        if service_children_profile is None and event_children_profile is None:
            return True
        if event_children_profile != service_children_profile:
            return False
        return True

    @staticmethod
    def is_disease_has_precision(field_value):
        if not field_value:
            return True
        disease = DISEASES.get(field_value, None)
        if disease and disease.is_precision:
            return False
        return True


class CheckVolume:
    # Проверка на сверхобъёмы по стационару и дневному стационару

    HOSPITAL_VOLUME_EXCLUSIONS = ('098977', '018103', '98977', '18103', '098975', '098994', '198994', '98994')
    DAY_HOSPITAL_VOLUME_EXCLUSIONS = ('098710', '098711', '098712', '098715',
                                      '098770', '98710', '98711', '98712', '98715',
                                      '98770', '098770', '098770', '198770', '098994', '198994', '98994')
    HOSPITAL_VOLUME_MO_EXCLUSIONS = ('280013', '280076', '280091', '280069')
    DAY_HOSPITAL_MO_EXCLUSIONS = ('280076', '280091', '280069')

    def __init__(self, registry_set):
        self.registry_set = registry_set
        self.hospital_volume_reg = set()
        self.day_hospital_volume_reg = set()
        volume = MedicalServiceVolume.objects.filter(
            organization__code=self.registry_set.mo_code,
            date='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period)
        )
        self.hospital_volume = volume[0].hospital if volume else None
        self.day_hospital_volume = volume[0].day_hospital if volume else None

    def check(self, event, service):
        if event.get('USL_OK', '') == '1' and service['CODE_USL'] not in CheckVolume.HOSPITAL_VOLUME_EXCLUSIONS \
                and not (service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B')):
            self.hospital_volume_reg.add(event['IDCASE'])

        if event.get('USL_OK', '') == '2' and service['CODE_USL'] not in CheckVolume.DAY_HOSPITAL_VOLUME_EXCLUSIONS \
                and not (service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B')):
            self.day_hospital_volume_reg.add(event['IDCASE'])

    def get_error(self):
        overvolume_hospital = self.hospital_volume \
            and (len(self.hospital_volume_reg) > self.hospital_volume) \
            and self.registry_set.mo_code not in CheckVolume.HOSPITAL_VOLUME_MO_EXCLUSIONS
        overvolume_day_hospital = self.day_hospital_volume \
            and (len(self.day_hospital_volume_reg) > self.day_hospital_volume) \
            and self.registry_set.mo_code not in CheckVolume.DAY_HOSPITAL_MO_EXCLUSIONS

        if overvolume_hospital or overvolume_day_hospital:
            error_message = (
                u'Амурский филиал АО «Страховая компания «СОГАЗ-Мед» сообщает, что в соответствии с п.6 статьи 39 \n'
                u'Федерального закона № 326-ФЗ от 29.11.2010г. и п. 5.3.2. Приложения № 33 \n'
                u'к тарифному соглашению в сфере обязательного медицинского страхования Амурской области \n'
                u'на 2016 год, страховая компания принимает реестры счетов и счета на оплату \n'
                u'медицинской помощи в пределах объемов, утвержденных решением комиссии по \n'
                u'разработке территориальной программы обязательного медицинского страхования Амурской области.\n'
                u'\n'
                u'В текущем реестре выполнено:\n'
            )
            if overvolume_hospital:
                error_message += u'Круглосуточный стационар - {0}, запланировано решением тарифной комисси - {1}\n'.\
                    format(len(self.hospital_volume_reg), self.hospital_volume)
            if overvolume_day_hospital:
                error_message += u'Дневной стационар - {0}, запланировано решением тарифной комисси - {1}\n'.\
                    format(len(self.day_hospital_volume_reg), self.day_hospital_volume)
            error_message += u'Вопросы распределения объёмов находятся в компетенции Тарифной Комиссии\n'
            return True, error_message
        else:
            return False, ''
