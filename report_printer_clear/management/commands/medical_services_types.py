#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from main.funcs import howlong
from medical_service_register.path import REESTR_EXP
from report_printer_clear.management.commands.medical_services_types_pages.clinic_all import ClinicAllPrimary, \
    ClinicAllSpec, ClinicAll
from report_printer_clear.management.commands.medical_services_types_pages.clinic_capitation_all import \
    ClinicCapitationAll, ClinicCapitationAllPrimary, ClinicCapitationAllSpec
from report_printer_clear.management.commands.medical_services_types_pages.clinic_capitation_disease import \
    ClinicCapitationDiseaseTreatmentPrimary, ClinicCapitationDiseaseSingleVisitSpec, \
    ClinicCapitationDiseaseSingleVisitAll
from report_printer_clear.management.commands.medical_services_types_pages.clinic_capitation_other_purposes import \
    ClinicCapitationOtherPurposesPrimary
from report_printer_clear.management.commands.medical_services_types_pages.clinic_capitation_prevention import \
    ClinicCapitationPreventionSpec, ClinicCapitationPreventionAll
from report_printer_clear.management.commands.medical_services_types_pages.clinic_disease import \
    ClinicDiseaseTreatmentSpec, ClinicDiseaseTreatmentAll, ClinicDiseaseSingleVisitSpec, ClinicDiseaseSingleVisitAll
from report_printer_clear.management.commands.medical_services_types_pages.clinic_emergency import ClinicEmergencySpec, \
    ClinicEmergencyAll, EmergencyCareEmergencyDepartment
from report_printer_clear.management.commands.medical_services_types_pages.clinic_other_purposes import \
    ClinicOtherPurposesPrimary
from report_printer_clear.management.commands.medical_services_types_pages.clinic_prevention import \
    ClinicPreventionPrimary, ClinicPreventionSpec, ClinicPreventionAll, ProphylacticExaminationAdult
from report_printer_clear.management.commands.medical_services_types_pages.day_hospital_all import DayHospitalAll
from report_printer_clear.management.commands.medical_services_types_pages.day_hospital_home import DayHospitalHome
from report_printer_clear.management.commands.medical_services_types_pages.day_hospital_hospital import \
    DayHospitalHospital, InvasiveMethodsPage
from report_printer_clear.management.commands.medical_services_types_pages.day_hospital_hepatitis_C_virus import \
   DayHospitalHepatitisCVirus
from report_printer_clear.management.commands.medical_services_types_pages.day_hospital_policlinic import \
    DayHospitalPoliclinic
from report_printer_clear.management.commands.medical_services_types_pages.hospital_ambulance import \
    HospitalAmbulancePage
from report_printer_clear.management.commands.medical_services_types_pages.hospital_hmc import HospitalHmcPage
from report_printer_clear.management.commands.medical_services_types_pages.magnetic_resonance_imaging import MriPage
from report_printer_clear.management.commands.medical_services_types_pages.policlinic import \
    PoliclinicCapitationVisitOtherPurposesPage, PoliclinicCapitationTreatmentDiseasePage
from report_printer_clear.utils.report import Report, ReportParameters

from medical_services_types_pages.examination_adult import \
    ExamAdultFirstStagePage, ExamAdultSecondStagePage, PreventiveInspectionAdult

from medical_services_types_pages.acute_care import AcuteCarePage

from medical_services_types_pages.capitation import \
    CapitationAmbulatoryCarePage, CapitationAcuteCarePage

from medical_services_types_pages.examination_children import \
    PeriodicMedicalExamPage, \
    PrelimMedicalExamPrimaryPage, \
    PrelimMedicalExamSpecPage, \
    PreventMedicalExamPrimaryPage, \
    PreventMedicalExamSpecPage

from medical_services_types_pages.examination_children_orphans import \
    ExamChildrenDifficultSituationPrimaryPage, \
    ExamChildrenDifficultSituationSpecPage, \
    ExamChildrenWithoutCarePrimaryPage, \
    ExamChildrenWithoutCareSpecPage

from medical_services_types_pages.hospital import HospitalPage

from medical_services_types_pages.stomatology import StomatologyPage


