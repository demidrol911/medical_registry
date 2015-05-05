#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection

from medical_service_register.path import REGISTRY_IMPORT_DIR, TEMP_DIR, \
    FLC_DIR, OUTBOX_DIR, OUTBOX_SUCCESS, REGISTRY_PROCESSING_DIR
from main.models import MedicalRegister, SERVICE_XML_TYPES, Gender, Patient, \
    MedicalRegisterRecord, ProvidedEventConcomitantDisease, \
    ProvidedEventComplicatedDisease, ProvidedEventSpecial, \
    ProvidedService, ProvidedEvent, MedicalRegisterStatus, MedicalServiceVolume
from registry_import.validation import get_person_patient_validation, \
    get_policy_patient_validation, get_record_validation, \
    get_event_validation, get_event_special_validation, \
    get_complicated_disease_validation, get_concomitant_disease_validation, \
    get_service_validation
from registry_import.xml_parser import XmlLikeFileReader
from helpers import xml_writer
from file_handler.funcs import get_outbox_dict, move_files_to_process, \
    move_files_to_archive, send_error_file
from registry_import.validation import GENDERS, PERSON_ID_TYPES, \
    POLICY_TYPES, DEPARTMENTS, ORGANIZATIONS, TERMS, KINDS, FORMS, \
    HOSPITALIZATIONS, PROFILES, OUTCOMES, RESULTS, SPECIALITIES_OLD, \
    SPECIALITIES_NEW, METHODS, TYPES, FAILURE_CUASES, DISEASES, DIVISIONS, \
    SPECIALS, CODES, HITECH_KINDS, HITECH_METHODS, EXAMINATION_RESULTS
from main.funcs import safe_int, safe_date, safe_float
import os
import re
import shutil
from datetime import datetime
from collections import defaultdict
from zipfile import ZipFile

cursor = connection.cursor()

ERROR_MESSAGE_BAD_FILENAME = u'Имя файла не соответствует регламентированному'
HOSPITAL_VOLUME_EXCLUSIONS = ('098977', '018103', '98977', '18103')
DAY_HOSPITAL_VOLUME_EXCLUSIONS = ('098710', '098711', '098712', '098715',
                                  '098770', '98710', '98711', '98712', '98715',
                                  '98770', '098770', '098770', '198770'
)
HOSPITAL_VOLUME_MO_EXCLUSIONS = ('280013', )
DAY_HOSPITAL_MO_EXCLUSIONS = ('280029', )

filename_pattern = r'^(l|h|t|dp|dv|do|ds|du|df|dd|dr)m?(28\d{4})s28002_(\d{2})(\d{2})\d+.xml'
registry_regexp = re.compile(filename_pattern, re.IGNORECASE)

gender_list = Gender.objects.all().values_list('code', flat=True)


def get_registry_type_dict(types_tuple):
    return dict((y, x) for x, y in types_tuple)


def is_files_completeness(files):
    check = 0

    for rec in files:
        matching = registry_regexp.match(rec)

        if matching:

            if matching.group(1).lower() in ('l', 'h'):
                check += 1

    return True if check == 2 else False


def get_registry_files_dict(files):
    registries = defaultdict(list)
    errors = defaultdict(list)

    for _file in files:
        matching = registry_regexp.match(_file)
        if matching:
            file_type, organization, year, period = matching.groups()

            registries[organization].append(_file)
        else:
            errors[_file] = ERROR_MESSAGE_BAD_FILENAME

    return registries, errors


def get_patient_registry(registries):
    for registry in registries:
        matching = registry_regexp.match(registry)
        if matching:
            if matching.group(1).lower() == 'l':
                return registry


def get_registry_info(registry):
    matching = registry_regexp.match(registry)

    return matching.groups()


def validate_person_patient_data(item):
    patient = dict(
        id=item['ID_PAC'],
        last_name=item['FAM'].upper() if item['FAM'] else None,
        first_name=item['IM'].upper() if item['IM'] else None,
        middle_name=item['OT'].upper() if item['OT'] else None,
        birthdate=item['DR'],
        snils=item['SNILS'],
        birthplace=item['MR'],
        gender=item['W'],
        person_id_type=item['DOCTYPE'],
        person_id_series=item['DOCSER'],
        person_id_number=item['DOCNUM'],
        weight=item['VNOV_D'],
        residence=item['OKATOP'],
        registration=item['OKATOG'],
        comment=item['COMENTP'],
        agent_last_name=item['FAM_P'].upper() if item['FAM_P'] else None,
        agent_first_name=item['IM_P'].upper() if item['IM_P'] else None,
        agent_middle_name=item['OT_P'].upper() if item['OT_P'] else None,
        agent_birthdate=item['DR_P'],
        agent_gender=item['W_P'], )

    return patient


