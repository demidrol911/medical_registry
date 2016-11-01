#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from main.models import (ProvidedService, Patient)
from main.models import SERVICE_XML_TYPES, EXAMINATION_TYPES
from helpers import xml_writer as writer
from main.models import MedicalRegister
from main.funcs import safe_str, safe_int
from medical_service_register.settings import YEAR, PERIOD
from main.funcs import howlong


def get_value_or_no(value):
    return safe_str(value) if value else u'НЕТ'.encode('cp1251')


def get_patients(year, period):
    """
    Получить всех пациентов в текущем периоде
    """
    query = """
        select p1.*, person_id_type.code as id_type
            , p1.attachment_code
        from
            patient p1
            LEFT join person_id_type
                on p1.person_id_type_fk = person_id_type.id_pk
        where p1.id_pk in (
            select DISTINCT medical_register_record.patient_fk
            from medical_register
            join medical_register_record
                on medical_register.id_pk = medical_register_record.register_fk
            join provided_event
                on medical_register_record.id_pk = provided_event.record_fk
            join provided_service
                on provided_service.event_fk = provided_event.id_pk
            where
                medical_register.is_active
                and medical_register.year = %(year)s
                and medical_register.period = %(period)s
            )
        """
    return Patient.objects.raw(query, dict(year=year, period=period))


