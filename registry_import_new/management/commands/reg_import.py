#! -*- coding: utf-8 -*-
from optparse import make_option
from django.core.management.base import BaseCommand
import os
import re
from collections import defaultdict
from registry_import_new.xml_parser import XmlLikeFileReader
from main.models import SERVICE_XML_TYPES
from registry_import_new.validator import RegistryValidator, CheckVolume, handle_errors
from registry_import_new.sender import Sender, save_to_economist_folder
import vipnet_handler
from registry_import_new.flc import FlcReportMaster
from registry_import_new.corrector import correct
from registry_import_new.objects import RegistryDb
from main.models import MedicalRegister
from medical_service_register.path import REGISTRY_IMPORT_DIR, IMPORT_ARCHIVE_DIR
import shutil
from medical_service_register.settings import YEAR, PERIOD


from main.logger import get_logger
logger = get_logger(__name__)


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

    def already_in_database(self):
        """
        Проверка на наличие реестра в базе
        """
        return MedicalRegister.objects.filter(
            year=self.year,
            period=self.period,
            is_active=True,
            organization_code=self.mo_code,
            status__in=[11, 20]
        ).count() > 0

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

    def move(self):
        """
        Перемещает реестры в архив
        """
        for reg_item in self._registry_items:
            shutil.copy(reg_item.path, IMPORT_ARCHIVE_DIR)
            os.remove(reg_item.path)

    def __repr__(self):
        return u'mo_code: {mo_code} year: {year} period {period} sets {items}'.\
            format(mo_code=self.mo_code, year=self.year, period=self.period, items=self._registry_items)


def load_registry_set():
    """
    Формирует комплекты реестров
    """
    filename_pattern = r'^(l|h|t|dp|dv|do|ds|du|df|dd|dr)m?(28\d{4})s(28002|28004)_(\d{2})(\d{2})(\d+).xml'
    registry_types = get_registry_type_dict(SERVICE_XML_TYPES)
    filename_regexp = re.compile(filename_pattern, re.IGNORECASE)
    registry_dicts = defaultdict(list)
    for file_name in os.listdir(REGISTRY_IMPORT_DIR):
        match = filename_regexp.match(file_name)
        if match:
            registry_type, mo_code, smo_code, year, period, version = match.groups()
            year = '20' + year
            registry_type = registry_type.lower()
            file_path = os.path.abspath(os.path.join(REGISTRY_IMPORT_DIR, file_name))
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


def registry_process(registry_set, is_commit):
    """
    Обработка реестра.
    Включает в себя загрузку реестра и форматно-логический контроль
    """
    # Загружает сведения о пациентах
    patient_file = registry_set.get_patients_file()
    logger.info(u'%s обрабатывается файл с пациентами' % patient_file.file_name)
    validator = RegistryValidator(patient_file.type_id)
    registry_db = RegistryDb(registry_set, is_commit)
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
    patient_file_errors = []
    service_file_errors = defaultdict(list)
    volume_checker = CheckVolume(registry_set)
    for service_item in registry_set.get_services_files():
        logger.info(u'%s обрабатывается файл с услугами' % service_item.file_name)
        services_file = XmlLikeFileReader(service_item.path)
        validator = RegistryValidator(service_item.type_id)
        for item in services_file.find(tags=('ZGLV', 'SCHET', 'ZAP', )):
            if 'SD_Z' in item:
                c_item = correct(item)
                service_file_errors[service_item.file_name] += validator.validate_header(c_item)
                volume_checker.set_count_invoiced_events(c_item['SD_Z'])
            if 'NSCHET' in item:
                c_item = correct(item)
                registry_obj = registry_db.create_registry_object(c_item, service_item)
            if 'N_ZAP' in item:
                c_item = correct(item)
                n_zap = c_item['N_ZAP']

                # Пациент
                patient_policy = c_item['PACIENT']

                patient_obj = patients.get(patient_policy['ID_PAC'], None)

                if not patient_obj:
                    service_file_errors[service_item.file_name] += handle_errors(
                        {'ID_PAC': [u'902;Нет сведений о пациенте в файле пациентов']},
                        parent='PACIENT', record_uid=n_zap)
                    continue
                else:
                    registry_db.patient_update_policy(patient_obj, patient_policy)

                patient_file_errors += handle_errors(patients_errors.get(patient_policy['ID_PAC'], {}),
                                                     parent='PERS', record_uid=n_zap)

                # Запись
                record = c_item
                record_obj = registry_db.create_record_obj(record, registry_obj, patient_obj)
                service_file_errors[service_item.file_name] += validator.validate_record(record)
                service_file_errors[service_item.file_name] += validator.validate_patient_policy(patient_policy)

                volume_checker.set_patient(patient_obj)

                # Случай
                for event in c_item['SLUCH']:
                    event_obj = registry_db.create_event_obj(event, record_obj)
                    service_file_errors[service_item.file_name] += validator.validate_event(event)
                    # Услуга
                    for service in event.get('USL', []):
                        registry_db.create_service_obj(service, event_obj)
                        service_file_errors[service_item.file_name] += validator.validate_service(service)
                        volume_checker.check(event, service, patient_policy)
        if volume_checker.check_count_events():
            service_file_errors[service_item.file_name] += handle_errors(
                {'SD_Z': [u'304;Количество случаев не соответствует указанному значению']}, parent='ZGLV')
    return registry_db, patient_file_errors, service_file_errors, volume_checker.get_error()


