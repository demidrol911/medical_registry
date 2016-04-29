# -*- coding: utf-8 -*-
from medical_service_register.path import INBOX_DIR, ARCHIVE_DIR
from medical_service_register.path import REGISTRY_IMPORT_DIR, OTHER_FILES_DIR
from medical_service_register.path import IDENT_TABLE
from main.models import MedicalOrganization
from registry_import_new.sender import Sender

import os
import re
import shutil
from main.logger import get_logger
from zipfile import ZipFile, is_zipfile, BadZipfile

DOC_FILES_EXT = ('.doc', '.docx', '.xls', 'xlsx', '.pdf', '.jpeg', '.jpg')
ARCHIVE_NAME_REGEXP = re.compile(r'^(hm|hl_m)(280\d{3})s(28002|28004)_\d+.zip$')
REGISTRY_FILENAME_REGEXP = re.compile(r'^(h|l|t|dp|do|dv|dd|dr|ds|du|dv|df)m(280\d{3})s(28002|28004)_\d+.xml$')
logger = get_logger(__name__)


def get_completed_mo():
    mo_code_match_pattern = re.compile(r'^28\d{4}$')
    completed = []
    for row in open(IDENT_TABLE):
        data = row.split(';')
        if mo_code_match_pattern.match(data[0]):
            try:
                if len(data) >= 3 and float(data[2]) > 0:
                    completed.append(data[0])
            except ValueError:
                pass
    return completed


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def move(filepath, target_dir):
    shutil.copy(filepath, target_dir)
    os.remove(filepath)


def get_vipnet_files():
    sender = Sender()
    completed = get_completed_mo()
    for root, dirs, files in os.walk(INBOX_DIR):
        sorted_zip_list = natural_sort([rec for rec in files if rec.lower().endswith('.zip')])
        not_zip_list = [rec for rec in files if not rec.lower().endswith('.zip')]
        sorted_files = not_zip_list + ([sorted_zip_list[-1]] if sorted_zip_list else [])
        for filename in sorted_files:
            filepath = root+'/'+filename
            name, ext = os.path.splitext(filename.lower())

            dir_mo_code = filepath[len(INBOX_DIR):len(INBOX_DIR)+6]
            sender.set_recipient(dir_mo_code)

            other_file_path = OTHER_FILES_DIR + \
                MedicalOrganization.objects.get(code=dir_mo_code, parent=None).name.replace('"', '') + '/'

            if not os.path.exists(other_file_path):
                os.makedirs(other_file_path)

            errors = []

            if is_zipfile(filepath) and ext not in DOC_FILES_EXT:
                archive_name_matching = ARCHIVE_NAME_REGEXP.match(filename.lower())

                if archive_name_matching:
                    mo_code = archive_name_matching.group(2)
                    if mo_code not in completed:
                        logger.warning(u'%s не прошли идентификацию' % mo_code)
                        continue
                    try:
                        zfile = ZipFile(filepath, )
                    except BadZipfile:
                        logger.error(u'%s не могу открыть zip-файл' % filename)
                        continue

                    # Распаковка архива
                    is_include_services_files = False
                    for zip_file_name in zfile.namelist():
                        if REGISTRY_FILENAME_REGEXP.match(zip_file_name.lower()):
                            zfile.extract(zip_file_name, path=REGISTRY_IMPORT_DIR)
                            is_include_services_files = True
                            logger.info(u'%s реестр извлечён из архива' % zip_file_name)

                        elif os.path.splitext(zip_file_name)[1] in DOC_FILES_EXT:
                            zfile.extract(zip_file_name, path=other_file_path)
                            logger.info(u'%s документ извлечён из архива ' % zip_file_name)
                        else:
                            errors.append(u'В архиве присутствуют данные не относящихся к предмету '
                                          u'информационного обмена.')
                            logger.error(u'%s посторонние файлы в архиве' % zip_file_name)
                    zfile.close()

                    if not is_include_services_files:
                        errors.append(u'В архиве отсутствуют файлы относящихся к предмету информационного обмена.')
                        logger.error(u'%s нет файлов с услугами' % filename)
                else:
                    errors.append(u'Неверный формат или повреждённый архив.')
                    logger.error(u'%s неверный формат или повреждённый архив' % filename)
            elif ext in DOC_FILES_EXT:
                move(filepath, other_file_path)
                logger.info(u'%s документ скопирован' % filename)
            elif ext in ('.rar', ):
                errors.append(u'Архив не соответствует формату ZIP.')
                move(filepath, ARCHIVE_DIR)
                logger.warning(u'%s неверный формат' % filename)
            else:
                move(filepath, other_file_path)
                logger.warning(u'%s неизвестный файл' % filename)
            try:
                move(filepath, ARCHIVE_DIR)
            except:
                pass
            if errors:
                sender.send_errors_message(u'Ошибка обработки %s.txt' % filename, errors)

        for filename in set(files) - set(sorted_files):
            print ARCHIVE_DIR+filename
            try:
                shutil.copy(filepath, ARCHIVE_DIR)
                os.remove(filepath)
            except:
                pass

