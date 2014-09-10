#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db.models import Max
from tfoms.models import (ProvidedEvent, ProvidedService, MedicalRegister,
                          Patient, ProvidedEventConcomitantDisease,
                          ProvidedEventComplicatedDisease,
                          Person, InsurancePolicy, MedicalRegisterRecord,
                          PersonIDType, MedicalServiceTerm,
                          MedicalServiceKind, MedicalServiceForm,
                          MedicalDivision, MedicalServiceProfile,
                          TreatmentResult, TreatmentOutcome, Special,
                          MedicalWorkerSpeciality, PaymentMethod,
                          PaymentType, PaymentFailureCause, MedicalRegister,
                          MedicalRegisterStatus, MedicalOrganization,
                          SERVICE_XML_TYPES)

from django.db import transaction
from helpers.xml_parser import XmlLikeFileReader
from helpers.validation import ValidPatient, ValidRecord, ValidEvent,\
    ValidService, ValidConcomitantDisease, ValidComplicatedDisease
from helpers import xml_writer

import os
import re
from datetime import datetime


def get_valid_xmls_info(files):
    valid_name_pattern = re.compile(r'^[hm|tm|dp|dv|do|ds|du|df|dd|dr]{2}M?28\d{4}s28002_\d{4}\d+.xml',
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
        code_token = re.search(r'28\d{4}', name)
        organization_code = code_token.group()

        #xml_code = name[15:-4]

        info = {'type': type, 'organization_code': organization_code,
                'filename': name}

        if info not in valid_xmls_info:
            valid_xmls_info.append(info)
    return valid_xmls_info


def main():
    patients = {}
    register_dir = "d:/work/register_import"
    flk_dir = "d:/work/medical_register/"
    files = os.listdir(register_dir)

    valid_xmls = get_valid_xmls_info(files)
    register_set = {}

    for xml in valid_xmls:
        if xml['organization_code'] in register_set:
            register_set[xml['organization_code']]['services'].append(xml)
        else:
            register_set[xml['organization_code']] = {
                'patients': 'LM'+xml['filename'][2:].strip('M'),
                'services': [xml]}

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

        error_organization = False
        print u'Обрабатаываю МО ', organization, \
            MedicalOrganization.objects.get(code=organization, parent=None).name
        patients_errors = []

        lflk = xml_writer.Xml("V%s" % register_set[organization]['patients'])
        lflk.plain_put('<?xml version="2.1" encoding="windows-1251"?>')
        lflk.start('FLK_P')
        lflk.put('FNAME', "V%s" % register_set[organization]['patients'][:-4])
        lflk.put('FNAME_I', '%s' % register_set[organization]['patients'][:-4])

        if register_set[organization]['patients']:
            person_file = XmlLikeFileReader('{0:s}/LM{1:s}'.format(
                register_dir, register_set[organization]['patients'][2:]))
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
            service_file = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, service_xml['filename']))

            errors = []
            patients_set = []
            records_set = []
            events_set = []
            services_set = []
            concomitant_disease_set = []
            complicated_disease_set = []

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
                        status=MedicalRegisterStatus.objects.get(pk=1),
                        invoice_date=invoice['date'])

                    old_registers = MedicalRegister.objects.filter(
                        type=service_xml['type'],
                        year=invoice['year'],
                        period=invoice['period'],
                        is_active=True,
                        organization_code=invoice['organization'])

                if 'N_ZAP' in item:
                    patient = patients.get(item['PACIENT']['ID_PAC'], None)

                    if not patient:
                        raise ValueError("Patient not found!!!")

                    record_obj = ValidRecord(item, record_pk, new_register,
                                             patient['id_pk'])

                    record_pk += 1

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

                        errors += patient_obj.validate()

                    else:
                        errors += [False, 904, 'PACIENT', 'ID_PAC', record_obj.id,
                                   None, None, u'Отстутствуют сведения о пациенте']
                    errors += record_obj.validate()

                    events = [item['SLUCH']] if type(item['SLUCH']) != list else \
                        item['SLUCH']

                    for event in events:
                        if not event:
                            raise ValueError("EVENT is None in RECORD %s" % record_obj.id)
                        event_obj = ValidEvent(event, event_pk, record_obj)

                        concomitant_diseases = [event['DS2']]
                        for disease in concomitant_diseases:
                            disease_instance = ValidConcomitantDisease(disease, event_obj)
                            errors += disease_instance.validate()
                            disease_obj = disease_instance.get_object()
                            if disease_obj:
                                concomitant_disease_set.append(disease_obj)

                        complicated_diseases = [event['DS3']]
                        for disease in complicated_diseases:
                            disease_instance = ValidComplicatedDisease(disease, event_obj)
                            errors += disease_instance.validate()
                            disease_obj = disease_instance.get_object()
                            if disease_obj:
                                complicated_disease_set.append(disease_obj)

                        errors += event_obj.validate()
                        event_pk += 1
                        events_set.append(event_obj.get_object())

                        if not event['USL']:
                            errors.append((True, '904', 'SLUCH', 'USL', record_obj.id,
                                       event_obj.id, 0,
                                       u'Отсутствие услуги в случае'))
                            services = []
                        else:
                            services = [event['USL']] if type(
                                event['USL']) != list else event['USL']

                        for service in services:
                            try:
                                service_obj = ValidService(service, service_pk,
                                                           event_obj)
                            except TypeError:
                                print services
                                raise TypeError("Oops!")
                            service_pk += 1
                            errors += service_obj.validate()
                            services_set.append(service_obj.get_object())
                            #print service_obj.id_pk, service_obj.event
                            if service_obj.get_object() is None:
                                print service_obj
            register_pk += 1

            if errors:
                error_organization = True
                print u'Есть ошибки: ', len(errors)
                hflk = xml_writer.Xml("V%s" % service_xml['filename'])
                hflk.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
                hflk.start('FLK_P')
                hflk.put('FNAME', "V%s" % service_xml['filename'][:-4])
                hflk.put('FNAME_I', '%s' % service_xml['filename'][:-4])

                for rec in errors:
                    if rec[0]:
                        hflk.start('PR')
                        hflk.put('OSHIB', rec[1])
                        hflk.put('IM_POL', rec[3])
                        hflk.put('BASE_EL', rec[2])
                        hflk.put('N_ZAP', rec[4])
                        hflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                        hflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                        hflk.put('COMMENT', rec[7].encode('cp1251'))
                        hflk.end('PR')
                    else:
                        try:
                            lflk.start('PR')
                            lflk.put('OSHIB', rec[1])
                            lflk.put('IM_POL', rec[3])
                            lflk.put('BASE_EL', rec[2])
                            lflk.put('N_ZAP', rec[4])
                            lflk.put('IDCASE', rec[5].encode('cp1251') if rec[5] else 0)
                            lflk.put('IDSERV', rec[6].encode('cp1251') if rec[6] else 0)
                            lflk.put('COMMENT', rec[7].encode('cp1251'))
                            hflk.end('PR')
                        except:
                            print rec, rec[-1]
                            raise ValueError('custom raise')

                hflk.end('FLK_P')
                lflk.end('FLK_P')
            else:
                old_registers.update(is_active=False)
                new_register.save()
                patients_super_set += patients_set
                records_super_set += records_set
                events_super_set += events_set
                services_super_set += services_set
                concomitant_disease_super_set += concomitant_disease_set
                complicated_disease_super_set += complicated_disease_set

        if error_organization:
            MedicalRegister.objects.filter(organization_code=organization,
                                           year=invoice['year'],
                                           period=invoice['period'],
                                           is_active=True)\
                                   .update(status=MedicalRegisterStatus.objects.get(pk=100),
                                           is_active=False)
            print u'Ошибки ФЛК'
        else:
            print u'ФЛК пройдён.'
            Patient.objects.bulk_create(set(patients_super_set))
            MedicalRegisterRecord.objects.bulk_create(set(records_super_set))
            ProvidedEvent.objects.bulk_create(set(events_super_set))
            ProvidedEventConcomitantDisease.objects.bulk_create(set(concomitant_disease_super_set))
            ProvidedEventComplicatedDisease.objects.bulk_create(set(complicated_disease_super_set))
            ProvidedService.objects.bulk_create(set(services_super_set))


class Command(BaseCommand):
    help = 'import MO xml'

    def handle(self, *args, **options):
        main()