def get_records(register_pk):
    """
    Получить все записи об услугах в текущем периоде
    """
    query = """
        select
            provided_service.id_pk,
            medical_register_record.id as record_uid,
            patient.id as patient_uid,
            patient.insurance_policy_type_fk as insurance_policy_type,
            patient.insurance_policy_series as insurance_policy_series,
            patient.insurance_policy_number as insurance_policy_number,
            patient.newborn_code as newborn_code,
            patient.weight as weight,
            provided_event.id as event_uid,
            provided_event.term_fk as event_term_code,
            medical_service_kind.code as event_kind_code,
            provided_event.form_fk as event_form_code,
            medical_service_hitech_kind.code as hitech_kind_code,
            medical_service_hitech_method.code as hitech_method_code,
            provided_event.hospitalization_fk as event_hospitalization_code,
            event_division.code as event_division_code,
            referred.code as event_referred_organization_code,
            medical_register.organization_code as event_organization_code,
            medical_organization.old_code as event_department_code,
            provided_event.division_fk,
            event_profile.code as event_profile_code,
            provided_event.is_children_profile as event_is_children,
            provided_event.anamnesis_number as anamnesis_number,
            provided_event.examination_rejection,
            (
                select min(ps2.start_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_start_date,
            (
                select max(ps2.end_date)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_end_date,
            idc_initial.idc_code as event_initial_disease_code,
            idc_basic.idc_code as event_basic_disease_code,
                idc_basic.idc_code as event_basic_disease_code,
            ARRAY(select idc.idc_code
                from provided_event_concomitant_disease
                    join idc
                        on idc.id_pk = provided_event_concomitant_disease.disease_fk
                where event_fk = provided_event.id_pk) as event_concomitant_disease_code,
            ARRAY(select idc.idc_code
                from provided_event_complicated_disease
                    join idc
                        on idc.id_pk = provided_event_complicated_disease.disease_fk
                where event_fk = provided_event.id_pk) as event_complicated_disease_code,
            treatment_result.code as treatment_result_code,
            treatment_outcome.code as treatment_outcome_code,
            medical_worker_speciality.code as event_worker_speciality_code,
            provided_event.speciality_dict_version,
            provided_event.worker_code as event_worker_code,
            provided_event.payment_method_fk as event_payment_method_code,
            provided_event.special_fk as event_special_code,
            (
                case provided_event.term_fk
                when 1 THEN
                    1
                WHEN 2 THEN
                    (SELECT sum(provided_service.quantity)
                    from provided_service
                    where event_fk = provided_event.id_pk)
                WHEN 3 THEN
                    (SELECT sum(provided_service.quantity)
                    from provided_service
                    where event_fk = provided_event.id_pk)
                ELSE
                    1
                end
            ) as event_payment_units_number,
            (
                select sum(ps2.tariff)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_tariff,
            (
                select sum(ps2.invoiced_payment)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
            ) as event_invoiced_payment,
            (
                case
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) = 2 then 1
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) = 3 then 2
                when
                    (select sum(payment)
                    from (
                        select distinct ps2.payment_type_fk as payment
                        from provided_service ps2
                        where provided_event.id_pk = ps2.event_fk
                    ) as t1) >= 4 then 3
                End
            ) as event_payment_type_code,
            (
                select sum(ps2.accepted_payment)
                from provided_service ps2
                where provided_event.id_pk = ps2.event_fk
                    and ps2.payment_type_fk in (2, 4)
            ) as event_accepted_payment,
            (
                select sum(provided_service_sanction.underpayment)
                from provided_service ps2
                    join provided_service_sanction
                        on provided_service_sanction.service_fk = ps2.id_pk
                            and provided_service_sanction.id_pk = (CASE
                                WHEN (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                                    and underpayment > 0
                            ) is NULL
                                THEN (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                            )
                            ELSE
                            (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                                    and underpayment > 0
                            )
                            END
                            )
                            and ps2.payment_type_fk in (3, 4)
                where ps2.event_fk = provided_event.id_pk
                    and provided_service_sanction.type_fk = 1
            ) as event_sanctions_mek,

            ARRAY(SELECT ROW(ps2.id
                    , provided_service_sanction.underpayment
                    , 1
                    , medical_error.failure_cause_fk
                    , ''
                    , 1)
                from provided_service ps2
                    join provided_service_sanction
                        on provided_service_sanction.service_fk = ps2.id_pk
                            and provided_service_sanction.id_pk = (CASE
                                WHEN (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                                    and underpayment > 0
                            ) is NULL
                                THEN (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                            )
                            ELSE
                            (
                                select max(id_pk)
                                from provided_service_sanction
                                where service_fk = ps2.id_pk
                                    and underpayment > 0
                            )
                            END
                            )
                            and ps2.payment_type_fk in (3, 4)
                    JOIN medical_error
                        on medical_error.id_pk = provided_service_sanction.error_fk
                where ps2.event_fk = provided_event.id_pk
                    and provided_service_sanction.type_fk = 1
                order by provided_service_sanction.underpayment desc
            ) as event_sanctions,
            provided_event.examination_result_fk as examination_result_code,
            provided_event.ksg_mo as ksg_mo,
            provided_event.ksg_smo as ksg_smo,
            provided_event.comment as event_comment,
            provided_service.id_pk as service_pk,
            provided_service.id as service_uid,
            medical_register.organization_code as service_organization_code,
            service_department.old_code as service_department_code,
            service_division.code as service_division_code,
            service_profile.code as service_profile_code,
            provided_service.is_children_profile as service_is_children,
            provided_service.start_date as service_start_date,
            provided_service.end_date as service_end_date,
            service_idc_basic.idc_code as service_basic_disease_code,
            medical_service.code as service_code,
            provided_service.quantity,
            provided_service.tariff as service_tariff,
            provided_service.invoiced_payment as service_invoiced_payment,
            payment_type.code as service_payment_type_code,
            provided_service.accepted_payment as service_accepted_payment,
            service_worker_speciality.code as service_worker_speciality_code,
            provided_service.worker_code as service_worker_code,
            provided_service.comment as service_comment,
            case coalesce((select min(payment_kind_fk) from provided_service where tariff > 0 and event_fk = provided_event.id_pk and payment_type_fk = 2), 1)
            when 3 then 1
            when 2 then 2
            else 1 end as payment_kind_code
        from
            medical_register
            join medical_register_record
                on medical_register.id_pk = medical_register_record.register_fk
            JOIN patient
                on patient.id_pk = medical_register_record.patient_fk
            join provided_event
                on provided_event.record_fk = medical_register_record.id_pk
            join provided_service
                on provided_service.event_fk = provided_event.id_pk
            LEFT join medical_service_profile event_profile
                on event_profile.id_pk = provided_event.profile_fk
            LEFT JOIN medical_division event_division
                on event_division.id_pk = provided_event.division_fk
            left join medical_service_hitech_kind
                on provided_event.hitech_kind_fk = medical_service_hitech_kind.id_pk
            left join medical_service_hitech_method
                on provided_event.hitech_method_fk = medical_service_hitech_method.id_pk

            JOIN medical_organization
                ON medical_organization.id_pk = provided_event.department_fk
            left join medical_organization referred
                on referred.id_pk = provided_event.refer_organization_fk
            left join idc idc_initial
                on idc_initial.id_pk = provided_event.initial_disease_fk
            LEFT join idc idc_basic
                on idc_basic.id_pk = provided_event.basic_disease_fk
            LEFT JOIN treatment_result
                on treatment_result.id_pk = provided_event.treatment_result_fk
            LEFT join treatment_outcome
                on treatment_outcome.id_pk = provided_event.treatment_outcome_fk
            LEFT JOin medical_worker_speciality
                on medical_worker_speciality.id_pk = provided_event.worker_speciality_fk
            LEFT join examination_result
                on examination_result.id_pk = provided_event.examination_result_fk

            left JOIN medical_division service_division
                on service_division.id_pk = provided_service.division_fk
            LEFT JOIN medical_organization service_department
                ON service_department.id_pk = provided_service.department_fk
            LEFT join idc service_idc_basic
                on service_idc_basic.id_pk = provided_service.basic_disease_fk
            LEFT join medical_service_profile service_profile
                on service_profile.id_pk = provided_service.profile_fk
            LEFT JOin medical_worker_speciality service_worker_speciality
                on service_worker_speciality.id_pk = provided_service.worker_speciality_fk
            JOIN medical_service
                on provided_service.code_fk = medical_service.id_pk
            LEFT JOIN payment_type
                on provided_service.payment_type_fk = payment_type.id_pk
            LEFT JOIN medical_service_kind
                on medical_service_kind.id_pk = provided_event.kind_fk
        where
            medical_register.id_pk = %s
        order by medical_register_record.id,
            provided_event.id,
            provided_service.id
    """

    return ProvidedService.objects.raw(query, [register_pk])


