# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import (ProvidedEvent, ProvidedService, MedicalRegister,
                          IDC, MedicalOrganization, Patient,
                          Person, InsurancePolicy, MedicalRegisterRecord,
                          PersonIDType, MedicalServiceTerm,
                          MedicalServiceKind, MedicalServiceForm,
                          MedicalDivision, MedicalServiceProfile,
                          TreatmentResult, TreatmentOutcome, Special,
                          MedicalWorkerSpeciality, PaymentMethod,
                          PaymentType, PaymentFailureCause, Gender,
                          InsurancePolicyType, MedicalHospitalization,
                          MedicalService)

import dbf
import os
from datetime import datetime
from profiling import profile
import sys
from django.db import transaction


def getsubs(dir):
    dirs = []
    files = []
    for dirname, dirnames, filenames in os.walk(dir):
        dirs.append(dirname)
        for subdirname in dirnames:
            dirs.append(os.path.join(dirname, subdirname))
        for filename in filenames:
            files.append(os.path.join(dirname, filename))

    return dirs, files


def q_to_d(qs):
    t = {}
    for rec in qs:
        t[rec.code] = rec.pk
    return t


def q_to_d_2(qs):
    t = {}
    for rec in qs:
        t[rec.old_code] = rec.pk
    return t


def q_to_d_3(qs):
    t = {}
    for rec in qs:
        t[rec.idc_code] = rec.pk
    return t

GENDERS = q_to_d(Gender.objects.all())
POLICY_TYPES= q_to_d(InsurancePolicyType.objects.all())
DEPARTMENTS = q_to_d_2(MedicalOrganization.objects.all())
ORGANIZATIONS = q_to_d(MedicalOrganization.objects.filter(parent=None))
TERMS = q_to_d(MedicalServiceTerm.objects.all())
KINDS = q_to_d(MedicalServiceKind.objects.all())
FORMS = q_to_d(MedicalServiceForm.objects.all())
HOSPITALIZATIONS = q_to_d(MedicalHospitalization.objects.all())
PROFILES = q_to_d(MedicalServiceProfile.objects.all())
OUTCOMES = q_to_d(TreatmentOutcome.objects.all())
RESULTS = q_to_d(TreatmentResult.objects.all())
SPECIALITIES = q_to_d(MedicalWorkerSpeciality.objects.all())
METHODS = q_to_d(PaymentMethod.objects.all())
TYPES = q_to_d(PaymentType.objects.all())
FAILURE_CUASES = q_to_d(PaymentFailureCause.objects.all())
DISEASES = q_to_d_3(IDC.objects.all())
DIVISIONS = q_to_d(MedicalDivision.objects.all())
SPECIALS = q_to_d(Special.objects.all())
CODES = q_to_d(MedicalService.objects.all())


def patient_converter(record):
    d = dict(
        id=record['id_pac'], newborn_code=record['novor'].strip(),
        is_newborn=False,
        last_name=record['fam'].strip(),
        first_name=record['im'].strip(),
        middle_name=record['ot'].strip(),
        gender_id=GENDERS.get(record['w'], None), birthdate=record['dr'],
        agent_last_name=record['fam_p'].strip(),
        agent_first_name=record['im_p'].strip(),
        agent_middle_name=record['ot_p'].strip(),
        agent_gender_id=GENDERS.get(record['w_p'], None),
        agent_birthdate=record['dr_p'], birthplace=record['mr'].strip(),
        person_id_series=record['docser'][:10],
        person_id_number=record['docnum'].strip(),
        snils=record['snils'].strip(),
        insurance_policy_type_id=POLICY_TYPES.get(record['vpolis'], None),
        insurance_policy_series=record['spolis'].strip(),
        insurance_policy_number=record['npolis'].strip(),
        okato_registration=record['okatog'].strip(),
        okato_residence=record['okatop'].strip(),)

    return d


def registry_converter(tfile):
    code_mo=tfile.filename[29:-4]
    d = dict(year='2010', period=tfile.filename[25:27],
        invoice_date=datetime.now(), filename=tfile.filename[28:],
        organization_id=ORGANIZATIONS.get(tfile.filename[29:-4], None),)

    return d


def record_converter(record):
    d = dict(id=record['n_zap'])
    return d


def event_converter(record):
    division=str(record['podr']) if record['podr'] else '0'
    if division and len(division) < 3:
        division='0'*(3-len(division))+division

    try:
        DS2 = record['DS2'].strip()
    except:
        DS2 = None
    d = dict(id=record['idcase'], term_id=TERMS.get(record['usl_ok'], None),
        kind_id=KINDS.get(record['vidpom'], None),
        refer_organization_id=ORGANIZATIONS.get(record['npr_mo'], None),
        organization_id=ORGANIZATIONS.get(record['lpu'].strip(), None),
        department_id=DEPARTMENTS.get(record['lpu_1'].strip(), None),
        profile_id=PROFILES.get(record['profil'], None),
        is_children_profile=True if record['det'] == '1' else False,
        anamnesis_number=record['nhistory'].strip(),
        start_date=record['date_1'],
        end_date=record['date_2'],
        initial_disease_id=DISEASES.get(record['ds0'].strip(), None),
        basic_disease_id=DISEASES.get(record['ds1'].strip(), None),
        concomitant_disease_id=DISEASES.get(DS2, None),
        payment_method_id=METHODS.get(record['idsp'], None),
        payment_units_number=record['ed_col'],
        comment=record['comentz'].strip(),
        division_id=DIVISIONS.get(division, None),
        treatment_result_id=RESULTS.get(record['rslt'], None),
        treatment_outcome_id=OUTCOMES.get(record['ishod'], None),
        worker_speciality_id=SPECIALITIES.get(record['prvs'], None),
        worker_code=record['iddokt'].strip(),
        special_id=SPECIALS.get(record['os_sluch'], None),
        hospitalization_id=HOSPITALIZATIONS.get(record['extr'], None))

    return d

