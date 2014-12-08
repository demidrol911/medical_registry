# -*- coding: utf-8 -*-

from medical_service_register.path import REGISTRY_IMPORT_DIR
from medical_service_register.path import REGISTRY_PROCESSING_DIR
from medical_service_register.path import IMPORT_ARCHIVE_DIR

import os
import re
import shutil


def get_outbox_dict(dir):
    dirs = os.listdir(dir)
    outbox_dict = {}

    for d in dirs:
        if os.path.isdir(os.path.join(dir, d)):
            t = d
            code, name = t[:6], t[7:]
            outbox_dict[code] = name

    return outbox_dict


def get_inbox_dict(dir):
    dirs = os.listdir(dir)
    inbox_dict = {}

    for d in dirs:
        t = d
        code, name = t[:6], t[7:]
        inbox_dict[code] = name

    return inbox_dict


def move_files_to_process(files_list):
    for name in files_list:
        shutil.move(os.path.join(REGISTRY_IMPORT_DIR, name),
                    REGISTRY_PROCESSING_DIR)


def move_files_to_archive(files_list):
    for name in files_list:
        if os.path.exists(IMPORT_ARCHIVE_DIR+name):
            os.remove(IMPORT_ARCHIVE_DIR+name)
        shutil.move(os.path.join(REGISTRY_PROCESSING_DIR, name),
                    IMPORT_ARCHIVE_DIR)


def send_error_file(path='', filename=None, message=''):
    f = open(path+u'Ошибка обработки %s.txt' % filename, 'w')
    f.write(message.encode('utf-8'))
    f.close()