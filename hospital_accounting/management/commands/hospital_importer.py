# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from hospital_accounting.models import HospitalizationsRoom, HospitalizationPatient
from hospital_accounting.models import Hospitalization, HospitalizationsAmount, Disease
from hospital_accounting.models import MedicalDivision
from hospital_accounting.models import MedicalServiceProfile, TreatmentResult
from hospital_accounting.models import MedicalOrganization, MedicalWorkerSpeciality
from lxml import etree
import re
import os
from datetime import datetime


class Node(dict):
    def __init__(self, element):
        self.element = element
        dict.__init__(self)

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            value = None

        if not value and isinstance(value, dict):
            value = value.element.text

        return value


class XmlLikeFileReader(object):

    def __init__(self, file_name):
        self.file_name = file_name

    def find(self, tags):

        file_stream = open(self.file_name, 'rb')

        item = Node(None)

        parents = []
        node_weight = 0

        for event, element in etree.iterparse(
                file_stream, events=("start", "end"),
                encoding='utf-8'):

            if event == 'start':

                if element.tag in tags:
                    node_weight += 1

                if node_weight > 0:
                    parents.append(item)
                    item = Node(element)

            else:

                if node_weight <= 0:
                    continue

                if element.tag in tags:
                    node_weight -= 1
                    yield item

                parent = parents.pop()

                if node_weight > 0:

                    if element.tag in parent:

                        items = parent.get(element.tag)

                        if type(items) != list:
                            items = [items]

                        parent[element.tag] = items
                        items.append(item)

                    else:

                        parent[element.tag] = item

                item = parent

        file_stream.close()


def get_valid_xmls_info(files):
    valid_name_pattern = re.compile(r'^(sn|sh|se|sa|sv|so|sm|sp|sr)s2800_\d{6}\d+.xml',
                                    re.IGNORECASE)

    XML_TYPE = {'SN': 1, 'SH': 2, 'SE': 3, 'SA': 4,
                'SV': 5, 'SO': 6, 'SM': 7, 'SP': 8,
                'SR': 9}

    valid_xmls_info = []

    for name in files:
        print name
        match = valid_name_pattern.match(name)

        if not match:
            print 'not match'
            continue

        type = XML_TYPE[name[:2].upper()]
        xml_code = name[15:-4]
        date = datetime.strptime(name[8:14], '%y%m%d').date()
        info = {'type': type, 'code': xml_code, 'name': name, 'date': date}

        if info not in valid_xmls_info:
            valid_xmls_info.append(info)

    print valid_xmls_info
    return valid_xmls_info

ORGANIZATIONS = {rec.code: rec for rec in MedicalOrganization.objects.filter(parent=None)}
DEPARTMENTS = {rec.old_code: rec for rec in MedicalOrganization.objects.all()}
PROFILES = {rec.code: rec for rec in MedicalServiceProfile.objects.all()}
WORKER_SPECIALITIES = {rec.code: rec for rec in MedicalWorkerSpeciality.objects.all()}
DISEASES = {rec.idc_code: rec for rec in Disease.objects.all()}
DIVISIONS = {rec.code: rec for rec in MedicalDivision.objects.all() if rec.code}
RESULTS = {rec.code: rec for rec in TreatmentResult.objects.all()}


