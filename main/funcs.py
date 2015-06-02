# -*- coding: utf-8 -*-

from datetime import datetime
import time


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


def safe_date_to_string(dtime):
    try:
        date = dtime.strftime('%Y-%m-%d').date()
    except:
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


def howlong(func):
    def wrapper_func(*a, **b):
        start = time.clock()
        result = func(*a, **b)
        elapsed = time.clock() - start
        #print func.__module__.split('.')[-1]
        print u'{0:s}.{1:s} завершилась за {2:d} мин {3:d} сек'.\
            format(
                func.__module__.split('.')[-1],
                func.__name__,
                int(elapsed//60),
                int(elapsed % 60)
            )
        return result
    return wrapper_func
