#! -*- coding: utf-8 -*-
from main.data_cache import GENDERS, PERSON_ID_TYPES, \
    POLICY_TYPES, DEPARTMENTS, ORGANIZATIONS, TERMS, KINDS, FORMS, \
    HOSPITALIZATIONS, PROFILES, OUTCOMES, RESULTS, \
    SPECIALITIES_NEW, METHODS, DISEASES, DIVISIONS, \
    SPECIALS, CODES, HITECH_KINDS, HITECH_METHODS, EXAMINATION_RESULTS, MEDICINES, BED_PROFILES, OPERATIONS
from main.funcs import safe_int, safe_date, safe_float
from main.models import Patient, MedicalRegisterRecord, ProvidedEvent, ProvidedService, MedicalRegister, \
    MedicalRegisterImport, MedicalRegisterStatus, ProvidedEventAdditionalDisease, \
    ProvidedEventSpecial, ProvidedEventAppointment, ProvidedEventMedicine
from django.db import connection, transaction
from datetime import datetime

from main.logger import get_logger
logger = get_logger(__name__)


class RegistryDb:
    def __init__(self, registry_set, is_commit=True):
        self.registry_set = registry_set
        self.patients = []
        self.registries = []
        self.records = []
        self.events = []
        self.services = []
        self.concomitant_list = []
        self.complicated_list = []
        self.special_list = []
        self.appointment_list = []
        self.medicine_list = []

        self._patient_pk_list = []
        self._register_pk_list = []
        self._record_pk_list = []
        self._event_pk_list = []
        self._service_pk_list = []
        self.cursor = connection.cursor()
        self.is_commit = is_commit

    def create_patient_obj(self, patient):
        patient_obj = Patient(
            id_pk=self._get_next_patient_pk(),
            id=patient.get('ID_PAC', ''),
            last_name=(patient.get('FAM', '') or '').upper(),
            first_name=(patient.get('IM', '') or '').upper(),
            middle_name=(patient.get('OT', '') or '').upper(),
            birthdate=safe_date(patient.get('DR', None)),
            snils=patient.get('SNILS', ''),
            birthplace=patient.get('MR', ''),
            gender=GENDERS.get(patient.get('W'), None),
            person_id_type=PERSON_ID_TYPES.get(patient.get('DOCTYPE'), None),
            person_id_series=(patient.get('DOCSER', '') or '').upper(),
            person_id_number=patient.get('DOCNUM', '') or '',
            weight=safe_float(patient.get('VNOV_D', 0)),
            okato_residence=patient.get('OKATOP', '') or '',
            okato_registration=patient.get('OKATOG', '') or '',
            comment=patient.get('COMENTP', ''),
            agent_last_name=(patient.get('FAM_P', '') or '').upper(),
            agent_first_name=(patient.get('IM_P', '') or '').upper(),
            agent_middle_name=(patient.get('OT_P', '') or '').upper(),
            agent_birthdate=safe_date(patient.get('DR_P', None)),
            agent_gender=GENDERS.get(patient.get('W_P'), None),
            newborn_code=patient.get('NOVOR', '0'),
            insurance_policy_type=POLICY_TYPES.get(patient.get('VPOLIS'), None),
            insurance_policy_series=patient.get('SPOLIS', '') or '',
            insurance_policy_number=patient.get('NPOLIS', '')
        )
        self.patients.append(patient_obj)
        return patient_obj

    def patient_update_policy(self, patient_obj, patient_policy):
        idx = self.patients.index(patient_obj)
        if idx >= 0:
            self.patients[idx].insurance_policy_type_id = patient_policy.get('VPOLIS', None)
            self.patients[idx].insurance_policy_series = patient_policy.get('SPOLIS', '') or ''
            self.patients[idx].insurance_policy_number = patient_policy.get('NPOLIS', '') or ''
            self.patients[idx].newborn_code = patient_policy.get('NOVOR', '0') or '0'
            self.patients[idx].weight = safe_float(patient_policy.get('VNOV_D', 0))
            self.patients[idx].disability_group = safe_int(patient_policy.get('INV', 0))
        else:
            logger.warning(u'Пациент не найден. Полис не может быть присоединён')
            print u'Пациент не найден. Полис не может быть присоединён'

    def create_registry_object(self, registry, registry_item):
        registry_object = MedicalRegister(pk=self._get_next_medical_register_pk(),
                                          timestamp=datetime.now(),
                                          type=registry_item.type_id,
                                          filename=registry_item.file_name,
                                          organization_code=self.registry_set.mo_code,
                                          is_active=True,
                                          year=self.registry_set.year,
                                          period=self.registry_set.period,
                                          status_id=12,
                                          reporting_date=datetime.strptime('01-%s-%s' % (self.registry_set.period,
                                                                                         self.registry_set.year),
                                                                           '%d-%m-%Y'),
                                          invoice_date=registry['DSCHET'])
        self.registries.append(registry_object)
        return registry_object

    def create_record_obj(self, record, registry_obj, patient_obj):
        record_obj = MedicalRegisterRecord(
            id_pk=self._get_next_medical_register_record_pk(),
            id=record.get('N_ZAP'),
            is_corrected=bool(record.get('PR_NOV', '').replace('0', '')),
            patient_id=patient_obj.id_pk,
            register_id=registry_obj.id_pk
        )
        self.records.append(record_obj)
        return record_obj

    def create_event_obj(self, event, record_obj):
        event_obj = ProvidedEvent(
            id_pk=self._get_next_provided_event_pk(),
            id=event.get('IDCASE', ''),
            term=TERMS.get(event.get('USL_OK'), None),
            kind=KINDS.get(event.get('VIDPOM'), None),
            hospitalization=HOSPITALIZATIONS.get(event.get('EXTR'), None),
            form=FORMS.get(event.get('FOR_POM', ''), None),
            refer_organization=ORGANIZATIONS.get(event.get('NPR_MO'), None),
            organization=ORGANIZATIONS.get(event.get('LPU'), None),
            department=DEPARTMENTS.get(event.get('LPU_1'), None),
            profile=PROFILES.get(event.get('PROFIL'), None),
            is_children_profile=True if event.get('DET', '') == '1' else False,
            anamnesis_number=event.get('NHISTORY', ''),
            examination_rejection=safe_int(event.get('P_OTK', 0)),
            start_date=safe_date(event.get('DATE_1')),
            end_date=safe_date(event.get('DATE_2')),
            initial_disease=DISEASES.get(event.get('DS0'), None),
            basic_disease=DISEASES.get(event.get('DS1'), None),
            payment_method=METHODS.get(event.get('IDSP', ''), None),
            payment_units_number=safe_float(event.get('ED_COL', 0)),
            comment=event.get('COMENTSL', '') or '',
            division=DIVISIONS.get(event.get('PODR'), None),
            treatment_result=RESULTS.get(event.get('RSLT'), None),
            treatment_outcome=OUTCOMES.get(event.get('ISHOD'), None),
            worker_speciality=SPECIALITIES_NEW.get(event.get('PRVS'), None),
            worker_code=event.get('IDDOKT', ''),
            hitech_kind=HITECH_KINDS.get(event.get('VID_HMP'), None),
            hitech_method=HITECH_METHODS.get(event.get('METOD_HMP'), None),
            examination_result=EXAMINATION_RESULTS.get(event.get('RSLT_D'), None),
            ksg_mo=event.get('KSG_MO', ''),
            incoming_sign=safe_int(event.get('P_PER', 0)),
            issue_talon_date=safe_date(event.get('TAL_D', '')),
            planned_hospitalization_date=safe_date(event.get('TAL_P', '')),
            mobile_brigade_sign=safe_int(event.get('VBR', 0)),
            newly_disease_sign=safe_int(event.get('DS1_PR', 0)),
            exam_observation_sign=safe_int(event.get('PR_D_N', 0)),
            record_id=record_obj.id_pk
        )
        self.events.append(event_obj)

        concomitants = event.get('DS2', [])
        if type(concomitants) != list:
            concomitants = [concomitants]
        for code in concomitants:
            if code:
                self.concomitant_list.append(ProvidedEventAdditionalDisease(
                    event_id=event_obj.id_pk, disease=DISEASES.get(code, None),
                    disease_type=1,
                    newly_disease_sign=0))

        complicateds = event.get('DS3', [])
        if type(complicateds) != list:
            complicateds = [complicateds]
        for code in complicateds:
            if code:
                self.complicated_list.append(ProvidedEventAdditionalDisease(
                    event_id=event_obj.id_pk, disease=DISEASES.get(code, None),
                    disease_type=2))

        specials = event.get('OS_SLUCH', [])
        if type(specials) != list:
            specials = [specials]
        for code in specials:
            if code:
                self.special_list.append(ProvidedEventSpecial(
                    event_id=event_obj.id_pk, special=SPECIALS.get(code, None)))

        exam_concomitant_diseases = event.get('DS2_N', [])
        if type(exam_concomitant_diseases) != list:
            exam_concomitant_diseases = [exam_concomitant_diseases]
        for disease in exam_concomitant_diseases:
            self.concomitant_list.append(ProvidedEventAdditionalDisease(
                event_id=event_obj.id_pk,
                disease=DISEASES.get(disease.get('DS2'), None),
                disease_type=1,
                newly_disease_sign=safe_int(disease.get('DS2_PR', 0))
            ))

        medicines = event.get('LEKPREP', [])
        if type(medicines) != list:
            medicines = [medicines]
        for medicine in medicines:
            self.medicine_list.append(ProvidedEventMedicine(
                event_id=event_obj.id_pk,
                medicine=MEDICINES.get(medicine.get('CODE_LP'), None),
                medicine_name=medicine.get('NAME_LP', None)
            ))

        appointments = event.get('NAZR', [])
        if type(appointments) != list:
            appointments = [appointments]
        appointment_types = {'NAZ_SP': None, 'NAZ_V': None, 'NAZ_PMP': None, 'NAZ_PK': None}
        for direction_type in appointment_types:
            values = event.get(direction_type, [])
            if type(values) != list:
                values = [values]
            appointment_types[direction_type] = values
        for appointment in appointments:
            if appointment in ['1', '2']:
                direction_type = 'NAZ_SP'
            elif appointment == '3':
                direction_type = 'NAZ_V'
            elif appointment in ['4', '5']:
                direction_type = 'NAZ_PMP'
            elif appointment == '6':
                direction_type = 'NAZ_PK'
            values = appointment_types[direction_type]
            for val in values:
                if direction_type == 'NAZ_SP':
                    self.appointment_list.append(ProvidedEventAppointment(
                        event_id=event_obj.id_pk,
                        direction_type=safe_int(appointment),
                        worker_speciality=SPECIALITIES_NEW.get(val, None)
                    ))
                elif direction_type == 'NAZ_V':
                    self.appointment_list.append(ProvidedEventAppointment(
                        event_id=event_obj.id_pk,
                        direction_type=safe_int(appointment),
                        examination_kind=safe_int(val)
                    ))
                elif direction_type == 'NAZ_PMP':
                    self.appointment_list.append(ProvidedEventAppointment(
                        event_id=event_obj.id_pk,
                        direction_type=safe_int(appointment),
                        profile=PROFILES.get(val, None)
                    ))
                elif direction_type == 'NAZ_PK':
                    self.appointment_list.append(ProvidedEventAppointment(
                        event_id=event_obj.id_pk,
                        direction_type=safe_int(appointment),
                        hospital_bed_profile=BED_PROFILES[val]
                    ))
        return event_obj

    def create_service_obj(self, service, event_obj):
        if service['CODE_USL'].startswith('A') or service['CODE_USL'].startswith('B'):
            code = OPERATIONS.get(service['CODE_USL'], CODES[service['CODE_USL']])
        else:
            code = CODES.get(service['CODE_USL'], None)

        service_obj = ProvidedService(
            id_pk=self._get_next_provided_service_pk(),
            id=service.get('IDSERV', ''),
            organization=ORGANIZATIONS.get(service.get('LPU'), None),
            department=DEPARTMENTS.get(service.get('LPU_1'), None),
            division=DIVISIONS.get(service.get('PODR'), None),
            profile=PROFILES.get(service.get('PROFIL'), None),
            is_children_profile=True if service.get('DET', '') == '1' else False,
            start_date=safe_date(service.get('DATE_IN', '')),
            end_date=safe_date(service.get('DATE_OUT', '')),
            basic_disease=DISEASES.get(service.get('DS', ''), None),
            code=code,
            quantity=safe_float(service.get('KOL_USL', 0)),
            tariff=safe_float(service.get('TARIF', 0)),
            invoiced_payment=safe_float(service.get('SUMV_USL', 0)),
            worker_speciality=SPECIALITIES_NEW.get(service.get('PRVS', None)),
            worker_code=service.get('CODE_MD', ''),
            comment=service.get('COMENTU', '') or '',
            incomplete_volume_reason=safe_int(service.get('NPL', '0')),
            examination_rejection=safe_int(service.get('P_OTK', 0)),
            event_id=event_obj.id_pk
        )
        self.services.append(service_obj)
        return service_obj

    def insert_registry(self):
        if self.is_commit:
            with transaction.atomic():
                MedicalRegisterImport.objects.filter(
                    organization=self.registry_set.mo_code,
                    filename=self.registry_set.filename,
                    status_num_id=3
                ).delete()
                MedicalRegisterImport.objects.create(
                    period='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period),
                    organization=self.registry_set.mo_code,
                    filename=self.registry_set.filename,
                    status=u'Принят',
                    status_num_id=6
                )
                MedicalRegister.objects.filter(
                    is_active=True, year=self.registry_set.year, period=self.registry_set.period,
                    organization_code=self.registry_set.mo_code).update(is_active=False)
                MedicalRegister.objects.bulk_create(self.registries)
                Patient.objects.bulk_create(set(self.patients))
                MedicalRegisterRecord.objects.bulk_create(self.records)
                ProvidedEvent.objects.bulk_create(self.events)
                ProvidedEventAdditionalDisease.objects.bulk_create(self.concomitant_list)
                ProvidedEventAdditionalDisease.objects.bulk_create(self.complicated_list)
                ProvidedEventSpecial.objects.bulk_create(self.special_list)
                ProvidedEventMedicine.objects.bulk_create(self.medicine_list)
                ProvidedEventAppointment.objects.bulk_create(self.appointment_list)
                ProvidedService.objects.bulk_create(self.services)
                MedicalRegister.objects.filter(
                    pk__in=[rec.pk for rec in self.registries]
                ).update(status=MedicalRegisterStatus.objects.get(pk=6))

    def insert_import_message(self):
        if self.is_commit:
            MedicalRegisterImport.objects.filter(
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status_num_id=2
            ).delete()
            MedicalRegisterImport.objects.create(
                period='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period),
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status=u'Импорт',
                status_num_id=3
            )

    def insert_error_message(self):
        if self.is_commit:
            MedicalRegisterImport.objects.filter(
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status_num_id=3
            ).delete()
            MedicalRegisterImport.objects.create(
                period='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period),
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status=u'Не пройден ФЛК',
                status_num_id=4
            )

    def insert_overvolume_message(self):
        if self.is_commit:
            MedicalRegisterImport.objects.filter(
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status_num_id=3
            ).delete()
            MedicalRegisterImport.objects.create(
                period='{0}-{1}-01'.format(self.registry_set.year, self.registry_set.period),
                organization=self.registry_set.mo_code,
                filename=self.registry_set.filename,
                status=u'Сверхобъёмы',
                status_num_id=5
            )

    def _get_next_patient_pk(self):
        if not self.is_commit:
            return 1
        if len(self._patient_pk_list) == 0:
            self._patient_pk_list = self._get_pk("select nextval('patient_seq')"
                                                 "from generate_series(0, 100)")
        return self._patient_pk_list.pop()

    def _get_next_medical_register_pk(self):
        if not self.is_commit:
            return 1
        if len(self._register_pk_list) == 0:
            self._register_pk_list = self._get_pk("select nextval('medical_register_seq')"
                                                  "from generate_series(0, 10)")
        return self._register_pk_list.pop()

    def _get_next_medical_register_record_pk(self):
        if not self.is_commit:
            return 1
        if len(self._record_pk_list) == 0:
            self._record_pk_list = self._get_pk("select nextval('medical_register_record_seq')"
                                                "from generate_series(0, 10)")
        return self._record_pk_list.pop()

    def _get_next_provided_event_pk(self):
        if not self.is_commit:
            return 1
        if len(self._event_pk_list) == 0:
            self._event_pk_list = self._get_pk("select nextval('provided_event_seq')"
                                               "from generate_series(0, 100)")
        return self._event_pk_list.pop()

    def _get_next_provided_service_pk(self):
        if not self.is_commit:
            return 1
        if len(self._service_pk_list) == 0:
            self._service_pk_list = self._get_pk("select nextval('provided_service_seq')"
                                                 "from generate_series(0, 100)")
        return self._service_pk_list.pop()

    def _get_pk(self, query):
        self.cursor.execute(query, [])
        pk = self.cursor.fetchall()
        return list(reversed([rec[0] for rec in pk]))

