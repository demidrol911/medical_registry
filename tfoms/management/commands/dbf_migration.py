# -*- coding: utf-8 -*-

from tfoms.models import (
    MedicalRegister, MedicalOrganization, MedicalRegisterStatus, Gender,
    InsurancePolicyType, Patient, Person, InsurancePolicy, PersonID,
    MedicalRegisterRecord, MedicalServiceTerm, MedicalServiceKind,
    MedicalServiceForm, MedicalServiceProfile, TreatmentOutcome,
    TreatmentResult, MedicalWorkerSpeciality, PaymentMethod, PaymentType,
    PaymentFailureCause, IDC, MedicalDivision, Special, ProvidedEvent,
    ProvidedService, MedicalHospitalization, MedicalService)
from django.db.models import Max
import datetime


class MedicalRegisterConverter:
    status = MedicalRegisterStatus.objects.get(pk=5)
    organizations = MedicalOrganization.objects.all()

    def __init__(self, tfile):
        now = datetime.datetime.now()
        self.code_mo = tfile.name[29:-4]
        self.year = '2011'
        self.period = tfile.name[25:27]
        self.day = '20'
        self.invoice_date = now
        self.instance = None
        try:
            self.organization = self.organizations.get(parent=None,
                                                       code=self.code_mo)
        except:
            self.organization = None
        self.filename = tfile.name[28:]

    def insert(self):
        active_registers = MedicalRegister.objects.filter(
            period=self.period, organization=self.organization, is_active=True,
            year=self.year)
        print active_registers

        active_registers.update(is_active=False)
        self.instance = MedicalRegister(filename=self.filename,
                                       timestamp=datetime.datetime.now(),
                                       status=self.status,
                                       organization=self.organization,
                                       is_active=True,
                                       period=self.period,
                                       year=self.year)
        #self.instance.save()

        return self.instance


def q_to_d(qs):
    t = {}
    for rec in qs:
        t[rec.code] = rec.pk
    return t

def q_to_d_2(qs):
    t = {}
    for rec in qs:
        t[rec.old_code] = rec.pk
    return t

def q_to_d_3(qs):
    t = {}
    for rec in qs:
        t[rec.idc_code] = rec.pk
    return t

