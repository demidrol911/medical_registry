# -*- coding: utf-8 -*-


def safe_int(string):
    try:
        integer = int(string)
    except:
        integer = 0

    return integer


def queryset_to_dict(qs):
    return {rec.code: rec for rec in qs}