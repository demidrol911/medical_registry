# -*- coding: utf-8 -*-

from django.contrib.humanize.templatetags.humanize import intcomma
from django import template
from viewer.forms import RegisterStatusForm
from tfoms.models import ProvidedService

register = template.Library()

@register.filter
def currency(money):
    if money:
        money = round(float(money), 2)
        return "%s%s" % (intcomma(int(money)), ("%0.2f" % money)[-3:])
    else:
        return '0'


@register.simple_tag
def print_my_select(my_value):
    form = RegisterStatusForm(initial={'status': my_value})
    if my_value == 2:
        status = form['status'].as_widget(attrs={'class': 'form-control my-select my-select-green'})
    elif my_value == 3:
        status = form['status'].as_widget(attrs={'class': 'form-control my-select my-select-red'})
    elif my_value == 4:
        status = form['status'].as_widget(attrs={'class': 'form-control my-select my-select-yellow'
                                                          ''})
    return status


@register.simple_tag
def is_checked_department(year, period, department):

    return ProvidedService.objects.filter(event__record__register__year=year,
                                          event__record__register__period=period,
                                          event__record__register__is_active=True,
                                          department__old_code=department
                                          ).distinct('status__type')
