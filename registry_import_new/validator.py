#! -*- coding: utf-8 -*-
from valid import _length, _pattern, validate, _required, _in, _isdate
from main.data_cache import GENDERS, PERSON_ID_TYPES, KINDS, ORGANIZATIONS, DEPARTMENTS, DISEASES, METHODS, CODES, \
    TERMS, FORMS, HOSPITALIZATIONS, DIVISIONS, PROFILES, RESULTS, OUTCOMES, SPECIALITIES_NEW, HITECH_KINDS, \
    HITECH_METHODS, EXAMINATION_RESULTS, ADULT_EXAMINATION_COMMENT_PATTERN


class ValidatorStageI:
    """
    Валидатор, осуществляющий начальную проверку полей
    xml реестра
    """
    def __init__(self, registry_type):
        # Правила валидации для пациента
        self.patient_valid = {
            'ID_PAC': [_required, _length(1, 36)],
            'FAM': _length(0, 40),
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
            'VNOV_D': _length(1, 4, pass_on_blank=True)
        }

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
            'DS1': [_required, _in(DISEASES)],
            'IDSP': [_required, _in(METHODS)],
            'USL': _required
        }
        if registry_type in (1, 2):
            self.event_valid['USL_OK'] = [_required, _in(list(TERMS))]
            self.event_valid['FOR_POM'] = [_required, _in(list(FORMS))]
            self.event_valid['NPR_MO'] = _in(list(ORGANIZATIONS), pass_on_blank=True)
            self.event_valid['EXTR'] = _in(list(HOSPITALIZATIONS) + ['0'], pass_on_blank=True)
            self.event_valid['PODR'] = _in(list(DIVISIONS))
            self.event_valid['PROFIL'] = [_required, _in(list(PROFILES))]
            self.event_valid['DET'] = [_required, _in(['0', '1'])]
            self.event_valid['DS0'] = _in(DISEASES)
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
        return validate(self.patient_valid, patient)

    def validate_record(self, record):
        return validate(self.record_valid, record)

    def validate_patient_policy(self, patient_policy):
        return validate(self.policy_valid, patient_policy)

    def validate_event(self, record):
        return validate(self.event_valid, record)

    def validate_service(self, service):
        return validate(self.service_valid, service)


class ValidatorStageII:
    """
    Валидатор, осуществляющий сложные проверки объектов реестра
    """
    def __init__(self):
        pass
