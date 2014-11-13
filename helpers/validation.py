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

from lxml import etree
import re
from datetime import datetime
import re


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

KIND_TERM_DICT = {1: [2, 3, 21, 22, 31, 32, 4],
                  2: [1, 2, 3, 21, 22, 31, 32, 4],
                  3: [1, 11, 12, 13, 4]}


class ValidPatient(object):
    def __init__(self, item, record_id=None):
        self.id_pk = item['id_pk']
        self.id = item['id']
        self.last_name = item['last_name']
        self.first_name = item['first_name']
        self.middle_name = item['middle_name']
        self.birthdate = item['birthdate']
        self.snils = item['snils']
        self.birthplace = item['birthplace']
        self.gender = safe_int(item['gender'])
        self.person_id_type = safe_int(item['person_id_type'])
        self.person_id_series = None
        if item['person_id_series']:
            self.person_id_series = item['person_id_series'][:10]
        self.person_id_number = item['person_id_number']
        self.residence = item['residence']
        self.registration = item['registration']
        self.comment = item['comment']
        self.agent_last_name = item['agent_last_name']
        self.agent_first_name = item['agent_first_name']
        self.agent_middle_name = item['agent_middle_name']
        self.agent_birthdate = item['agent_birthdate']
        self.agent_gender = safe_int(item['agent_gender'])
        self.newborn_code = item['newborn_code']
        self.insurance_policy_type = safe_int(item['insurance_policy_type'])
        self.insurance_policy_series = (item['insurance_policy_series'] or '')[:10]
        self.insurance_policy_number = item['insurance_policy_number']
        self.weight=item['weight']
        #self.person_instance = None
        #self.insurance_instance = None
        self.record_id = record_id

    def validate(self):
        errors = []
        record_id = self.record_id
        if not self.id:
            errors.append((2, '904', 'PERS', 'ID_PAC', record_id, None, None,
                           u'Отсутствует идентификатор пациента'))

        """
        if newborn_code == '0':
            if not service['last_name:
                errors.append((False, '904', 'PERS', 'FAM', record_id,
                            u'Отсутствует фамилия'))
            if not service['first_name:
                errors.append((False, '904', 'PERS', 'IM', record_id, u'Отсутствует имя'))
            if not self.middle_name:
                errors.append((False, '904', 'PERS', 'OT', record_id,
                            u'Отсутствует отчество'))
        elif self.newborn_code:
            if not self.agent_last_name:
                errors.append((False, '904', 'PERS', 'FAM_P', record_id,
                            u'Отсутствует фамилия'))
            if not self.agent_first_name:
                errors.append((False, '904', 'PERS', 'IM_P', record_id,
                            u'Отсутствует имя представителя'))
            if not self.agent_middle_name:
                errors.append((False, '904', 'PERS', 'OT_P', record_id,
                            u'Отсутствует отчество представителя'))
            if not self.agent_birthdate:
                errors.append((False, '904', 'PERS', 'DR_P', record_id,
                           u'Отсутствует дата рождения представителя'))
        else:
            if not self.agent_birthdate:
                errors.append((False, '904', 'PERS', 'DR_P', record_id,
                            u'Отсутствует дата рождения представителя'))
        """

        if self.newborn_code and self.newborn_code != '0' \
            and not (self.agent_last_name or self.agent_first_name or
                         self.agent_middle_name or self.agent_birthdate or
                         self.agent_gender):
            errors.append((True, '902', 'PACIENT', '', None, None,
                           u'Отсутствуют данные представителя %s' % self.newborn_code))

        if self.newborn_code and len(self.newborn_code) > 1 and self.newborn_code[-1] == '0':
            errors.append((True, '904', 'PACIENT', 'NOVOR', record_id, None, None,
                           u'Недопустимый код новорожденного'))

        if self.gender and int(self.gender) not in GENDERS:
            errors.append((True, '902', 'PACIENT', 'W', record_id, None, None,
                           u'Пол не соответствует допустимому'))

        elif not self.gender:
            errors.append((True, '904', 'PACIENT', 'W', record_id, None, None,
                           u'Отсутствует пол'))

        if not self.birthdate:
            errors.append((False, '904', 'PERS', 'DR', record_id, None, None,
                           u'Отсутствует дата рождения'))

        if not self.insurance_policy_type:
            errors.append((True, '904', 'PACIENT', 'VPOLIS', record_id, None, None,
                           u'Отсутствует тип полиса'))

        if self.insurance_policy_type == '1':
            if not self.insurance_policy_series:
                errors.append((True, '904', 'PACIENT', 'SPOLIS', record_id, None, None,
                               u'Отсутствует серия полиса'))

        if not self.insurance_policy_number:
            errors.append((True, '904', 'PACIENT', 'NPOLIS', record_id, None, None,
                           u'Отсутствует номер полиса'))

        if self.insurance_policy_series and \
                        len(self.insurance_policy_series) > 10:
            errors.append((True, '902', 'PACIENT', 'SPOLIS', record_id, None, None,
                           u'Длина серии полиса превышает допустимую'))
            self.insurance_policy_series = \
                self.insurance_policy_series[0:10]

        #if self.person_id_type and len(self.person_id_type) > 10:
        #    errors.append((True, '902', 'PACIENT', 'DOCTYPE', record_id,
        #                   u'Длина серии документа УДЛ превышает допустимую'))
        #    self.insurance_policy_series = \
        #        self.insurance_policy_series[0:10]

        return errors

    def get_object(self):
        patient = Patient(
            id_pk=self.id_pk,
            id=self.id,
            last_name=self.last_name,
            first_name=self.first_name,
            middle_name=self.middle_name,
            birthdate=self.birthdate,
            snils=self.snils,
            birthplace=self.birthplace,
            gender=GENDERS.get(self.gender, None),
            person_id_type=PERSON_ID_TYPES.get(self.person_id_type, None),
            person_id_series=self.person_id_series,
            person_id_number=self.person_id_number,
            okato_residence=self.residence,
            okato_registration=self.registration,
            comment=self.comment,
            weight=self.weight,
            agent_last_name=self.agent_last_name,
            agent_first_name=self.agent_first_name,
            agent_middle_name=self.agent_middle_name,
            agent_birthdate=self.agent_birthdate,
            agent_gender=GENDERS.get(self.agent_gender, None),
            newborn_code=self.newborn_code,
            insurance_policy_type=POLICY_TYPES.get(
                self.insurance_policy_type, None),
            insurance_policy_series=self.insurance_policy_series,
            insurance_policy_number=self.insurance_policy_number)

        return patient


