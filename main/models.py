# -*- coding: utf-8 -*-

from django.db import models
from django.db import connection, transaction
from django.db.models.query import QuerySet
from django.db.models import Sum
import datetime
from medical_service_register.settings import DATE_ATTACHMENT
from decimal import Decimal
from medical_service_register.settings import YEAR, PERIOD
from main.funcs import dictfetchall

SERVICE_XML_TYPE_PERSON = 0
SERVICE_XML_TYPE_REGULAR = 1
SERVICE_XML_TYPE_HITECH = 2
SERVICE_XML_TYPE_EXAMINATION_ADULT_1 = 3 #comment: F0000
SERVICE_XML_TYPE_EXAMINATION_ADULT_2 = 4 #comment: F0000
SERVICE_XML_TYPE_EXAMINATION_ADULT_PREVENTIVE = 5 #comment: F00
SERVICE_XML_TYPE_EXAMINATION_CHILDREN_DIFFICULT = 6
SERVICE_XML_TYPE_EXAMINATION_CHILDREN_ADOPTED = 7
SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PREVENTIVE = 8
SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PRELIMINARY = 9
SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PERIODICALLY = 10
# 10, 9, 8, 7, 6, 5, 4, 3
SERVICE_XML_TYPES = (
    (SERVICE_XML_TYPE_PERSON, 'l'),
    (SERVICE_XML_TYPE_REGULAR, 'h'),
    (SERVICE_XML_TYPE_HITECH, 't'),
    (SERVICE_XML_TYPE_EXAMINATION_ADULT_1, 'dp'),
    (SERVICE_XML_TYPE_EXAMINATION_ADULT_2, 'dv'),
    (SERVICE_XML_TYPE_EXAMINATION_ADULT_PREVENTIVE, 'do'),
    (SERVICE_XML_TYPE_EXAMINATION_CHILDREN_DIFFICULT, 'ds'),
    (SERVICE_XML_TYPE_EXAMINATION_CHILDREN_ADOPTED, 'du'),
    (SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PREVENTIVE, 'df'),
    (SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PRELIMINARY, 'dd'),
    (SERVICE_XML_TYPE_EXAMINATION_CHILDREN_PERIODICALLY, 'dr'),
)

EXAMINATION_TYPES = (
    (1, u'ДВ1'),
    (2, u'ДВ2'),
    (3, u'ОПВ'),
    (4, u'ДС1'),
    (5, u'ДС2'),
    (6, u'ОН1'),
    (7, u'ОН2'),
    (8, u'ОН3'),
)

SERVICE_TERM_KINDS = {}



class ExtendedQuerySet(QuerySet):
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None


class ExtendedObjectManager(models.Manager):
    def get_query_set(self):
        return ExtendedQuerySet(self.model, using=self._db)


class Gender(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=20)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "gender"


class Citizenship(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    oksm = models.CharField(max_length=3)
    name = models.CharField(max_length=20)

    class Meta:
        db_table = "citizenship"


class Person(models.Model):
    version = models.BigIntegerField(primary_key=True,
                                     db_column='version_id_pk')
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40)
    gender = models.ForeignKey(Gender, db_column='gender_fk')
    birthdate = models.DateField()
    deathdate = models.DateField()
    citizenship_fk = models.ForeignKey(Citizenship, db_column='citizenship_fk')
    snils = models.CharField(max_length=14)
    phone = models.CharField(max_length=40)
    id = models.BigIntegerField()
    birthplace = models.CharField(max_length=100)
    is_active = models.BooleanField()

    class Meta:
        db_table = "person"


class Address(models.Model):
    id_pk = models.BigIntegerField(primary_key=True, db_column='id_pk')
    administrative_area = models.ForeignKey('AdministrativeArea',
                                            db_column='administrative_area_fk')
    street = models.CharField(max_length=80)
    house_number = models.CharField(max_length=7)
    extra_number = models.CharField(max_length=6)
    room_number = models.CharField(max_length=47)
    person = models.ForeignKey('Person', db_column='person_fk')
    type = models.IntegerField(db_column='type_fk')

    class Meta:
        db_table = 'address'


class AdministrativeArea(models.Model):
    ID = models.BigIntegerField(primary_key=True, db_column='id_pk')
    parent = models.ForeignKey('self', db_column='parent_fk')
    name = models.CharField(max_length=60)
    okato_code = models.CharField(max_length=12)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "administrative_area"


class InsurancePolicyForm(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=30)

    class Meta:
        db_table = "insurance_policy_form"


class InsurancePolicyType(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=30)

    class Meta:
        db_table = "insurance_policy_type"


class InsurancePolicy(models.Model):
    version = models.BigIntegerField(primary_key=True,
                                     db_column='version_id_pk')
    type = models.ForeignKey(InsurancePolicyType, db_column='type_fk')
    series = models.CharField(max_length=10)
    number = models.CharField(max_length=20)
    enp = models.CharField(max_length=16)
    start_date = models.DateField()
    end_date = models.DateField()
    stop_date = models.DateField()
    ready_date = models.DateField()
    issue_region = models.ForeignKey(AdministrativeArea,
                                     db_column='issue_region_fk')
    id = models.BigIntegerField()
    person = models.ForeignKey(Person, db_column='person_fk')
    is_active = models.BooleanField()

    class Meta:
        db_table = "insurance_policy"


class ActiveInsurancePolicy(models.Model):
    ID = models.BigIntegerField(primary_key=True, db_column='id_pk')
    version = models.ForeignKey(InsurancePolicy, db_column='version_fk')
    id = models.BigIntegerField()

    class Meta:
        db_table = "active_insurance_policy"


class PersonIDType(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=80)
    code = models.IntegerField()
    is_visible = models.BooleanField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "person_id_type"


class IssuingOrganization(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=80)
    code = models.CharField(max_length=80)

    class Meta:
        db_table = "issuing_organization"


class PersonID(models.Model):
    version = models.BigIntegerField(primary_key=True, db_column='id_pk')
    type = models.ForeignKey(PersonIDType, db_column='type_fk')
    series = models.CharField(max_length=10)
    number = models.CharField(max_length=20)
    issue_date = models.DateField()
    issuing_organization = models.ForeignKey(IssuingOrganization,
                                             db_column='issuing_organization_fk')
    id = models.BigIntegerField()
    person = models.ForeignKey(Person, db_column='person_fk')
    end_date = models.DateField()
    is_active = models.BooleanField()

    class Meta:
        db_table = "person_id"


class AgeBracket(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=15)
    code = models.IntegerField()

    class Meta:
        db_table = "age_bracket"


