# -*- coding: utf-8 -*-

from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalOrganization,
    Patient, Person, InsurancePolicy, MedicalRegisterRecord, PersonIDType,
    MedicalServiceTerm, MedicalServiceKind, MedicalServiceForm, MedicalDivision,
    MedicalServiceProfile, TreatmentResult, TreatmentOutcome, Special,
    MedicalWorkerSpeciality, PaymentMethod, PaymentType, PaymentFailureCause,
    Gender, InsurancePolicyType, MedicalHospitalization, MedicalService)
from lxml import etree


def safe_int(string):
    try:
        integer = int(string)
    except:
        integer = 0

    return integer


def queryset_to_dict(qs):
    return {rec.code: rec for rec in qs}

GENDERS = queryset_to_dict(Gender.objects.all())
POLICY_TYPES = queryset_to_dict(InsurancePolicyType.objects.all())
departments_set = MedicalOrganization.objects.all()
DEPARTMENTS = {rec.old_code: rec for rec in departments_set}
ORGANIZATIONS = queryset_to_dict(MedicalOrganization.objects.filter(parent=None))
TERMS = queryset_to_dict(MedicalServiceTerm.objects.all())
KINDS = queryset_to_dict(MedicalServiceKind.objects.all())
FORMS = queryset_to_dict(MedicalServiceForm.objects.all())
HOSPITALIZATIONS = queryset_to_dict(MedicalHospitalization.objects.all())
PROFILES = queryset_to_dict(MedicalServiceProfile.objects.filter(is_active=True))
OUTCOMES = queryset_to_dict(TreatmentOutcome.objects.all())
RESULTS = queryset_to_dict(TreatmentResult.objects.all())
SPECIALITIES = queryset_to_dict(MedicalWorkerSpeciality.objects.all())
METHODS = queryset_to_dict(PaymentMethod.objects.all())
TYPES = queryset_to_dict(PaymentType.objects.all())
FAILURE_CUASES = queryset_to_dict(PaymentFailureCause.objects.all())
DISEASES = {rec.idc_code: rec for rec in IDC.objects.all()}
DIVISIONS = queryset_to_dict(MedicalDivision.objects.all())
SPECIALS = queryset_to_dict(Special.objects.all())
CODES = queryset_to_dict(MedicalService.objects.all())
PERSON_ID_TYPES = queryset_to_dict(PersonIDType.objects.all())


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
        self.insurance_policy_series = item['insurance_policy_series']
        self.insurance_policy_number = item['insurance_policy_number']
        #self.person_instance = None
        #self.insurance_instance = None
        self.record_id = record_id

    def validate(self):
        errors = []
        record_id = self.record_id
        if not self.id:
            errors.append((2, '904', 'PERS', 'ID_PAC', record_id,
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
            errors.append((True, '902', 'PACIENT', '',
                           u'Отсутствуют данные представителя %s' % self.newborn_code))

        if self.gender and int(self.gender) not in GENDERS:
            errors.append((True, '902', 'PACIENT', 'W', record_id,
                           u'Пол не соответствует допустимому'))

        elif not self.gender:
            errors.append((True, '904', 'PACIENT', 'W', record_id,
                           u'Отсутствует пол'))

        if not self.birthdate:
            errors.append(
                (False, '904', 'PERS', 'DR', u'Отсутствует дата рождения'))

        if not self.insurance_policy_type:
            errors.append((True, '904', 'PACIENT', 'VPOLIS', record_id,
                           u'Отсутствует тип полиса'))

        if self.insurance_policy_type == '1':
            if not self.insurance_policy_series:
                errors.append((True, '904', 'PACIENT', 'SPOLIS', record_id,
                               u'Отсутствует серия полиса'))

        if not self.insurance_policy_number:
            errors.append((True, '904', 'PACIENT', 'NPOLIS', record_id,
                           u'Отсутствует номер полиса'))

        if self.insurance_policy_series and \
                        len(self.insurance_policy_series) > 10:
            errors.append((True, '902', 'PACIENT', 'SPOLIS', record_id,
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
    def __init__(self, item, record_pk, register_pk, patient_pk):
        self.id = item['N_ZAP']
        self.id_pk = record_pk
        self.register_pk = register_pk
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
            register_id=self.register_pk,
            patient_id=self.patient_pk)

        return record


class ValidEvent(object):
    def __init__(self, item, pk, record_pk, record_id):
        self.id = item['IDCASE']
        self.id_pk = pk
        self.term = safe_int(item['USL_OK'])
        self.kind = safe_int(item['VIDPOM'])
        self.hospitalization = item['EXTR']
        self.refer_organization = item['NPR_MO']
        self.organization = item['LPU']
        self.department = item['LPU_1']
        self.profile = safe_int(item['PROFIL'])
        self.is_children_profile = item['DET'] if item['DET'] == '1' else False
        self.anamnesis_number = item['NHISTORY']
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
        self.worker_code = item['IDDOKT']
        self.special = item['OS_SLUCH']
        self.record_id = record_pk
        self.record_number = record_id

    def validate(self):
        record_id = self.record_number
        errors = []
        if not self.id:
            errors.append((True, '904', 'SLUCH', 'IDCASE', record_id,
                           u'Отсутствует номер случая'))

        if not self.term:
            errors.append((True, '904', 'SLUCH', 'USL_OK', record_id,
                           u'Отсутствует код условия оказания МП'))

        if int(self.term) not in TERMS:
            errors.append((True, '902', 'SLUCH', 'USL_OK', record_id,
                           u'Недопустимый код условия оказания МП'))

        if not self.kind:
            errors.append((True, '904', 'SLUCH', 'VIDPOM', record_id,
                           u'Отсутствует код вида помощи'))

        if self.kind and safe_int(self.kind) not in KINDS:
            errors.append((True, '902', 'SLUCH', 'VIDPOM', record_id,
                           u'Недопустимый код вида помощи'))

        if self.refer_organization and self.refer_organization not in ORGANIZATIONS:
            errors.append((True, '904', 'SLUCH', 'NPR_MO', record_id,
                           u'Недопустимый код МО, направившего на лечение'))

        if safe_int(self.hospitalization) not in HOSPITALIZATIONS:
            errors.append((True, '902', 'SLUCH', 'EXTR', record_id,
                           u'Недопустимый код направления'))

        if self.division not in DIVISIONS:
            errors.append((True, '902', 'SLUCH', 'PODR', record_id,
                           u'Недопустимый код отделения'))

        if self.organization not in ORGANIZATIONS:
            errors.append((True, '902', 'SLUCH', 'LPU', record_id,
                           u'Недопустимый код МО'))

        if self.department not in DEPARTMENTS:
            errors.append((True, '902', 'SLUCH', 'LPU_1', record_id,
                           u'Недопустимый код подразделения МО'))

        if safe_int(self.profile) not in PROFILES:
            errors.append((True, '902', 'SLUCH', 'PROFIL', record_id,
                           u'Недопустимый код профиля: %s' % self.profile))

        if self.is_children_profile is None:
            errors.append((True, '904', 'SLUCH', 'DET', record_id,
                           u'Отсутствует признак детского профиля'))

        if not self.anamnesis_number:
            errors.append((True, '904', 'SLUCH', 'NHISTORY', record_id,
                           u'Отсутствует номер истории болезни'))

        if not self.start_date:
            errors.append((True, '904', 'SLUCH', 'DATE_1', record_id,
                           u'Отсутствует дата начала лечения'))

        if not self.end_date:
            errors.append((True, '904', 'SLUCH', 'DATE_2', record_id,
                           u'Отсутствует дата конца лечения'))

        if self.initial_disease not in DISEASES:
            errors.append((True, '902', 'SLUCH', 'DS0', record_id,
                           u'Недопустимый код первичного диагноза'))

        if self.basic_disease not in DISEASES:
            errors.append((True, '902', 'SLUCH', 'DS1', record_id,
                           u'Недопустимый код основного диагноза'))

        if self.concomitant_disease and self.concomitant_disease not in DISEASES:
            errors.append((True, '902', 'SLUCH', 'DS2', record_id,
                           u'Недопустимый код сопутствующего диагноза'))

        if safe_int(self.treatment_result) not in RESULTS:
            errors.append((True, '902', 'SLUCH', 'RSLT', record_id,
                           u'Недопустимый код результата обращения'))

        if safe_int(self.treatment_outcome) not in OUTCOMES:
            errors.append((True, '902', 'SLUCH', 'ISHOD', record_id,
                           u'Недопустимый код исхода заболевания'))

        if self.worker_speciality not in SPECIALITIES:
            errors.append((True, '902', 'SLUCH', 'PRVS', record_id,
                           u'Недопустимый код специальности врача'))

        if not self.worker_code:
            errors.append((True, '904', 'SLUCH', 'IDDOKT', record_id,
                           u'Отсутствует код врача'))

        for special in self.special or []:
            if safe_int(special) not in SPECIALS:
                errors.append((True, '902', 'SLUCH', 'OS_SLUCH', record_id,
                               u'Недопустимый код особого случая'))

        if safe_int(self.payment_method) not in METHODS:
            errors.append((True, '902', 'SLUCH', 'PRVS', record_id,
                           u'Недопустимый код способа оплаты'))

        return errors

    def get_object(self):
        event = ProvidedEvent(
            id=self.id,
            id_pk=self.id_pk,
            term_id=TERMS.get(self.term, None),
            kind_id=KINDS.get(self.kind, None),
            hospitalization_id=HOSPITALIZATIONS.get(self.hospitalization, None),
            refer_organization_id=ORGANIZATIONS.get(self.refer_organization,
                                                    None),
            organization_id=ORGANIZATIONS.get(self.organization, None),
            department_id=DEPARTMENTS.get(self.department, None),
            profile_id=PROFILES.get(self.profile, None),
            is_children_profile=self.is_children_profile or False,
            anamnesis_number=self.anamnesis_number,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_disease_id=DISEASES.get(self.initial_disease, None),
            basic_disease_id=DISEASES.get(self.basic_disease, None),
            concomitant_disease_id=DISEASES.get(self.concomitant_disease, None),
            payment_method_id=self.payment_method,
            payment_units_number=self.payment_units_number,
            comment=self.comment,
            division_id=DIVISIONS.get(self.division, None),
            treatment_result_id=RESULTS.get(self.treatment_result, None),
            treatment_outcome_id=OUTCOMES.get(self.treatment_outcome, None),
            worker_speciality_id=SPECIALITIES.get(self.worker_speciality, None),
            worker_code=self.worker_code,
            special_id=SPECIALS.get(self.special, None),
            record_id=self.record_id, )

        return event


class ValidService(object):
    def __init__(self, item, service_pk, event_pk, record_id):
        self.id = item['IDSERV']
        self.id_pk = service_pk
        self.organization = item['LPU']
        self.department = item['LPU_1']
        self.division = item['PODR'][:3] if item['PODR'] else None
        self.profile = safe_int(item['PROFIL'])
        self.is_children_profile = item['DET'] if item['DET'] == '1' else False
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
        self.event = event_pk
        self.record_id = record_id

    def validate(self):
        errors = []

        if not self.id:
            errors.append((True, '904', 'USL', 'IDSERV', self.record_id,
                           u'Отсутствует номер услуги'))

        if self.division not in DIVISIONS:
            errors.append((True, '902', 'USL', 'PODR', self.record_id,
                           u'Недопустимый код отделения %s' % self.division))

        if self.organization not in ORGANIZATIONS:
            errors.append((True, '902', 'USL', 'LPU', self.record_id,
                           u'Недопустимый код МО'))

        if self.department not in DEPARTMENTS:
            errors.append((True, '902', 'USL', 'LPU_1', self.record_id,
                           u'Недопустимый код подразделения МО'))

        if safe_int(self.profile) not in PROFILES:
            errors.append((True, '902', 'USL', 'PROFIL', self.record_id,
                           u'Недопустимый код профиля'))

        if self.is_children_profile is None:
            errors.append((True, '904', 'USL', 'DET', self.record_id,
                           u'Отсутствует признак детского профиля'))

        if not self.start_date:
            errors.append((True, '904', 'USL', 'DATE_IN', self.record_id,
                           u'Отсутствует дата начала лечения'))

        if not self.end_date:
            errors.append((True, '904', 'USL', 'DATE_OUT', self.record_id,
                           u'Отсутствует дата конца лечения'))

        if self.basic_disease not in DISEASES:
            errors.append((True, '902', 'USL', 'DS', self.record_id,
                           u'Недопустимый код диагноза'))

        if self.worker_speciality not in SPECIALITIES:
            errors.append((True, '902', 'USL', 'PRVS', self.record_id,
                           u'Недопустимый код специальности врача %s' % self.worker_speciality))

        if not self.worker_code:
            errors.append((True, '904', 'USL', 'CODE_MD', self.record_id,
                           u'Отсутствует код врача'))

        if self.code not in CODES:
            print self.code
            errors.append((True, '902', 'USL', 'CODE_USL', self.record_id,
                           u'Недопустимый код услуги'))

        return errors

    def get_object(self):
        service = ProvidedService(
            id=self.id,
            id_pk=self.id_pk,
            organization_id=ORGANIZATIONS.get(self.organization, None),
            department_id=DEPARTMENTS.get(self.department, None),
            division_id=DIVISIONS.get(self.division, None),
            profile_id=PROFILES.get(self.profile, None),
            is_children_profile=self.is_children_profile or False,
            start_date=self.start_date,
            end_date=self.end_date,
            basic_disease_id=DISEASES.get(self.basic_disease, None),
            code_id=CODES.get(self.code, None),
            quantity=self.quantity,
            tariff=self.tariff,
            invoiced_payment=self.invoiced_payment,
            worker_speciality_id=SPECIALITIES.get(self.worker_speciality, None),
            worker_code=self.worker_code,
            comment=self.comment,
            event_id=self.event)

        return service