def get_policy_patient_data(item):
    patient = dict(
        insurance_policy_type=item['PACIENT']['VPOLIS'],
        insurance_policy_series=item['PACIENT']['SPOLIS'],
        insurance_policy_number=item['PACIENT']['NPOLIS'],
        newborn_code=item['PACIENT']['NOVOR']
    )

    return patient


def get_registry_data(record):
    pass


def get_next_patient_pk():
    query = ("select nextval('patient_seq')"
             "from generate_series(0, 512)")
    cursor.execute(query, [])
    pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in pk]))


def get_next_medical_register_pk():
    query = ("select nextval('medical_register_seq')"
             "from generate_series(0, 512)")
    cursor.execute(query, [])
    pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in pk]))


def get_next_medical_register_record_pk():
    query = ("select nextval('medical_register_record_seq')"
             "from generate_series(0, 512)")
    cursor.execute(query, [])
    pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in pk]))


def get_next_provided_event_pk():
    query = ("select nextval('provided_event_seq')"
             "from generate_series(0, 1024)")
    cursor.execute(query, [])
    pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in pk]))


def get_next_provided_service_pk():
    query = ("select nextval('provided_service_seq')"
             "from generate_series(0, 512)")
    cursor.execute(query, [])
    pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in pk]))


def get_person_filename(file_list):
    for _file in file_list:
        if _file.lower().startswith('lm'):
            return _file


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


def get_patients_objects(patients_list):
    objects = []
    pk = []
    for rec in patients_list:
        pk.append(rec['pk'])
        patient = Patient(
            id_pk=rec['pk'],
            id=rec.get('ID_PAC', ''),
            last_name=rec.get('FAM', '').upper(),
            first_name=rec.get('IM', '').upper(),
            middle_name=rec.get('OT', '').upper(),
            birthdate=safe_date(rec.get('DR', None)),
            snils=rec.get('SNILS', ''),
            birthplace=rec.get('MR', ''),
            gender=GENDERS.get(rec.get('W'), None),
            person_id_type=PERSON_ID_TYPES.get(rec.get('DOCTYPE'), None),
            person_id_series=rec.get('DOCSER', ''),
            person_id_number=rec.get('DOCNUM', ''),
            weight=safe_float(rec.get('VNOV_D', 0)),
            okato_residence=rec.get('OKATOP', ''),
            okato_registration=rec.get('OKATOG', ''),
            comment=rec.get('COMENTP', ''),
            agent_last_name=rec.get('FAM_P', '').upper(),
            agent_first_name=rec.get('IM_P', '').upper(),
            agent_middle_name=rec.get('OT_P', '').upper(),
            agent_birthdate=safe_date(rec.get('DR_P', None)),
            agent_gender=GENDERS.get(rec.get('W_P'), None),
            newborn_code=rec.get('NOVOR', ''),
            insurance_policy_type=POLICY_TYPES.get(rec.get('VPOLIS'), None),
            insurance_policy_series=rec.get('SPOLIS', ''),
            insurance_policy_number=rec.get('NPOLIS', ''), )
        objects.append(patient)

    return objects


def get_records_objects(records_list):
    objects = []

    for rec in records_list:
        record = MedicalRegisterRecord(
            id_pk=rec['pk'],
            id=rec.get('N_ZAP'),
            is_corrected=bool(rec.get('PR_NOV', '').replace('0', '')),
            patient_id=rec.get('patient_id', None),
            register_id=rec.get('register_id', None)
        )

        objects.append(record)
    return objects