def service_converter(record):
    division = str(record['podr']) if record['podr'] else '0'
    if division and len(division) < 3:
        division = '0'*(3-len(division))+division

    try:
        koef_l = record['koef_l'] or 1
    except:
        koef_m = 1
    try:
        koef_m = record['koef_m'] or 1
    except:
        koef_m = 1
    try:
        koef_s = record['koef_s'] or 1
    except:
        koef_s = 1
    try:
        o_dop = record['o_dop'] or 0
    except:
        o_dop = 0
    try:
        t_dop = record['t_dop'] or 0
    except:
        t_dop = 0
    try:
        f_dop = record['f_dop'] or 0
    except:
        f_dop = 0

    #koef_s = 1
    accepted_payment = float(record['sumv_usl']) * koef_l * koef_m * koef_s + o_dop + t_dop + f_dop
    invoiced_payment = float(record['sumv_usl']) * koef_l * koef_m * koef_s + o_dop + t_dop + f_dop

    d = dict(
        id=record['idserv'],
        organization_id=ORGANIZATIONS.get(record['lpu'].strip(), None),
        department_id=DEPARTMENTS.get(record['lpu_1'].strip(), None),
        division_id=DIVISIONS.get(division, None),
        profile_id=PROFILES.get(record['profil'], None),
        is_children_profile=True if record['det'] == '1' else False,
        start_date=record['date_in'], end_date=record['date_out'],
        basic_disease_id=DISEASES.get(record['ds'].strip(), None),
        code_id=CODES.get(record['code_usl'].strip(), None),
        quantity=record['kol_usl'], comment=record['comentu'].strip(),
        worker_speciality_id=SPECIALITIES.get(record['prvs'], None),
        worker_code=record['code_md'].strip(),
        accepted_payment=accepted_payment,
        invoiced_payment=invoiced_payment,
        tariff=record['tarif_2'],
        payment_type_id=TYPES.get(record['oplata'], None),
        payment_failure_cause_id=FAILURE_CUASES.get(record['refreason'], None),
        tfoms_surcharge=t_dop, ffoms_surcharge=f_dop,
        single_channel_surcharge=o_dop,
        sanctions_mek=record['sank_mek'], sanctions_mee=record['sank_mee'],
        sanctions_ekmp=record['sank_ekmp'],
        comment_error=record['err_all'].strip())
    return d


@transaction.commit_on_success()
def main():
    dirs, files = getsubs('d:/work/try_reestr')

    patient_pk = Patient.objects.latest('id_pk').pk
    record_pk = MedicalRegisterRecord.objects.latest('id_pk').pk
    event_pk = ProvidedEvent.objects.latest('id_pk').pk
    service_pk = ProvidedService.objects.latest('id_pk').pk

    for filename in files:
        start = datetime.now()
        print filename
        patients_pk = []
        patients = []
        records_pk = []
        records = []
        events = []
        events_pk = []
        services = []

        db = dbf.Table(filename)
        db.open()

        registry = registry_converter(db)
        active_registries = MedicalRegister.objects.filter(
            period=registry['period'], year=registry['year'], is_active=True,
            organization_id=registry['organization_id'])
        active_registries.update(is_active=False)

        registry_insert = MedicalRegister(**registry)
        registry_insert.save()

        for service_no, rec in enumerate(db):

            if rec['id_pac'] not in patients_pk:
                patient_pk += 1
                patient = patient_converter(rec)
                patient['id_pk'] = patient_pk
                patients_pk.append(patient['id'])
                patients.append(Patient(**patient))

            if rec['n_zap'] not in records_pk:
                record_pk += 1
                record = record_converter(rec)
                record['patient_id'] = patient_pk
                record['register_id'] = registry_insert.pk
                record['id_pk'] = record_pk
                records_pk.append(record['id'])
                records.append(MedicalRegisterRecord(**record))

            if rec['idcase'] not in events_pk:
                event_pk += 1
                event = event_converter(rec)
                event['record_id'] = record_pk
                event['id_pk'] = event_pk
                events_pk.append(event['id'])
                events.append(ProvidedEvent(**event))

            service = service_converter(rec)
            service_pk += 1
            service['id_pk'] = service_pk
            service['event_id'] = event_pk
            services.append(ProvidedService(**service))

        db.close()
        Patient.objects.bulk_create(patients)
        MedicalRegisterRecord.objects.bulk_create(records)
        ProvidedEvent.objects.bulk_create(events)
        ProvidedService.objects.bulk_create(services)
        end = datetime.now()
        print end-start
        transaction.commit()


class Command(BaseCommand):
    help = 'export big XML'

    def handle(self, *args, **options):
        main()
