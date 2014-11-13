# -*- coding: utf-8 -*-

from datetime import datetime


def safe_int(string):
    try:
        integer = int(string)
    except:
        integer = 0

    return integer


def safe_date(string):
    try:
        date = datetime.strptime(string, '%Y-%m-%d').date()
    except:
        date = datetime.strptime('1900-01-01', '%Y-%m-%d').date()

    return date


def safe_float(string):
    try:
        float = float(string)
    except:
        float = 0.0

    return float

def queryset_to_dict(qs):
    return {str(rec.code): rec for rec in qs}