def main(options):
    if not options['no-check-vipnet']:
        vipnet_handler.get_vipnet_files()
    sender = Sender()
    for registry_set in load_registry_set():
        #try:
            logger.info(u'%s реестр подготавливается к импорту' % registry_set.mo_code)
            sender.set_recipient(registry_set.mo_code)
            fatal_errors = registry_set.check()
            already_in_database = registry_set.already_in_database()
            if fatal_errors:
                sender.send_errors_message(
                    u'ОШИБКИ ОБРАБОТКИ %s ВЕРСИЯ %s' % (registry_set.mo_code, registry_set.version), fatal_errors)
                logger.info(u'%s обнаружены фатальные ошибки во время обработки' % registry_set.mo_code)
            if already_in_database:
                logger.info(u'%s уже есть заимпорченный итоговый реестр' % registry_set.mo_code)

            if not fatal_errors and not already_in_database:
                registry_db, patient_file_errors, services_file_errors, volume_errors = registry_process(
                    registry_set, not options['no-insert'])

                flc_master = FlcReportMaster(registry_set)
                if volume_errors[0] and not options['no-overvolume']:
                    #save_to_economist_folder(registry_set, volume_errors[1])
                    sender.send_errors_message(u'ОШИБКИ ОБРАБОТКИ (СВЕРХОБЪЁМЫ) %s ВЕРСИЯ %s' %
                                               (registry_set.mo_code, registry_set.version),
                                               [volume_errors[1], ])
                    registry_db.insert_overvolume_message()
                else:
                    if patient_file_errors:
                        logger.info(u'%s обнаружены ошибки ФЛК в файле с пациентами'
                                    % registry_set.get_patients_file().file_name)
                        flc_master.create_report_patients(registry_set.get_patients_file().file_name, patient_file_errors)
                    for file_name in services_file_errors:
                        if services_file_errors[file_name]:
                            logger.info(u'%s обнаружены ошибки ФЛК в файле с услугами' % file_name)
                            flc_master.create_report_services(file_name, services_file_errors[file_name])

                    flc_file_path = flc_master.create_flc_archive()
                    if flc_file_path and not options['no-flc']:
                        sender.send_file(flc_file_path)
                        registry_db.insert_error_message()
                    else:
                        logger.info(u'%s инсертим реестр в базу' % registry_set.mo_code)
                        registry_db.insert_registry()
                        sender.send_success_message()
            logger.info(u'%s импорт реестра завершён' % registry_set.mo_code)
            registry_set.move()
        #except:
        #    logger.error(u'%s не могу обработать' % registry_set.mo_code)
        #    registry_set.move()


class Command(BaseCommand):
    """
    Импорт реестров услуг
    """
    option_list = BaseCommand.option_list + (
        make_option(
            '--no-insert',
            action='store_true',
            dest='no-insert',
            default=False,
            help=u'Не загружать реестр в базу'
        ),
        make_option(
            '--no-check-vipnet',
            action='store_true',
            dest='no-check-vipnet',
            default=False,
            help=u'Не проверять випнет на наличие присланных реестров'
        ),
        make_option(
            '--no-overvolume',
            action='store_true',
            dest='no-overvolume',
            default=False,
            help=u'Игнорировать сверхобъёмы'
        ),
        make_option(
            '--no-flc',
            action='store_true',
            dest='no-flc',
            default=False,
            help=u'Игнорировать ошибки ФЛК'
        ),
    )

    def handle(self, *args, **options):
        main(options)