class PatientConverter:
    genders = q_to_d(Gender.objects.all())
    policy_types = q_to_d(InsurancePolicyType.objects.all())

    def __init__(self, record):
        self.id = record['id_pac'].decode('cp1251')
        self.newborn_code = record['novor']
        self.last_name = record['fam'].decode('cp1251')
        self.first_name = record['im'].decode('cp1251')
        self.middle_name = record['ot'].decode('cp1251')
        self.gender = record['w']
        self.gender_instance = None
        if self.gender:
            self.gender_instance = self.genders.get(self.gender, None)
        self.birthdate = record['dr']
        self.agent_last_name = record['fam_p'].decode('cp1251')
        self.agent_first_name = record['im_p'].decode('cp1251')
        self.agent_middle_name = record['ot_p'].decode('cp1251')
        self.agent_gender = record['w_p']
        self.agent_gender_instance = None
        if self.agent_gender:
            self.agent_gender_instance = self.genders.get(self.agent_gender, None)
        self.agent_birthdate = record['dr_p']
        self.birthplace = record['mr']
        self.person_id_series = record['docser'].decode('cp1251')
        if self.person_id_series:
            self.person_id_series = self.person_id_series[:10]
        self.person_id_number = record['docnum'].decode('cp1251')
        self.snils = record['snils']
        self.policy_type = self.policy_types.get(record['vpolis'], None)
        self.policy_series = record['spolis'].decode('cp1251')
        self.policy_number = record['npolis'].decode('cp1251')
        self.okato_registration = record['okatog']
        self.okato_residence = record['okatop']

    def insert(self):
        """
        if self.newborn_code and self.newborn_code != u'0':
            last_name = self.agent_last_name.upper()
            first_name = self.agent_first_name.upper()
            middle_name = self.agent_middle_name.upper()
            birthdate = self.agent_birthdate
        else:
            last_name = self.last_name.upper()
            first_name = self.first_name.upper()
            middle_name = self.middle_name.upper()
            birthdate = self.birthdate


        persons_pk = Person.objects.filter(
            last_name=last_name, first_name=first_name,
            middle_name=middle_name, birthdate=birthdate
        ).values_list('id', flat=True)
        try:
            person_instance = Person.objects.get(id__in=persons_pk,
                                                 is_active=True)
        except:
            person_instance = None

        print persons_pk, person_instance
        """
        person_instance = None
        policies_pk = []
        """
        if self.policy_type == '1':
            policies_pk = InsurancePolicy.objects.filter(
                series=self.policy_series, number=self.policy_number
            ).values_list('id', flat=True)
        elif self.policy_type == '2':
            policies_pk = InsurancePolicy.objects.filter(
                number=self.policy_number).values_list('id', flat=True)
        elif self.policy_type == '3':
            policies_pk = InsurancePolicy.objects.filter(
                enp=self.policy_number).values_list('id', flat=True)
        """
        policy_instance = None
        #if policies_pk:
        #    policy_instance = InsurancePolicy.objects.get(id__in=policies_pk,
        #                                                  is_active=True)

        person_ids_pk = person_id_instance = None
        """
        person_ids_pk = PersonID.objects.filter(
            series=self.person_id_series, number=self.person_id_number
        ).values_list('id', flat=True)

        #person_id_instance = PersonID.objects.get(id__in=person_ids_pk,
        #                                          is_active=True)
        """
        self.instance = Patient(id=self.id, newborn_code=self.newborn_code,
                                last_name=self.last_name,
                                first_name=self.first_name,
                                middle_name=self.middle_name,
                                gender_id=self.gender_instance,
                                birthdate=self.birthdate,
                                agent_last_name=self.agent_last_name,
                                agent_first_name=self.agent_first_name,
                                agent_middle_name=self.agent_middle_name,
                                agent_gender_id=self.agent_gender_instance,
                                agent_birthdate=self.agent_birthdate,
                                birthplace=self.birthplace,
                                person_id_series=self.person_id_series,
                                person_id_number=self.person_id_number,
                                snils=self.snils,
                                insurance_policy_type_id=self.policy_type,
                                insurance_policy_series=self.policy_series,
                                insurance_policy_number=self.policy_number,
                                person=person_instance,
                                insurance_policy=policy_instance,
                                personID=person_id_instance,
                                okato_registration=self.okato_registration,
                                okato_residence=self.okato_residence,)

        #self.instance.save()
        return self.instance


class MedicalRegisterRecordConverter:
    def __init__(self, record, register, patient):
        self.id = record['n_zap']
        self.register_instance = register
        self.patient_instance = patient

    def insert(self):
        self.instance = MedicalRegisterRecord(id=self.id,
                                              register=self.register_instance,
                                              patient=self.patient_instance)
        #self.instance.save()
        return self.instance


class ProvidedBase:
    departments = q_to_d_2(MedicalOrganization.objects.all())

    organizations = q_to_d(MedicalOrganization.objects.filter(parent=None))
    terms = q_to_d(MedicalServiceTerm.objects.all())
    kinds = q_to_d(MedicalServiceKind.objects.all())
    forms = q_to_d(MedicalServiceForm.objects.all())
    hospitalizations = q_to_d(MedicalHospitalization.objects.all())
    profiles = q_to_d(MedicalServiceProfile.objects.all())
    outcomes = q_to_d(TreatmentOutcome.objects.all())
    results = q_to_d(TreatmentResult.objects.all())
    specialities = q_to_d(MedicalWorkerSpeciality.objects.all())
    methods = q_to_d(PaymentMethod.objects.all())
    types = q_to_d(PaymentType.objects.all())
    failure_causes = q_to_d(PaymentFailureCause.objects.all())
    diseases = q_to_d_3(IDC.objects.all())
    divisions = q_to_d(MedicalDivision.objects.all())
    specials = q_to_d(Special.objects.all())
    codes = q_to_d(MedicalService.objects.all())