def hospital_import():

    register_dir = "c:/work/hospitalizations"
    files = os.listdir(register_dir)
    print files
    hospitalizations_referral = hospitalized_by_referral = \
    hospitalized_urgently = canceled_hospitalizations = \
    finished_hospitalizations = hospitalizations_amount = \
    hospitalizations_room = None

    valid_xmls = get_valid_xmls_info(files)

    for xml in valid_xmls:
        print xml['name']

        if xml['type'] == 1:
            hospitalizations_referrals = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in hospitalizations_referrals.find('ZL'):
                last_name = item['FAM']
                first_name = item['IM']
                middle_name = item['OT']
                birthdate = item['DR']
                gender = item['W']
                contact = item['CONTACT']
                enp = item['ENP']
                policy_series = item['SPOLIS']
                policy_number = item['NPOLIS']
                policy_type = item['VPOLIS']
                id_type = int((item['DOCTYPE'] or '0').replace(',', ''))
                id_series = item['DOCSER']
                id_number = item['DOCNUM']
                snils = item['SNILS']

                try:
                    patient = HospitalizationPatient.objects.get(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp)
                except:
                    patient = HospitalizationPatient(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp, gender=gender,
                        contact=contact, insurance_policy_type=policy_type,
                        person_id_type=id_type, person_id_number=id_number,
                        person_id_series=id_series, snils=snils)
                    patient.save()

                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                organization_sender = ORGANIZATIONS.get(item['MCODE1'], None)
                department_sender = DEPARTMENTS.get(item['PODR1'], None)
                organization_reciever = ORGANIZATIONS.get(item['MCODE2'], None)
                department_reciever = DEPARTMENTS.get(item['PODR2'], None)
                worker_speciality = WORKER_SPECIALITIES.get(item['PRVS'], None)
                worker_code = item['IDDOKT']
                form = item['FORM'] or 1
                disease = DISEASES.get(item['DS'], None)
                profile = PROFILES.get(item['PROFIL_K'], None)
                division = DIVISIONS.get(item['PROFIL_O'], None)
                start_date = item['PDATE']
                comment = item['COMENTZ']

                Hospitalization.objects.create(
                    patient=patient, uid=uid, number=number, date=date,
                    organization_sender=organization_sender,
                    department_sender=department_sender,
                    organization_reciever=organization_reciever,
                    department_reciever=department_reciever,
                    worker_speciality=worker_speciality,
                    worker_code=worker_code, form=int(form), disease=disease,
                    profile=profile, division=division, start_date=start_date,
                    comment=comment, type=1, received_date=xml['date'])

        elif xml['type'] == 2:
            hospitalized_by_referral = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in hospitalized_by_referral.find('ZL'):
                last_name = item['FAM']
                first_name = item['IM']
                middle_name = item['OT']
                birthdate = item['DR']
                gender = item['W']
                contact = item['CONTACT']
                enp = item['ENP']
                policy_series = item['SPOLIS']
                policy_number = item['NPOLIS']
                policy_type = item['VPOLIS']
                id_type = int((item['DOCTYPE'] or '0').replace(',', ''))
                id_series = item['DOCSER']
                id_number = item['DOCNUM']
                snils = item['SNILS']

                try:
                    patient = HospitalizationPatient.objects.get(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp)
                except:
                    patient = HospitalizationPatient(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp, gender=gender,
                        contact=contact, insurance_policy_type=policy_type,
                        person_id_type=id_type, person_id_number=id_number,
                        person_id_series=id_series, snils=snils)
                    patient.save()

                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                organization_sender = ORGANIZATIONS.get(item['MCODE1'], None)
                department_sender = DEPARTMENTS.get(item['PODR1'], None)
                organization_reciever = ORGANIZATIONS.get(item['MCODE2'], None)
                department_reciever = DEPARTMENTS.get(item['PODR2'], None)
                form = item['FORM'] or 1

                if type(item['DS']) == list:
                    disease_elem = item['DS'][0].element.text
                else:
                    disease_elem = item['DS']

                disease = DISEASES.get(disease_elem, None)
                profile = PROFILES.get(item['PROFIL_K'], None)
                division = DIVISIONS.get(item['PROFIL_O'], None)
                anamnesis_number = item['CARD_NUM']
                start_date = item['FDATE'] or '1900-01-01'
                if item['FTIME']:
                    start_time = datetime.strptime(item['FTIME'], '%H%M')
                else:
                    start_time = None
                comment = item['COMENTZ']

                Hospitalization.objects.create(
                    patient=patient, uid=uid, number=number, date=date,
                    organization_sender=organization_sender,
                    department_sender=department_sender,
                    organization_reciever=organization_reciever,
                    department_reciever=department_reciever,
                    form=int(form), disease=disease, time=start_time,
                    profile=profile, division=division, start_date=start_date,
                    comment=comment, type=2, anamnesis_number=anamnesis_number,
                    received_date=xml['date'])

        elif xml['type'] == 3:
            hospitalized_urgently = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in hospitalized_urgently.find('ZL'):
                last_name = item['FAM']
                first_name = item['IM']
                middle_name = item['OT']
                birthdate = item['DR']
                gender = item['W']
                contact = item['CONTACT']
                enp = item['ENP']
                policy_series = item['SPOLIS']
                policy_number = item['NPOLIS']
                policy_type = item['VPOLIS']
                id_type = int((item['DOCTYPE'] or '0').replace(',', ''))
                id_series = item['DOCSER']
                id_number = item['DOCNUM']
                snils = item['SNILS']

                try:
                    patient = HospitalizationPatient.objects.get(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp)
                except:
                    patient = HospitalizationPatient(
                        last_name=last_name, first_name=first_name,
                        middle_name=middle_name, birthdate=birthdate,
                        insurance_policy_series=policy_series,
                        insurance_policy_number=policy_number,
                        insurance_policy_enp=enp, gender=gender,
                        contact=contact, insurance_policy_type=policy_type,
                        person_id_type=id_type, person_id_number=id_number,
                        person_id_series=id_series, snils=snils)
                    patient.save()

                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                organization_reciever = ORGANIZATIONS.get(item['MCODE2'], None)
                department_reciever = DEPARTMENTS.get(item['PODR2'], None)
                disease = DISEASES.get(item['DS'], None)
                profile = PROFILES.get(item['PROFIL_K'], None)
                division = DIVISIONS.get(item['PROFIL_O'], None)
                start_date = item['FDATE']
                if item['FTIME']:
                    start_time = datetime.strptime(item['FTIME'], '%H%M').time()
                else:
                    start_date = None
                anamnesis_number = item['CARD_NUM']
                comment = item['COMENTZ']
                form = int(item['FORM'] or 1)
                Hospitalization.objects.create(
                    patient=patient, uid=uid, number=number, date=date,
                    organization_reciever=organization_reciever,
                    department_reciever=department_reciever,
                    form=form, disease=disease, time=start_time,
                    profile=profile, division=division, start_date=start_date,
                    comment=comment, type=3, anamnesis_number=anamnesis_number,
                    received_date=xml['date'])

        elif xml['type'] == 4:
            canceled_hospitalizations = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in canceled_hospitalizations.find(tags=('NAPR',)):
                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                source = int(item['ISTOCH'] or 0)
                organization_reciever = ORGANIZATIONS.get(item['ICODE'], None)
                department_reciever = DEPARTMENTS.get(item['IPODR'], None)
                reason = int(item['REASON'] or 0)
                if item['FDATE']:
                    end_date = datetime.strptime(item['FDATE'], "%Y-%m-%d")
                else:
                    end_date = None
                comment = item['COMENTZ']

                Hospitalization.objects.create(
                    uid=uid, number=number, date=date,
                    organization_reciever=organization_reciever,
                    department_reciever=department_reciever,
                    source=source, reason=reason, end_date=end_date,
                    comment=comment, type=4,
                    received_date=xml['date'])

        elif xml['type'] == 5:
            finished_hospitalizations = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in finished_hospitalizations.find(tags=('ZL',)):
                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                organization_sender = ORGANIZATIONS.get(item['MCODE1'], None)
                department_sender = DEPARTMENTS.get(item['PODR1'], None)
                organization_reciever = ORGANIZATIONS.get(item['MCODE2'], None)
                department_reciever = DEPARTMENTS.get(item['PODR2'], None)
                profile = PROFILES.get(item['PROFIL_K'], None)
                division = DIVISIONS.get(item['PROFIL_O'], None)
                profile_reciever = PROFILES.get(item['PROFIL_K2'], None)
                division_reciever = DIVISIONS.get(item['PROFIL_O2'], None)
                if item['DATE_IN']:
                    start_date = datetime.strptime(item['DATE_IN'], '%Y-%m-%d').date()
                else:
                    start_date = None
                if item['DATE_OUT']:
                    end_date = datetime.strptime(item['DATE_OUT'], '%Y-%m-%d').date()
                else:
                    end_date = None
                #anamnesis_number = item['CARD_NUM']
                result = RESULTS.get(item['RSLT'], None)
                gender = int(item['W'] or 0)
                if item['DR']:
                    birthdate = datetime.strptime(item['DR'], '%Y-%m-%d').date()
                else:
                    birthdate = None
                form = int(item['FORM'] or 1)

                Hospitalization.objects.create(
                    uid=uid, number=number, date=date,
                    organization_sender=organization_sender,
                    department_sender=department_sender,
                    organization_reciever=organization_reciever,
                    department_reciever=department_reciever,
                    profile=profile, division=division,
                    profile_reciever=profile_reciever,
                    division_reciever=division_reciever,
                    start_date=start_date, end_date=end_date,
                    #anamnesis_number=anamnesis_number,
                    result=result,
                    gender=gender, birthdate=birthdate, form=form,
                    type=5, received_date=xml['date'])

        elif xml['type'] == 6:
            hospitalizations_amount = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))

            for item in hospitalizations_amount.find('SVED'):
                uid = item['N_REC']
                organization = ORGANIZATIONS.get(item['MCODE'], None)
                department = DEPARTMENTS.get(item['PODR'], None)
                profile = PROFILES.get(item['PROFIL'], None)
                planned = item['VPLANH']
                days_planned = item['VPLAND']
                remained = item['VRESTH']
                days_remained = item['VRESTD']
                comment = item['COMENTZ']

                HospitalizationsAmount.objects.create(
                    uid=uid,
                    organization=organization, department=department,
                    profile=profile, planned=planned, days_planned=days_planned,
                    days_remained=days_remained, remained=remained,
                    comment=comment, received_date=xml['date'])

        elif xml['type'] == 7:
            hospitalizations_room = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))

            for item in hospitalizations_room.find(tags=('MEST')):
                uid = item['N_REC']
                organization = ORGANIZATIONS.get(item['MCODE'], None)
                department = DEPARTMENTS.get(item['PODR'], None)
                profile = DIVISIONS.get(item['PROFIL'], None)
                profile = profile.pk if profile else None
                males_amount = item['MALLM']
                females_amount = item['MALLG']
                children_amount = item['MALLD']
                males_free_amount = item['MSVOBM']
                females_free_amount = item['MSVOBG']
                children_free_amount = item['MSVOBD']
                patients = item['ZL_SOST']
                patients_recieved = item['ZL_IN']
                patients_retired = item['ZL_OUT']
                patients_planned = item['ZL_PLAN']
                comment = item['COMENTZ']

                HospitalizationsRoom.objects.create(
                    uid=uid,
                    organization=organization, department=department,
                    profile=profile, males_amount=males_amount,
                    females_amount=females_amount,
                    children_amount=children_amount,
                    males_free_amount=males_free_amount,
                    females_free_amount=females_free_amount,
                    children_free_amount=children_free_amount,
                    patients_amount=patients,
                    patients_recieved=patients_recieved,
                    patients_retired=patients_retired, planned=patients_planned,
                    comment=comment, received_date=xml['date'])

        if xml['type'] == 9:
            hospitalizations_dates_clarifying = XmlLikeFileReader(
                '{0:s}/{1:s}'.format(register_dir, xml['name']))
            for item in hospitalizations_dates_clarifying.find('ZL'):
                uid = item['N_REC']
                number = item['NAPR_NUM']
                date = item['NAPR_DATE']
                organization_sender = ORGANIZATIONS.get(item['MCODE1'], None)
                organization_reciever = ORGANIZATIONS.get(item['MCODE2'], None)
                start_date = item['PDATE']

                Hospitalization.objects.create(
                    uid=uid, number=number, date=date,
                    organization_sender=organization_sender,
                    organization_reciever=organization_reciever,
                    start_date=start_date,
                    type=9, received_date=xml['date'])


class Command(BaseCommand):

    def handle(self, *args, **options):
        hospital_import()