#! -*- coding: utf-8 -*-
from shutil import copy2
from medical_service_register.path import OUTBOX_SUCCESS, FLC_DIR, OUTBOX_DIR, ECONOMIST_DIR
from main.data_cache import ORGANIZATIONS
import os

from main.logger import get_logger
logger = get_logger(__name__)


class Sender:
    def __init__(self):
        self.send_path = ''
        outbox_dir = OUTBOX_DIR
        dirs = os.listdir(outbox_dir)
        self.available_addresses = {}
        for d in dirs:
            t = d  # .decode('cp1251')
            address = os.path.join(outbox_dir, t)
            if os.path.isdir(address):
                code, name = t[:6], t[7:]
                self.available_addresses[code] = os.path.abspath(address)

    def add_address(self, recipient_key, recipient_path):
        self.available_addresses[recipient_key] = recipient_path

    def set_recipient(self, recipient_key):
        if recipient_key in self.available_addresses:
            self.send_path = self.available_addresses[recipient_key]
        else:
            logger.warning(u'Нет доступных адресов для получателя %s' % recipient_key)
            print u'Нет доступных адресов для получателя %s' % recipient_key

    def send_errors_message(self, filename, errors):
        """
        Отправить сообщение о фатальных ошибках обработки реестра
        """
        if errors:
            file_path = os.path.join(FLC_DIR, filename + '.txt')
            file_errors = open(file_path, 'w')
            for error in errors:
                file_errors.write(error.encode('cp1251')+'\n')
            file_errors.close()
            self.send_file(file_path)

    def send_success_message(self):
        """
        Отправить сообщение об успешной обработке реестра
        """
        self.send_file(OUTBOX_SUCCESS)

    def send_file(self, file_path):
        if self.send_path and file_path:
            copy2(file_path, self.send_path)
        else:
            logger.warning(u'Получатель не указан')
            print u'Получатель не указан'


def save_to_economist_folder(registry_set, message):
    """
    Сохранить письмо о сверхобъёмов в папку экономиста
    """
    filename = u'%s ВЕРСИЯ %s' % (ORGANIZATIONS[registry_set.mo_code].name.replace('"', '').strip(),
                                  registry_set.version)
    file_path = os.path.join(FLC_DIR, filename + '.txt')
    file_errors = open(file_path, 'w')
    file_errors.write(message.encode('cp1251')+'\n')
    file_errors.close()
    copy2(file_path, ECONOMIST_DIR % (registry_set.year, registry_set.period))
