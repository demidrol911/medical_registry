# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.db import transaction
from main.models import TariffProfile
import time


class Command(BaseCommand):
    help = u'Проводим МЭК'

    def handle(self, *args, **options):
        main()


def main():
    pk = 10000

    for rec in range(1, 10):
        a = TariffProfile(id_pk=pk+rec, name=u'ТЕСТ №1')
        a.save()
        print a.pk
        time.sleep(2)