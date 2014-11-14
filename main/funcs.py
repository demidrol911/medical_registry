# -*- coding: utf-8 -*-

from datetime import datetime


def safe_int(string):
    try:
        integer = int(string)
    except:
        integer = 0

    return integer


def safe_date(string):
    if string:
        try:
            date = datetime.strptime(string, '%Y-%m-%d').date()
        except:
            date = None
    else:
        date = None
    return date


def safe_float(string):
    try:
        _float = float(string)
    except:
        _float = 0.0

    return _float

def queryset_to_dict(qs):
    return {str(rec.code): rec for rec in qs}