#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection

from medical_service_register.path import REGISTRY_IMPORT_DIR, TEMP_DIR, \
    FLC_DIR, OUTBOX_DIR, OUTBOX_SUCCESS, REGISTRY_PROCESSING_DIR
from main.models import MedicalRegister, SERVICE_XML_TYPES, Gender, Patient, \
    MedicalRegisterRecord
from registry_import.validation import get_person_patient_validation, \
    get_policy_patient_validation, get_record_validation, \
    get_event_validation, get_event_special_validation, \
    get_complicated_disease_validation, get_concomitant_disease_validation, \
    get_service_validation
from registry_import.xml_parser import XmlLikeFileReader
from helpers import xml_writer
from file_handler.funcs import get_outbox_dict, move_files_to_process, \
    move_files_to_archive
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
    for rec in patients_list:
        patient = Patient(
            pk=rec['pk'],
            id=rec.get('ID_PAC', ''),
            last_name=rec.get('FAM', '').upper(),
            first_name=rec.get('IM', '').upper(),
            middle_name=rec.get('OT', '').upper(),
            birthdate=rec.get('DR', ''),
            snils=rec.get('SNILS', ''),
            birthplace=rec.get('MR', ''),
            gender=GENDERS.get(rec.get('W'), None),
            person_id_type=PERSON_ID_TYPES.get(rec.get('DOCTYPE'), None),
            person_id_series=rec.get('DOCSER', ''),
            person_id_number=rec.get('DOCNUM', ''),
            weight=rec.get('VNOV_D', ''),
            residence=rec.get('OKATOP', ''),
            registration=rec.get('OKATOG', ''),
            comment=rec.get('COMENTP', ''),
            agent_last_name=rec.get('FAM_P', '').upper(),
            agent_first_name=rec.get('IM_P', '').upper(),
            agent_middle_name=rec.get('OT_P', '').upper(),
            agent_birthdate=rec.get('DR_P'),
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
            pk=rec['pk'],
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
        event = MedicalRegisterRecord(
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
            division=DIVISIONS.get(rec.get('PODR', ''), None),
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
    pass


def main():
    outbox = get_outbox_dict(OUTBOX_DIR)
    files = os.listdir(REGISTRY_IMPORT_DIR)
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    for organization in registries:
        files = registries[organization]
        move_files_to_process(files)

    for organization in registries:
        if not is_files_completeness(registries[organization]):
            #send_error_file(OUTBOX_DIR, registry, u'Не полный пакет файлов')
            continue

        registry_list = registries[organization]
        new_registries_pk = []
        patients = {}
        fatal_error = False

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

        person_filename = get_person_filename(registry_list)
        patient_path = os.path.join(REGISTRY_IMPORT_DIR, person_filename)
        patient_file = XmlLikeFileReader(patient_path)

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
                #send_error_file(OUTBOX_DIR, registry, files_errors[registry])
                continue

            services_errors = []
            _type, organization_code, year, period = get_registry_info(registry)

            if current_year \
                    and current_period \
                    and current_year != year \
                    and current_period != period:

                raise ValueError('Different periods in one regsitry')

            else:
                current_year = year
                current_period = period

            registry_type = registry_types.get(_type.lower())

            if registry_pk_list:
                registry_pk = registry_pk_list.pop()
            else:
                registry_pk_list = get_next_medical_register_pk()
                registry_pk = registry_pk_list.pop()

            service_path = os.path.join(REGISTRY_IMPORT_DIR, registry)
            service_file = XmlLikeFileReader(service_path)

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

                    old_registries = MedicalRegister.objects.filter(
                        year=current_year,
                        period=current_period,
                        is_active=True,
                        organization_code=organization_code)

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
                         'NOVOR':  item['PACIENT']['NOVOR'], })

                    policy = raw_policy.get_dict()
                    new_patient.update(policy)
                    new_record['patient_id'] = new_patient.get('pk', None)

                    new_patient_list.append(new_patient)
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
                        new_event_list.append(new_event)

                        for concomitant in item['DS2'] or []:
                            raw_concomitant = get_concomitant_disease_validation(concomitant)
                            new_concomitant = raw_concomitant.get_dict()
                            new_concomitant['event_id'] = new_event['pk']
                            new_concomitant_list.append(new_concomitant)

                            services_errors += handle_errors(
                                raw_concomitant.errors() or [], parent='SLUCH',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['ISCASE']
                            )

                        for complicated in item['DS3'] or []:
                            raw_complicated = get_complicated_disease_validation(complicated)
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
                            new_service_list.append(new_service)

                            services_errors += handle_errors(
                                raw_service.errors() or [], parent='USL',
                                record_uid=new_record['N_ZAP'],
                                event_uid=new_event['IDCASE'],
                                service_uid=new_service['IDSERV']
                            )

            if services_errors:
                registry_has_errors = True
                errors_files.append("V%s" % registry)
                hflk = xml_writer.Xml(TEMP_DIR+"V%s" % registry)
                hflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
                hflk.start('FLK_P')
                hflk.put('FNAME', "V%s" % registry[:-4])
                hflk.put('FNAME_I', '%s' % registry[:-4])

                for rec in services_errors:
                    hflk.start('PR')
                    hflk.put('OSHIB', rec[1])
                    hflk.put('IM_POL', rec[3])
                    hflk.put('BASE_EL', rec[2])
                    hflk.put('N_ZAP', rec[4])
                    hflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                    hflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                    hflk.put('COMMENT', rec[7].encode('cp1251'))
                    hflk.end('PR')

                hflk.end('FLK_P')
                hflk.close()

            if patients_errors:
                registry_has_errors = True
                errors_files.append("V%s" % person_filename)
                lflk = xml_writer.Xml(TEMP_DIR+"V%s" % person_filename)
                lflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
                lflk.start('FLK_P')
                lflk.put('FNAME', "V%s" % person_filename[:-4])
                lflk.put('FNAME_I', '%s' % person_filename[:-4])

                for rec in patients_errors:
                    lflk.start('PR')
                    lflk.put('OSHIB', rec[1])
                    lflk.put('IM_POL', rec[3])
                    lflk.put('BASE_EL', rec[2])
                    lflk.put('N_ZAP', rec[4])
                    lflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                    lflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                    lflk.put('COMMENT', rec[7].encode('cp1251'))
                    lflk.end('PR')

                lflk.end('FLK_P')
                lflk.close()

        if registry_has_errors:
            print u'Ошибки ФЛК'

            zipname = TEMP_DIR+'VM%sS28002_%s.zip' % (
                organization_code, person_filename[person_filename.index('_')+1:-4]
            )

            with ZipFile(zipname, 'w') as zipfile:
                for filename in errors_files:
                    zipfile.write(TEMP_DIR+filename, filename, 8)
                    os.remove(TEMP_DIR+filename)

            shutil.copy2(zipname, FLC_DIR)

            copy_path = '%s%s %s' % (OUTBOX_DIR, organization_code,
                                     outbox[organization_code])

            if os.path.exists(copy_path):
                shutil.copy2(zipname, copy_path)

            os.remove(zipname)
        else:
            print u'ФЛК пройден'




        print organization, current_year, current_period

    for rec in patients_errors:
        for k in rec:
            print k, rec[k],
        print

    print
    for rec in services_errors:
        for k in rec:
            print k, rec[k],
        print


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()