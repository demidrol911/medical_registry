# -*- coding: utf-8 -*-

from django import forms
from django.forms import (
    ModelForm, TextInput, DateField, Select, IntegerField, ChoiceField,
    BooleanField, CharField, ModelChoiceField, RadioSelect, NumberInput,
    DateInput, NullBooleanSelect)
from models import Complaint, Status, Reason
from tfoms.models import MedicalOrganization


class MyModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s" % obj.name


class NewComplaint(ModelForm):
    KINDS = (
        (1, u'Консультация'),
        (2, u'Жалоба'),
        (3, u'Экспертиза'),)

    TYPES = (
        (1, u'Устно'),
        (2, u'Письменно'),)

    number = IntegerField(label=u'Номер',
                          widget=NumberInput(attrs={'class': 'form-control'}))
    kind = ChoiceField(choices=KINDS, label=u'Вид',
                       widget=Select(attrs={'class': 'form-control'}))
    type = ChoiceField(choices=TYPES, label=u'Тип',
                       widget=Select(attrs={'class': 'form-control'}))
    person_name = CharField(max_length=128, label=u'ФИО',
                            widget=TextInput(attrs={'class': 'form-control'}))
    person_birthday = DateField(label=u'Дата рождения',
                                widget=DateInput(attrs={'class': 'form-control'}))
    person_address = CharField(max_length=80, label=u'Адрес',
                               widget=TextInput(attrs={'class': 'form-control'}))
    content = CharField(label=u'Суть',
                        widget=TextInput(attrs={'class': 'form-control'}))
    reason = MyModelChoiceField(label=u'Причина',
                                queryset=Reason.objects.all(),
                                widget=Select(attrs={'class': 'form-control'}))
    result = CharField(max_length=60, label=u'Результат',
                       widget=TextInput(attrs={'class': 'form-control'}))
    organization = MyModelChoiceField(queryset=MedicalOrganization.objects.filter(parent=None).order_by('name'),
                                      label=u'Организация',
                                      widget=Select(attrs={'class': 'form-control'}))
    is_justified = BooleanField(label=u'Обосновано', required=False,
                                widget=NullBooleanSelect(attrs={'class': 'form-control'}))

    class Meta:
        model = Complaint