class ValidRecord(object):
    def __init__(self, item, record_pk, register, patient_pk):
        self.id = item['N_ZAP']
        self.is_corrected = True if item['PR_NOV'] == '1' else False
        self.id_pk = record_pk
        self.register = register
        self.patient_pk = patient_pk

    def validate(self):
        errors = []
        if not self.id:
            errors.append((False, '904', 'ZAP', 'N_ZAP', self.id,
                           u'Отсутствует номер записи'))
        return errors

    def get_object(self):
        record = MedicalRegisterRecord(
            id=self.id,
            id_pk=self.id_pk,
            is_corrected=self.is_corrected,
            register_id=self.register.pk,
            patient_id=self.patient_pk)

        return record


class ValidEvent(object):
    def __init__(self, item, pk, record):
        self.id = item['IDCASE']
        self.id_pk = pk
        self.term = safe_int(item['USL_OK'])
        self.kind = safe_int(item['VIDPOM'])
        self.hospitalization = item['EXTR']
        self.form = safe_int(item['FOR_POM'])
        self.refer_organization = item['NPR_MO']
        self.organization = item['LPU']
        self.department = item['LPU_1']
        self.profile = safe_int(item['PROFIL'])
        self.is_children_profile = True if item['DET'] == '1' else False
        self.anamnesis_number = item['NHISTORY']
        self.examination_rejection = item['P_OTK']
        self.start_date = item['DATE_1']
        self.end_date = item['DATE_2']
        self.initial_disease = item['DS0']
        self.basic_disease = item['DS1']
        self.concomitant_disease = item['DS2']
        self.payment_method = safe_int(item['IDSP'])
        self.payment_units_number = item['ED_COL']
        self.comment = item['COMENTSL']
        self.division = item['PODR']
        self.treatment_result = safe_int(item['RSLT'])
        self.treatment_outcome = safe_int(item['ISHOD'])
        self.worker_speciality = item['PRVS']
        self.speciality_dict_version = item['VERS_SPEC']
        self.worker_code = item['IDDOKT']
        self.special = item['OS_SLUCH']
        self.record_id = record.id_pk
        self.record_number = record.id
        self.hitech_kind = item['VID_HMP']
        self.hitech_method = item['METOD_HMP']
        self.examination_result = safe_int(item['RSLT_D'])
        self.record = record

    def validate(self):
        record_id = self.record_number
        errors = []
        if not self.id:
            errors.append((True, '904', 'SLUCH', 'IDCASE', record_id, self.id, 0,
                           u'Отсутствует номер случая'))

        if not self.term and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'USL_OK', record_id, self.id, 0,
                           u'Отсутствует код условия оказания МП'))

        if int(self.term) not in TERMS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'USL_OK', record_id, self.id, 0,
                           u'Недопустимый код условия оказания МП'))

        if not self.kind:
            errors.append((True, '904', 'SLUCH', 'VIDPOM', record_id, self.id, 0,
                           u'Отсутствует код вида помощи'))

        if self.kind and safe_int(self.kind) not in KINDS:
            errors.append((True, '902', 'SLUCH', 'VIDPOM', record_id, self.id, 0,
                           u'Недопустимый код вида помощи'))

        if self.term in KIND_TERM_DICT and self.kind not in KIND_TERM_DICT[self.term]:
            errors.append((True, '904', 'SLUCH', 'VIDPOM', record_id, self.id, 0,
                           u'Вид медицинской помощи не соответствует условиям оказания'))

        if self.form not in FORMS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'FOR_POM', record_id, self.id, 0,
                           u'Недопустимый код формы медицинской помощи'))

        if self.refer_organization and self.refer_organization not in ORGANIZATIONS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'NPR_MO', record_id, self.id, 0,
                           u'Недопустимый код МО, направившего на лечение'))

        if safe_int(self.hospitalization) not in HOSPITALIZATIONS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'EXTR', record_id, self.id, 0,
                           u'Недопустимый код направления'))

        if self.division not in DIVISIONS and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'PODR', record_id, self.id, 0,
                           u'Недопустимый код отделения'))

        if self.organization not in ORGANIZATIONS:
            errors.append((True, '902', 'SLUCH', 'LPU', record_id, self.id, 0,
                           u'Недопустимый код МО'))

        if self.department not in DEPARTMENTS:
            errors.append((True, '902', 'SLUCH', 'LPU_1', record_id, self.id, 0,
                           u'Недопустимый код подразделения МО'))

        if safe_int(self.profile) not in PROFILES and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'SLUCH', 'PROFIL', record_id, self.id, 0,
                           u'Недопустимый код профиля: %s' % self.profile))

        if self.is_children_profile is None and self.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DET', record_id, self.id, 0,
                           u'Отсутствует признак детского профиля'))

        if not self.anamnesis_number:
            errors.append((True, '904', 'SLUCH', 'NHISTORY', record_id, self.id, 0,
                           u'Отсутствует номер истории болезни'))

        if self.examination_rejection not in ('0', '1') \
                and self.record.register.type in (3, 4, 6, 7):
            errors.append((True, '902', 'SLUCH', 'P_OTK', record_id, self.id, 0,
                           u'Недопустимый код признака отказа от диспансеризации'))

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
        return errors

    def get_object(self):
        if self.speciality_dict_version == 'V015' or self.record.register.type in list(range(3, 11)):
            speciality = SPECIALITIES_NEW.get(self.worker_speciality, None)
        else:
            speciality = SPECIALITIES_OLD.get(self.worker_speciality, None)
        event = ProvidedEvent(
            id=self.id,
            id_pk=self.id_pk,
            term=TERMS.get(self.term, None),
            kind=KINDS.get(self.kind, None),
            form=FORMS.get(self.form, None),
            hospitalization=HOSPITALIZATIONS.get(self.hospitalization, None),
            refer_organization=ORGANIZATIONS.get(self.refer_organization,
                                                    None),
            organization=ORGANIZATIONS.get(self.organization, None),
            department=DEPARTMENTS.get(self.department, None),
            profile=PROFILES.get(self.profile, None),
            is_children_profile=self.is_children_profile or False,
            anamnesis_number=self.anamnesis_number,
            examination_rejection=int(self.examination_rejection or 0),
            start_date=self.start_date,
            end_date=self.end_date,
            initial_disease=DISEASES.get(self.initial_disease, None),
            basic_disease=DISEASES.get(self.basic_disease, None),
            concomitant_disease=DISEASES.get(self.concomitant_disease, None),
            payment_method=METHODS.get(self.payment_method, None),
            payment_units_number=self.payment_units_number,
            comment=self.comment,
            division=DIVISIONS.get(self.division, None),
            treatment_result=RESULTS.get(self.treatment_result, None),
            treatment_outcome=OUTCOMES.get(self.treatment_outcome, None),
            worker_speciality=speciality,
            worker_code=self.worker_code,
            special=SPECIALS.get(self.special, None),
            hitech_kind=HITECH_KINDS.get(self.hitech_kind, None),
            hitech_method=HITECH_METHODS.get(self.hitech_method, None),
            examination_result=EXAMINATION_RESULTS.get(self.examination_result, None),
            speciality_dict_version=self.speciality_dict_version,
            record_id=self.record_id, )

        return event


