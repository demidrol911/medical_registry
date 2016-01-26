#! -*- coding: utf-8 -*-
from shutil import copy2
import os


class Sender:
    def __init__(self):
        self.send_path = ''
        outbox_dir = 'C:/REESTR/send'
        dirs = os.listdir(outbox_dir)
        self.available_addresses = {}
        for d in dirs:
            t = d.decode('cp1251')
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
            print u'Нет доступных адресов для получателя %s' % recipient_key

    def send_errors_message(self, errors):
        """
        Отправить сообщение о фатальных ошибках обработки реестра
        """
        if errors:
            tmp_path = u'C:/REESTR/tmp'
            file_path = os.path.join(tmp_path, u'ОШИБКИ ОБРАБОТКИ.txt')
            file_errors = open(file_path, 'w')
            for error in errors:
                file_errors.write(error.encode('cp1251')+'\n')
            file_errors.close()
            self.send_file(file_path)

    def send_sucsses_messasge(self):
        """
        Отправить сообщение об успешной обработке реестра
        """
        pass

    def send_file(self, file_path):
        if self.send_path and file_path:
            copy2(file_path, self.send_path)
        else:
            print u'Получатель не указан'
