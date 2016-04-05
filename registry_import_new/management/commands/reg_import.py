#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
import os
import re
from collections import defaultdict
from registry_import.xml_parser import XmlLikeFileReader
from main.models import SERVICE_XML_TYPES
from registry_import_new.validator import RegistryValidator, CheckVolume, handle_errors
from registry_import_new.sender import Sender
from registry_import_new.logger import log
from registry_import_new.flc import FlcReportMaster
from registry_import_new.corrector import correct
from registry_import_new.objects import RegistryDb


YEAR = '2016'
PERIOD = '03'


def get_registry_type_dict(types_tuple):
    return dict((y, x) for x, y in types_tuple)


class RegistryItem:
    def __init__(self, registry_type, registry_type_id, file_path):
        self.type = registry_type
        self.type_id = registry_type_id
        self.path = file_path
        self.file_name = os.path.basename(file_path)

    def __str__(self):
        return self.path


class RegistrySet:
    def __init__(self, mo_code, year, period, version, registry_items):
        self.mo_code = mo_code
        self.year = year
        self.period = period
        self.version = version
        self._registry_items = registry_items

    def check(self):
        """
        Проверка реестра на целостность
        """
        errors = []
        if not self.year == YEAR:
            errors.append(u'Год указанный в имени файла не соответствует отчётному году')
        if not self.period == PERIOD:
            errors.append(u'Период указанный в имени файла не соответствует отчётному периоду')
        if not self.get_patients_file():
            errors.append(u'Комплект реестров не полный: отсутствует файл с информацией о пациентах')
        return errors

    def get_patients_file(self):
        """
        Возвращает путь к файлу с пациентами
        """
        for reg_item in self._registry_items:
            if reg_item.type == 'l':
                return reg_item
        return None

    def get_services_files(self):
        """
        Возвращает пути к файлам с услугами
        """
        return [reg_item for reg_item in self._registry_items if reg_item.type != 'l']

    def __repr__(self):
        return u'mo_code: {mo_code} year: {year} period {period} sets {items}'.\
            format(mo_code=self.mo_code, year=self.year, period=self.period, items=self._registry_items)


def load_registry_set():
    """
    Формирует комплекты реестров
    """
    registry_path = 'C:/REESTR/registry'
    filename_pattern = r'^(l|h|t|dp|dv|do|ds|du|df|dd|dr)m?(28\d{4})s(28002|28004)_(\d{2})(\d{2})(\d+).xml'
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)
    filename_regexp = re.compile(filename_pattern, re.IGNORECASE)
    registry_dicts = defaultdict(list)
    for file_name in os.listdir(registry_path):
        match = filename_regexp.match(file_name)
        if match:
            registry_type, mo_code, smo_code, year, period, version = match.groups()
            year = '20' + year
            registry_type = registry_type.lower()
            file_path = os.path.abspath(os.path.join(registry_path, file_name))
            registry_key = (mo_code, year, period, version)
            registry_dicts[registry_key].append({'registry_type': registry_type,
                                                 'file_path': file_path,
                                                 'registry_type_id': registry_types[registry_type]})
    registry_sets = []
    for (mo_code, year, period, version), files_dict in registry_dicts.iteritems():
        registry_items = [
            RegistryItem(registry_type=file_inf['registry_type'],
                         registry_type_id=file_inf['registry_type_id'],
                         file_path=file_inf['file_path'])
            for file_inf in files_dict
        ]
        registry_sets.append(RegistrySet(mo_code=mo_code, year=year,
                                         period=period, version=version,
                                         registry_items=registry_items))
    return registry_sets


