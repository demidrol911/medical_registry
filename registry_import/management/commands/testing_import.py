#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import connection

from medical_service_register.path import REGISTRY_IMPORT_DIR, TEMP_DIR, \
    FLC_DIR, OUTBOX_DIR, OUTBOX_SUCCESS, REGISTRY_PROCESSING_DIR

from main.models import MedicalRegister, SERVICE_XML_TYPES, Gender, Patient, \
    MedicalRegisterRecord, ProvidedEventConcomitantDisease, \
    ProvidedEventComplicatedDisease, ProvidedEventSpecial, \
    ProvidedService, ProvidedEvent, MedicalRegisterStatus, \
    MedicalServiceVolume, MedicalRegisterImport

from registry_import.simple_validation import get_person_patient_validation, \
    get_policy_patient_validation, get_record_validation, \
    get_event_validation, get_event_special_validation, \
    get_complicated_disease_validation, get_concomitant_disease_validation, \
    get_service_validation

from registry_import.complex_validation import (
    is_disease_has_precision, is_examination_result_matching_comment,
    is_expired_service, is_service_code_matching_hitech_method,
    is_service_children_profile_matching_event_children_profile,
    is_event_kind_corresponds_term, is_service_corresponds_registry_type )

from registry_import.xml_parser import XmlLikeFileReader
from helpers import xml_writer

from file_handler.funcs import get_outbox_dict, move_files_to_process, \
    move_files_to_archive, send_error_file

from main.data_cache import GENDERS, PERSON_ID_TYPES, \
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

import time

ERROR_MESSAGE_BAD_FILENAME = u'Имя файла не соответствует регламентированному'

HOSPITAL_VOLUME_EXCLUSIONS = ('098977', '018103', '98977', '18103')

DAY_HOSPITAL_VOLUME_EXCLUSIONS = ('098710', '098711', '098712', '098715',
                                  '098770', '98710', '98711', '98712', '98715',
                                  '98770', '098770', '098770', '198770')

HOSPITAL_VOLUME_MO_EXCLUSIONS = ('280013', )
DAY_HOSPITAL_MO_EXCLUSIONS = ('280029', )

filename_pattern = r'^(l|h|t|dp|dv|do|ds|du|df|dd|dr)m?(28\d{4})s(28002|28004)_(\d{2})(\d{2})\d+.xml'
registry_regexp = re.compile(filename_pattern, re.IGNORECASE)


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


def main():
    files = os.listdir(REGISTRY_IMPORT_DIR)

    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)

    registries, files_errors = get_registry_files_dict(files)

    for organization in registries:
        files = registries[organization]

    for organization in registries:
        print organization


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()