class ProvidedEventConverter(ProvidedBase):
    def __init__(self, record):
        self.id = record['idcase']
        self.term = self.terms.get(record['usl_ok'], None)
        self.kind = self.kinds.get(record['vidpom'], None)
        self.refer_organization = self.organizations.get(record['npr_mo'], None)
        self.organization = self.organizations.get(record['LPU'].decode('cp1251'), None)
        self.department = self.departments.get(record['lpu_1'].decode('cp1251'), None)
        self.profile = self.profiles.get(record['profil'], None)
        self.is_children_profile = True if record['det'] == '1' else False
        self.anamnesis_number = record['nhistory'].decode('cp1251')
        self.start_date = record['date_1']
        self.end_date = record['date_2']
        self.initial_disease = self.diseases.get(record['ds0'].decode('cp1251'), None)
        self.basic_disease = self.diseases.get(record['ds1'].decode('cp1251'), None)
        try:
            self.concomitant_disease = self.diseases.get(record['ds2'].decode('cp1251'), None)
        except:
            self.concomitant_disease = None
        self.payment_method = self.methods.get(record['idsp'], None)
        self.payment_units_number = record['ed_col']
        self.comment = record['comentz'].decode('cp1251')

        division = str(record['podr']) if record['podr'] else '0'
        if division and len(division) < 3:
            division = '0'*(3-len(division))+division

        self.division = self.divisions.get(record['podr'], None)
        self.treatment_result = self.results.get(record['rslt'], None)
        self.treatment_outcome = self.outcomes.get(record['ishod'], None)
        self.worker_speciality = self.specialities.get(record['prvs'], None)
        self.worker_code = record['iddokt'].decode('cp1251')
        self.special = self.specials.get(record['os_sluch'], None)
        self.hospitalization = self.hospitalizations.get(record['extr'], None)

    def insert(self, register_record):
        self.instance = ProvidedEvent(id=self.id, term_id=self.term, kind_id=self.kind,
            refer_organization_id=self.refer_organization,
            hospitalization_id=self.hospitalization, division_id=self.division,
            organization_id=self.organization,
            department_id=self.department,
            profile_id=self.profile, is_children_profile=self.is_children_profile,
            anamnesis_number=self.anamnesis_number, start_date=self.start_date,
            end_date=self.end_date, initial_disease_id=self.initial_disease,
            basic_disease_id=self.basic_disease,
            concomitant_disease_id=self.concomitant_disease,
            treatment_result_id=self.treatment_result,
            treatment_outcome_id=self.treatment_outcome,
            worker_speciality_id=self.worker_speciality,
            worker_code=self.worker_code, special_id=self.special,
            payment_method_id=self.payment_method,
            payment_units_number=self.payment_units_number,
            comment=self.comment,
            record=register_record)

        #self.instance.save()
        return self.instance