class RegistryToXmlExporter():
    EXAMINATIONS = dict(EXAMINATION_TYPES)
    XML_TYPES = {t[0]: t[1] for t in SERVICE_XML_TYPES if t[0] != 0}

    def __init__(self, year, period, version):
        self.year = year
        self.short_year = self.year[2:4]
        self.period = period
        self.version = version
        self.service_filename_pattern = '{type}S28004T28_{year}{period}{version}'
        self.latest_record = None
        self.current_record = None
        self.current_register_type = None

    @howlong
    def export_patients(self):
        """
        Выгружает пациентов в xml
        """
        filename = 'LS28004T28_{year}{period}{version}'.format(
            year=self.short_year,
            period=self.period,
            version=self.version
        )
        print u'Выгрузка файла с пациентами %s...' % filename
        lm_xml = writer.Xml(filename+'.xml')
        lm_xml.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
        lm_xml.start('PERS_LIST')
        lm_xml.start('ZGLV')
        lm_xml.put('VERSION', '2.1')
        lm_xml.put('DATA', '18.{period}.{year}'.format(period=self.period, year=self.year))
        lm_xml.put('FILENAME', filename)
        lm_xml.put('FILENAME1', self.service_filename_pattern.format(
            type='H', year=self.short_year, period=self.period, version=self.version
        ))
        lm_xml.end('ZGLV')
        for i, patient in enumerate(get_patients(self.year, self.period)):
            lm_xml.start('PERS')
            lm_xml.put('ID_PAC', safe_str(patient.id))
            lm_xml.put('FAM', get_value_or_no(patient.last_name))
            lm_xml.put('IM', get_value_or_no(patient.first_name))
            lm_xml.put('OT', get_value_or_no(patient.middle_name))
            lm_xml.put('W', safe_int(patient.gender_id))
            lm_xml.put('DR', patient.birthdate if patient.birthdate else '')
            lm_xml.put('FAM_P', safe_str(patient.agent_last_name))
            lm_xml.put('IM_P', safe_str(patient.agent_first_name))
            lm_xml.put('OT_P', safe_str(patient.agent_middle_name))
            lm_xml.put('W_P', safe_int(patient.agent_gender_id))
            lm_xml.put('DR_P', patient.agent_birthdate if patient.agent_birthdate else '')
            lm_xml.put('MR', safe_str(patient.birthplace))
            lm_xml.put('DOCTYPE', safe_int(patient.id_type))
            lm_xml.put('DOCSER', safe_str(patient.person_id_series))
            lm_xml.put('DOCNUM', safe_str(patient.person_id_number))
            lm_xml.put('SNILS', safe_str(patient.snils))
            lm_xml.put('OKATOG', safe_str(patient.okato_registration))
            lm_xml.put('OKATOP', safe_str(patient.okato_residence))
            lm_xml.put('COMENTP', patient.attachment_code or '')
            lm_xml.end('PERS')
        lm_xml.end('PERS_LIST')

    @howlong
    def export_services(self):
        """
        Выгружает услуги в xml
        """
        registers = MedicalRegister.objects.filter(is_active=True, period=self.period, year=self.year).\
            order_by('organization_code')
        for register_type in RegistryToXmlExporter.XML_TYPES:
            self.current_register_type = register_type
            filename = self.service_filename_pattern.format(
                type=RegistryToXmlExporter.XML_TYPES[register_type].upper(),
                year=self.short_year, period=self.period,
                version=self.version
            )
            print u'Выгрузка файла с услугами %s...' % filename
            hm_xml = writer.Xml('%s.XML' % filename)
            self._put_header(hm_xml, filename)

            for index, register in enumerate(registers.filter(type=self.current_register_type)):
                self._put_bill(hm_xml, register, index)

                current_record_id = None
                current_event_id = None
                self.latest_record = None
                for i, record in enumerate(list(get_records(register.pk))):
                    self.current_record = record

                    if current_record_id != record.record_uid:
                        self._put_tag_end_event(hm_xml, current_event_id)
                        if current_record_id:
                            hm_xml.end('ZAP')
                        self._put_record(hm_xml)
                        current_record_id = record.record_uid
                        current_event_id = None

                    if current_event_id != record.event_uid:
                        self._put_tag_end_event(hm_xml, current_event_id)
                        self._put_event(hm_xml)
                        current_event_id = record.event_uid
                        self._put_sanction(hm_xml)
                    self._put_service(hm_xml)
                    self.latest_record = self.current_record
                self._put_tag_end_event(hm_xml, current_event_id)
                if current_record_id:
                    hm_xml.end('ZAP')
            hm_xml.end('ZL_LIST')

    def _put_tag_end_event(self, hm_xml, current_event_id):
        """
        Поместить тег закрытия случая в XML
        """
        if current_event_id:
            if self.current_register_type in (1, 2):
                hm_xml.put('KSG_MO', safe_str(self.latest_record.ksg_mo))
                hm_xml.put('KSG_SMO', safe_str(self.latest_record.ksg_smo))
            hm_xml.put('COMENTSL', safe_str(self.latest_record.event_comment))
            hm_xml.put('PAYMENT_KIND', self.latest_record.payment_kind_code)
            hm_xml.end('SLUCH')

    def _put_header(self, hm_xml, filename):
        """
        Поместить заголовок в XML
        """
        hm_xml.plain_put('<?xml version="1.0" encoding="windows-1251"?>')
        hm_xml.start('ZL_LIST')
        hm_xml.start('ZGLV')
        hm_xml.put('VERSION', '2.1')
        hm_xml.put('DATA', '18.{period}.{year}'.format(period=self.period, year=self.year))
        hm_xml.put('FILENAME', filename)
        hm_xml.end('ZGLV')

    def _put_bill(self, hm_xml, register, index):
        """
        Поместить информацию о счёте в XML
        """
        hm_xml.start('SCHET')
        hm_xml.put('CODE', index+1)
        hm_xml.put('CODE_MO', register.organization_code)
        hm_xml.put('YEAR', register.year)
        hm_xml.put('MONTH', register.period)
        hm_xml.put('NSCHET', index+1)
        hm_xml.put('DSCHET', register.invoice_date.strftime("%Y-%m-%d"))
        hm_xml.put('PLAT', '28004')
        invoiced_payment = register.get_invoiced_payment()
        accepted_payment = register.get_accepted_payment()
        sanctions_mek = register.get_sanctions_mek()

        if sanctions_mek < 0:
            sanctions_mek = 0
        hm_xml.put('SUMMAV', round(invoiced_payment or 0, 2))
        hm_xml.put('COMENTS', safe_str(register.invoice_comment))
        hm_xml.put('SUMMAP', round(float(accepted_payment or 0), 2))
        hm_xml.put('SANK_MEK', round(float(sanctions_mek or 0), 2))
        hm_xml.put('SANK_MEE', 0)
        hm_xml.put('SANK_EKMP', 0)
        hm_xml.put('SANK_ORG', 0)

        if self.current_register_type == 1:
            # Подушевой норматив по поликлиники
            policlinic_capitation_population = 0
            policlinic_capitation_tariff = 0
            policlinic_capitation = MedicalRegister.calculate_capitation(3, register.organization_code)
            if policlinic_capitation[0]:
                policlinic_capitation_population = policlinic_capitation[1]['adult']['population'] + \
                                                   policlinic_capitation[1]['child']['population']
                policlinic_capitation_tariff = round(policlinic_capitation[1]['adult']['accepted'] +
                                                     policlinic_capitation[1]['child']['accepted'], 2)

            # Подушевой норматив по скорой помощи
            ambulance_capitation_population = 0
            ambulance_capitation_tariff = 0
            ambulance_capitation = MedicalRegister.calculate_capitation(4, register.organization_code)
            if ambulance_capitation[0]:
                ambulance_capitation_population = ambulance_capitation[1]['adult']['population'] + \
                                                  ambulance_capitation[1]['child']['population']
                ambulance_capitation_tariff = round(ambulance_capitation[1]['adult']['accepted'] +
                                                    ambulance_capitation[1]['child']['accepted'], 2)

            # Флюорография доплата для ГП2, вычет для всех остальных
            fluorography_population = 0
            fluorography_tariff = 0
            fluorography = MedicalRegister.calculate_fluorography(register.organization_code)
            if fluorography[0]:
                fluorography_population = fluorography[1]['adult']['population'] + \
                                                  fluorography[1]['child']['population']
                fluorography_tariff = round(
                    (fluorography[1]['adult']['accepted'] if register.organization_code == '280085'
                     else -fluorography[1]['adult']['accepted']) +
                    (fluorography[1]['child']['accepted'] if register.organization_code == '280085'
                     else -fluorography[1]['child']['accepted']), 2)

            hm_xml.put('POL_COL', policlinic_capitation_population)
            hm_xml.put('POL_SUMPF', policlinic_capitation_tariff)
            hm_xml.put('SMP_COL', ambulance_capitation_population)
            hm_xml.put('SMP_SUMPF', ambulance_capitation_tariff)
            hm_xml.put('FS_COL', fluorography_population)
            hm_xml.put('FS_SUMPF', fluorography_tariff)

        if self.current_register_type > 2:
            hm_xml.put('DISP', RegistryToXmlExporter.EXAMINATIONS[self.current_register_type-2].encode('cp1251'))
        hm_xml.end('SCHET')

    def _put_record(self, hm_xml):
        """
        Поместить информацию о записи в XML
        """
        hm_xml.start('ZAP')
        hm_xml.put('N_ZAP', self.current_record.record_uid)
        hm_xml.put('PR_NOV', '0')
        hm_xml.start('PACIENT')
        hm_xml.put('ID_PAC', safe_str(self.current_record.patient_uid))
        hm_xml.put('VPOLIS', safe_int(self.current_record.insurance_policy_type))
        hm_xml.put('SPOLIS', safe_str(self.current_record.insurance_policy_series))
        hm_xml.put('NPOLIS', safe_str(self.current_record.insurance_policy_number))
        hm_xml.put('ST_OKATO', '')
        hm_xml.put('SMO', '28004')
        hm_xml.put('SMO_OGRN', '1027739008440')
        hm_xml.put('SMO_OK', '10000')
        hm_xml.put('SMO_NAM', u'АО "Страховая компания "СОГАЗ-Мед" Амурский филиал'.encode('cp1251'))
        if self.current_register_type in (1, 2):
            hm_xml.put('NOVOR', self.current_record.newborn_code if self.current_record.newborn_code else '0')
        hm_xml.put('VNOV_D', self.current_record.weight or '')
        hm_xml.end('PACIENT')

    def _put_event(self, hm_xml):
        """
        Поместить информацию о случае в XML
        """
        hm_xml.start('SLUCH')
        hm_xml.put('IDCASE', self.current_record.event_uid)

        if self.current_register_type in (1, 2):
            hm_xml.put('USL_OK', self.current_record.event_term_code or '')
        hm_xml.put('VIDPOM', self.current_record.event_kind_code or '')

        if self.current_register_type in (1, 2):
            hm_xml.put('FOR_POM', self.current_record.event_form_code or '')

        if self.current_register_type == 2:
            hm_xml.put('VID_HMP', self.current_record.hitech_kind_code or '')
            hm_xml.put('METOD_HMP', self.current_record.hitech_method_code or '')

        if self.current_register_type in (1, 2):
            hm_xml.put('NPR_MO', self.current_record.event_referred_organization_code or '')
            hm_xml.put('EXTR', self.current_record.event_hospitalization_code or '')
        hm_xml.put('LPU', self.current_record.event_organization_code or '')
        hm_xml.put('LPU_1', self.current_record.event_department_code or '')

        if self.current_register_type in (1, 2):
            hm_xml.put('PODR', self.current_record.event_division_code or '')
            hm_xml.put('PROFIL', self.current_record.event_profile_code or '')
            hm_xml.put('DET', '1' if self.current_record.event_is_children else '0')
        hm_xml.put('NHISTORY', self.current_record.anamnesis_number.encode('cp1251'))

        if self.current_register_type in (3, 4, 5, 6, 7, 8, 9, 10, 11):
            hm_xml.put('P_OTK', self.current_record.examination_rejection or '0')

        start_date = self.current_record.event_start_date
        end_date = self.current_record.event_end_date

        if start_date > end_date:
            hm_xml.put('DATE_1', end_date)
            hm_xml.put('DATE_2', start_date)
        else:
            hm_xml.put('DATE_1', start_date)
            hm_xml.put('DATE_2', end_date)
        if self.current_register_type in (1, 2):
            hm_xml.put('DS0', self.current_record.event_initial_disease_code or '')
        hm_xml.put('DS1', self.current_record.event_basic_disease_code or '')
        if self.current_register_type in (1, 2):
            for rec in self.current_record.event_concomitant_disease_code:
                hm_xml.put('DS2', rec or '')
            for rec in self.current_record.event_complicated_disease_code:
                hm_xml.put('DS3', rec or '')
            hm_xml.put('VNOV_M', self.current_record.weight or '')
            hm_xml.put('CODE_MES1', '')
            hm_xml.put('CODE_MES2', '')
            hm_xml.put('RSLT', self.current_record.treatment_result_code or '')
            hm_xml.put('ISHOD', self.current_record.treatment_outcome_code or '')
            hm_xml.put('PRVS', self.current_record.event_worker_speciality_code or '')
            hm_xml.put('VERS_SPEC', 'V015' or '')
            hm_xml.put('IDDOKT', (self.current_record.event_worker_code or '').encode('cp1251'))
            hm_xml.put('OS_SLUCH', self.current_record.event_special_code or '')
        if self.current_register_type > 2:
            hm_xml.put('RSLT_D', self.current_record.examination_result_code or '')
        hm_xml.put('IDSP', self.current_record.event_payment_method_code or '')
        hm_xml.put('ED_COL', self.current_record.event_payment_units_number or 0)
        hm_xml.put('TARIF', round(float(self.current_record.event_tariff or 0), 2))
        hm_xml.put('SUMV', round(float(self.current_record.event_invoiced_payment or 0), 2))
        if self.current_record.event_sanctions_mek > 0:
            hm_xml.put('OPLATA', self.current_record.event_payment_type_code or '')
        else:
            if self.current_record.event_payment_type_code == 3:
                hm_xml.put('OPLATA', 1)
            else:
                hm_xml.put('OPLATA', self.current_record.event_payment_type_code or '')
        sump = round(float(self.current_record.event_accepted_payment or 0), 2)

        hm_xml.put('SUMP', sump or 0)
        hm_xml.put('SANK_IT', round(float(self.current_record.event_sanctions_mek or 0), 2))

    def _put_sanction(self, hm_xml):
        """
        Поместить информацию о санкциях в XML
        """
        s = self.current_record.event_sanctions[1:-1].replace('"', '').\
            replace("(", '').replace('),', ';').replace(')', '')
        if s:
            sanctions = s.split(';')
            for rec in sanctions:
                sanc_rec = rec.split(',')
                hm_xml.start('SANK')
                hm_xml.put('S_CODE', sanc_rec[0])
                hm_xml.put('S_SUM', round(float(sanc_rec[1] or 0), 2))
                hm_xml.put('S_ORG', 0)
                hm_xml.put('S_TIP', sanc_rec[2])
                hm_xml.put('S_OSN', sanc_rec[3])
                hm_xml.put('S_COM', '')
                hm_xml.put('S_IST', sanc_rec[5])
                hm_xml.end('SANK')

    def _put_service(self, hm_xml):
        """
        Поместить информацию об услугах в XML
        """
        service_is_children_profile = '1' if self.current_record.service_is_children else '0'
        hm_xml.start('USL')
        hm_xml.put('IDSERV', self.current_record.service_uid)
        hm_xml.put('LPU', self.current_record.service_organization_code)
        hm_xml.put('LPU_1', self.current_record.service_department_code or '')
        if self.current_register_type in (1, 2):
            hm_xml.put('PODR', self.current_record.service_division_code or '')
            hm_xml.put('PROFIL', self.current_record.service_profile_code or '')
            hm_xml.put('VID_VME', '')
            hm_xml.put('DET', service_is_children_profile)
        start_date = self.current_record.service_start_date
        end_date = self.current_record.service_end_date

        if start_date > end_date:
            hm_xml.put('DATE_IN', end_date)
            hm_xml.put('DATE_OUT', start_date)
        else:
            hm_xml.put('DATE_IN', start_date)
            hm_xml.put('DATE_OUT', end_date)
        if self.current_register_type in (1, 2):
            hm_xml.put('DS', self.current_record.service_basic_disease_code or '')
        hm_xml.put('CODE_USL', self.current_record.service_code or '')
        if self.current_register_type in (1, 2):
            hm_xml.put('KOL_USL', self.current_record.quantity or '')
        hm_xml.put('TARIF', round(float(self.current_record.service_tariff or 0), 2) or 0)
        accepted_payment = self.current_record.service_accepted_payment or 0

        if self.current_record.service_payment_type_code == 2:
            accepted_payment = 0

        sumv_usl = round(float(accepted_payment), 2)
        hm_xml.put('SUMV_USL', sumv_usl or 0)
        hm_xml.put('PRVS', self.current_record.service_worker_speciality_code or '')
        hm_xml.put('CODE_MD', (self.current_record.service_worker_code or '').encode('cp1251'))
        hm_xml.put('COMENTU', self.current_record.service_comment or '')
        hm_xml.end('USL')


class Command(BaseCommand):
    """
    Выгрузка реестров за текущий месяц для ТФОМС
    """
    
    def handle(self, *args, **options):
        version = '1'
        if args and len(args) > 0:
            version = args[0]
        xml_exporter = RegistryToXmlExporter(year=YEAR, period=PERIOD, version=version)
        xml_exporter.export_patients()
        xml_exporter.export_services()