# -*- coding: utf-8 -*-

from django import forms
from tfoms.models import ProvidedService, PaymentType


class PeriodFastSearchForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={
        #'oninput':'ajaxGetRegisters(this.value)',
        'class': 'col-md-12 form-control'}))


class RegisterSearchForm(forms.Form):
    last_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-2 form-control'}), required=False)
    first_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-2 form-control'}), required=False)
    middle_name = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-2 form-control'}), required=False)
    policy = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    service1 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    service2 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    division = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    diagnosis1 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    diagnosis2 = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    date1 = forms.DateField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    date2 = forms.DateField(widget=forms.TextInput(attrs={
        'class': 'col-md-1 form-control'}), required=False)
    status = forms.ModelChoiceField(queryset=PaymentType.objects.all(), empty_label='',
                                    widget=forms.Select(
                                    attrs={'class': 'form-control col-md-2'}),
                                    required=False)


class RegisterStatusForm(forms.Form):
    status = forms.ModelChoiceField(queryset=PaymentType.objects.all(), empty_label=None,
                                    widget=forms.Select(
                                        attrs={'class': 'form-control my-select'}))