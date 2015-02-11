#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from tfoms.models import (
    ProvidedEvent, ProvidedService, MedicalRegister, IDC, MedicalService,
    MedicalOrganization, Address, Patient)

from dbfpy import dbf


def unicode_to_cp866(string):
    return string.encode('cp866') if string else ''


def main():
    year = '2014'
    period = '11'
    path = 'd:/work/expertiza_export/%s/%s' % (year, period)

    services = ProvidedService.objects.filter(
        #event__record__register__organization_code='280015',
        event__record__register__year=year,
        event__record__register__period=period,
        event__record__register__is_active=True,
        payment_type_id__in=(2, 4),
    ).exclude(code__code__startswith='A')

    departments = services.values_list('department__old_code', flat=True).distinct('department__old_code')
    pass_departments = []
    #departments = ['0301061', ]
    print departments
    for department in departments:
        print department
        if department in pass_departments:
            continue
        if not department:
            continue

        db = dbf.Dbf('%s/t%s.dbf' % (path, department), new=True)
        db.addField(
            ("COD", "C", 15),
            ("OTD", "C", 3),
            ("ERR_ALL", "C", 8),
            ("SN_POL", "C", 25),
            ("FAM", "C", 20),
            ("IM", "C", 20),
            ("OT", "C", 25),
            ("DR", "D"),
            ("DS", "C", 6),
            ("DS2", "C", 6),
            ("C_I", "C", 16),
            ("D_BEG", "D"),
            ("D_U", "D"),
            ("K_U", "N", 4),
            ("F_DOP_R", "N", 10, 2),
            ("T_DOP_R", "N", 10, 2),
            ("S_OPL", "N", 10, 2),
            ("ADRES", "C", 80),
            ("SPOS", "C", 2),
            ("GENDER", "C", 1),
            ("EMPL_NUM", "C", 16),
            ("HOSP_TYPE", "N", 2),
            ("OUTCOME", "C", 3),
        )

        department_services = services.filter(department__old_code=department)
        department_services = department_services.values(
            'code__code', 'division__code', 'comment_error',
            'event__record__patient__insurance_policy_series',
            'event__record__patient__insurance_policy_number',
            'event__record__patient__first_name',
            'event__record__patient__last_name',
            'event__record__patient__middle_name',
            'event__record__patient__birthdate',
            'event__record__patient__gender_id',
            'basic_disease__idc_code',
            'event__concomitant_disease__idc_code',
            'event__basic_disease__idc_code',
            'event__anamnesis_number',
            'start_date', 'end_date',
            'quantity',
            'accepted_payment',
            'event__record__patient',
            'comment',
            'code__group_id',
            'event__treatment_outcome__code',
            'event__hospitalization_id',
            'event__worker_code',
        )
        exclude_departments = []
        for department_service in department_services:

            address_string = u'Амурская область, %(area)s, , , %(street)s, %(house)s, %(extra)s, %(room)s'
            address = patient.get_address()

            new = db.newRecord()
            new["COD"] = unicode_to_cp866(department_service['code__code'])
            new["OTD"] = department_service['division__code'] or '000'
            new["ERR_ALL"] = unicode_to_cp866(department_service['comment_error'])

            new["SN_POL"] = '%s %s' % (
                unicode_to_cp866(department_service['event__record__patient__insurance_policy_series']),
                unicode_to_cp866(department_service['event__record__patient__insurance_policy_number'])
            )

            new["FAM"] = unicode_to_cp866(department_service['event__record__patient__last_name']) or ''
            new["IM"] = unicode_to_cp866(department_service['event__record__patient__first_name']) or ''
            new["OT"] = unicode_to_cp866(department_service['event__record__patient__middle_name']) or ''
            new["DR"] = department_service['event__record__patient__birthdate'] or '1900-01-01'
            if department_service['code__group_id'] in (7, 25, 26, 9, 10, 11,
                                                        12, 13, 14, 15, 16):
                new["DS"] = department_service['event__basic_disease__idc_code']
            else:
                new["DS"] = unicode_to_cp866(department_service['basic_disease__idc_code'])

            if department_service['event__concomitant_disease__idc_code']:
                new["DS2"] = ''
            else:
                new["DS2"] = ''
            new["C_I"] = unicode_to_cp866(
                department_service['event__anamnesis_number']) or ''
            new["D_BEG"] = department_service['start_date'] or '1900-01-01'
            new["D_U"] = department_service['end_date'] or '1900-01-01'
            new["K_U"] = department_service['quantity'] or 0
            if 'SC2' in (department_service['comment'] or ''):
                new["S_OPL"] = round(float(department_service['accepted_payment']) / 0.3, 2)
            else:
                new["S_OPL"] = department_service['accepted_payment'] or 0
            if address:
                try:
                    address_string = address_string % dict(
                        area=address.administrative_area.name or '',
                        street=address.street or '', house=address.house_number or '',
                        extra=address.extra_number or '', room=address.room_number or '')
                    new["ADRES"] = unicode_to_cp866(address_string)
                except:
                    new["ADRES"] = ''
            else:
                new["ADRES"] = ''

            try:
                code = int(department_service['code__code'])
            except:
                code = None

            if code and department not in exclude_departments and (
                    (17001 <= code <= 17061) or (117001 <= code <= 117061)):
                SPOS = 'P'
            else:
                SPOS = 'T'

            new["SPOS"] = SPOS
            new["GENDER"] = department_service['event__record__patient__gender_id'] or 0
            new["OUTCOME"] = department_service['event__treatment_outcome__code'] or ''
            new["HOSP_TYPE"] = department_service['event__hospitalization_id'] or 0
            new["EMPL_NUM"] = unicode_to_cp866(department_service['event__worker_code']) or ''
            new.store()
        db.close()


class Command(BaseCommand):
    help = 'export big XML'

    def handle(self, *args, **options):
        main()