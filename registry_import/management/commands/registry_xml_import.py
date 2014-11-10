#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection

from medical_service_register.path import REGISTRY_IMPORT_DIR
from main.models import MedicalRegister, SERVICE_XML_TYPES, Gender
from registry_import.validation import get_person_patient_validation
from registry_import.validation import get_policy_patient_validation
from registry_import.validation import get_record_validation
from registry_import.xml_parser import XmlLikeFileReader

import os
import re
from datetime import datetime
from collections import defaultdict
import shutil

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
             "from generate_series(0, 512)")
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


def main():

    files = os.listdir(REGISTRY_IMPORT_DIR)
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    #for organization in registries:
    #    files = registries[organization]
    #    move_files_to_process(files)

    for organization in registries:
        if not is_files_completeness(registries[organization]):
            #send_error_file(OUTBOX_DIR, registry, u'Не полный пакет файлов')
            continue

        registry_list = registries[organization]
        patient_dict = {}
        service_dict = {}
        event_dict = {}
        record_dict = {}
        new_registries_pk = []
        patients = {}
        fatal_error = False

        current_year = current_period = None

        patient_pk_list = []
        registry_pk_list = []
        record_pk_list = []

        patients_errors = []

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
                    record = raw_record.get_dict()

                    _patient = item['PACIENT']

                    if not _patient:
                        services_errors.append(set_error(
                            '902', field='', parent='PACIENT',
                            record_uid=record['uid'],
                            comment=u'Нет сведений о пациенте'))
                        continue

                    _patient = patients.get(item['PACIENT']['ID_PAC'])

                    if _patient:
                        raw_patient = get_person_patient_validation(_patient)
                        patient = raw_patient.get_dict()

                        patients_errors += \
                            handle_errors(
                                raw_patient.errors() or [], parent='PERS',
                                record_uid=record['uid'])
                    else:
                        services_errors.append(set_error(
                            '902', field='ID_PAC', parent='PACIENT',
                            record_uid=record['uid'],
                            comment=u'Нет сведений о пациенте в файле пациентов'
                        ))
                        patient = {}

                    raw_policy = get_policy_patient_validation(
                        {'VPOLIS': item['PACIENT']['VPOLIS'],
                         'SPOLIS': item['PACIENT']['SPOLIS'],
                         'NPOLIS': item['PACIENT']['NPOLIS'],
                         'NOVOR':  item['PACIENT']['NOVOR']})

                    policy = raw_policy.get_dict()
                    patient.update(policy)
                    record['patient_id'] = patient.get('pk', None)

                    #print record

                    services_errors += handle_errors(
                        raw_record.errors() or [], parent='ZAP',
                        record_uid=record['uid'])

                    services_errors += handle_errors(
                        raw_policy.errors() or [], parent='PACIENT',
                        record_uid=record['uid'])

                    if type(item['SLUCH']) == list:
                        events = item['SLUCH']
                    else:
                        events = [item['SLUCH']]

                    for event in events:

                        if type(item['USL']) == list:
                            services = item['USL']
                        else:
                            services = [item['USL']]

                        for service in services:
                            pass



        print organization, current_year, current_period

    for rec in patients_errors:
        for k in rec:
            print k, rec[k]
        print

    print
    for rec in services_errors:
        for k in rec:
            print k, rec[k]
        print



class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()