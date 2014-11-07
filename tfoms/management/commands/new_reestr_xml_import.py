#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Max
from medical_service_register.path import BASE_DIR
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
#import valideer as V

cursor = connection.cursor()

OUTBOX_DIR = '//alpha/vipnet/medical_registry/outbox/'
OUTBOX_SUCCESS = os.path.join(BASE_DIR, u'templates/outcoming_messages/ФЛК пройден.txt')
REGISTER_DIR = "c:/work/register_import/"
temp_dir = "c:/work/register_temp/"
flk_dir = "c:/work/medical_register/"
IMPORT_ARCHIVE_DIR = u"c:/work/register_import_archive/"
REGISTER_IN_PROCESS_DIR = u'c:/work/register_import_in_process/'

ERROR_MESSAGE_BAD_FILENAME = u'Имя файла не соответствует регламентированному'

filename_pattern = r'^(l|h|t|dp|dv|do|ds|du|df|dd|dr)m?(28\d{4})s28002_(\d{2})(\d{2})\d+.xml'
registry_regexp = re.compile(filename_pattern, re.IGNORECASE)

schema_msg = {
    'required': u'Отстутвует значение в обязательном поле %s',
    'length': 'Длина поля %s больше допустимого',
    'in': u'Значение поля %s не соответствует справочнику %s'

}

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


def get_registry_files_dict(files):
    registries = defaultdict(list)
    errors = defaultdict(list)

    for _file in files:
        matching = registry_regexp.match(_file)
        if matching:
            file_type, organization, year, period = matching.groups()

            #registries[organization].append(
            #    {'year': '20%s' % year, 'period': period,
            #     'type': registry_type_dict.get(file_type.lower()),
            #     'filename': _file})

            registries[organization].append(_file)
        else:
            errors[_file].append(ERROR_MESSAGE_BAD_FILENAME)
            #registries[organization].append({'filename': _file,
            #    'error': ERROR_MESSAGE_BAD_FILENAME})

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


def get_person_patient_data(record):
    patient = dict(
        id=record['ID_PAC'],
        last_name=record['FAM'].upper() if record['FAM'] else None,
        first_name=record['IM'].upper() if record['IM'] else None,
        middle_name=record['OT'].upper() if record['OT'] else None,
        birthdate=record['DR'],
        snils=record['SNILS'],
        birthplace=record['MR'],
        gender=record['W'],
        person_id_type=record['DOCTYPE'],
        person_id_series=record['DOCSER'],
        person_id_number=record['DOCNUM'],
        weight=record['VNOV_D'],
        residence=record['OKATOP'],
        registration=record['OKATOG'],
        comment=record['COMENTP'],
        agent_last_name=record['FAM_P'].upper() if record['FAM_P'] else None,
        agent_first_name=record['IM_P'].upper() if record['IM_P'] else None,
        agent_middle_name=record['OT_P'].upper() if record['OT_P'] else None,
        agent_birthdate=record['DR_P'],
        agent_gender=record['W_P'], )

    return patient


def get_policy_patient_data(record):
    patient = dict(
        insurance_policy_type=record['PACIENT']['VPOLIS'],
        insurance_policy_series=record['PACIENT']['SPOLIS'],
        insurance_policy_number=record['PACIENT']['NPOLIS'],
        newborn_code=record['PACIENT']['NOVOR']
    )

    return patient


def get_registry_data(record):
    pass


def get_next_patient_pk():
    get_patient_pk_query = ("select nextval('patient_seq')"
                            "from generate_series(0, 512)")
    cursor.execute(get_patient_pk_query, [])
    patient_pk = cursor.fetchall()

    return list(reversed([rec[0] for rec in patient_pk]))


def main():

    files = os.listdir(REGISTER_DIR)
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    #patient_pk = Patient.objects.all().aggregate(max=Max('id_pk'))['max']+1

    for organization in registries:
        if not is_files_completeness(registries[organization]):
            continue

        patient_dict = {}
        service_dict = {}
        event_dict = {}
        record_dict = {}

        current_year = current_period = None

        for registry in registries[organization]:
            if registry in files_errors:
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
                print 'ok!', registry
                patient_path = os.path.join(REGISTER_DIR, registry)
                patient_file = XmlLikeFileReader(patient_path)
                patient_pk_list = get_next_patient_pk()

                for item in patient_file.find(tags=('PERS')):
                    try:
                        pass
                    except:
                        pass
                        #patient_pk =  #q

            else:
                pass

        print organization, current_year, current_period


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()