class Command(BaseCommand):

    @howlong
    def handle(self, *args, **options):
        reports_desc = (
            {'pattern': 'stomatology.xls',
             'pages': (StomatologyPage, ),
             'title':  u'cтоматология'},

            # Диспансеризация и профосмотры взрослых
            {'pattern': 'examination_adult.xls',
             'pages': (ExamAdultFirstStagePage, ExamAdultSecondStagePage),
             'title': u'диспансеризация взрослых'},

            {'pattern': 'preventive_inspection_adult.xls',
             'pages': (PreventiveInspectionAdult, ),
             'title': u'профилактический осмотр взрослого населения'},

            # Диспансеризация и профосмотры несовершеннолетних
            {'pattern': 'examination_children_difficult_situation.xls',
             'pages': (ExamChildrenDifficultSituationPrimaryPage,
                       ExamChildrenDifficultSituationSpecPage),
             'title': u'диспансеризация несовершеннолетних в трудной жизненной ситуации'},

            {'pattern': 'examination_children_without_care.xls',
             'pages': (ExamChildrenWithoutCarePrimaryPage,
                       ExamChildrenWithoutCareSpecPage),
             'title': u'диспансеризация несовершеннолетних без попечения родителей'},

            {'pattern': 'periodic_medical_examination.xls',
             'pages': (PeriodicMedicalExamPage, ),
             'title': u'периодический медицинский осмотр несовершеннолетних'},

            {'pattern': 'preliminary_medical_examination.xls',
             'pages': (PrelimMedicalExamPrimaryPage, PrelimMedicalExamSpecPage),
             'title': u'предварительный медицинский осмотр несовершеннолетних'},

            {'pattern': 'preventive_medical_examination.xls',
             'pages': (PreventMedicalExamPrimaryPage, PreventMedicalExamSpecPage),
             'title': u'профилактический медицинский осмотр несовершеннолетних'},

            # Дневной стационар
            {'pattern': 'day_hospital_hospital.xls',
             'pages': (DayHospitalHospital, InvasiveMethodsPage),
             'title': u'дневной стационар при стационаре'},

            {'pattern': 'day_hospital_policlinic.xls',
             'pages': (DayHospitalPoliclinic, ),
             'title': u'дневной стационар при поликлинике'},

            {'pattern': 'day_hospital_home.xls',
             'pages': (DayHospitalHome, ),
             'title': u'дневной стационар на дому'},

            {'pattern': 'day_hospital_hepatitis_C_virus.xls',
             'pages': (DayHospitalHepatitisCVirus, ),
             'title': u'дневной стационар (вирус гепатита С)'},

            {'pattern': 'day_hospital_all.xls',
             'pages': (DayHospitalAll, InvasiveMethodsPage),
             'title': u'дневной стационар свод'},

            # Круглосуточный стационар
            {'pattern': 'hospital.xls',
             'pages': (HospitalPage, ),
             'title': u'круглосуточный стационар'},

            {'pattern': 'hospital_hmc.xls',
             'pages': (HospitalHmcPage, ),
             'title': u'круглосуточный стационар ВМП'},

            # Поликлиника
            {'pattern': 'magnetic_resonance_imaging.xls',
             'pages': (MriPage, ),
             'title': u'КТ и МРТ'},

            {'pattern': 'hospital_ambulance.xls',
             'pages': (HospitalAmbulancePage, ),
             'title': u'приемное отделение стационара (неотложная помощь)'},

            # Поликлиника (за единицу объёма)
            {'pattern': 'clinic_emergency_all.xls',
             'pages': (ClinicEmergencyAll, ),
             'title': u'поликлиника (в неотложной форме) свод'},

            {'pattern': 'clinic_disease_single_visit_all.xls',
             'pages': (ClinicDiseaseSingleVisitAll, ),
             'title': u'поликлиника (разовые посещения в связи с заболеванием) свод'},

            {'pattern': 'clinic_other_purposes_primary.xls',
             'pages': (ClinicOtherPurposesPrimary, ),
             'title': u'поликлиника (с иными целями) перв.мед.помощь'},

            {'pattern': 'clinic_disease_treatment_all.xls',
             'pages': (ClinicDiseaseTreatmentAll, ),
             'title': u'поликлиника (обращения по поводу заболевания) свод'},

            {'pattern': 'clinic_prevention_all.xls',
             'pages': (ClinicPreventionAll, ProphylacticExaminationAdult),
             'title': u'поликлиника (с профилактической целью) свод'},

            # Поликлиника (подушевое)
            {'pattern': 'clinic_capitation_other_purposes_primary.xls',
             'pages': (ClinicCapitationOtherPurposesPrimary, ),
             'title': u'поликлиника фин-ние по подушевому нормативу '
                      u'(посещения с иными целями) перв.мед.помощь'},

            {'pattern': 'clinic_capitation_prevention_all.xls',
             'pages': (ClinicCapitationPreventionAll, ),
             'title': u'поликлиника фин-ние по подушевому нормативу '
                      u'(посещения с профилактической целью) свод'},

            {'pattern': 'clinic_capitation_disease_single_visit_all.xls',
             'pages': (ClinicCapitationDiseaseSingleVisitAll, ),
             'title': u'поликлиника фин-ние по подушевому нормативу (разовые посещения в связи с '
                      u'заболеванием) свод.xls'},

            {'pattern': 'clinic_capitation_disease_treatment_primary.xls',
             'pages': (ClinicCapitationDiseaseTreatmentPrimary, ),
             'title': u'поликлиника фин-ние по подушевому нормативу (обращения по поводу заболевания) перв.мед.помощь'},

            # Подушевое
            {'pattern': 'capitation_ambulatory_care.xls',
             'pages': (CapitationAmbulatoryCarePage, ),
             'title': u'подушевой норматив (амбулаторная помощь)'},

            {'pattern': 'capitation_acute_care.xls',
             'pages': (CapitationAcuteCarePage, ),
             'title': u'подушевой норматив (СМП)'},

            {'pattern': 'acute_care.xls',
             'pages': (AcuteCarePage, ),
             'title':  u'СМП финансирование по подушевому нормативу (кол-во вызовов, основной тариф)'},
        )

        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )

        print u'будет сделано %s актов...' % len(reports_desc)

        for desc in reports_desc:
            print desc['title']
            report = Report('medical_services_types/' + desc['pattern'])
            for page in desc['pages']:
                report.add_page(page())
            parameters.report_name = desc['title']
            report.print_pages(parameters)
            print