def registry_process(registry_set):
    """
    Обработка реестра.
    Включает в себя загрузку реестра и форматно-логический контроль
    """
    # Загружает сведения о пациентах
    patient_file = registry_set.get_patients_file()
    log.debug(u'Обработка файла с пациентами %s ...' % patient_file)
    validator = RegistryValidator(patient_file.type_id)
    registry_db = RegistryDb(registry_set)
    patients_file = XmlLikeFileReader(patient_file.path)
    patients_errors = defaultdict(list)
    patients = {}
    for patient in patients_file.find(tags=('PERS',)):
        patient = correct(patient)
        patient_obj = registry_db.create_patient_obj(patient)
        errors = validator.validate_patient(patient)
        if errors:
            patients_errors[patient['ID_PAC']] = errors
        patients[patient['ID_PAC']] = patient_obj

    # Загружает сведения об услугах
    log.debug(u'Обработка файлов с услугами...')
    patient_errors = []
    service_errors = defaultdict(list)
    volume_checker = CheckVolume(registry_set)
    for service_item in registry_set.get_services_files():
        services_file = XmlLikeFileReader(service_item.path)
        validator = RegistryValidator(service_item.type_id)
        for item in services_file.find(tags=('SCHET', 'ZAP', )):
            if 'NSCHET' in item:
                c_item = correct(item)
                registry_obj = registry_db.create_registry_object(c_item, service_item)
            if 'N_ZAP' in item:
                c_item = correct(item)
                n_zap = c_item['N_ZAP']

                # Запись
                record = c_item
                record_obj = registry_db.create_record_obj(record, registry_obj, patient_obj)
                service_errors[service_item.file_name] += validator.validate_record(record)

                # Пациент
                patient_policy = c_item['PACIENT']
                service_errors[service_item.file_name] += validator.validate_patient_policy(patient_policy)

                id_pac = patient_policy['ID_PAC']
                patient_obj = patients[id_pac]
                registry_db.patient_update_policy(patient_obj, patient_policy)
                patient_errors += handle_errors(patients_errors.get(id_pac, {}),  parent='PERS', record_uid=n_zap)

                # Случай
                for event in c_item['SLUCH']:
                    event_obj = registry_db.create_event_obj(event, record_obj)
                    service_errors[service_item.file_name] += validator.validate_event(event)
                    # Услуга
                    for service in event['USL']:
                        registry_db.create_service_obj(service, event_obj)
                        service_errors[service_item.file_name] += validator.validate_service(service)
                        volume_checker.check(event, service)
    return registry_db, patient_errors, service_errors, volume_checker.get_error()


def main():
    sender = Sender()
    log.debug(u'Поиск реестров...')
    registry_sets = load_registry_set()
    for registry_set in registry_sets:
        log.debug(u'Обработка %s' % registry_set.mo_code)
        sender.set_recipient(registry_set.mo_code)

        log.debug(u'Проверка целостности реестра...')
        fatal_errors = registry_set.check()
        if fatal_errors:
            sender.send_errors_message(u'ОШИБКИ ОБРАБОТКИ', fatal_errors)
            log.debug(u'Обнаружены фатальные ошибки во время обработки. Обработка прекращена.')
            continue

        registry_db, patient_errors, services_errors, volume_errors = registry_process(registry_set)
        flc_master = FlcReportMaster(registry_set)
        if volume_errors[0]:
            sender.send_errors_message(u'ОШИБКИ ОБРАБОТКИ (СВЕРХОБЪЁМЫ)', [volume_errors[1], ])
        else:
            if patient_errors:
                log.debug(u'Обнаружены ошибки ФЛК в файле с пациентами.')
                flc_master.create_report_patients(registry_set.get_patients_file().file_name, patient_errors)
            for file_name in services_errors:
                if services_errors[file_name]:
                    log.debug(u'Обнаружены ошибки ФЛК в файле с услугами. %s' % file_name)
                    flc_master.create_report_services(file_name,
                                                      services_errors[file_name])

            flc_file_path = flc_master.create_flc_archive()
            if flc_file_path:
                sender.send_file(flc_file_path)
            else:
                print u'Инсертим в базу реестр'
                sender.send_sucsses_messasge()


class Command(BaseCommand):
    def handle(self, *args, **options):
        main()
