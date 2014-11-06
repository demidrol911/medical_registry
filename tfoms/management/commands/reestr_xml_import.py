#! -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from zipfile import ZipFile
import shutil

from django.core.management.base import BaseCommand
from django.db.models import Max

from tfoms.models import (ProvidedEvent, ProvidedService, Patient,
                          ProvidedEventConcomitantDisease,
                          ProvidedEventComplicatedDisease,
                          MedicalRegisterRecord, MedicalRegister,
                          MedicalRegisterStatus, MedicalOrganization,
                          SERVICE_XML_TYPES)
from registry_import.xml_parser import XmlLikeFileReader
from helpers.validation import ValidPatient, ValidRecord, ValidEvent,\
    ValidService, ValidConcomitantDisease, ValidComplicatedDisease
from medical_service_register.path import OUTBOX_DIR, OUTBOX_SUCCESS
from medical_service_register.path import REGISTRY_IMPORT_DIR, TEMP_DIR
from medical_service_register.path import IMPORT_ARCHIVE_DIR
from medical_service_register.path import REGISTRY_PROCESSING_DIR
from helpers import xml_writer
from file_handler.funcs import get_outbox_dict, move_files_to_archive
from file_handler.funcs import move_files_to_process


def get_valid_xmls_info(files):
    valid_name_pattern = re.compile(r'^[hm|tm|dp|dv|do|ds|du|df|dd|dr]{2}M?(28\d{4})s28002_(\d{2})(\d{2})\d+.xml',
                                    re.IGNORECASE)
    XML_TYPE = {}

    for rec in SERVICE_XML_TYPES:
        if len(rec[1]) < 2:
            XML_TYPE[rec[1]+'m'] = rec[0]
        else:
            XML_TYPE[rec[1]] = rec[0]

    valid_xmls_info = []

    for name in files:
        match = valid_name_pattern.match(name)

        if not match:
            continue
        type = XML_TYPE[name[:2].lower()]
        organization_code = match.group(1)
        year = '20' + match.group(2)
        #xml_code = name[15:-4]
        period = match.group(3)

        info = {'type': type, 'organization_code': organization_code,
                'filename': name, 'year': year, 'period': period}

        if info not in valid_xmls_info:
            valid_xmls_info.append(info)
    return valid_xmls_info