class IDC(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.CharField(max_length=12)
    name = models.CharField(max_length=96)
    idc_code = models.CharField(max_length=8)
    gender = models.ForeignKey(Gender, db_column='gender_fk',
                               related_name='disease_gender')
    parent = models.ForeignKey('self', db_column='parent_fk')
    is_paid = models.BooleanField()
    is_precision = models.BooleanField()

    class Meta:
        db_table = "idc"


class KPG(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=120)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "kpg"


class MedicalDivision(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.CharField(max_length=4)
    name = models.CharField(max_length=60)
    parent = models.ForeignKey('self', db_column='parent_fk')
    term = models.ForeignKey('MedicalServiceTerm', db_column='term_fk')
    nkd = models.FloatField()
    kpg = models.ForeignKey(KPG, db_column='kpg_fk')
    age_bracket = models.ForeignKey(AgeBracket, db_column='age_bracket_fk')

    class Meta:
        db_table = "medical_division"


class MedicalHospitalization(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.SmallIntegerField()
    name = models.CharField(max_length=80)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_hospitalization"


class MedicalOrganizationAttachClass(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)

    class Meta:
        db_table = "medical_organization_attach_class"


class MedicalOrganization(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.CharField(max_length=12)
    name = models.CharField(max_length=155)
    old_code = models.CharField(max_length=12)
    ogrn = models.CharField(max_length=16)
    parent = models.ForeignKey('self', db_column='parent_fk',
                               related_name="medical_organization_parent")
    attach_class = models.ForeignKey(MedicalOrganizationAttachClass,
                                     db_column='attach_class_fk')
    region = models.ForeignKey(AdministrativeArea, db_column='region_fk',
                               related_name="medical_organization_region")
    is_ambulance = models.BooleanField()
    ambulance_region = models.ForeignKey(AdministrativeArea,
                                         db_column='ambulance_region_fk',
                                         related_name="medical_organization_ambulance_region")
    ambulance = models.ForeignKey('self', db_column='ambulance_fk',
                                  related_name="medical_organization_ambulance")
    attach_limit = models.IntegerField()
    tariff_group = models.ForeignKey('TariffGroup', db_column='tariff_group_fk')
    is_agma_cathedra = models.BooleanField()
    level = models.IntegerField()
    regional_coefficient = models.FloatField()
    alternate_tariff_group = models.ForeignKey('TariffGroup',
                                               db_column='alternate_tariff_group_fk',
                                               related_name='alternate_group')
    act_number = models.CharField(max_length=4)
    act_head_fullname = models.CharField(max_length=256)
    act_head_position = models.CharField(max_length=64)

    class Meta:
        db_table = "medical_organization"

    def get_attachment_count(self, date):
        populations = AttachmentStatistics.objects.filter(organization=self.code, at=date)
        result = {
            1: {'men': 0, 'fem': 0},
            2: {'men': 0, 'fem': 0},
            3: {'men': 0, 'fem': 0},
            4: {'men': 0, 'fem': 0},
            5: {'men': 0, 'fem': 0}
        }
        for population in populations:
            result[1]['men'] += population.less_one_age_male
            result[1]['fem'] += population.less_one_age_female
            result[2]['men'] += population.one_four_age_male
            result[2]['fem'] += population.one_four_age_female
            result[3]['men'] += population.five_seventeen_age_male
            result[3]['fem'] += population.five_seventeen_age_female
            result[4]['men'] += population.eighthteen_fiftynine_age_male
            result[4]['fem'] += population.eighthteen_fiftyfour_age_female
            result[5]['men'] += population.older_sixty_age_male
            result[5]['fem'] += population.older_fiftyfive_age_female
        return result

    def get_attachment_ambulance_count_since_2015_08_01(self, date):
        populations = AttachmentStatistics.objects.filter(organization=self.code, at=date)
        result = {
            1: {'men': 0, 'fem': 0},
            2: {'men': 0, 'fem': 0},
            3: {'men': 0, 'fem': 0},
            4: {'men': 0, 'fem': 0},
            5: {'men': 0, 'fem': 0}
        }
        for population in populations:
            result[1]['men'] += population.less_one_age_male_ambulance
            result[1]['fem'] += population.less_one_age_female_ambulance
            result[2]['men'] += population.one_four_age_male_ambulance
            result[2]['fem'] += population.one_four_age_female_ambulance
            result[3]['men'] += population.five_seventeen_age_male_ambulance
            result[3]['fem'] += population.five_seventeen_age_female_ambulance
            result[4]['men'] += population.eighthteen_fiftynine_age_male_ambulance
            result[4]['fem'] += population.eighthteen_fiftyfour_age_female_ambulance
            result[5]['men'] += population.older_sixty_age_male_ambulance
            result[5]['fem'] += population.older_fiftyfive_age_female_ambulance
        return result

    def get_ambulance_attachment_count(self, date):
        result = self.get_attachment_ambulance_count_since_2015_08_01(date)
        return result

    @staticmethod
    def get_partial_register(mo_code):
        return list(ProvidedService.objects.filter(
            event__record__register__year=YEAR,
            event__record__register__period=PERIOD,
            event__record__register__is_active=True,
            event__record__register__organization_code=mo_code).\
            values_list('department__old_code', flat=True).distinct())

    @staticmethod
    def get_mo_info(mo_code, department_code=None):
        if department_code:
            mo = MedicalOrganization.objects.get(code=mo_code, old_code=department_code)
        else:
            mo = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True)
        return {'code': mo.code, 'name': mo.name, 'is_agma_cathedra': mo.is_agma_cathedra,
                'act_number': mo.act_number, 'act_head_fullname': mo.act_head_fullname,
                'act_head_position': mo.act_head_position}

    @staticmethod
    def get_mo_name(mo_code, department=None):
        if department:
            return MedicalOrganization.objects.get(old_code=department).name
        return MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).name


class MedicalRegisterStatus(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)

    class Meta:
        db_table = "medical_register_status"


class MedicalRegister(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    filename = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.ForeignKey(MedicalRegisterStatus, db_column='status_fk')
    organization = models.ForeignKey(MedicalOrganization,
                                     db_column='organization_fk', null=True)
    is_active = models.BooleanField()
    period = models.CharField(max_length=2)
    year = models.CharField(max_length=4)
    invoice_date = models.DateField()
    invoice_comment = models.CharField(max_length=255)
    invoiced_payment = models.DecimalField(max_digits=15, decimal_places=4)
    accepted_payment = models.DecimalField(max_digits=15, decimal_places=4)
    sanctions_mek = models.DecimalField(max_digits=15, decimal_places=4)
    sanctions_mee = models.DecimalField(max_digits=15, decimal_places=4)
    sanctions_ekmp = models.DecimalField(max_digits=15, decimal_places=4)
    tfoms_surcharge = models.DecimalField(max_digits=15, decimal_places=4)
    ffoms_surcharge = models.DecimalField(max_digits=15, decimal_places=4)
    single_channel_surcharge = models.DecimalField(max_digits=15,
                                                   decimal_places=4)
    organization_code = models.CharField(max_length=6)
    type = models.SmallIntegerField()
    pse_export_date = models.DateField(db_column='pse_export_date')

    class Meta:
        db_table = "medical_register"

    def get_all_records(self):
        return MedicalRegisterRecord.objects.filter(register=self)

    def get_all_patients(self, records):
        return Patient.objects.filter(
            pk__in=records.values_list('patient_id', flat=True))

    def get_all_events(self):
        return ProvidedEvent.objects.filter(
            record__register=self).select_related('term', 'kind',
                                                  'organization', 'department')

    def get_all_services(self):
        return ProvidedService.objects.filter(event__record__register=self)

    def get_departments(self):
        return MedicalOrganization.objects.filter(code=self.organization.code
        ).order_by('old_code')

    def get_invoiced_payment(self):
        return ProvidedService.objects.filter(
            event__record__register__organization_code=self.organization_code,
            event__record__register__period=self.period,
            event__record__register__year=self.year,
            event__record__register__is_active=True
        ).aggregate(Sum('invoiced_payment'))['invoiced_payment__sum']

    def get_accepted_payment(self):
        return ProvidedService.objects.filter(
            event__record__register__organization_code=self.organization_code,
            event__record__register__period=self.period,
            event__record__register__year=self.year,
            event__record__register__is_active=True,
            payment_type_id__in=(2, 4)
        ).aggregate(Sum('accepted_payment'))['accepted_payment__sum']

    def get_sanctions_mek(self):
        query = """
            select sum(pss.underpayment)
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on pe.record_fk = mrr.id_pk
                JOIN medical_register mr
                    on mrr.register_fk = mr.id_pk
                LEFT join provided_service_sanction pss
                    on pss.service_fk = ps.id_pk and pss.id_pk = (
                        select max(id_pk) from provided_service_sanction
                        where service_fk = ps.id_pk
                    ) and ps.payment_type_fk in (3, 4) and pss.underpayment > 0
                        and pss.type_fk = 1
            where
                mr.is_active = True
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
        """
        cursor = connection.cursor()
        cursor.execute(query, [self.year, self.period, self.organization_code])
        result = cursor.fetchone()[0]

        return result

    def get_sanctions_mee(self):
        query = """
            select sum(pss.underpayment)
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on pe.record_fk = mrr.id_pk
                JOIN medical_register mr
                    on mrr.register_fk = mr.id_pk
                LEFT join provided_service_sanction pss
                    on pss.service_fk = ps.id_pk
                        and pss.type_fk = 2
            where
                mr.is_active = True
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
        """
        cursor = connection.cursor()
        cursor.execute(query, [self.year, self.period, self.organization_code])
        result = cursor.fetchone()[0]

        return result

    def get_sanctions_ekmp(self):
        query = """
            select sum(pss.underpayment)
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    on pe.record_fk = mrr.id_pk
                JOIN medical_register mr
                    on mrr.register_fk = mr.id_pk
                LEFT join provided_service_sanction pss
                    on pss.service_fk = ps.id_pk
                        and pss.type_fk = 3
            where
                mr.is_active = True
                and mr.year = %s
                and mr.period = %s
                and mr.organization_code = %s
        """
        cursor = connection.cursor()
        cursor.execute(query, [self.year, self.period, self.organization_code])
        result = cursor.fetchone()[0]

        return result

    # Возвращает список кодов медицинских организаций, реестры которых имеют указанный статус
    @staticmethod
    def get_mo_register(status=None):
        organizations = MedicalRegister.objects.filter(year=YEAR, period=PERIOD, is_active=True, type=1)
        if status:
            organizations = organizations.filter(status__pk=status)
        return organizations.values_list('organization_code', flat=True)

    '''
    @staticmethod
    def get_mo_code(status):
        organizations = MedicalRegister.objects.filter(
            year=YEAR,
            period=PERIOD,
            is_active=True,
            type=1,
            status__pk=status
        )
        if organizations:
            organization_code = organizations[0].organization_code
        else:
            organization_code = ''
        return organization_code
    '''

    # Рассчет подушевого тарифа
    @staticmethod
    def calculate_capitation(term, mo_code):
        """
        Новая функция для рассчета тарифа по подушевому
        """
        tariff = TariffCapitation.objects.filter(
            term=term, organization__code=mo_code,
            start_date__lte=DATE_ATTACHMENT,
            start_date__gte='2016-01-01',
            is_children_profile=True
        )
        result = {'adult': {}, 'child': {}}

        if tariff:
            if term == 3:
                population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                    get_attachment_count(DATE_ATTACHMENT)
            elif term == 4:
                population = MedicalOrganization.objects.get(code=mo_code, parent__isnull=True).\
                    get_ambulance_attachment_count(DATE_ATTACHMENT)
        else:
            return False, result

        # Чмсленность
        result['adult']['population'] = population[4]['men'] + population[4]['fem'] + \
            population[5]['men'] + population[5]['fem']

        result['child']['population'] = population[1]['men'] + population[1]['fem'] + \
            population[2]['men'] + population[2]['fem'] + \
            population[3]['men'] + population[3]['fem']

        result['adult']['basic_tariff'] = tariff.order_by('-start_date')[0].value
        result['child']['basic_tariff'] = tariff.order_by('-start_date')[0].value

        for key in result:
            result[key]['tariff'] = Decimal(round(result[key]['population']*result[key]['basic_tariff'], 2))

        for key in result:
            result[key]['coeff'] = 0

        for key in result:
            result[key]['accepted'] = Decimal(round(result[key]['tariff'] + result[key].get('coeff', 0), 2))

        return True, result

    # Рассчёт вычета и индексации по флюорографии
    @staticmethod
    def calculate_fluorography(mo_code):
        if mo_code == '280085':
            query = """
                select count(distinct case when age(f.start_date, f.birthdate) >= '18 years' THEN f.insurance_policy_fk END) AS adult_population,
                      count(distinct case when age(f.start_date, f.birthdate) < '18 years' THEN f.insurance_policy_fk END) AS child_population
                    from fluorography f
                    join medical_organization mo ON mo.code = f.attachment_code and mo.parent_fk is null
                    where mo.code <> '280085'
                          and date = format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE
                """
        else:
            query = """
                select count(distinct case when age(f.start_date, f.birthdate) >= '18 years' THEN f.insurance_policy_fk END) AS adult_population,
                     count(distinct case when age(f.start_date, f.birthdate) < '18 years' THEN f.insurance_policy_fk END) AS child_population
                    from fluorography f
                    join medical_organization mo ON mo.code = f.attachment_code and mo.parent_fk is null
                    where mo.code = %(organization_code)s
                          and date = format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE
                """
        cursor = connection.cursor()
        cursor.execute(query, dict(organization_code=mo_code, year=YEAR, period=PERIOD))
        data = dictfetchall(cursor)
        result = {'adult': {}, 'child': {}}
        if data[0]['adult_population'] or data[0]['child_population']:
            result['adult']['population'] = data[0]['adult_population']
            result['child']['population'] = data[0]['child_population']

            result['adult']['basic_tariff'] = 140 if mo_code == '280085' else -140
            result['child']['basic_tariff'] = 140 if mo_code == '280085' else -140

            for key in result:
                result[key]['tariff'] = Decimal(round(result[key]['population']*result[key]['basic_tariff'], 2))

            for key in result:
                result[key]['coeff'] = 0

            for key in result:
                result[key]['accepted'] = result[key]['tariff']

            return True, result
        else:
            return False, {}

    # Поменять статус у реестра
    @staticmethod
    def change_register_status(mo_code, status):
        MedicalRegister.objects.filter(
            year=YEAR,
            period=PERIOD,
            organization_code=mo_code,
            is_active=True
        ).update(status=status)
        if status == 8:
            MedicalRegister.objects.filter(
                year=YEAR,
                period=PERIOD,
                organization_code=mo_code,
                is_active=True).update(pse_export_date=datetime.now())

    # Возвращает отображение кода подразделения на федеральный код мо
    @staticmethod
    def get_mo_map():
        query = """
            SELECT DISTINCT dep.old_code AS dep_code, mo.code AS mo_code
            FROM provided_service ps
                JOIN provided_event pe
                    ON ps.event_fk = pe.id_pk
                JOIN medical_register_record mrr
                    ON mrr.id_pk = pe.record_fk
                JOIN medical_register mr
                    ON mr.id_pk = mrr.register_fk
                JOIN medical_organization mo
                    ON mo.id_pk = ps.organization_fk
                JOIN medical_organization dep
                    ON dep.id_pk = ps.department_fk
            WHERE mr.is_active
                AND mr.year = %(year)s
                AND mr.period = %(period)s
            """
        cursor = connection.cursor()
        cursor.execute(query, dict(year=YEAR, period=PERIOD))
        mo_map = {item['dep_code']: item['mo_code'] for item in dictfetchall(cursor)}
        cursor.close()
        return mo_map


class MedicalRegisterRecord(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    register = models.ForeignKey(MedicalRegister, db_column='register_fk')
    patient = models.ForeignKey('Patient', db_column='patient_fk')
    is_corrected = models.BooleanField()
    id = models.IntegerField()

    class Meta:
        db_table = "medical_register_record"

    def get_events(self):
        return ProvidedEvent.objects.filter(record=self)

    def get_actual_events(self):
        return ProvidedEvent.objects.filter(record=self).count()

    def get_patient(self):
        return Patient.objects.get(pk=self.patient.pk)


class MedicalServiceGroup(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)
    parent = models.ForeignKey('self', db_column='parent_fk')

    class Meta:
        db_table = "medical_service_group"


class MedicalService(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.CharField(max_length=12)
    name = models.CharField(max_length=180)
    parent = models.ForeignKey('self', db_column='parent_fk')
    uet = models.FloatField()
    reason = models.ForeignKey('MedicalServiceReason', db_column='reason_fk')
    gender = models.ForeignKey(Gender, db_column='gender_fk', null=True)
    age_bracket = models.ForeignKey(AgeBracket, db_column='age_bracket_fk')
    profile = models.ForeignKey('MedicalServiceProfile', db_column='profile_fk')
    division = models.ForeignKey('MedicalDivision', db_column='division_fk')
    payment_method = models.ForeignKey('PaymentMethod',
                                       db_column='payment_method_fk')
    nkd = models.FloatField()
    outpatient_division = models.ForeignKey('OutpatientDivision',
                                            db_column='outpatient_division_fk')
    inpatient_division = models.ForeignKey('InpatientDivision',
                                           db_column='inpatient_division_fk')
    group = models.ForeignKey('MedicalServiceGroup', db_column='group_fk')
    subgroup = models.ForeignKey('MedicalServiceSubgroup', db_column='subgroup_fk')
    examination_group = models.IntegerField()
    examination_special = models.NullBooleanField()
    tariff_profile = models.ForeignKey('TariffProfile',
                                       db_column='tariff_profile_fk')
    is_paid = models.BooleanField()
    vmp_group = models.IntegerField(db_column='vmp_group')

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service"


class MedicalServiceDivision(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey(MedicalService, db_column='service_fk')
    division = models.ForeignKey(MedicalDivision, db_column='division_fk')

    class Meta:
        db_table = "medical_service_division"


class MedicalServiceForm(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)
    code = models.IntegerField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service_form"


class MedicalServiceKind(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=128)
    code = models.IntegerField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service_kind"


class MedicalServiceHiTechKind(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=16)
    is_active = models.BooleanField()

    class Meta:
        db_table = "medical_service_hitech_kind"


class MedicalServiceHiTechMethod(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=128)
    code = models.CharField(max_length=10)
    is_active = models.BooleanField()

    class Meta:
        db_table = "medical_service_hitech_method"


class ExaminationResult(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=128)
    code = models.IntegerField()

    class Meta:
        db_table = "examination_result"


class MedicalIntervention(models.Model):
    id_pk = models.SmallIntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=80)

    class Meta:
        db_table = "medical_intervention"


class MedicalServiceProfile(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=180)
    code = models.IntegerField()
    is_active = models.BooleanField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service_profile"


class MedicalServiceReason(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=50)
    code = models.IntegerField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service_reason"


class MedicalServiceTerm(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=50)
    code = models.IntegerField()
    old_code = models.IntegerField()

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "medical_service_term"


class Attachment(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    person = models.ForeignKey(Person, db_column='person_fk')
    organization = models.ForeignKey(MedicalOrganization,
                                     db_column='medical_organization_fk')
    status = models.IntegerField(db_column='status_fk')
    confirmation_date = models.DateField()
    is_active = models.BooleanField()
    date = models.DateField(db_column='date')

    class Meta:
        db_table = "attachment"


class Patient(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    id = models.CharField(max_length=36)
    is_adult = models.BooleanField()
    person = models.ForeignKey(Person, db_column='person_fk', null=True)
    insurance_policy = models.ForeignKey(InsurancePolicy,
                                         db_column='insurance_policy_fk',
                                         null=True)
    personID = models.ForeignKey(PersonID, db_column='person_id_fk', null=True)
    #is_newborn = models.BooleanField()
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40)
    gender = models.ForeignKey(Gender, db_column='gender_fk',
                               related_name='patient_gender', null=True)
    birthdate = models.DateField()
    agent_first_name = models.CharField(max_length=40)
    agent_last_name = models.CharField(max_length=40)
    agent_middle_name = models.CharField(max_length=40)
    agent_gender = models.ForeignKey(Gender, db_column='agent_gender_fk',
                                     related_name='patient_agent_gender',
                                     null=True)
    agent_birthdate = models.DateField()
    birthplace = models.CharField(max_length=100)
    person_id_type = models.ForeignKey(PersonIDType,
                                       db_column='person_id_type_fk',
                                       null=True)
    person_id_series = models.CharField(max_length=10)
    person_id_number = models.CharField(max_length=20)
    snils = models.CharField(max_length=14)
    okato_registration = models.CharField(max_length=11)
    okato_residence = models.CharField(max_length=11)
    comment = models.CharField(max_length=250)
    insurance_policy_type = models.ForeignKey(InsurancePolicyType,
                                              db_column='insurance_policy_type_fk',
                                              null=True)
    insurance_policy_series = models.CharField(max_length=10)
    insurance_policy_number = models.CharField(max_length=20)
    newborn_code = models.CharField(max_length=9)
    weight = models.DecimalField(max_digits=10, decimal_places=4)
    attachment_code = models.CharField(max_length=6)

    class Meta:
        db_table = 'patient'

    def get_attachment_at(self, date):
        q = """
        select medOrg.id_pk
        from patient p1
        join insurance_policy on p1.insurance_policy_fk = insurance_policy.version_id_pk
        join person on person.version_id_pk = (select version_id_pk
        from person where id = (select id from person where
        version_id_pk = insurance_policy.person_fk) and is_active)
        join attachment on attachment.id_pk = (select max(id_pk)
        from attachment where person_fk = person.version_id_pk and status_fk = 1
        and date <= %s and attachment.is_active)
        join medical_organization medOrg on (
        medOrg.id_pk = attachment.medical_organization_fk and
        medOrg.parent_fk is null) or medOrg.id_pk =
        (select parent_fk from medical_organization where id_pk = attachment.medical_organization_fk)
        where p1.id_pk = %s
        """
        if self.insurance_policy:
            attachment = list(
                MedicalOrganization.objects.raw(q, [date, self.id_pk]))
        else:
            attachment = None

        if attachment:
            return attachment[0].code
        else:
            return None

    def get_address(self):
        address = None
        if self.insurance_policy:
            address = Address.objects.filter(
                person=self.insurance_policy.person,
                type=2)
        if address:
            address = address[0]
        return address


class MedicalWorkerSpeciality(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=18)
    is_active = models.BooleanField()

    class Meta:
        db_table = 'medical_worker_speciality'


class PaymentFailureCause(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=50)
    comment = models.TextField()
    number = models.CharField(max_length=12)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = 'payment_failure_cause'


class PaymentMethod(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=80)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = 'payment_method'


class PaymentType(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=30)

    objects = ExtendedObjectManager()

    def __unicode__(self):
        return '%s' % self.name

    class Meta:
        db_table = 'payment_type'


class ProvidedEventStatusType(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)

    class Meta:
        db_table = "provided_event_status_type"


class ProvidedServiceStatusType(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40)

    class Meta:
        db_table = "provided_service_status_type"


class ProvidedEventStatus(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    type = models.ForeignKey(ProvidedEventStatusType, db_column='type_fk')
    timestamp = models.DateTimeField()
    operator = models.IntegerField(db_column='operator_fk')
    event = models.BigIntegerField('ProvidedEvent', db_column='event_fk')

    class Meta:
        db_table = "provided_event_status"


class ProvidedServiceStatus(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    type = models.ForeignKey(ProvidedServiceStatusType, db_column='type_fk')
    timestamp = models.DateTimeField()
    operator = models.IntegerField(db_column='operator_fk')
    service = models.BigIntegerField('ProvidedService', db_column='service_fk')

    class Meta:
        db_table = "provided_service_status"


class ProvidedServiceFailureCause(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey('ProvidedService', db_column='service_fk')
    cause = models.ForeignKey('PaymentFailureCause', db_column='cause_fk')

    class Meta:
        db_table = "provided_service_failure_cause"


class ProvidedEvent(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    id = models.IntegerField()
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk', null=True)
    kind = models.ForeignKey(MedicalServiceKind, db_column='kind_fk', null=True)
    form = models.ForeignKey(MedicalServiceForm, db_column='form_fk')
    organization = models.ForeignKey(MedicalOrganization,
                                     db_column='organization_fk',
                                     related_name='provided_event_organization',
                                     null=True)
    department = models.ForeignKey(MedicalOrganization,
                                   db_column='department_fk',
                                   related_name='proviede_event_department',
                                   null=True)
    profile = models.ForeignKey(MedicalServiceProfile, db_column='profile_fk',
                                null=True)
    is_children_profile = models.NullBooleanField(null=True)
    anamnesis_number = models.CharField(max_length=50, null=True)
    examination_rejection = models.SmallIntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    initial_disease = models.ForeignKey(IDC, db_column='initial_disease_fk',
                                        related_name='provided_event_initial_disease',
                                        null=True)
    basic_disease = models.ForeignKey(IDC, db_column='basic_disease_fk',
                                      related_name='provided_event_basic_disease_dv',
                                      null=True)
    concomitant_disease = models.ForeignKey(IDC,
                                            db_column='concomitant_disease_fk',
                                            related_name='provided_event_concomitant_disease',
                                            null=True)
    payment_method = models.ForeignKey(PaymentMethod,
                                       db_column='payment_method_fk', null=True)
    payment_units_number = models.DecimalField(default=0, max_digits=5,
                                               decimal_places=2)
    tariff = models.DecimalField(default=0, max_digits=16, decimal_places=4)
    invoiced_payment = models.DecimalField(default=0, max_digits=16,
                                           decimal_places=4)
    accepted_payment = models.DecimalField(default=0, max_digits=16,
                                           decimal_places=4)
    payment_type = models.ForeignKey(PaymentType, db_column='payment_type_fk',
                                     null=True)
    sanctions_mek = models.DecimalField(default=0, max_digits=16,
                                        decimal_places=4)
    sanctions_mee = models.DecimalField(default=0, max_digits=16,
                                        decimal_places=4)
    sanctions_ekmp = models.DecimalField(default=0, max_digits=16,
                                         decimal_places=4)
    comment = models.CharField(max_length=256)
    refer_organization = models.ForeignKey(MedicalOrganization,
                                           db_column='refer_organization_fk',
                                           null=True)
    form = models.ForeignKey(MedicalServiceForm, db_column='form_fk', null=True)
    division = models.ForeignKey(MedicalDivision, db_column='division_fk',
                                 null=True)
    treatment_result = models.ForeignKey('TreatmentResult',
                                         db_column='treatment_result_fk',
                                         null=True)
    treatment_outcome = models.ForeignKey('TreatmentOutcome',
                                          db_column='treatment_outcome_fk',
                                          null=True)
    worker_speciality = models.ForeignKey(MedicalWorkerSpeciality,
                                          db_column='worker_speciality_fk',
                                          null=True)
    speciality_dict_version = models.CharField(max_length=6)
    worker_code = models.CharField(max_length=16)
    special = models.ForeignKey('Special', db_column='special_fk', null=True)
    standard_fk = models.IntegerField()
    concomitant_standard_fk = models.IntegerField()
    record = models.ForeignKey(MedicalRegisterRecord, db_column='record_fk')
    hospitalization = models.ForeignKey(MedicalHospitalization,
                                        db_column='hospitalization_fk',
                                        null=True)
    tfoms_surcharge = models.DecimalField(default=0, max_digits=16,
                                          decimal_places=4)
    ffoms_surcharge = models.DecimalField(default=0, max_digits=16,
                                          decimal_places=4)
    single_channel_surcharge = models.DecimalField(default=0, max_digits=16,
                                                   decimal_places=4)
    status = models.ForeignKey(ProvidedEventStatus, db_column='status_fk',
                               null=True)
    sanctions_mek = models.DecimalField(default=0, max_digits=16,
                                        decimal_places=4)
    sanctions_mee = models.DecimalField(default=0, max_digits=16,
                                        decimal_places=4)
    sanctions_ekmp = models.DecimalField(default=0, max_digits=16,
                                         decimal_places=4)
    sanctions_org = models.DecimalField(default=0, max_digits=16,
                                        decimal_places=4)
    hitech_kind = models.ForeignKey('MedicalServiceHiTechKind',
                                    db_column='hitech_kind_fk',
                                    null=True)
    hitech_method = models.ForeignKey('MedicalServiceHiTechMethod',
                                      db_column='hitech_method_fk',
                                      null=True)
    examination_result = models.ForeignKey('ExaminationResult',
                                           db_column='examination_result_fk',
                                           null=True)

    ksg_mo = models.CharField(max_length=3)
    ksg_smo = models.CharField(max_length=3)

    class Meta:
        db_table = "provided_event"

    def get_invoiced_payment(self):
        return ProvidedService.objects.filter(event=self) \
            .aggregate(Sum('invoiced_payment'))['invoiced_payment__sum']

    def get_accepted_payment(self):
        return ProvidedService.objects.filter(
            event=self, payment_type_id__in=(2, 4)) \
            .aggregate(Sum('accepted_payment'))['accepted_payment__sum']

    def get_sanctions_mee(self):
        return Sanction.objects.filter(service__event=self,
                                       type_id=2
        ).aggregate(sum=Sum('underpayment'))['sum']

    def get_sanctions_ekmp(self):
        return 0

    def get_sanctions_mek(self):
        query = """
            select sum(pss.underpayment)
            from provided_service ps
                join provided_event pe
                    on ps.event_fk = pe.id_pk
                LEFT join provided_service_sanction pss
                    on pss.service_fk = ps.id_pk and pss.id_pk = (
                        select max(id_pk) from provided_service_sanction
                        where service_fk = ps.id_pk
                    ) and ps.payment_type_fk in (3, 4) and pss.underpayment > 0
                        and pss.type_fk = 1

            where
                    pe.id_pk = %s
        """
        cursor = connection.cursor()
        cursor.execute(query, [self.pk])
        result = cursor.fetchone()[0]

        return result

    def get_payment_type(self):
        service_payments = set(ProvidedService.objects.filter(
            event=self).values_list('payment_type_id', flat=True).distinct())

        payments_sum = sum(service_payments)

        if payments_sum == 2:
            return 2
        elif payments_sum == 3:
            return 3
        elif payments_sum >= 4:
            return 4


class ProvidedEventSpecial(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    event = models.ForeignKey(ProvidedEvent, db_column='event_fk')
    special = models.ForeignKey('Special', db_column='special_fk')

    class Meta:
        db_table = "provided_event_special"


class ProvidedEventConcomitantDisease(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    event = models.ForeignKey(ProvidedEvent, db_column='event_fk',
                              related_name='concomitant_event_fkey')
    disease = models.ForeignKey(IDC, db_column='disease_fk')

    class Meta:
        db_table = 'provided_event_concomitant_disease'


class ProvidedEventComplicatedDisease(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    event = models.ForeignKey(ProvidedEvent, db_column='event_fk',
                              related_name='complicated_event_fkey')
    disease = models.ForeignKey(IDC, db_column='disease_fk')

    class Meta:
        db_table = 'provided_event_complicated_disease'


class OutpatientDivision(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=60)

    class Meta:
        db_table = "medical_outpatient_division"


class InpatientDivision(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=60)

    class Meta:
        db_table = "medical_inpatient_division"


class ProvidedService(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    id = models.CharField(max_length=36, null=True)
    organization = models.ForeignKey(MedicalOrganization,
                                     db_column='organization_fk', null=True)
    department = models.ForeignKey(MedicalOrganization,
                                   db_column='department_fk',
                                   related_name='provided_service_department',
                                   null=True)
    division = models.ForeignKey(MedicalDivision, db_column='division_fk',
                                 null=True)
    profile = models.ForeignKey(MedicalServiceProfile, db_column='profile_fk',
                                null=True)
    is_children_profile = models.NullBooleanField()
    start_date = models.DateField()
    end_date = models.DateField()
    basic_disease = models.ForeignKey(IDC, db_column='basic_disease_fk',
                                      related_name='provided_event_basic_disease',
                                      null=True)
    code = models.ForeignKey(MedicalService, db_column='code_fk', null=True)
    quantity = models.DecimalField(default=0, max_digits=6, decimal_places=2)
    tariff = models.DecimalField(default=0, max_digits=16, decimal_places=4)
    invoiced_payment = models.DecimalField(default=0, max_digits=16,
                                           decimal_places=4)
    worker_speciality = models.ForeignKey(MedicalWorkerSpeciality,
                                          db_column='worker_speciality_fk',
                                          null=True)
    worker_code = models.CharField(max_length=16, null=True)
    comment = models.CharField(max_length=256)
    status = models.ForeignKey(ProvidedServiceStatus, db_column='status_fk')
    event = models.ForeignKey(ProvidedEvent, db_column='event_fk')
    accepted_payment = models.DecimalField(default=0, max_digits=16,
                                           decimal_places=4)
    tfoms_surcharge = models.DecimalField(default=0, max_digits=16,
                                          decimal_places=4)
    ffoms_surcharge = models.DecimalField(default=0, max_digits=16,
                                          decimal_places=4)
    single_channel_surcharge = models.DecimalField(default=0, max_digits=16,
                                                   decimal_places=4)
    payment_type = models.ForeignKey(PaymentType, db_column="payment_type_fk",
                                     null=True)
    payment_failure_cause = models.ForeignKey(PaymentFailureCause,
                                              db_column="payment_failure_cause_fk",
                                              null=True)
    tfoms_surcharge = models.DecimalField(max_digits=16, decimal_places=4)
    ffoms_surcharge = models.DecimalField(max_digits=16, decimal_places=4)
    single_channel_surcharge = models.DecimalField(max_digits=16,
                                                   decimal_places=4)
    sanctions_mek = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_mee = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_ekmp = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_org = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_mee_tfoms = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_mee_ffoms = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_mee_single_channel = models.DecimalField(max_digits=16,
                                                       decimal_places=4)
    sanctions_ekmp_tfoms = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_ekmp_ffoms = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_ekmp_single_channel = models.DecimalField(max_digits=16,
                                                        decimal_places=4)
    correction = models.DecimalField(max_digits=16, decimal_places=4)
    tfoms_correction = models.DecimalField(max_digits=16, decimal_places=4)
    ffoms_correction = models.DecimalField(max_digits=16, decimal_places=4)
    single_channel_correction = models.DecimalField(max_digits=16,
                                                    decimal_places=4)
    comment_error = models.CharField(max_length=24)
    sanction_date = models.DateField()
    #penalty = models.DecimalField(max_digits=16, decimal_places=4)
    sanctions_act = models.CharField(max_length=13)
    calculated_payment = models.DecimalField(max_digits=16, decimal_places=4)
    provided_tariff = models.DecimalField(max_digits=16, decimal_places=4)
    migration = models.IntegerField(db_column='migration_id')
    payment_kind = models.ForeignKey("PaymentKind", db_column='payment_kind_fk')

    def get_sanctions_mee(self):
        return Sanction.objects.filter(service=self,
                                       type_id=2
        ).aggregate(sum=Sum('underpayment'))['sum']

    def get_sanctions_ekmp(self):
        return Sanction.objects.filter(service=self,
                                       type_id=3
        ).aggregate(sum=Sum('underpayment'))['sum']

    def get_sanctions_org(self):
        return Sanction.objects.filter(service=self,
                                       type_id__in=(2, 3)
        ).aggregate(sum=Sum('penalty'))['sum']

    def get_latest_sanction(self):
        sanctions = Sanction.objects.filter(service=self, type_id=1).order_by(
            'id_pk')
        if sanctions:
            return sanctions[0]
        else:
            return ''

    class Meta:
        db_table = "provided_service"


class Special(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=120)

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "special"


class TariffGroup(models.Model):
    ID = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=58)
    old_bb_name = models.CharField(max_length=20)

    class Meta:
        db_table = "tariff_group"


class TariffBasic(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey(MedicalService, db_column='service_fk')
    group = models.ForeignKey(TariffGroup, db_column='group_fk')
    value = models.DecimalField(max_digits=16, decimal_places=4)
    capitation = models.DecimalField(max_digits=16, decimal_places=4)
    start_date = models.DateField()

    class Meta:
        db_table = "tariff_basic"


class TariffMaintenance(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    #klass = models.ForeignKey(MedicalServiceClass, db_column='class_fk')
    group = models.ForeignKey(TariffGroup, db_column='group_fk')
    value = models.DecimalField(max_digits=16, decimal_places=4)
    #start_date = models.DateField()

    class Meta:
        db_table = "tariff_maintenance"


class TreatmentOutcome(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=60)
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk')

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "treatment_outcome"


class TreatmentResult(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=120)
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk')

    objects = ExtendedObjectManager()

    class Meta:
        db_table = "treatment_result"


class SanctionType(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=65)
    code = models.IntegerField()

    class Meta:
        db_table = "provided_service_sanction_type"


class MedicalError(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=60)
    old_code = models.CharField(max_length=2)
    failure_cause = models.ForeignKey(PaymentFailureCause,
                                      db_column='failure_cause_fk',
                                      related_name='error_failure_cause')
    weight = models.IntegerField(db_column='weight')

    class Meta:
        db_table = "medical_error"


class Sanction(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    type = models.ForeignKey(SanctionType, db_column='type_fk')
    underpayment = models.DecimalField(max_digits=16, decimal_places=4)
    penalty = models.DecimalField(max_digits=16, decimal_places=4)
    failure_cause = models.ForeignKey(PaymentFailureCause,
                                      db_column='failure_cause_fk')
    error = models.ForeignKey(MedicalError, db_column='error_fk')
    comment = models.CharField(max_length=250)
    date = models.DateField()
    act = models.CharField(max_length=16)
    service = models.ForeignKey(ProvidedService, db_column='service_fk')
    is_active = models.BooleanField(db_column='is_active')

    class Meta:
        db_table = "provided_service_sanction"


class ExaminationAgeBracket(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    group = models.IntegerField()
    age = models.IntegerField()
    months = models.IntegerField()
    year = models.IntegerField()

    class Meta:
        db_table = "examination_age_bracket"


class TariffCoefficient(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        db_table = "tariff_coefficient"


class ProvidedServiceCoefficient(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey(ProvidedService, db_column='service_fk')
    coefficient = models.ForeignKey(TariffCoefficient,
                                    db_column='coefficient_fk')

    class Meta:
        db_table = "provided_service_coefficient"


class TariffProfile(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=80)
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk')

    class Meta:
        db_table = 'tariff_profile'


class TariffNkd(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    profile = models.ForeignKey(TariffProfile, db_column='profile_fk')
    level = models.IntegerField()
    is_children_profile = models.BooleanField()
    value = models.DecimalField(max_digits=6, decimal_places=2)
    start_date = models.DateField()

    class Meta:
        db_table = 'tariff_nkd'


class MedicalServiceSubgroup(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=80)

    class Meta:
        db_table = 'medical_service_subgroup'


class MedicalServiceDisease(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey(MedicalService, db_column='service_fk')
    disease = models.ForeignKey(IDC, db_column='disease_fk')

    class Meta:
        db_table = 'medical_service_disease'


class TariffFap(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    organization = models.ForeignKey(MedicalOrganization, db_column='organization_fk')
    is_children_profile = models.BooleanField()
    value = models.DecimalField(max_digits=4, decimal_places=3)
    start_date = models.DateField(db_column='start_date')

    class Meta:
        db_table = 'tariff_fap'


class TariffCapitation(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk')
    organization = models.ForeignKey(MedicalOrganization, db_column='organization_fk')
    is_children_profile = models.BooleanField()
    value = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(db_column='start_date')
    gender = models.ForeignKey(Gender, db_column='gender_fk')
    age_group = models.IntegerField(db_column='age_group')

    class Meta:
        db_table = 'tariff_capitation'


class AttachmentStatistics(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    organization = models.CharField(max_length=6, db_column='organization')
    less_one_age_male = models.IntegerField()
    less_one_age_female = models.IntegerField()
    one_four_age_male = models.IntegerField()
    one_four_age_female = models.IntegerField()
    five_seventeen_age_male = models.IntegerField()
    five_seventeen_age_female = models.IntegerField()
    eighthteen_fiftynine_age_male = models.IntegerField()
    eighthteen_fiftyfour_age_female = models.IntegerField()
    older_sixty_age_male = models.IntegerField()
    older_fiftyfive_age_female = models.IntegerField()

    less_one_age_male_ambulance = models.IntegerField()
    less_one_age_female_ambulance = models.IntegerField()
    one_four_age_male_ambulance = models.IntegerField()
    one_four_age_female_ambulance = models.IntegerField()
    five_seventeen_age_male_ambulance = models.IntegerField()
    five_seventeen_age_female_ambulance = models.IntegerField()
    eighthteen_fiftynine_age_male_ambulance = models.IntegerField()
    eighthteen_fiftyfour_age_female_ambulance = models.IntegerField()
    older_sixty_age_male_ambulance = models.IntegerField()
    older_fiftyfive_age_female_ambulance = models.IntegerField()

    at = models.DateField()
    group = models.IntegerField()

    class Meta:
        db_table = 'attachment_statistics'


class PaymentKind(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    name = models.CharField(max_length=40, db_column='name')

    class Meta:
        db_table = 'payment_kind'


class SanctionStatus(models.Model):

    SANCTION_TYPE_ADDED_BY_MEK = 1
    SANCTION_TYPE_ADDED_BY_EXPERT = 2
    SANCTION_TYPE_ADDED_BY_ECONOMIST = 3
    SANCTION_TYPE_ADDED_BY_DEVELOPER = 4
    SANCTION_TYPE_REMOVED_BY_EXPERT = 5
    SANCTION_TYPE_REMOVED_BY_ECONOMIST = 6
    SANCTION_TYPE_REMOVED_BY_DEVELOPER = 7
    SANCTION_TYPE_ADDED_MAX_ERROR_BY_MEK = 8
    TYPES = (
        (SANCTION_TYPE_ADDED_BY_MEK, u'Ошибка добавлена на первоначальном МЭК'),
        (SANCTION_TYPE_ADDED_BY_EXPERT, u'Ошибка добавлена врачём-экспертом'),
        (SANCTION_TYPE_ADDED_BY_ECONOMIST, u'Ошибка добавлена экономистом'),
        (SANCTION_TYPE_ADDED_BY_DEVELOPER, u'Ошибка добавлена программистом'),
        (SANCTION_TYPE_REMOVED_BY_EXPERT, u'Ошибка снята врачём-экспертом'),
        (SANCTION_TYPE_REMOVED_BY_ECONOMIST, u'Ошибка снята экономистом'),
        (SANCTION_TYPE_REMOVED_BY_DEVELOPER, u'Ошибка снята программистом'),
        (SANCTION_TYPE_ADDED_MAX_ERROR_BY_MEK, u'Ошибка проставлена на всём случае с максимальным весом')
    )

    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    sanction = models.ForeignKey(Sanction, db_column='sanction_fk')
    created_at = models.DateTimeField(default=datetime.datetime.utcnow())
    type = models.SmallIntegerField(choices=TYPES)
    comment = models.CharField(max_length=128)

    class Meta:
        db_table = 'provided_service_sanction_status'


class MedicalServiceVolume(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    organization = models.ForeignKey(MedicalOrganization,
                                     db_column='organization_fk')
    date = models.DateField()
    hospital = models.IntegerField()
    day_hospital = models.IntegerField()
    clinic_prevention = models.IntegerField()
    clinic_emergency = models.IntegerField()
    clinic_disease = models.IntegerField()
    stomatology_prevention = models.DecimalField(default=0, max_digits=15,
                                                 decimal_places=2)
    stomatology_emergency = models.DecimalField(default=0, max_digits=15,
                                                decimal_places=2)
    stomatology_disease = models.DecimalField(default=0, max_digits=15,
                                              decimal_places=2)

    class Meta:
        db_table = 'medical_service_volume'


class MedicalRegisterImport(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    organization = models.CharField(max_length=10)
    filename = models.CharField(max_length=30)
    status = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)
    period = models.CharField(max_length=10)

    class Meta:
        db_table = 'medical_register_import'


class ExaminationTariff(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    service = models.ForeignKey(MedicalService, db_column='service_fk')
    value = models.DecimalField(max_digits=15, decimal_places=2, db_column='value')
    regional_coefficient = models.DecimalField(max_digits=4, decimal_places=1, db_column='regional_coefficient')
    gender = models.SmallIntegerField(db_column='gender_fk')
    age = models.SmallIntegerField(db_column='age')
    start_date = models.DateField(db_column='start_date')

    class Meta:
        db_table = 'examination_tariff'


class KPG(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=80)

    class Meta:
        db_table = 'kpg'


class KSG(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    code = models.IntegerField()
    name = models.CharField(max_length=80)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2)
    start_date = models.DateField(db_column='start_date')
    kpg = models.ForeignKey(KPG, db_column='kpg_fk')
    term = models.ForeignKey(MedicalServiceTerm, db_column='term_fk')

    class Meta:
        db_table = 'ksg'


class TariffKSG(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    ksg = models.ForeignKey(KSG, db_column='ksg_fk')
    level = models.SmallIntegerField()
    regional_coefficient = models.DecimalField(max_digits=2, decimal_places=1)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField(db_column='start_date')

    class Meta:
        db_table = 'tariff_ksg'


class TariffNkdKSG(models.Model):
    id_pk = models.IntegerField(primary_key=True, db_column='id_pk')
    ksg = models.ForeignKey(KSG, db_column='ksg_fk')
    level = models.SmallIntegerField()
    value = models.DecimalField(max_digits=6, decimal_places=2)
    start_date = models.DateField(db_column='start_date')

    class Meta:
        db_table = 'tariff_nkd_ksg'


class Fluorography(models.Model):
    id_pk = models.AutoField(primary_key=True, db_column='id_pk')
    first_name = models.CharField(max_length=40)
    last_name = models.CharField(max_length=40)
    middle_name = models.CharField(max_length=40)
    birthdate = models.DateField()
    gender = models.ForeignKey(Gender, db_column='gender_fk')
    insurance_policy_series = models.CharField(max_length=10)
    insurance_policy_number = models.CharField(max_length=20)
    insurance_policy = models.IntegerField(db_column='insurance_policy_fk')
    attachment_code = models.CharField(max_length=6)
    start_date = models.DateField()
    date = models.DateField()

    class Meta:
        db_table = 'fluorography'


class DMS(models.Model):
    id = models.AutoField(primary_key=True)
    last_name = models.CharField(max_length=70)
    first_name = models.CharField(max_length=70)
    middle_name = models.CharField(max_length=70)
    birth_date = models.DateField()
    organization = models.CharField(max_length=70)
    series_zhaco = models.CharField(max_length=10)
    number_zhaco = models.CharField(max_length=20)
    service_code = models.CharField(max_length=20)
    service_name = models.CharField(max_length=250)
    quantity = models.IntegerField()
    cost = models.DecimalField(max_digits=20, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    worker_code = models.IntegerField()
    disease = models.CharField(max_length=5)
    accepted_payment = models.DecimalField(max_digits=20, decimal_places=2)
    filename = models.CharField(max_length=255)

    class Meta:
        db_table = 'voluntary_medical_insurance'
