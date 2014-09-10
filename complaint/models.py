# -*- coding: utf-8 -*-

from django.db.models import (
    Model, ForeignKey, CharField, DateField, IntegerField, AutoField, TextField,
    BooleanField, NullBooleanField)
from tfoms.models import MedicalOrganization


class Complaint(Model):
    KINDS = (
        (1, u'Консультация'),
        (2, u'Жалоба'),
        (3, u'Экспертиза'),)

    TYPES = (
        (1, u'Устно'),
        (2, u'Письменно'),)
    id_pk = AutoField(primary_key=True, db_column='id_pk')
    number = IntegerField()
    kind = IntegerField(choices=KINDS)
    type = IntegerField(choices=TYPES)
    person_name = CharField(max_length=128)
    person_birthday = DateField()
    person_address = CharField(max_length=80)
    content = TextField()
    reason = ForeignKey('Reason', db_column='reason_fk')
    result = CharField(max_length=60)
    organization = ForeignKey(MedicalOrganization, db_column='organization_fk')
    is_justified = NullBooleanField(null=True)

    class Meta:
        db_table = 'complaint'

    def get_creating_status(self):
        return Status.objects.get(complaint=self, type=1)


class Status(Model):
    TYPES = (
        (1, u'Рассмотрение'),
        (2, u'Промежуточный ответ'),
        (3, u'Окончание'),)

    id_pk = AutoField(primary_key=True, db_column='id_pk')
    type = IntegerField(choices=TYPES)
    date = DateField()
    complaint = ForeignKey(Complaint, db_column='complaint_fk')

    class Meta:
        db_table = 'complaint_status'


class Reason(Model):
    id_pk = IntegerField(primary_key=True, db_column='id_pk')
    name = CharField(max_length=50)

    class Meta:
        db_table = 'complaint_reason'
