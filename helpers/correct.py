import datetime


def date_correct(date):
    if date.year < 1900:
        return datetime.date(1900, date.month, date.day)
    else:
        return date