class ValidService(object):
    def __init__(self, item, service_pk, event):
        self.id = item['IDSERV']
        self.id_pk = service_pk
        self.organization = item['LPU']
        self.department = item['LPU_1']
        self.division = item['PODR'][:3] if item['PODR'] else None
        self.profile = safe_int(item['PROFIL'])
        self.is_children_profile = True if item['DET'] == '1' else False
        self.start_date = item['DATE_IN']
        self.end_date = item['DATE_OUT']
        self.basic_disease = item['DS']
        code = item['CODE_USL']
        if code:
            code = '0'*(6-len(code))+code
        self.code = code
        self.quantity = item['KOL_USL']
        self.tariff = item['TARIF']
        self.invoiced_payment = item['SUMV_USL']
        self.worker_speciality = item['PRVS']
        self.worker_code = item['CODE_MD']
        self.comment = item['COMENTU']
        self.event = event
        self.intervention = item['VID_VME']

    def validate(self):
        errors = []

        if not self.id:
            errors.append((True, '904', 'USL', 'IDSERV', self.event.record.id,
                           self.event.id, self.id,
                           u'Отсутствует номер услуги'))

        if self.division not in DIVISIONS and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'USL', 'PODR', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код отделения %s' % self.division))

        if self.organization not in ORGANIZATIONS:
            errors.append((True, '902', 'USL', 'LPU', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код МО'))

        if self.department not in DEPARTMENTS:
            errors.append((True, '902', 'USL', 'LPU_1', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код подразделения МО'))

        if safe_int(self.profile) not in PROFILES \
                and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '902', 'USL', 'PROFIL', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код профиля'))

        if self.is_children_profile is None \
                and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'USL', 'DET', self.event.record.id,
                           self.event.id, self.id,
                           u'Отсутствует признак детского профиля'))

        if not self.start_date:
            errors.append((True, '904', 'USL', 'DATE_IN', self.event.record.id,
                           self.event.id, self.id,
                           u'Отсутствует дата начала лечения'))

        if not self.end_date:
            errors.append((True, '904', 'USL', 'DATE_OUT', self.event.record.id,
                           self.event.id, self.id,
                           u'Отсутствует дата конца лечения'))

        basic_disease = DISEASES.get(self.basic_disease, None)
        if self.basic_disease not in DISEASES:
            errors.append((True, '902', 'USL', 'DS', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код диагноза'))

        if basic_disease and basic_disease.is_precision \
            and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'USL', 'DS', self.event.record.id,
                           self.event.id, self.id,
                           u'Диагноз указан без подрубрики!'))

        if (self.event.speciality_dict_version == 'V015' or self.event.record.register.type in list(range(3, 11))) \
                and self.worker_speciality not in SPECIALITIES_NEW:
            errors.append((True, '904', 'USL', 'PRVS', self.event.record.id, self.event.id, self.id,
                           u'Недопустимый код специальности врача'))

        if ((not self.event.speciality_dict_version or self.event.speciality_dict_version == 'V004') \
                and self.event.record.register.type in (1, 2)) and self.worker_speciality not in SPECIALITIES_OLD:
            errors.append((True, '904', 'USL', 'PRVS', self.event.record.id, self.even.id, self.id,
                           u'Недопустимый код специальности врача'))

        if not self.worker_code:
            errors.append((True, '904', 'USL', 'CODE_MD', self.event.record.id,
                           self.event.id, self.id,
                           u'Отсутствует код врача'))

        if self.code not in CODES:
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Недопустимый код услуги'))

        service = CODES.get(self.code, None)

        if service and self.event.record.register.type == 1 and \
                service.group_id in list(range(6, 17)) + [20, ]:
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Услуга не соответсвует типу файла'))

        elif service and self.event.record.register.type == 2 and \
                service.group_id != 20:
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Услуга не соответсвует типу файла'))

        elif service and self.event.record.register.type in list(range(3, 11))\
                and service.group_id not in list(range(6, 17) + [25, 26]):
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Услуга не соответсвует типу файла'))

        if self.event.record.register.type == 2:
            if safe_int(self.code[-3:]) != safe_int(self.event.hitech_method):
                errors.append((True, '904', 'SLUCH', 'METHOD_HMP',
                               self.event.record.id, self.event.id, 0,
                               u'Некорректный код метода ВМП'))

        if self.is_children_profile != self.event.is_children_profile:
                errors.append((True, '904', 'USL', 'DET',
                               self.event.record.id, self.event.id, self.id,
                               u'Признак детского профиля услуги не совпадает с случаем'))

        if self.code and self.code[0] in ('0', '1') and self.event.record.register.type not in list(range(3, 11)):
            if self.code not in ['00' + str(x) for x in range(1441, 1460)] + ['098703', '098770', '098940','098913', '098914'] \
                    and self.code[0] == '0' and self.is_children_profile:
                errors.append((True, '904', 'USL', 'DET',
                           self.event.record.id, self.event.id, self.id,
                           u'Код услуги не соответствует десткому профилю'))
            if self.code[0] == '1' and not self.is_children_profile:
                errors.append((True, '904', 'USL', 'DET',
                           self.event.record.id, self.event.id, self.id,
                           u'Код услуги не соответствует взрослому профилю'))

        if (self.code in self.NEW_EXAMINATION_ADULT_PREVENTIVE \
                or self.code in self.NEW_EXAMINATION_CHILDREN_ADOPTED \
                or self.code in self.NEW_EXAMINATION_CHILDREN_HARD_LIFE \
                or self.code in self.NEW_EXAMINATION_CHILDREN_PREVENTIVE) \
                and datetime.strptime(self.event.end_date, '%Y-%m-%d').date() < datetime.strptime('2014-07-01', '%Y-%m-%d').date():
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Код услуги не действует с 01.07.2014'))

        if (self.code in self.OLD_EXAMINATION_ADULT_PREVENTIVE \
                or self.code in self.OLD_EXAMINATION_CHILDREN_ADOPTED \
                or self.code in self.OLD_EXAMINATION_CHILDREN_HARD_LIFE \
                or self.code in self.OLD_EXAMINATION_CHILDREN_PREVENTIVE) \
                and datetime.strptime(self.event.end_date, '%Y-%m-%d').date() > datetime.strptime('2014-07-01', '%Y-%m-%d').date():
            errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                           self.event.id, self.id,
                           u'Код услуги разрешен к использованию для услуг до 01.07.2014'))

        if self.event.term in (1, 2) and service.tariff_profile_id and service.tariff_profile_id != 999:
            event_term = CODES.get(self.code, 0).tariff_profile.term_id
            if not ((self.event.term == 1 and event_term == 1) \
                    or (self.event.term == 2 and event_term in (2, 10, 11, 12))):
                errors.append((True, '904', 'USL', 'CODE_USL', self.event.record.id,
                               self.event.id, self.id,
                               u'Услуга не оказывается в текущих условиях'))

        return errors

    def get_object(self):
        if self.event.speciality_dict_version == 'V015' or self.event.record.register.type in list(range(3, 11)):
            speciality = SPECIALITIES_NEW.get(self.worker_speciality, None)
        else:
            speciality = SPECIALITIES_OLD.get(self.worker_speciality, None)

        service = ProvidedService(
            id=str(self.id or ''),
            id_pk=self.id_pk,
            organization=ORGANIZATIONS.get(self.organization, None),
            department=DEPARTMENTS.get(self.department, None),
            division=DIVISIONS.get(self.division, None),
            profile=PROFILES.get(self.profile, None),
            is_children_profile=self.is_children_profile or False,
            start_date=self.start_date,
            end_date=self.end_date,
            basic_disease=DISEASES.get(self.basic_disease, None),
            code=CODES.get(self.code, None),
            quantity=self.quantity,
            tariff=self.tariff,
            invoiced_payment=self.invoiced_payment,
            worker_speciality=speciality,
            worker_code=self.worker_code,
            comment=self.comment,
            event_id=self.event.id_pk)

        return service


