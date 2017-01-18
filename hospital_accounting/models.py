# -*- coding: utf-8 -*-

from django.db.models import (Model, AutoField, CharField, BooleanField,
                              SmallIntegerField, ForeignKey, DateField,
                              IntegerField, TimeField)


class Disease(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    name = CharField(max_length=60)
    idc_code = CharField(max_length=6)

    class Meta:
        db_table = 'idc'


class MedicalOrganization(Model):
    id_pk = AutoField(primary_key=True, db_column='id_pk')
    code = CharField(max_length=6)
    name = CharField(max_length=80)
    old_code = CharField(max_length=8)
    parent = ForeignKey('self', db_column='parent_fk')

    class Meta:
        db_table = 'medical_organization'


class MedicalServiceProfile(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    code = CharField(max_length=3)
    name = CharField(max_length=40)

    class Meta:
        db_table = 'medical_service_profile'


class MedicalServiceLicense(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    code = CharField(max_length=3)
    name = CharField(max_length=230)

    class Meta:
        db_table = 'medical_service_license'


class TreatmentResult(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    code = IntegerField()
    name = CharField(max_length=120)

    class Meta:
        db_table = 'treatment_result'


class HospitalizationPatient(Model):
    id_pk = AutoField(primary_key=True, db_column='id_pk')
    first_name = CharField(max_length=40)
    last_name = CharField(max_length=40)
    middle_name = CharField(max_length=40)
    gender = SmallIntegerField()
    birthdate = DateField()
    contact = CharField(max_length=40)
    person_id_type = SmallIntegerField()
    person_id_series = CharField(max_length=10)
    person_id_number = CharField(max_length=20)
    snils = CharField(max_length=14)
    comment = CharField(max_length=250)
    insurance_policy_type = SmallIntegerField()
    insurance_policy_series = CharField(max_length=20)
    insurance_policy_number = CharField(max_length=20)
    insurance_policy_enp = CharField(max_length=20)

    class Meta:
        db_table = 'hospitalization_patient'


class HospitalizationsRoom(Model):
    id_pk = AutoField(primary_key=True, db_column='id_pk')
    uid = CharField(max_length=36)
    organization = ForeignKey(MedicalOrganization, db_column='organization_fk',
                              related_name='organization_room', null=True)
    department = ForeignKey(MedicalOrganization, db_column='department_fk',
                            related_name='department_room', null=True)
    profile = IntegerField(db_column='profile_fk',
                           null=True)
    males_amount = IntegerField()
    females_amount = IntegerField()
    children_amount = IntegerField()
    males_free_amount = IntegerField()
    females_free_amount = IntegerField()
    children_free_amount = IntegerField()
    patients_amount = IntegerField()
    patients_recieved = IntegerField()
    patients_retired = IntegerField()
    planned = IntegerField()
    comment = CharField(max_length=250)
    received_date = DateField()

    class Meta:
        db_table = 'hospitalizations_room'


class HospitalizationsAmount(Model):
    id_pk = AutoField(primary_key=True, db_column='id_pk')
    uid = CharField(max_length=36)
    organization = ForeignKey(MedicalOrganization, db_column='organization_fk',
                              related_name='organization', null=True)
    department = ForeignKey(MedicalOrganization, db_column='department_fk',
                            related_name='department', null=True)
    profile = ForeignKey(MedicalServiceLicense, db_column='profile_fk',
                         null=True)
    planned = IntegerField()
    remained = IntegerField()
    days_planned = IntegerField()
    days_remained = IntegerField()
    comment = CharField(max_length=250)
    received_date = DateField()

    class Meta:
        db_table = 'hospitalizations_amount'


class MedicalWorkerSpeciality(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    name = CharField(max_length=50)
    code = CharField(max_length=18)

    class Meta:
        db_table = "medical_worker_speciality"


class MedicalDivision(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    code = CharField(max_length=4)
    name = CharField(max_length=60)

    class Meta:
        db_table = "medical_division"


class Hospitalization(Model):

    TYPES = ((1, u'Направление'),
             (2, u'Плановая'),
             (3, u'Экстренная'),
             (4, u'Аннулирование'),
             (5, u'Выбытие'), )

    FORMS = ((1, u'Плановая'),
             (2, u'Неотложная'),
             (3, u'Экстренная'), )

    SOURCES = ((1, u'СМО'),
              (2, u'Стационар'),
              (3, u'Поликлиника'), )

    REASONS = ((1, u'Неявка'),
              (2, u'Отказ МО'),
              (3, u'Отказ пациента'),
              (4, u'Смерть'),
              (5, u'Прочие'), )

    id_pk = AutoField(primary_key=True, db_column='id_pk')
    uid = CharField(max_length=36)
    number = CharField(max_length=16)
    patient = ForeignKey(HospitalizationPatient, db_column='patient_fk')
    organization_sender = ForeignKey(MedicalOrganization,
                                     db_column='organization_sender_fk',
                                     related_name='sender_organization_fkey',
                                     null=True)
    department_sender = ForeignKey(MedicalOrganization,
                                   db_column='department_sender_fk',
                                   related_name='sender_department_fkey',
                                   null=True)
    organization_reciever = ForeignKey(MedicalOrganization,
                                       db_column='organization_reciever_fk',
                                       related_name='reciever_organization_fkey',
                                       null=True)
    department_reciever = ForeignKey(MedicalOrganization,
                                     db_column='department_reciever_fk',
                                     related_name='reciever_department_fkey',
                                     null=True)
    worker_speciality = ForeignKey(MedicalWorkerSpeciality,
                                   db_column='worker_speciality_fk', null=True)
    worker_code = CharField(max_length=25)
    form = SmallIntegerField(choices=FORMS)
    disease = ForeignKey(Disease, db_column='disease_fk', null=True)
    profile = ForeignKey(MedicalServiceLicense, db_column='profile_fk', null=True)
    division = ForeignKey(MedicalDivision, db_column='division_fk', null=True)
    profile_reciever = ForeignKey(MedicalServiceLicense, null=True,
                                  db_column='profile_reciever_fk',
                                  related_name='profile_reciever_fkey')
    division_reciever = ForeignKey(MedicalDivision, null=True,
                                   db_column='division_reciever_fk',
                                   related_name='profile_reciever_fkey')
    date = DateField()
    start_date = DateField()
    end_date = DateField()
    anamnesis_number = CharField(max_length=200)
    time = TimeField()
    type = SmallIntegerField(choices=TYPES)
    source = SmallIntegerField(choices=SOURCES)
    reason = SmallIntegerField(choices=REASONS)
    result = ForeignKey(TreatmentResult, db_column='result_fk', null=True)
    gender = SmallIntegerField(db_column='gender_fk')
    birthdate = DateField()
    comment = CharField(max_length=250)
    received_date = DateField()

    class Meta:
        db_table = 'hospitalization'