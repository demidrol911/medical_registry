#! -*- coding: utf-8 -*-
from hospital_accounting.models import MedicalOrganization
from valid import _length, _pattern, validate, _required, _in, _isdate
from main.data_cache import GENDERS, PERSON_ID_TYPES, KINDS, ORGANIZATIONS, \
    DEPARTMENTS, DISEASES, METHODS, CODES, SPECIALS, TERMS, FORMS, \
    HOSPITALIZATIONS, DIVISIONS, PROFILES, RESULTS, OUTCOMES, SPECIALITIES_NEW, \
    HITECH_KINDS, HITECH_METHODS, EXAMINATION_RESULTS, \
    ADULT_EXAMINATION_COMMENT_PATTERN, KIND_TERM_DICT, \
    OLD_ADULT_EXAMINATION, NEW_ADULT_EXAMINATION, \
    EXAMINATION_HEALTH_GROUP_EQUALITY, HOSPITAL_KSGS, DAY_HOSPITAL_KSGS, DISABILITY_GROUPS, INCOMING_SIGNS, \
    INCOMPLETE_VOLUME_REASONS, EXAMINATION_KINDS, MEDICINES, BED_PROFILES, OPERATIONS

import re
from datetime import datetime
from main.funcs import safe_int
from main.models import MedicalServiceVolume, MedicalServiceVolumeHitech


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

        self.header_valid = {
            'SD_Z': _required,
        }

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

        # Правила валидации для полиса
        self.policy_valid = {
            'VPOLIS': [_required, _in(['1', '2', '3'])],
            'SPOLIS': _length(1, 10, pass_on_blank=True),
            'NPOLIS': [_required, _length(1, 20)],
            'INV': _in(DISABILITY_GROUPS),
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
            self.event_valid['TAL_D'] = [_required, _isdate()]
            self.event_valid['TAL_P'] = [_required, _isdate()]

        if registry_type in [10, 9, 8, 7, 6, 5, 4, 3]:
            self.event_valid['VBR'] = [_required, _in(['0', '1'])]
            self.event_valid['P_OTK'] = [_required, _in(['0', '1'])]
            self.event_valid['DS1_PR'] = _in(['0', '1'])
            self.event_valid['PR_D_N'] = _in(['0', '1'])
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
            'CODE_USL': [_required, _in(CODES)],
            'NPL': _in(INCOMPLETE_VOLUME_REASONS, pass_on_blank=True)
        }
        if registry_type in (1, 2):
            self.service_valid['DS'] = [_required, _in(DISEASES)]
            self.service_valid['PODR'] = _in(list(DIVISIONS), pass_on_blank=True)
            self.service_valid['PROFIL'] = [_required, _in(list(PROFILES))]
            self.service_valid['DET'] = [_required, _in(['0', '1'])]
            self.service_valid['PRVS'] = [_required, _in(SPECIALITIES_NEW)]
        if registry_type in [10, 9, 8, 7, 6, 5, 4, 3]:
            self.service_valid['P_OTK'] = [_required, _in(['0', '1'])]

    def validate_header(self, header):
        return validate(self.header_valid, header)

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

        if event.get('USL_OK', '') in ['1', '2'] and self.registry_type == 1 \
                and event.get('P_PER', '0') not in INCOMING_SIGNS:
            errors['P_PER'] = [u'904;Значение не соответствует справочному.']
        if event.get('USL_OK', '') in ['1', '2'] and event.get('P_PER', '0') == '0' and self.registry_type == 1:
            errors['P_PER'] = [u'902;Отсутствует обязательное значение.']

        h_errors += handle_errors(errors, parent='SLUCH', record_uid=self.current_record['N_ZAP'],
                                  event_uid=event['IDCASE'])

        # Проверка на соостветствие вида помощи усуловию оказания
        if not CheckFunction.is_event_kind_corresponds_term(event.get('VIDPOM', None), event.get('USL_OK', None)):
            h_errors += handle_errors(
                {'SLUCH': [u'904;Указанный вид помощи не может быть оказанным в текущих условиях']},
                parent='ZAP', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        # Проверка на соостветствие результата диспансеризации комментарию
        if self.registry_type in (3, 4) and not CheckFunction.is_examination_result_matching_comment(
                event.get('RSLT_D'), event.get('COMENTSL')):
            h_errors += handle_errors(
                {'RSLT_D': [u'904;Указанный код результата диспансеризации не совпадает с указанным комментарием']},
                parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        if self.registry_type == 1:
            # Проверка КСГ
            if event.get('USL_OK', '') in ('1', '2') and not event.get('KSG_MO', None):
                h_errors += handle_errors(
                    {'KSG_MO': [u'902;Отсутствует обязательное значение.']},
                    parent='SLUCH', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

            if event.get('KSG_MO', None) and \
                    ((event.get('USL_OK', '') == '1' and event.get('KSG_MO', None) not in HOSPITAL_KSGS)
                     or (event.get('USL_OK', '') == '2' and event.get('KSG_MO', None) not in DAY_HOSPITAL_KSGS)):
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

        # Проверка лекарственных препаратов
        medicine_valid = {
            'CODE_LP': [_required, _in(MEDICINES)],
            'NAME_LP': _required
        }

        medicines = event.get('LEKPREP', [])
        if type(medicines) != list:
            medicines = [medicines]

        for medicine in medicines:
            h_errors += handle_errors(validate(medicine_valid, medicine), parent='LEKPREP',
                                      record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

        if self.registry_type in (10, 9, 8, 7, 6, 5, 4, 3):
            # Проверка сопутствующих заболеваний
            exam_concomitants_valid = {
                'DS2': [_required, _in(DISEASES)],
                'DS2_PR': _in(['0', '1'])
            }
            exam_concomitant_diseases = event.get('DS2_N', [])
            if type(exam_concomitant_diseases) != list:
                exam_concomitant_diseases = [exam_concomitant_diseases]
            for disease in exam_concomitant_diseases:
                h_errors += handle_errors(validate(exam_concomitants_valid, disease), parent='DS2_N',
                                          record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])
                if not CheckFunction.is_disease_has_precision(disease.get('DS2', None)):
                    h_errors += handle_errors(
                        {'DS2_N': [u'904;Диагноз указан без уточняющей подрубрики']},
                        parent='DS2_N', record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])

            # Проверка назначения после присвоения группы здоровья, кроме I и II
            health_group = HealthGroup.get_health_group(self.registry_type, event.get('COMENTSL', '') or '')
            is_required_appointment = False
            if health_group not in ('0', '1', '2') or event.get('RSLT_D', '0') in ('3', '4', '5', '31', '32'):
                is_required_appointment = True
            if event.get('RSLT_D', '0') in ('6', '11', '12', '13', '14', '15'):
                is_required_appointment = False

            if is_required_appointment:
                appointments = event.get('NAZR', [])
                if not appointments:
                    h_errors += handle_errors({'NAZR': [u'902;Отсутствует обязательное значение для '
                                                        u'группы здоровья %s, рассчитанной из комментария случая (%s) '
                                                        u'и результата диспансеризации %s.'
                                                        % (health_group, event.get('COMENTSL', '') or '',
                                                           event.get('RSLT_D', '0'))]},
                                              parent='SLUCH',
                                              record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])
                if type(appointments) != list:
                    appointments = [appointments]
                appointment_valid = {
                    'NAZ_SP': {'check': None, 'valid': SPECIALITIES_NEW},
                    'NAZ_V': {'check': None, 'valid': EXAMINATION_KINDS},
                    'NAZ_PMP': {'check': None, 'valid': PROFILES},
                    'NAZ_PK': {'check': None, 'valid': BED_PROFILES},
                }
                for direction_type in appointment_valid:
                    check_values = event.get(direction_type, [])
                    if type(check_values) != list:
                        check_values = [check_values]
                    appointment_valid[direction_type]['check'] = check_values

                direction_type = None
                for appointment in appointments:
                    if appointment in ['1', '2']:
                        direction_type = 'NAZ_SP'
                    elif appointment == '3':
                        direction_type = 'NAZ_V'
                    elif appointment in ['4', '5']:
                        direction_type = 'NAZ_PMP'
                    elif appointment == '6':
                        direction_type = 'NAZ_PK'
                    else:
                        h_errors += handle_errors(
                            {'NAZR': [u'904;Значение не соответствует справочному для '
                                      u'группы здоровья %s, рассчитанной из комментария случая (%s) '
                                      u'и результата диспансеризации %s.'
                                      % (health_group, event.get('COMENTSL', '') or '',
                                         event.get('RSLT_D', '0'))]}, parent='SLUCH',
                            record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])
                    if direction_type:
                        valid_values = appointment_valid[direction_type]['valid']
                        check_values = appointment_valid[direction_type]['check']
                        if not check_values:
                            h_errors += handle_errors(
                                {direction_type: [u'902;Отсутствует обязательное значение.']}, parent='SLUCH',
                                record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])
                        for value in check_values:
                            if value not in valid_values:
                                h_errors += handle_errors(
                                    {direction_type: [u'904;Значение не соответствует справочному.']}, parent='SLUCH',
                                    record_uid=self.current_record['N_ZAP'], event_uid=event['IDCASE'])
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

        if not CheckFunction.is_active_operation(service['CODE_USL']):
            h_errors += handle_errors({'CODE_USL': [u'904;Код услуги отсутствует в номенклатуре']},
                                      parent='USL', record_uid=self.current_record['N_ZAP'],
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
        code_obj = CODES.get(service['CODE_USL'], None)
        if code_obj and self.current_event.get('USL_OK', '') == '3' and not service['CODE_USL'].startswith('A'):
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
        service = CODES.get(field_value, None)
        if not service:
            return True
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
        if disease and not disease.is_precision:
            return False
        return True

    @staticmethod
    def is_active_operation(code):
        if code.startswith('A') or code.startswith('B'):
            return code in OPERATIONS
        else:
            return True


class HealthGroup:
    # Класс для получения значения группы здоровья из комментария
    ADULT_EXAMINATION_COMMENT_REGEXP = re.compile(ADULT_EXAMINATION_COMMENT_PATTERN, re.IGNORECASE)
    ADULT_PREVENTIVE_COMMENT_REGEXP = re.compile(r'^F(?P<student>(0|1))(?P<health_group>[0-3]{1})(?P<unknown>(0|1))$', re.IGNORECASE)
    CHILDREN_EXAMINATION_COMMENT_REGEXP = re.compile(r'^F(?P<student>(0|1))(?P<health_group>[0-9]{1})$', re.IGNORECASE)

    def __init__(self):
        pass

    @staticmethod
    def get_health_group(registry_type, comment):
        if registry_type in (3, 4):
            match = HealthGroup.ADULT_EXAMINATION_COMMENT_REGEXP.match(comment)
        elif registry_type == 5:
            match = HealthGroup.ADULT_PREVENTIVE_COMMENT_REGEXP.match(comment)
        elif registry_type in (6, 7, 8, 9, 10):
            match = HealthGroup.CHILDREN_EXAMINATION_COMMENT_REGEXP.match(comment)
        if match:
            return match.group('health_group')
        else:
            return '0'


class CheckVolume:
    """
    Проверка на сверхобъёмы по стационару, дневному стационару
    поликлинике профилактика, поликлинике неотложка,
    стоматологии профилактика, стоматологии неотложка,
    диспансеризациям и профосмотрам
    """

    CLINIC_VOLUME_MO_EXCLUSIONS = (
        '280029', '280001', '280078', '280075', '280084', '280064', '280003',
        '280027', '280017', '280067', '280022', '280088', '280024', '280019',
        '280085', '280038', '280066', '280052', '280076', '280083', '280069',
        '280068', '280065', '280037', '280009', '280007', '280039', '280020',
        '280053', '280071', '280025', '280059', '280080', '280041', '280015',
        '280040', '280061', '280074', '280012', '280036', '280002', '280125'
    )

    def __init__(self, registry_set):
        self.registry_set = registry_set
        self.event_reg = set()
        self.count_invoiced_events = 0
        self.patient_data = None
        self.volume_checker_settings = {}
        self.volume_reg = {}

        volume_obj = MedicalServiceVolume.objects.filter(
            organization__code=self.registry_set.mo_code,
            date='{0}-{1}-01'.format(self.registry_set.year,
                                     self.registry_set.period)
        )
        if volume_obj:
            volume_limit = volume_obj[0]

            self.volume_checker_settings = {
                'hospital': {
                    'volume_limit': volume_limit.hospital,
                    'text': u'Круглосуточный стационар',
                    'except_code': (
                        '098977', '018103', '98977', '18103', '098975',
                        '098994', '198994', '98994', '98975'
                    ),
                    'except_mo': ('280013',)
                },
                'day_hospital': {
                    'volume_limit': volume_limit.day_hospital,
                    'text': u'Дневной стационар',
                    'except_code': (
                        '098710', '098711', '098712', '098715',
                        '098770', '98710', '98711', '98712',
                        '98715', '98770', '098770', '098770',
                        '198770', '098994', '198994', '98994'
                    ),
                    'except_mo': ()
                },
                'clinic_disease': {
                    'volume_limit': volume_limit.clinic_disease,
                    'text': u'Амбулаторно-поликлиническая помощь обращения',
                    'except_mo': CheckVolume.CLINIC_VOLUME_MO_EXCLUSIONS
                },
                'clinic_prevention': {
                    'volume_limit': volume_limit.clinic_prevention,
                    'text': u'Амбулаторно-поликлиническая помощь профилактическая',
                    'except_mo': CheckVolume.CLINIC_VOLUME_MO_EXCLUSIONS + ('280026', )
                },
                'clinic_emergency': {
                    'volume_limit': volume_limit.clinic_emergency,
                    'text': u'Амбулаторно-поликлиническая помощь неотложная',
                    'except_mo': ('280013', '280043', '280076')
                },
                'stomatology_prevention': {
                    'volume_limit': volume_limit.stomatology_prevention,
                    'text': u'Стоматология профилактика', 'units': u'ует',
                    'except_mo':  CheckVolume.CLINIC_VOLUME_MO_EXCLUSIONS
                },
                'stomatology_emergency': {
                    'volume_limit': volume_limit.stomatology_emergency,
                    'text': u'Стоматология неотложка', 'units': u'ует'
                },
                'exam_children_difficult_situation': {
                    'volume_limit': volume_limit.exam_children_difficult_situation,
                    'text': u'Диспанцеризация детей сирот в стац. учреждениях',
                    'units': u'пациентов'
                },
                'exam_children_without_care': {
                    'volume_limit': volume_limit.exam_children_without_care,
                    'text': u'Диспанцеризация детей сирот, прин. под опеку',
                    'units': u'пациентов'
                },
                'prelim_medical_exam': {
                    'volume_limit': volume_limit.prelim_medical_exam,
                    'text': u'Предварительные медосмотры несовершеннолетних',
                    'units': u'пациентов'
                },
                'periodic_medical_exam': {
                    'volume_limit': volume_limit.periodic_medical_exam,
                    'text': u'Периодические медосмотры несовершеннолетних',
                    'units': u'пациентов'
                },
                'prevent_medical_exam': {
                    'volume_limit': volume_limit.prevent_medical_exam,
                    'text': u'Профосмотры несовершеннолетних',
                    'units': u'пациентов'
                },
                'exam_adult': {
                    'volume_limit': volume_limit.exam_adult,
                    'text': u'Диспанцеризация взрослого населения',
                    'units': u'пациентов'
                },
                'preventive_inspection_adult': {
                    'volume_limit': volume_limit.preventive_inspection_adult,
                    'text': u'Профосмотр взрослых',
                    'units': u'пациентов'
                },
            }

            for service_type in self.volume_checker_settings:
                if self.volume_checker_settings[service_type]['volume_limit'] < 0:
                    self.volume_checker_settings[service_type]['volume_limit'] = 0

            for service_type in self.volume_checker_settings:
                if self.volume_checker_settings[service_type].get('units', '') == u'ует':
                    self.volume_reg[service_type] = 0
                else:
                    self.volume_reg[service_type] = set()

        self.vollume_hitech_limit = {
            volume['vmp_group']: volume['value'] for volume in MedicalServiceVolumeHitech.objects.filter(
                organization__code=self.registry_set.mo_code,
                date='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period)).values('vmp_group', 'value')
        }
        self.volume_hitech_reg = {}
        self.exam_patients_dict = self.__get_exam_patients_in_previous_periods()

    def __get_exam_patients_in_previous_periods(self):
        query = '''
            SELECT
            DISTINCT
                mo.id_pk, ms.group_fk AS group_id,
                regexp_replace(regexp_replace(
                    CASE WHEN p.last_name = 'НЕТ' THEN '' ELSE p.last_name END
                    || CASE WHEN p.first_name = 'НЕТ' THEN '' ELSE p.first_name END
                    || CASE WHEN p.middle_name = 'НЕТ' THEN '' ELSE p.middle_name END
                    || p.birthdate, 'Ё', 'Е' , 'g'),  ' ', '' , 'g') AS patient_data
            FROM medical_register mr
            JOIN medical_register_record mrr
              ON mr.id_pk=mrr.register_fk
            JOIN provided_event pe
              ON mrr.id_pk=pe.record_fk
            JOIN provided_service ps
              ON ps.event_fk=pe.id_pk
            JOIN medical_service ms
              ON ms.id_pk = ps.code_fk
            JOIN patient p
              ON p.id_pk = mrr.patient_fk
            JOIN medical_organization mo
              ON mo.id_pk = ps.organization_fk
            WHERE mr.is_active
                AND format('%%s-%%s-01', mr.year, mr.period)::DATE >= format('%%s-%%s-01', %(year)s, '01')::DATE
                AND format('%%s-%%s-01', mr.year, mr.period)::DATE < format('%%s-%%s-01', %(year)s, %(period)s)::DATE
            AND mr.organization_code = %(organization_code)s
            AND ms.group_fk in (12, 13, 15, 16, 11, 7, 9)
            AND ps.payment_type_fk = 2
            ORDER BY group_id, patient_data
        '''

        data = MedicalOrganization.objects.raw(query, dict(year=self.registry_set.year,
                                                           period=self.registry_set.period,
                                                           organization_code=self.registry_set.mo_code))
        exam_patients_dict = {12: [], 13: [], 15: [], 16: [], 11: [], 7: [], 9: []}
        for item in data:
            exam_patients_dict[item.group_id].append(item.patient_data)
        return exam_patients_dict

    def set_count_invoiced_events(self, count_events):
        self.count_invoiced_events = int(count_events)
        self.event_reg.clear()

    def set_patient(self, patient_obj):
        self.patient_data = ''
        self.patient_data += ('' if patient_obj.last_name == 'НЕТ' else patient_obj.last_name)
        self.patient_data += ('' if patient_obj.first_name == 'НЕТ' else patient_obj.first_name)
        self.patient_data += ('' if patient_obj.middle_name == 'НЕТ' else patient_obj.middle_name)
        self.patient_data += patient_obj.birthdate.strftime('%Y-%m-%d')
        self.patient_data = self.patient_data.upper()
        self.patient_data = self.patient_data.replace(u'Ё', u'Е')
        self.patient_data = self.patient_data.replace(' ', '')

    def check(self, event, service, patient_policy):
        self.event_reg.add(event['IDCASE'])
        code_obj = CODES.get(service['CODE_USL'], None)

        if code_obj:
            if event.get('USL_OK', '') == '1' \
                    and service['CODE_USL'] not in self.volume_checker_settings['hospital']['except_code'] \
                    and not (service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B')):
                self.volume_reg['hospital'].add(event['IDCASE'])

            if event.get('USL_OK', '') == '2' \
                and service['CODE_USL'] not in self.volume_checker_settings['day_hospital']['except_code'] \
                    and not (service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B')):
                self.volume_reg['day_hospital'].add(event['IDCASE'])

            # Новые проверки
            if event.get('USL_OK', '') == '3' \
                    and not (service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B')):
                count_services = 0
                stomatology_subgroup = 0
                for s in event.get('USL', []):
                    cur_code_obj = CODES[s['CODE_USL']]
                    if cur_code_obj.group_id not in (27, 3, 5, 42):
                        count_services += 1
                    if cur_code_obj.group_id == 19 and cur_code_obj.subgroup_id in (13, 14, 17):
                        stomatology_subgroup = cur_code_obj.subgroup_id

                # Поликлиника заболевание
                if code_obj.reason_id == 1 and (not code_obj.group_id or code_obj.group_id in [24, ]) and count_services > 1:
                    self.volume_reg['clinic_disease'].add(event['IDCASE'])

                # Поликлиника профилактика
                if (code_obj.reason_id in [2, 3, 8] and (not code_obj.group_id or code_obj.group_id in [24, ])) \
                    or (code_obj.reason_id == 1 and (not code_obj.group_id or code_obj.group_id in [24, ]) and
                        count_services == 1):
                    self.volume_reg['clinic_prevention'].add(event['IDCASE'])

                # Поликлиника неотложка
                if code_obj.reason_id == 5 and (not code_obj.group_id or code_obj.group_id in [24, 44, 31]):
                    self.volume_reg['clinic_emergency'].add(event['IDCASE'])

                if code_obj.group_id == 19:
                    uet = float(service['KOL_USL'] or 0) * (code_obj.uet or 0)
                    # Стоматология профилактика
                    if stomatology_subgroup == 13:
                        self.volume_reg['stomatology_prevention'] += uet

                    # Стоматология неотложка
                    if stomatology_subgroup in (17, ):
                        self.volume_reg['stomatology_emergency'] += uet

            if event.get('USL_OK', '') == '' and \
                    not self.patient_data in self.exam_patients_dict.get(code_obj.group_id, []):
                if code_obj.group_id == 12:
                    self.volume_reg['exam_children_difficult_situation'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 13:
                    self.volume_reg['exam_children_without_care'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 15:
                    self.volume_reg['prelim_medical_exam'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 16:
                    self.volume_reg['periodic_medical_exam'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 11:
                    self.volume_reg['prevent_medical_exam'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 7:
                    self.volume_reg['exam_adult'].add(patient_policy['ID_PAC'])
                elif code_obj.group_id == 9:
                    self.volume_reg['preventive_inspection_adult'].add(patient_policy['ID_PAC'])

    def check_count_events(self):
        return len(self.event_reg) != self.count_invoiced_events

    def get_error(self):
        error_message = ''
        for service_type, settings in self.volume_checker_settings.iteritems():
            if type(self.volume_reg[service_type]) == set:
                volume = len(self.volume_reg[service_type])
            else:
                volume = self.volume_reg[service_type]
            if volume > settings['volume_limit'] \
                    and self.registry_set.mo_code not in settings.get('except_mo', ()):
                units = ''
                if 'units' in settings:
                    units = ' '+settings['units']
                error_message += u'{text} - {volume_reg}{units}, ' \
                                 u'запланировано решением тарифной комиссии - {volume_limit}{units}\n'.\
                    format(text=settings['text'], volume_reg=volume, units=units,
                           volume_limit=settings['volume_limit'])

        for vmp_group, value in self.volume_hitech_reg.iteritems():
            volume_limit = self.vollume_hitech_limit.get(vmp_group, 0)
            if len(value) > volume_limit:
                error_message += u'{text} - {volume_reg}, ' \
                    u'запланировано решением тарифной комиссии - {volume_limit}\n'.format(
                    text=u'ВМП '+MedicalServiceVolumeHitech.VMP_GROUPS[vmp_group]+u' группа '+str(vmp_group),
                    volume_reg=len(value), volume_limit=volume_limit)
        if error_message:
            return True, (
                u'Амурский филиал АО «Страховая компания «СОГАЗ-Мед» сообщает,что в соответствии с п.6 статьи 39 \n'
                u'Федерального закона № 326-ФЗ от 29.11.2010г. и п. 5.3.2. Приложения № 33 \n'
                u'к тарифному соглашению в сфере обязательного медицинского страхования \n'
                u'Амурской области на 2016 год, страховая компания принимает реестры счетов и счета\n'
                u'на оплату  медицинской помощи в пределах объемов, утвержденных решением Комиссии по\n'
                u'разработке территориальной программы обязательного медицинского страхования Амурской области.\n'
                u'Дополнительно сообщаем, что принятие решения об оплате услуг, выполненных сверх установленного\n'
                u'планового объема медицинской помощи, а так же об увеличении установленных плановых объемов \n'
                u'медицинской помощи входит в компетенцию Комиссии по разработке территориальной программы \n'
                u'обязательного медицинского страхования Амурской области (далее – Комиссия). \n'
                u'Согласно п.6 Дополнительного соглашения № 03 от 25.04.2016 года к Договору на оказание и оплату \n'
                u'медицинской помощи по обязательному медицинскому страхованию медицинская организация обязана \n'
                u'при необходимости в течении 5 рабочих дней месяца, следующего за отчетным, направлять в Комиссию \n'
                u'заявку на перераспределение объемов предоставления медицинской помощи.\n'
                u'Объемы медицинской помощи, выполненные в стационарных условиях и условиях дневных стационаров \n'
                u'сверх установленных плановых объемов рассматриваются  Комиссией, '
                u'по обращению медицинской организации \n'
                u'с учетом обоснования причин превышения, анализа в динамике заболеваемости, удельного веса плановых \n'
                u'госпитализаций и наличия листов ожидания в соответствии с условиями оказания вышеупомянутых видов \n'
                u'медицинской помощи Территориальной программы обязательного медицинского страхования – до 30 дней.\n'
                u'Для решения вопроса об оплате услуг, выполненных сверх установленного планового объема медицинской \n'
                u'помощи вам необходимо направить списки пациентов пролеченных сверх установленного планового объема \n'
                u'медицинской помощи, с обоснованием причин превышения, в Комиссию, а так же списки пациентов, \n'
                u'пролеченных сверх плана, в электронном виде, '
                u'формате Excel по защищенному каналу связи VipNet в СМО.\n'
                u'В электронном списке пациентов необходимо заполнить графы: ФИО, дата рождения пациента; \n'
                u'номер страхового полиса; срок госпитализации (дата начала госпитализации, дата выписки); \n'
                u'диагноз; код отделения, в котором проходило лечение; сумма предъявленного тарифа;'
                u' показания для госпитализации. \n\n'
                u'В текущем реестре выполнено:\n'
                u'%s') % error_message

        else:
            return False, ''
