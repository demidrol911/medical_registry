from helpers import xml_writer
from zipfile import ZipFile
import os
from medical_service_register.path import FLC_DIR, TEMP_DIR


class FlcReportMaster:

    def __init__(self, registry_set):
        self.errors_files = []
        self.registry_set = registry_set

    def create_report_patients(self, person_filename, patients_errors):
        file_path = os.path.join(TEMP_DIR, 'V' + person_filename)
        lflk = xml_writer.Xml(file_path)
        lflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
        lflk.start('FLK_P')
        lflk.put('FNAME', "V%s" % person_filename[:-4])
        lflk.put('FNAME_I', '%s' % person_filename[:-4])
        for rec in patients_errors:
            lflk.start('PR')
            lflk.put('OSHIB', rec['code'])
            lflk.put('IM_POL', rec['field'])
            lflk.put('BASE_EL', rec['parent'])
            lflk.put('N_ZAP', rec['record_uid'])
            lflk.put('IDCASE', rec.get('event_uid', '').encode('cp1251'))
            lflk.put('IDSERV', rec.get('service_uid', '').encode('cp1251'))
            lflk.put('COMMENT', rec['comment'].encode('cp1251'))
            lflk.end('PR')
        lflk.plain_put('</FLK_P>')
        lflk.close()
        self.errors_files.append(file_path)

    def create_report_services(self, services_filename, services_errors):
        file_path = os.path.join(TEMP_DIR, 'V' + services_filename)
        hflk = xml_writer.Xml(file_path)
        hflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
        hflk.start('FLK_P')
        hflk.put('FNAME', "V%s" % services_filename[:-4])
        hflk.put('FNAME_I', '%s' % services_filename[:-4])
        for rec in services_errors:
            hflk.start('PR')
            hflk.put('OSHIB', rec['code'])
            hflk.put('IM_POL', rec['field'])
            hflk.put('BASE_EL', rec['parent'])
            hflk.put('N_ZAP', rec['record_uid'])
            hflk.put('IDCASE',
                     rec.get('event_uid', '').encode('cp1251'))
            hflk.put('IDSERV',
                     rec.get('service_uid', '').encode('cp1251'))
            hflk.put('COMMENT', rec['comment'].encode('cp1251'))
            hflk.end('PR')
        hflk.plain_put('</FLK_P>')
        hflk.close()
        self.errors_files.append(file_path)

    def create_flc_archive(self):
        if self.errors_files:
            zipname = os.path.join(FLC_DIR, 'VM%sS28004_%s%s%s.zip' % (
                self.registry_set.mo_code,
                self.registry_set.year[2:],
                self.registry_set.period,
                self.registry_set.version
            ))
            with ZipFile(zipname, 'w') as zipfile:
                for file_path in self.errors_files:
                    zipfile.write(file_path, os.path.basename(file_path), 8)
                    os.remove(file_path)
            return zipname