class ValidConcomitantDisease(object):
    def __init__(self, disease_code, event):
        self.disease = disease_code
        self.event = event
        self.record_id = event.record.id
        self.event_id = event.id

    def validate(self):
        errors = []
        disease = DISEASES.get(self.disease, None)
        if self.disease and not disease and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DS2', self.record_id, self.event_id, '',
                           u'Недопустимый код сопутствующего диагноза'))
        if self.disease and disease and disease.is_precision and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DS2', self.record_id, self.event_id, '',
                           u'Сопутствующий диагноз указан без подрубрики!'))

        return errors

    def get_object(self):
        if self.disease and DISEASES.get(self.disease, None):
            disease = ProvidedEventConcomitantDisease(
                disease=DISEASES.get(self.disease, None),
                event_id=self.event.id_pk)
        else:
            disease = None

        return disease


class ValidComplicatedDisease(object):
    def __init__(self, disease_code, event):
        self.disease = disease_code
        self.event = event
        self.record_id = event.record.id
        self.event_id = event.id

    def validate(self):
        errors = []
        disease = DISEASES.get(self.disease, None)
        if self.disease and not disease and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DS3', self.record_id, self.event_id, '',
                           u'Недопустимый код осложнённого заболевания'))
        if self.disease and disease and disease.is_precision and self.event.record.register.type not in list(range(3, 11)):
            errors.append((True, '904', 'SLUCH', 'DS3', self.record_id, self.event_id, '',
                           u'Осложнённое заболевание указан без подрубрики!'))

        return errors

    def get_object(self):
        if self.disease:
            disease = ProvidedEventComplicatedDisease(
                disease=DISEASES.get(self.disease, None),
                event_id=self.event.id_pk)
        else:
            disease = None

        return disease