def main():
    patients = {}
    files = os.listdir(REGISTRY_IMPORT_DIR)

    outbox = get_outbox_dict(OUTBOX_DIR)
    valid_xmls = get_valid_xmls_info(files)
    register_set = {}

    for xml in valid_xmls:
        if xml['organization_code'] in register_set:
            register_set[xml['organization_code']]['services'].append(xml)
        else:
            register_set[xml['organization_code']] = {
                'patients': 'LM'+xml['filename'][2:].strip('M'),
                'services': [xml],
                'year': xml['year'],
                'period': xml['period']}

    for code in register_set:
        files = [rec['filename'] for rec in register_set[code]['services']] + [register_set[code]['patients']]
        move_files_to_process(files)

    patient_pk = Patient.objects.all().aggregate(max_pk=Max('id_pk'))['max_pk'] + 1
    register_pk = \
        MedicalRegister.objects.all().aggregate(max_pk=Max('id_pk'))['max_pk']+1
    record_pk = \
        MedicalRegisterRecord.objects.all().aggregate(max_pk=Max('id_pk'))[
            'max_pk'] + 1
    event_pk = ProvidedEvent.objects.all().aggregate(max_pk=Max('id_pk'))[
        'max_pk'] + 1
    service_pk = \
        ProvidedService.objects.all().aggregate(max_pk=Max('id_pk'))['max_pk']+1

    for organization in register_set:
        patients = {}
        patients_super_set = []
        records_super_set = []
        events_super_set = []
        services_super_set = []
        concomitant_disease_super_set = []
        complicated_disease_super_set = []
        registers_set_id = []
        patient_errors = []
        error_organization = False
        errors_filenames = []

        print u'Обрабатаываю МО ', organization, \
            MedicalOrganization.objects.get(code=organization, parent=None).name

        old_register_status = MedicalRegister.objects.filter(
            is_active=True, year=register_set[organization]['year'],
            period=register_set[organization]['period'],
            organization_code=organization
        ).values_list('status_id', flat=True).distinct()

        print old_register_status

        if old_register_status and old_register_status[0] in (4, 6, 8):
            continue

        if register_set[organization]['patients']:
            person_file = XmlLikeFileReader('{0:s}/LM{1:s}'.format(
                REGISTRY_PROCESSING_DIR, register_set[organization]['patients'][2:]))
        else:
            raise ValueError("Patients file not exists!")

        for item in person_file.find(tags='PERS'):
            patient = dict(
                id_pk=patient_pk,
                id=item['ID_PAC'],
                last_name=item['FAM'].upper() if item['FAM'] else None,
                first_name=item['IM'].upper() if item['IM'] else None,
                middle_name=item['OT'].upper() if item['OT'] else None,
                birthdate=item['DR'],
                snils=item['SNILS'],
                birthplace=item['MR'],
                gender=item['W'],
                person_id_type=item['DOCTYPE'],
                person_id_series=item['DOCSER'],
                person_id_number=item['DOCNUM'],
                weight=item['VNOV_D'],
                residence=item['OKATOP'],
                registration=item['OKATOG'],
                comment=item['COMENTP'],
                agent_last_name=item['FAM_P'].upper() if item['FAM_P'] else None,
                agent_first_name=item['IM_P'].upper() if item['IM_P'] else None,
                agent_middle_name=item['OT_P'].upper() if item['OT_P'] else None,
                agent_birthdate=item['DR_P'],
                agent_gender=item['W_P'],
                newborn_code=None,
                insurance_policy_type=None,
                insurance_policy_series=None,
                insurance_policy_number=None,
                person_instance=None,
                insurance_instance=None, )
            # patient
            if patient['id'] in patients:
                print patient['last_name'], patient['first_name'], patient['middle_name']
                raise ValueError("Patient unique constraint ID error: %s" % patient['id'])
            patients[patient['id']] = patient

            patient_pk += 1

        for service_xml in register_set[organization]['services']:

            registers_set_id.append(register_pk)

            service_file = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(REGISTRY_PROCESSING_DIR, service_xml['filename']))

            copy_path = '%s%s %s/' % (OUTBOX_DIR,
                                      service_xml['organization_code'],
                                      outbox[service_xml['organization_code']])

            service_errors = []
            patients_set = []
            records_set = []
            events_set = []
            services_set = []
            concomitant_disease_set = []
            complicated_disease_set = []
            record_numbers = []
            event_numbers = []
            service_numbers = []

            invoiced = False

            for item in service_file.find(tags=('SCHET', 'ZAP')):
                if 'NSCHET' in item and not invoiced:
                    invoiced = True

                    invoice = dict(id=item['NSCHET'], organization=item['CODE_MO'],
                                   year=item['YEAR'], date=item['DSCHET'])

                    invoice['period'] = item['MONTH'] if len(
                        item['MONTH']) == 2 else '0' + item['MONTH']

                    new_register = MedicalRegister(pk=register_pk,
                        timestamp=datetime.now(),
                        type=service_xml['type'],
                        filename=service_xml['filename'],
                        organization_code=invoice['organization'],
                        is_active=True,
                        year=invoice['year'],
                        period=invoice['period'],
                        status=MedicalRegisterStatus.objects.get(pk=12),
                        invoice_date=invoice['date'])
                    registers_set_id.append(register_pk)

                    old_registers = MedicalRegister.objects.filter(
                        #type=service_xml['type'],
                        year=invoice['year'],
                        period=invoice['period'],
                        is_active=True,
                        organization_code=invoice['organization'])

                if 'N_ZAP' in item:
                    event_numbers = []
                    patient = patients.get(item['PACIENT']['ID_PAC'], None)

                    if not patient:
                        raise ValueError("Patient not found!!!")

                    record_obj = ValidRecord(item, record_pk, new_register,
                                             patient['id_pk'])

                    record_pk += 1

                    if record_obj.id in record_numbers:
                        service_errors.append((
                            True, '904', 'ZAP', 'N_ZAP', record_obj.id, 0, 0,
                            u'Дубликат уникального номера записи %s' % record_obj.id))
                    else:
                        record_numbers.append(record_obj.id)

                    records_set.append(record_obj.get_object())
                    if patient:
                        patient['insurance_policy_type'] = item['PACIENT']['VPOLIS']
                        patient['insurance_policy_series'] = item['PACIENT'][
                            'SPOLIS']
                        patient['insurance_policy_number'] = item['PACIENT'][
                            'NPOLIS']
                        patient['newborn_code'] = item['PACIENT']['NOVOR']

                        patient_obj = ValidPatient(patient, record_obj.id)

                        patients_set.append(patient_obj.get_object())

                        patient_errors += filter(lambda a: a[0] is False, patient_obj.validate())
                        service_errors += filter(lambda a: a[0] is True, patient_obj.validate())

                    else:
                        patient_errors += [False, 904, 'PACIENT', 'ID_PAC', record_obj.id,
                                   None, None, u'Отстутствуют сведения о пациенте']
                    service_errors += record_obj.validate()

                    events = [item['SLUCH']] if type(item['SLUCH']) != list else \
                        item['SLUCH']

                    for event in events:
                        if not event:
                            raise ValueError("EVENT is None in RECORD %s" % record_obj.id)
                        event_obj = ValidEvent(event, event_pk, record_obj)
                        if event_obj.id in event_numbers:
                            service_errors.append((True, '904', 'SLUCH', 'IDCASE', record_obj.id,
                                       event_obj.id, 0,
                                       u'Дубликат номера случая %s в записи' % event_obj.id))
                        else:
                            event_numbers.append(event_obj.id)

                        concomitant_diseases = [event['DS2']]
                        for disease in concomitant_diseases:
                            disease_instance = ValidConcomitantDisease(disease, event_obj)
                            service_errors += disease_instance.validate()
                            disease_obj = disease_instance.get_object()
                            if disease_obj:
                                concomitant_disease_set.append(disease_obj)

                        complicated_diseases = [event['DS3']]
                        for disease in complicated_diseases:
                            disease_instance = ValidComplicatedDisease(disease, event_obj)
                            service_errors += disease_instance.validate()
                            disease_obj = disease_instance.get_object()
                            if disease_obj:
                                complicated_disease_set.append(disease_obj)

                        service_errors += event_obj.validate()
                        event_pk += 1
                        events_set.append(event_obj.get_object())

                        if not event['USL']:
                            service_errors.append((True, '904', 'SLUCH', 'USL', record_obj.id,
                                       event_obj.id, 0,
                                       u'Отсутствие услуги в случае'))
                            services = []
                        else:
                            services = [event['USL']] if type(
                                event['USL']) != list else event['USL']
                        service_numbers = []
                        for service in services:
                            try:
                                service_obj = ValidService(service, service_pk,
                                                           event_obj)
                            except TypeError:
                                print services
                                raise TypeError("Oops!")

                            if service_obj.id in service_numbers:
                                service_errors.append((True, '904', 'USL', 'IDSERVE', record_obj.id,
                                           event_obj.id, service_obj.id,
                                           u'Дубликат номера услуги %s в случае' % service_obj.id))
                            else:
                                service_numbers.append(service_obj.id)

                            service_pk += 1
                            service_errors += service_obj.validate()
                            services_set.append(service_obj.get_object())
                            #print service_obj.id_pk, service_obj.event
                            if service_obj.get_object() is None:
                                print service_obj

            register_pk += 1

            if service_errors:
                error_organization = True
                print u'Есть ошибки: ', len(service_errors)
                errors_filenames.append("V%s" % service_xml['filename'])
                hflk = xml_writer.Xml(TEMP_DIR+"V%s" % service_xml['filename'])
                hflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
                hflk.start('FLK_P')
                hflk.put('FNAME', "V%s" % service_xml['filename'][:-4])
                hflk.put('FNAME_I', '%s' % service_xml['filename'][:-4])

                for rec in service_errors:
                    hflk.start('PR')
                    hflk.put('OSHIB', rec[1])
                    hflk.put('IM_POL', rec[3])
                    hflk.put('BASE_EL', rec[2])
                    hflk.put('N_ZAP', rec[4])
                    hflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                    hflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                    hflk.put('COMMENT', rec[7].encode('cp1251'))
                    hflk.end('PR')

                hflk.end('FLK_P')
                hflk.close()
            else:
                #old_registers.update(is_active=False)
                new_register.save()
                patients_super_set += patients_set
                records_super_set += records_set
                events_super_set += events_set
                services_super_set += services_set
                concomitant_disease_super_set += concomitant_disease_set
                complicated_disease_super_set += complicated_disease_set

        if patient_errors:
            error_organization = True
            errors_filenames.append("V%s" % register_set[organization]['patients'])
            lflk = xml_writer.Xml(TEMP_DIR+"V%s" % register_set[organization]['patients'])
            lflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
            lflk.start('FLK_P')
            lflk.put('FNAME', "V%s" % register_set[organization]['patients'][:-4])
            lflk.put('FNAME_I', '%s' % register_set[organization]['patients'][:-4])

            for rec in patient_errors:
                lflk.start('PR')
                lflk.put('OSHIB', rec[1])
                lflk.put('IM_POL', rec[3])
                lflk.put('BASE_EL', rec[2])
                lflk.put('N_ZAP', rec[4])
                lflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                lflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                lflk.put('COMMENT', rec[7].encode('cp1251'))
                lflk.end('PR')

            lflk.end('FLK_P')
            lflk.close()

        if error_organization:

            MedicalRegister.objects.filter(organization_code=organization,
                                           year=invoice['year'],
                                           period=invoice['period'],
                                           is_active=True,
                                           status_id=12)\
                                   .update(status=MedicalRegisterStatus.objects.get(pk=100),
                                           is_active=False)

            print u'Ошибки ФЛК'
            #transaction.rollback()
            zipname = TEMP_DIR+'VM%sS28002_%s.zip' % (
                service_xml['organization_code'],
                service_xml['filename'][service_xml['filename'].index('_')+1:-4]
            )

            with ZipFile(zipname, 'w') as zipfile:
                for filename in errors_filenames:
                    zipfile.write(TEMP_DIR+filename, filename, 8)
                    os.remove(TEMP_DIR+filename)

            shutil.copy2(zipname, 'd:/work/xml_archive/')

            if os.path.exists(copy_path):
                shutil.copy2(zipname, copy_path)

            os.remove(zipname)

        else:
            print u'ФЛК пройдён.'

            Patient.objects.bulk_create(set(patients_super_set))
            MedicalRegisterRecord.objects.bulk_create(set(records_super_set))
            ProvidedEvent.objects.bulk_create(set(events_super_set))
            ProvidedEventConcomitantDisease.objects.bulk_create(set(concomitant_disease_super_set))
            ProvidedEventComplicatedDisease.objects.bulk_create(set(complicated_disease_super_set))
            ProvidedService.objects.bulk_create(set(services_super_set))

            old_registers.update(is_active=False)
            MedicalRegister.objects.filter(pk__in=registers_set_id).update(
                status=MedicalRegisterStatus.objects.get(pk=1), is_active=True)
            #transaction.commit()
            if os.path.exists(copy_path):
                shutil.copy2(OUTBOX_SUCCESS, copy_path)


    for code in register_set:
        files = [rec['filename'] for rec in register_set[code]['services']] + [register_set[code]['patients']]
        move_files_to_archive(files)


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()