def get_events_objects(events_list):
    objects = []
    for rec in events_list:

        division = (rec.get('PODR') or '')[:3]
        if division:
            if len(division) < 3:
                division = ('0' * (3 - len(division))) + division

        event = ProvidedEvent(
            id=rec.get('IDCASE', ''),
            id_pk=rec['pk'],
            term=TERMS.get(rec.get('USL_OK'), None),
            kind=KINDS.get(rec.get('VIDPOM'), None),
            hospitalization=HOSPITALIZATIONS.get(rec.get('EXTR'), None),
            form=FORMS.get(rec.get('FOR_POM', ''), None),
            refer_organization=ORGANIZATIONS.get(rec.get('NPR_MO'), None),
            organization=ORGANIZATIONS.get(rec.get('LPU'), None),
            department=DEPARTMENTS.get(rec.get('LPU_1'), None),
            profile=PROFILES.get(rec.get('PROFIL'), None),
            is_children_profile=True if rec.get('DET', '') == '1' else False,
            anamnesis_number=rec.get('NHISTORY', ''),
            examination_rejection=safe_int(rec.get('P_OTK', 0)),
            start_date=safe_date(rec.get('DATE_1')),
            end_date=safe_date(rec.get('DATE_2')),
            initial_disease=DISEASES.get(rec.get('DS0'), None),
            basic_disease=DISEASES.get(rec.get('DS1'), None),
            payment_method=METHODS.get(rec.get('IDSP', ''), None),
            payment_units_number=safe_float(rec.get('ED_COL', 0)),
            comment=rec.get('COMENTSL', ''),
            division=DIVISIONS.get(division, None),
            treatment_result=RESULTS.get(rec.get('RSLT'), None),
            treatment_outcome=OUTCOMES.get(rec.get('ISHOD'), None),
            worker_speciality=SPECIALITIES_NEW.get(rec.get('PRVS'), None),
            worker_code=rec.get('IDDOKT', ''),
            hitech_kind=HITECH_KINDS.get(rec.get('VID_HMP'), None),
            hitech_method=HITECH_METHODS.get(rec.get('METOD_HMP'), None),
            examination_result=EXAMINATION_RESULTS.get(rec.get('RSLT_D'), None),
            record_id=rec.get('record_id'))
        objects.append(event)

    return objects


def get_concomitant_diseases_objects(disease_list):
    objects = []
    for rec in disease_list:
        disease = ProvidedEventConcomitantDisease(
            event_id=rec['event_id'],
            disease=DISEASES.get(rec.get('DS2'), None)
        )

        objects.append(disease)

    return objects


def get_concomitant_diseases_objects(disease_list):
    objects = []
    for rec in disease_list:
        disease = ProvidedEventConcomitantDisease(
            event_id=rec['event_id'],
            disease=DISEASES.get(rec.get('DS2'), None)
        )

        objects.append(disease)

    return objects


def get_complicated_diseases_objects(disease_list):
    objects = []
    for rec in disease_list:
        disease = ProvidedEventComplicatedDisease(
            event_id=rec['event_id'],
            disease=DISEASES.get(rec.get('DS3'), None)
        )

        objects.append(disease)

    return objects


def get_specials_objects(specials_list):
    objects = []
    for rec in specials_list:
        special = ProvidedEventSpecial(
            event_id=rec['event_id'],
            special=SPECIALS.get(rec.get('OS_SLUCH'), None)
        )

        objects.append(special)

    return objects


def get_services_objects(services_list):
    objects = []
    for rec in services_list:
        code = rec['CODE_USL']
        if code:
            code = '0' * (6 - len(code)) + code

        division = (rec.get('PODR') or '')[:3]
        if division:
            if len(division) < 3:
                division = ('0' * (3 - len(division))) + division

        service = ProvidedService(
            id_pk=rec['pk'],
            id=rec.get('IDSERV', ''),
            organization=ORGANIZATIONS.get(rec.get('LPU'), None),
            department=DEPARTMENTS.get(rec.get('LPU_1'), None),
            division=DIVISIONS.get(division, None),
            profile=PROFILES.get(rec.get('PROFIL'), None),
            is_children_profile=True if rec.get('DET', '') == '1' else False,
            start_date=safe_date(rec.get('DATE_IN', '')),
            end_date=safe_date(rec.get('DATE_OUT', '')),
            basic_disease=DISEASES.get(rec.get('DS', ''), None),
            code=CODES.get(code, None),
            quantity=safe_float(rec.get('KOL_USL', 0)),
            tariff=safe_float(rec.get('TARIF', 0)),
            invoiced_payment=safe_float(rec.get('SUMV_USL', 0)),
            worker_speciality=SPECIALITIES_NEW.get(rec.get('PRVS', None)),
            worker_code=rec.get('CODE_MD', ''),
            comment=rec.get('COMENTU', ''),
            event_id=rec['event_id'],
            # intervention=rec.get('VID_VME', ''),
        )

        objects.append(service)

    return objects


