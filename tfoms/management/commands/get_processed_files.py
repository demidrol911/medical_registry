# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import MedicalOrganization

import os
import re
import shutil
import xlrd
import logging
from zipfile import ZipFile, is_zipfile, BadZipfile


INBOX_DIR = u'//alpha/vipnet/medical_registry/inbox/'
OUTBOX_DIR = u'//alpha/vipnet/medical_registry/outbox/'
ARCHIVE_DIR = u'd:/work/register_import_archive/'
register_dir = u"d:/work/register_import/"
other_files_dir = u'x:/vipnet/'
IDENT_TABLE = u'd:/work/medical_service_register/templates/ident_table/table.xls'
MO_CODE_PATTERN = r'^28\d{4}$'
ARCHIVE_TYPE_MISMATCH_ERROR = u'Архив не соответствует формату ZIP.'
NO_ARCHIVE_ERROR = u'Пакет должен быть упакован в архив формата ZIP.'
ARCHIVE_EXTRA_FILES_ERROR = u'В архиве присутствуют данные не относящихся к предмету информационного обмена.'
ARCHIVE_FILES_NOT_EXISTS = u'В архиве отсутствуют файлы относящихся к предмету информационного обмена.'
ARCHIVE_NAME_ERROR = u'Недопустимое имя пакета.'
ARCHIVE_AND_FILE_NAME_MISMATCH = u'Имя архива не соответствует упакованному файлу.'
LOGGING_FILE = u'd:/work/medical_register_log/get_files_log.txt'

ZIP_PATTERN = r'^(hm|hl_m)(2800\d{2})s28002_\d+.zip$'
REGISTER_FILES_PATTERN = r'^(h|l|t|dp|do|dv|dd|dr|ds|du|dv|df)m(2800\d{2})s28002_\d+.xml$'


def get_completed_mo():
    table = xlrd.open_workbook(IDENT_TABLE)

    sheets = table.sheet_names()

    mo_code_match_pattern = re.compile(MO_CODE_PATTERN)

    completed = []

    for sheet_name in sheets:
        work_sheet = table.sheet_by_name(sheet_name)
        rows_count = work_sheet.nrows
        current_row = -1
        while current_row < rows_count-1:
            current_row += 1
            row = work_sheet.row(current_row)
            if mo_code_match_pattern.match(row[1].value) \
                    and type(row[3].value) is float \
                    and row[3].value > 0:
                completed.append(row[1].value)

    return completed


def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
    return sorted(l, key = alphanum_key)


def get_inbox_dict(dir):
    dirs = os.listdir(dir)
    inbox_dict = {}

    for d in dirs:
        t = d#.decode('cp1251')
        code, name = t[:6], t[7:]
        inbox_dict[code] = name

    return inbox_dict


def get_outbox_dict(dir):
    dirs = os.listdir(dir)
    outbox_dict = {}

    for d in dirs:
        t = d#.encode('cp1251')
        code, name = t[:6], t[7:]
        outbox_dict[code] = name

    return outbox_dict

archive_name = re.compile(ZIP_PATTERN)
registry_filename = re.compile(REGISTER_FILES_PATTERN)
inbox_dict = get_inbox_dict(INBOX_DIR)
outbox_dict = get_outbox_dict(OUTBOX_DIR)

def send_error_file(path='', filename=None, message=''):
    f = open(path+u'Ошибка обработки %s.txt' % filename, 'w')
    f.write(message.encode('utf-8'))
    f.close()


def main():
    logging.basicConfig(filename=LOGGING_FILE,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)

    w = os.walk(INBOX_DIR)
    completed = get_completed_mo()

    logging.info(u'----- старт разбора файлов -----')

    for root, dirs, files in w:
        sorted_zip_list = natural_sort([rec for rec in files if rec.lower().endswith('.zip')])
        not_zip_list = [rec for rec in files if not rec.lower().endswith('.zip')]
        sorted_files = not_zip_list + ([sorted_zip_list[-1]] if sorted_zip_list else [])

        for filename in sorted_files:
            filepath = root+'/'+filename
            name, ext = os.path.splitext(filename.lower())
            dir_mo_code = filepath[len(INBOX_DIR):len(INBOX_DIR)+6]
            dir_organization = MedicalOrganization.objects.get(
                code=dir_mo_code, parent=None)
            dir_organization_name = dir_organization.name.replace('"', '')
            vipnet_path = other_files_dir+dir_organization_name+'/'
            mo_send_path = '%s%s %s/' % (OUTBOX_DIR, dir_mo_code,
                                         outbox_dict[dir_mo_code])


            if not os.path.exists(vipnet_path):
                os.makedirs(vipnet_path)

            if is_zipfile(filepath) and ext not in ('.docx', '.xlsx', '.xls', '.doc'):
                archive_name_matching = archive_name.match(filename.lower())
                if archive_name_matching:
                    mo_code = archive_name_matching.group(2)
                    print mo_code
                    if mo_code not in completed:
                        logging.warning(u'%s не прошли идентификацию' % mo_code)
                        continue
                    try:
                        zfile = ZipFile(filepath, )
                    except BadZipfile:
                        logging.error(u'%s не могу открыть zip-файл' % filename)
                        continue

                    zip_file_name_list = zfile.namelist()
                    print zip_file_name_list


                    is_include_services_files = False
                    for zip_file_name in zfile.namelist():
                        if registry_filename.match(zip_file_name.lower()):
                            zfile.extract(zip_file_name, path=register_dir)
                            is_include_services_files = True
                            logging.info(u'%s реестр извлечён из архива' % zip_file_name)
                        elif os.path.splitext(zip_file_name)[1] in (
                                '.doc', 'docx', '.xls', 'xlsx',
                                '.pdf', '.jpeg', '.jpg'):
                            if not os.path.exists(vipnet_path):
                                os.makedirs(vipnet_path)
                            zfile.extract(zip_file_name, path=vipnet_path)
                            logging.info(u'%s документ извлечён из архива ' % zip_file_name)
                        else:
                            send_error_file(mo_send_path, filename, ARCHIVE_EXTRA_FILES_ERROR)
                            logging.error(u'%s посторонние файлы в архиве' % zip_file_name)
                        if not is_include_services_files:
                            send_error_file(mo_send_path, filename, ARCHIVE_FILES_NOT_EXISTS)
                            logging.error(u'%s нет файлов с услугами' % zip_file_name)
                    zfile.close()
                else:
                    send_error_file(mo_send_path, filename, u'Неверный формат или повреждённый архив.')
                    logging.error(u'%s неверный файл' % filename)
            elif ext in ('.doc', '.docx', '.xls', '.xlsx', '.pdf', '.jpeg',
                         '.jpg'):

                shutil.copy2(filepath, vipnet_path)
                os.remove(filepath)
                logging.info(u'%s документ скопирован' % filename)
            elif ext in ('.rar'):
                send_error_file(mo_send_path,
                                filename, ARCHIVE_TYPE_MISMATCH_ERROR)

                shutil.copy(filepath, ARCHIVE_DIR)
                os.remove(filepath)
                logging.warning(u'%s неверный формат' % filename)
            else:
                shutil.copy2(filepath, vipnet_path)
                os.remove(filepath)
                logging.warning(u'%s неизвестный файл' % filename)
            try:
                shutil.copy(filepath, ARCHIVE_DIR)
                os.remove(filepath)
            except:
                pass
        for filename in set(files) - set(sorted_files):
            print ARCHIVE_DIR+filename
            try:
                shutil.copy(filepath, ARCHIVE_DIR)
                os.remove(filepath)
            except:
                pass

class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()