class ProvidedServiceConverter(ProvidedBase):
    def __init__(self, record):
        self.id = record['idserv']
        self.organization = self.organizations.get(record['lpu'], None)
        self.department = self.departments.get(record['lpu_1'], None)
        division = str(record['podr']) if record['podr'] else '0'
        if division and len(division) < 3:
            division = '0'*(3-len(division))+division
        self.division = self.divisions.get(division, None)
        self.profile = self.profiles.get(record['profil'], None)
        self.is_children_profile = True if record['det'] == '1' else False
        self.start_date = record['date_in']
        self.end_date = record['date_out']
        self.basic_disease = self.diseases.get(record['ds'].decode('cp1251'), None)
        self.code = self.codes.get(record['code_usl'], None)
        self.quantity = record['kol_usl']
        self.comment = record['comentu'].decode('cp1251')
        self.worker_speciality = self.specialities.get(record['prvs'], None)
        self.worker_code = record['code_md'].decode('cp1251')
        self.accepted_payment = record['sumv_usl']*(record['koef_l'] or 1)*(record['koef_m'] or 1)# + record['o_dop']
        #if 'PA' not in record.err_all and record.o_dop:
        #    self.accepted_payment += record.o_dop
        self.invoiced_payment = record['sumv_usl'] * record['koef_l'] * record['koef_m'] #+ record['o_dop']
        #if record.o_dop:
        #    self.invoiced_payment += record.o_dop
        #    self.accepted_payment += record.o_dop
        #if 'koef_s' in record:
        #    self.invoiced_payment *= record['koef_s'] or 1
        #    self.accepted_payment *= record['koef_s'] or 1
        self.accepted_payment = self.invoiced_payment
        self.tariff = record['tarif_2']
        self.payment_type = self.types.get(record['oplata'], None)
        self.payment_failure_cause = self.failure_causes.get(record['refreason'], None)
        self.tfoms_surcharge = record['t_dop']
        self.ffoms_surcharge = record['f_dop']
        #self.single_channel_surcharge = record['o_dop']
        self.sanctions_mek = record['sank_mek']
        self.sanctions_mee = record['sank_mee']
        self.sanctions_ekmp = record['sank_ekmp']
        #self.sanctions_org = record.sank_org
        #self.sanctions_mee_tfoms = record.mee_tf
        #self.sanctions_mee_ffoms = record.mee_ff
        #self.sanctions_mee_single_channel = record.mee_of
        #self.sanctions_ekmp_tfoms = record.ekmp_tf
        #self.sanctions_ekmp_ffoms = record.ekmp_ff
        #self.sanctions_ekmp_single_channel = record.ekmp_of
        #self.correction = record.vozvr
        #self.tfoms_correction = record.vozvr_tf
        #self.ffoms_correction = record.vozvr_ff
        #self.single_channel_correction = record.vozvr_of

        if not record['err_all']:
            self.payment_type = 2

    def insert(self, event):
        self.instance = ProvidedService(id=self.id, division_id=self.division,
            organization_id=self.organization,
            department_id=self.department,
            profile_id=self.profile, is_children_profile=self.is_children_profile,
            start_date=self.start_date, end_date=self.end_date,
            code_id=self.code,
            basic_disease_id=self.basic_disease,
            worker_speciality_id=self.worker_speciality,
            worker_code=self.worker_code,
            quantity=self.quantity,
            payment_failure_cause_id=self.payment_failure_cause,
            tariff=self.tariff, payment_type_id=self.payment_type,
            invoiced_payment=self.invoiced_payment,
            accepted_payment=self.accepted_payment,
            tfoms_surcharge=self.tfoms_surcharge,
            ffoms_surcharge=self.ffoms_surcharge,
            single_channel_surcharge=self.single_channel_surcharge,
            sanctions_mek=self.sanctions_mek, sanctions_mee=self.sanctions_mee,
            sanctions_ekmp=self.sanctions_ekmp,

            comment=self.comment, event=event)

        #self.instance.save()
        return self.instance
"""
sanctions_org=self.sanctions_org,
sanctions_mee_tfoms=self.sanctions_mee_tfoms,
sanctions_mee_ffoms=self.sanctions_mee_ffoms,
sanctions_mee_single_channel=self.sanctions_mee_single_channel,
sanctions_ekmp_tfoms=self.sanctions_ekmp_tfoms,
sanctions_ekmp_ffoms=self.sanctions_ekmp_ffoms,
sanctions_ekmp_single_channel=self.sanctions_ekmp_single_channel,
correction=self.correction, tfoms_correction=self.tfoms_correction,
ffoms_correction=self.ffoms_correction,
single_channel_correction=self.single_channel_correction,
"""