def main():
    outbox = get_outbox_dict(OUTBOX_DIR)
    files = os.listdir(REGISTRY_IMPORT_DIR)
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    for organization in registries:
        files = registries[organization]
        move_files_to_process(files)

    for organization in registries:
        print organization
        if not is_files_completeness(registries[organization]):
            send_error_file(OUTBOX_DIR, registry, u'Не полный пакет файлов')
            continue

        registry_list = registries[organization]
        new_registries_pk = []
        patients = {}
        fatal_error = False
        registry_has_errors = False
        has_surgery = False
        has_hospitalization = False
        has_insert = True

        current_year = current_period = None

        patient_pk_list = []
        registry_pk_list = []
        record_pk_list = []
        event_pk_list = []
        service_pk_list = []

        new_patient_list = []
        registries_objects = []
        new_record_list = []
        new_event_list = []
        new_concomitant_list = []
        new_complicated_list = []
        new_special_list = []
        new_service_list = []

        patients_errors = []
        errors_files = []

        hospital_volume_service = set()
        day_hospital_volume_service = set()

        copy_path = '%s%s %s' % (OUTBOX_DIR, organization,
                                 outbox[organization])

        person_filename = get_person_filename(registry_list)
        patient_path = os.path.join(REGISTRY_PROCESSING_DIR, person_filename)
        patient_file = XmlLikeFileReader(patient_path)
        temp_pk = []
        for item in patient_file.find(tags=('PERS', )):
            if patient_pk_list:
                patient_pk = patient_pk_list.pop()
            else:
                patient_pk_list = get_next_patient_pk()
                patient_pk = patient_pk_list.pop()

            item['pk'] = patient_pk

            if item['ID_PAC'] in patients:
                patients_errors.append(
                    set_error(code='904', field='ID_PAC', parent='PERS',
                              record_uid='', event_uid='', service_uid='',
                              comment=u'Дубликат идентификатора '
                                      u'пациента %s' % item['ID_PAC']))
                fatal_error = True

            else:
                patients[item['ID_PAC']] = item

        print len(patients)
        registry_list.remove(person_filename)

        if fatal_error:
            registry_list = []

        for registry in registry_list:

            if registry in files_errors:
                # send_error_file(OUTBOX_DIR, registry, files_errors[registry])
                continue

            services_errors = []
            _type, organization_code, year, period = get_registry_info(registry)

            print organization, current_year, current_period, _type

            if current_year \
                    and current_period \
                    and current_year != '20' + year \
                    and current_period != period:

                raise ValueError('Different periods in one regsitry')

            else:
                current_year = '20' + year
                current_period = period

            old_register_status = MedicalRegister.objects.filter(
                is_active=True, year=current_year,
                period=current_period,
                organization_code=organization_code
            ).values_list('status_id', flat=True).distinct()

            print old_register_status

            if old_register_status and old_register_status[0] in (4, 6, 8):
                has_insert = False
                continue

            registry_type = registry_types.get(_type.lower())
            print type(registry_type), registry_type

            if registry_pk_list:
                registry_pk = registry_pk_list.pop()
            else:
                registry_pk_list = get_next_medical_register_pk()
                registry_pk = registry_pk_list.pop()

            service_path = os.path.join(REGISTRY_PROCESSING_DIR, registry)
            service_file = XmlLikeFileReader(service_path)

            try:
                volume = MedicalServiceVolume.objects.get(
                    organization__code=organization_code,
                    date='{0}-{1}-01'.format(current_year, current_period))
            except:
                volume = None

            invoiced = False

            for item in service_file.find(tags=('SCHET', 'ZAP', )):
                if 'NSCHET' in item:
                    invoiced = True
                    invoice = dict(id=item['NSCHET'], date=item['DSCHET'])

                    new_registry = MedicalRegister(pk=registry_pk,
                                                   timestamp=datetime.now(),
                                                   type=registry_type,
                                                   filename=registry,
                                                   organization_code=organization_code,
                                                   is_active=True,
                                                   year=current_year,
                                                   period=current_period,
                                                   status_id=12,
                                                   invoice_date=invoice['date'])

                    new_registries_pk.append(registry_pk)
                    registries_objects.append(new_registry)

                if 'N_ZAP' in item:

                    if record_pk_list:
                        record_pk = record_pk_list.pop()
                    else:
                        record_pk_list = get_next_medical_register_record_pk()
                        record_pk = record_pk_list.pop()

                    item['pk'] = record_pk
                    item['registry_pk'] = registry_pk

                    raw_record = get_record_validation(item)
                    new_record = raw_record.get_dict()

                    patient = item['PACIENT']

                    if not patient:
                        services_errors.append(set_error(
                            '902', field='', parent='PACIENT',
                            record_uid=new_record['N_ZAP'],
                            comment=u'Нет сведений о пациенте'))
                        continue

                    patient = patients.get(item['PACIENT']['ID_PAC'])

                    if patient:
                        raw_patient = get_person_patient_validation(patient)
                        new_patient = raw_patient.get_dict()

                        patients_errors += \
                            handle_errors(
                                raw_patient.errors() or [], parent='PERS',
                                record_uid=new_record['N_ZAP'])
                    else:
                        services_errors.append(set_error(
                            '902', field='ID_PAC', parent='PACIENT',
                            record_uid=new_record['N_ZAP'],
                            comment=u'Нет сведений о пациенте в файле пациентов'
                        ))
                        new_patient = {}

                    raw_policy = get_policy_patient_validation(
                        {'VPOLIS': item['PACIENT']['VPOLIS'],
                         'SPOLIS': item['PACIENT']['SPOLIS'],
                         'NPOLIS': item['PACIENT']['NPOLIS'],
                         'NOVOR': item['PACIENT']['NOVOR'], })

                    policy = raw_policy.get_dict()
                    new_patient.update(policy)
                    new_record['patient_id'] = new_patient.get('pk', None)

                    # if new_patient not in new_patient_list:
                    new_patient_list.append(new_patient)

                    #if new_record not in new_record_list:
                    new_record_list.append(new_record)

                    #print record

                    services_errors += handle_errors(
                        raw_record.errors() or [], parent='ZAP',
                        record_uid=new_record['N_ZAP'])

                    services_errors += handle_errors(
                        raw_policy.errors() or [], parent='PACIENT',
                        record_uid=new_record['N_ZAP'])

                    if type(item['SLUCH']) == list:
                        events = item['SLUCH']
                    else:
                        events = [item['SLUCH']]

                    for event in events:
                        if event_pk_list:
                            event_pk = event_pk_list.pop()
                        else:
                            event_pk_list = get_next_provided_event_pk()
                            event_pk = event_pk_list.pop()

                        raw_event = get_event_validation(event, registry_type)
                        new_event = raw_event.get_dict()
                        new_event['pk'] = event_pk
                        new_event['record_id'] = new_record['pk']
                        new_event_list.append(new_event)

                        if new_event.get('USL_OK', '') == '1' and _type == 'H':
                            has_hospitalization = True

                        if event['DS2'] and type(event['DS2']) != list:
                            concomitants = [event['DS2']]
                        else:
                            concomitants = event['DS2'] or []

                        for concomitant in concomitants:
                            raw_concomitant = get_concomitant_disease_validation(
                                concomitant)
                            new_concomitant = raw_concomitant.get_dict()
                            new_concomitant['event_id'] = new_event['pk']
                            new_concomitant_list.append(new_concomitant)

                            services_errors += handle_errors(
                                raw_concomitant.errors() or [], parent='SLUCH',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['IDCASE']
                            )

                        if event['DS3'] and type(event['DS3']) != list:
                            complicateds = [event['DS3']]
                        else:
                            complicateds = event['DS3'] or []

                        for complicated in complicateds or []:
                            raw_complicated = get_complicated_disease_validation(
                                complicated)
                            new_complicated = raw_complicated.get_dict()
                            new_complicated['event_id'] = new_event['pk']
                            new_complicated_list.append(new_complicated)

                            services_errors += handle_errors(
                                raw_complicated.errors() or [], parent='SLUCH',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['IDCASE']
                            )

                        for special in item['SPECIAL'] or []:
                            raw_special = get_event_special_validation(special)
                            new_special = raw_special.get_dict()
                            new_special['event_id'] = new_event['pk']
                            new_special_list.append(new_special)

                            services_errors += handle_errors(
                                raw_special.errors() or [], parent='SLUCH',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['IDCASE']
                            )

                        services_errors += handle_errors(
                            raw_event.errors() or [], parent='SLUCH',
                            record_uid=new_record['N_ZAP'],
                            event_uid=new_event['IDCASE']
                        )

                        if not event['USL']:
                            services_errors.append(set_error(
                                '902', field='USL', parent='SLUCH',
                                record_uid=new_record['N_ZAP'],
                                event_uid=event['IDCASE'],
                                comment=u'Отсутствуют услуги в случае'))
                            continue

                        if type(event['USL']) == list:
                            services = event['USL']
                        else:
                            services = [event['USL']]

                        for service in services:
                            if service_pk_list:
                                service_pk = service_pk_list.pop()
                            else:
                                service_pk_list = get_next_provided_service_pk()
                                service_pk = service_pk_list.pop()

                            raw_service = get_service_validation(service,
                                                                 event=event)
                            new_service = raw_service.get_dict()
                            new_service['pk'] = service_pk
                            new_service['event_id'] = new_event['pk']
                            new_service_list.append(new_service)
                            #print '*', _type


                            #if new_event.get('USL_OK',
                            #                '') == '1' and new_service.get(
                            #     'CODE_USL', '').startswith(
                            #      'A') and _type == 'H':
                            #  has_surgery = True


                            services_errors += handle_errors(
                                raw_service.errors() or [], parent='USL',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['IDCASE'],
                                service_uid=new_service['IDSERV']
                            )

                            if new_event.get('USL_OK', '') == '1' \
                                    and new_service[
                                        'CODE_USL'] not in HOSPITAL_VOLUME_EXCLUSIONS\
                                    and not new_service['CODE_USL'].startswith('A'):
                                hospital_volume_service.add(new_event['IDCASE'])

                            if new_event.get('USL_OK', '') == '2' \
                                    and new_service[
                                        'CODE_USL'] not in DAY_HOSPITAL_VOLUME_EXCLUSIONS\
                                    and not new_service['CODE_USL'].startswith('A'):

                                day_hospital_volume_service.add(
                                    new_event['IDCASE'])

            """
            if not has_surgery and has_hospitalization:
                services_errors.append(set_error(
                    '902', field='', parent='',
                    record_uid='',
                    comment=u'Нет сведений об операциях (услуги класса А) в круглосуточном стационаре'
                ))
                print u'Нет операции'
            """

            if services_errors:
                registry_has_errors = True
                errors_files.append("V%s" % registry)
                hflk = xml_writer.Xml(TEMP_DIR + "V%s" % registry)
                hflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
                hflk.start('FLK_P')
                hflk.put('FNAME', "V%s" % registry[:-4])
                hflk.put('FNAME_I', '%s' % registry[:-4])

                for rec in services_errors:
                    hflk.start('PR')
                    hflk.put('OSHIB', rec['code'])
                    hflk.put('IM_POL', rec['field'])
                    hflk.put('BASE_EL', rec['parent'])
                    hflk.put('N_ZAP', rec['record_uid'])
                    hflk.put('IDCASE',
                             rec.get('event_uid', '').encode('cp1251'))
                    hflk.put('IDSERV',
                             rec.get('service_uid', '').encode('cp1251'))
                    hflk.put('COMMENT', rec['comment'].encode('cp1251'))
                    hflk.end('PR')

                hflk.end('FLK_P')
                hflk.close()

        if patients_errors:
            registry_has_errors = True
            errors_files.append("V%s" % person_filename)
            print '#', errors_files
            lflk = xml_writer.Xml(TEMP_DIR + "V%s" % person_filename)
            lflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
            lflk.start('FLK_P')
            lflk.put('FNAME', "V%s" % person_filename[:-4])
            lflk.put('FNAME_I', '%s' % person_filename[:-4])

            for rec in patients_errors:
                lflk.start('PR')
                lflk.put('OSHIB', rec['code'])
                lflk.put('IM_POL', rec['field'])
                lflk.put('BASE_EL', rec['parent'])
                lflk.put('N_ZAP', rec['record_uid'])
                lflk.put('IDCASE', rec.get('event_uid', '').encode('cp1251'))
                lflk.put('IDSERV', rec.get('service_uid', '').encode('cp1251'))
                lflk.put('COMMENT', rec['comment'].encode('cp1251'))
                lflk.end('PR')

            lflk.end('FLK_P')
            lflk.close()

        over_volume = volume and (len(hospital_volume_service) > volume.hospital
                                  or len(day_hospital_volume_service) > volume.day_hospital)

        if over_volume and organization not in HOSPITAL_VOLUME_MO_EXCLUSIONS \
                and organization not in DAY_HOSPITAL_MO_EXCLUSIONS:

            has_insert = False
            message_file = open(TEMP_DIR+u'Ошибка обработки {0}  - сверхобъёмы.txt'.encode('cp1251').format(organization), 'w')
            message = (u'ОАО «МСК «Дальмедстрах» сообщает, что в соответствии с п.6 статьи 39 \n'
                       u'Федерального закона № 326-ФЗ от 29.11.2010г. и п. 5.3.2. Приложения № 33 \n'
                       u'к тарифному соглашению в сфере обязательного медицинского страхования Амурской области \n'
                       u'на 2015 год, страховая компания принимает реестры счетов и счета на оплату \n'
                       u'медицинской помощи в пределах объемов, утвержденных решением комиссии по \n'
                       u'разработке территориальной программы обязательного медицинского страхования Амурской области.\n'
                       u'\n'
                       u'В текущем реестре выполнено:\n'
                       )
            message += \
                (u'Круглосуточный стационар - {0}, запланировано решением тарифной комисси - {1}\n'.format(
                 len(hospital_volume_service), volume.hospital)) \
                if len(hospital_volume_service) > volume.hospital \
                else u''
            message += \
                (u'Дневной стационар - {0}, запланировано решением тарифной комисси - {1}\n'.format(
                 len(day_hospital_volume_service), volume.day_hospital)) \
                if len(day_hospital_volume_service) > volume.day_hospital \
                else u''
            message += u'Вопросы распределения объёмов находятся в компетенции Тарифной Комиссии\n'
            print len(hospital_volume_service), volume.hospital, len(day_hospital_volume_service), volume.day_hospital
            message_file.write(message.encode('cp1251'))
            message_file.close()

        if has_insert:
            if registry_has_errors:
                print u'Ошибки ФЛК'

                zipname = TEMP_DIR + 'VM%sS28002_%s.zip' % (
                    organization_code,
                    person_filename[person_filename.index('_') + 1:-4]
                )

                print errors_files
                with ZipFile(zipname, 'w') as zipfile:
                    for filename in errors_files:
                        zipfile.write(TEMP_DIR + filename, filename, 8)
                        os.remove(TEMP_DIR + filename)

                shutil.copy2(zipname, FLC_DIR)

                if os.path.exists(copy_path):
                    shutil.copy2(zipname, copy_path)

                os.remove(zipname)

            else:
                print u'ФЛК пройден. Вставка данных...'

                MedicalRegister.objects.filter(
                    is_active=True, year=current_year, period=current_period,
                    organization_code=organization_code).update(is_active=False)
                MedicalRegister.objects.bulk_create(registries_objects)
                Patient.objects.bulk_create(
                    set(get_patients_objects(new_patient_list)))
                MedicalRegisterRecord.objects.bulk_create(
                    get_records_objects(new_record_list))
                ProvidedEvent.objects.bulk_create(
                    get_events_objects(new_event_list))
                ProvidedEventConcomitantDisease.objects.bulk_create(
                    get_concomitant_diseases_objects(new_concomitant_list))
                ProvidedEventComplicatedDisease.objects.bulk_create(
                    get_complicated_diseases_objects(new_complicated_list))
                ProvidedEventSpecial.objects.bulk_create(
                    get_specials_objects(new_special_list))
                ProvidedService.objects.bulk_create(
                    get_services_objects(new_service_list))
                MedicalRegister.objects.filter(
                    pk__in=[rec.pk for rec in registries_objects]
                ).update(status=MedicalRegisterStatus.objects.get(pk=1))

                print u'...ок'

                if os.path.exists(copy_path):
                    shutil.copy2(OUTBOX_SUCCESS, copy_path)

        print organization, current_year, current_period

        move_files_to_archive(registry_list + [patient_path])

    try:
        for rec in patients_errors:
            for k in rec:
                print k, rec[k],
            print
    except:
        pass

    print

    try:
        for rec in services_errors:
            for k in rec:
                print k, rec[k],
            print
    except:
        pass


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()