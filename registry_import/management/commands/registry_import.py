#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Max
from tfoms.models import (
    ProvidedEvent, ProvidedService, Patient, ProvidedEventConcomitantDisease,
    ProvidedEventComplicatedDisease, MedicalRegisterRecord, MedicalRegister,
    MedicalRegisterStatus, MedicalOrganization, SERVICE_XML_TYPES,
    SERVICE_XML_TYPE_PERSON, SERVICE_XML_TYPE_REGULAR, Gender)

from django.db import transaction, connection
from helpers.xml_parser import XmlLikeFileReader
from helpers.validation import ValidPatient, ValidRecord, ValidEvent,\
    ValidService, ValidConcomitantDisease, ValidComplicatedDisease
from helpers import xml_writer

import os
import re
from datetime import datetime
from zipfile import ZipFile
from collections import defaultdict
import shutil

cursor = connection.cursor()

OUTBOX_DIR = '//alpha/vipnet/medical_registry/outbox/'
OUTBOX_SUCCESS = u'D:/work/medical_service_register/templates/outcoming_messages/ФЛК пройден.txt'
REGISTER_DIR = "d:/work/register_import_test/"
temp_dir = "d:/work/register_temp/"
flk_dir = "d:/work/medical_register/"
IMPORT_ARCHIVE_DIR = u"d:/work/register_import_archive/"
REGISTER_IN_PROCESS_DIR = u'd:/work/register_import_in_process/'

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


def get_outbox_dict(dir):
    dirs = os.listdir(dir)
    outbox_dict = {}

    for d in dirs:
        t = d.decode('cp1251')
        code, name = t[:6], t[7:]
        outbox_dict[code] = name

    return outbox_dict


def move_files_to_process(files_list):
    for name in files_list:
        shutil.move(os.path.join(REGISTER_DIR, name), REGISTER_IN_PROCESS_DIR)


def move_files_to_archive(files_list):
    for name in files_list:
        if os.path.exists(IMPORT_ARCHIVE_DIR+name):
            os.remove(IMPORT_ARCHIVE_DIR+name)
        shutil.move(REGISTER_IN_PROCESS_DIR+name, IMPORT_ARCHIVE_DIR)


def send_error_file(path='', filename=None, message=''):
    f = open(path+u'Ошибка обработки %s.txt' % filename, 'w')
    f.write(message.encode('utf-8'))
    f.close()


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


def main():

    files = os.listdir(REGISTER_DIR)
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    #for organization in registries:
    #    files = registries[organization]
    #    move_files_to_process(files)

    for organization in registries:
        if not is_files_completeness(registries[organization]):
            #send_error_file(OUTBOX_DIR, registry, u'Не полный пакет файлов')
            continue

        patient_dict = {}
        service_dict = {}
        event_dict = {}
        record_dict = {}
        new_registries_pk = []
        patients = {}

        current_year = current_period = None

        patient_pk_list = []
        registry_pk_list = []
        record_pk_list = []

        for registry in registries[organization]:
            if registry in files_errors:
                #send_error_file(OUTBOX_DIR, registry, files_errors[registry])
                continue

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

            if registry_type == 0:
                patient_path = os.path.join(REGISTER_DIR, registry)
                patient_file = XmlLikeFileReader(patient_path)

                for item in patient_file.find(tags=('PERS', )):
                    if patient_pk_list:
                        patient_pk = patient_pk_list.pop()
                    else:
                        patient_pk_list = get_next_patient_pk()
                        patient_pk = patient_pk_list.pop()

                    item['pk'] = patient_pk
                    patients[item.get('ID_PAC')] = item

            else:
                if registry_pk_list:
                    registry_pk = registry_pk_list.pop()
                else:
                    registry_pk_list = get_next_medical_register_pk()
                    registry_pk = registry_pk_list.pop()

                service_path = os.path.join(REGISTER_DIR, registry)
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

                        item['record_pk'] = record_pk

                        patient = patients.get(item['PACIENT']['ID_PAC'])
                        policy = {'VPOLIS': item['PACIENT']['VPOLIS'],
                                  'SPOLIS': item['PACIENT']['SPOLIS'],
                                  'NPOLIS': item['PACIENT']['NPOLIS'],
                                  'NOVOR':  item['PACIENT']['NOVOR']}

        print organization, current_year, current_period


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()