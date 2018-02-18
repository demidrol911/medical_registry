#! -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from main.funcs import howlong
from medical_service_register.path import REESTR_EXP
from report_printer.libs.report import Report, ReportParameters

from order146_pages.clinic_capitation_disease import \
    ClinicCapitationDiseaseTreatmentPrimaryPage, ClinicCapitationDiseaseSingleVisitAllPage

from order146_pages.clinic_capitation_other_purposes import \
    ClinicCapitationOtherPurposesPrimaryPage

from order146_pages.clinic_capitation_prevention import \
    ClinicCapitationPreventionAllPage

from order146_pages.clinic_disease import\
    ClinicDiseaseTreatmentAllPage, ClinicDiseaseSingleVisitAllPage

from order146_pages.clinic_emergency import \
    ClinicEmergencyAllPage

from order146_pages.clinic_other_purposes import \
    ClinicOtherPurposesPrimaryPage

from order146_pages.clinic_prevention import \
    ClinicPreventionAllPage

from order146_pages.day_hospital_home import DayHospitalHomePage

from order146_pages.day_hospital_hospital import \
    DayHospitalHospitalPage, InvasiveMethodsPage, DayHospitalMedRehabilitationPage, InvasiveMethodsInPartPage, \
    InvasiveMethodsAllPage

from order146_pages.day_hospital_all import DayHospitalAllPage, DayHospitalPrimaryPage, DayHospitalSpecPage

from order146_pages.day_hospital_hepatitis_C_virus import \
    DayHospitalHepatitisCVirusPage

from order146_pages.day_hospital_clinic import \
    DayHospitalClinicPage, DayHospitalClinicTotalPage

from order146_pages.hospital_ambulance import \
    HospitalAmbulancePage, AmbulanceVisitNursingStaffPage

from order146_pages.hospital_hmc import HospitalHmcPage

from order146_pages.day_hospital_hmc import DayHospitalHmcPage

from order146_pages.magnetic_resonance_imaging import MriPage

from order146_pages.examination_adult import \
    ExamAdultFirstStagePage, ExamAdultSecondStagePage, PreventiveInspectionAdultPage

from order146_pages.acute_care import AcuteCarePage, ThrombolysisAcuteCarePage

from order146_pages.capitation import \
    CapitationAmbulatoryCarePage, CapitationAcuteCarePage

from order146_pages.examination_children import \
    PeriodicMedicalExamPage, \
    PrelimMedicalExamPrimaryPage, \
    PrelimMedicalExamSpecPage, \
    PreventMedicalExamPrimaryPage, \
    PreventMedicalExamSpecPage

from order146_pages.examination_children_orphans import \
    ExamChildrenDifficultSituationPrimaryPage, \
    ExamChildrenDifficultSituationSpecPage, \
    ExamChildrenWithoutCarePrimaryPage, \
    ExamChildrenWithoutCareSpecPage

from order146_pages.hospital import HospitalPage, HospitalClearPage, AbortionVolumeExceededPage, HospitalMedRehabilitationPage, \
    AbortionVolumeExceededInPartPage

from order146_pages.stomatology import StomatologyPage

from order146_pages.pregnant import IntegratedPrenatalDiagnosisPage, ScreeningUltrasoundPage

from order146_pages.fluorography import FluorographyPage

from order146_pages.day_hospital_in_parts import DayHospitalPrimaryInPartPage, DayHospitalSpecialInPartPage

from order146_pages.hospital_in_parts import HospitalInPartPage


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
             'pages': (PreventiveInspectionAdultPage, ),
             'title': u'сведения об объмах и стоимости профилактического медицинского осмотра взрослого населения'},

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

            #Дневной стационар
            {'pattern': 'day_hospital_hmc.xls',
             'pages': (DayHospitalHmcPage, ),
             'title': u'дневной стационар ВМП'},

            {'pattern': 'day_hospital_primary.xls',
             'pages': (DayHospitalPrimaryPage, ),
             'title': u'Дневной стационар свод  (перв.м.п.)'},

            {'pattern': 'day_hospital_spec.xls',
             'pages': (DayHospitalSpecPage, ),
             'title': u'Дневной стационар свод  (спец.м.п.)'},


            {'pattern': 'day_hospital_all.xls',
             'pages': (DayHospitalAllPage, InvasiveMethodsAllPage),
             'title': u'дневной стационар всех типов (спец. и перв.м.п.)'},

            # Круглосуточный стационар
            {'pattern': 'hospital.xls',
             'pages': (HospitalPage, AbortionVolumeExceededPage),
             'title': u'круглосуточный стационар'},

            {'pattern': 'hospital_hmc.xls',
             'pages': (HospitalHmcPage, ),
             'title': u'круглосуточный стационар ВМП'},

            # Поликлиника
            {'pattern': 'magnetic_resonance_imaging.xls',
             'pages': (MriPage, ),
             'title': u'сведения об объемах и стоимости КТ и МРТ'},

            {'pattern': 'hospital_ambulance.xls',
             'pages': (HospitalAmbulancePage, ),
             'title': u'сведения об объемах и стоимости в приемном отделении стационара (неотложная форма)'},

            # Поликлиника (за единицу объёма)
            {'pattern': 'clinic_emergency_all.xls',
             'pages': (ClinicEmergencyAllPage, ),
             'title': u'поликлиника (в неотложной форме) перв.мед.помощь'},

            {'pattern': 'clinic_disease_single_visit_all.xls',
             'pages': (ClinicDiseaseSingleVisitAllPage, ),
             'title': u'поликлиника (разовые посещения в связи с заболеванием) перв.мед.помощь'},

            {'pattern': 'clinic_other_purposes_primary.xls',
             'pages': (ClinicOtherPurposesPrimaryPage, ),
             'title': u'поликлиника (с иными целями) перв.мед.помощь'},

            {'pattern': 'clinic_disease_treatment_all.xls',
             'pages': (ClinicDiseaseTreatmentAllPage, ),
             'title': u'поликлиника (обращения по поводу заболевания) перв. и спец.мед.помощь'},

            {'pattern': 'clinic_prevention_all.xls',
             'pages': (ClinicPreventionAllPage, ),
             'title': u'поликлиника (с профилактической целью+вакцинация+проф.взр.населения+ЦЗ) перв.мед.помощь'},

            # Поликлиника (подушевое)
            {'pattern': 'clinic_capitation_other_purposes_primary.xls',
             'pages': (ClinicCapitationOtherPurposesPrimaryPage, ),
             'title': u'поликлиника фин-ние по подушевому нормативу (посещения с иными целями) перв.мед.помощь'},

            {'pattern': 'clinic_capitation_prevention_all.xls',
             'pages': (ClinicCapitationPreventionAllPage, ),
             'title': u'поликлиника фин-ние по подушевому нормативу (посещения с профилактической целью + вакцинация) '
                      u'перв.мед.помощь'},

            {'pattern': 'clinic_capitation_disease_single_visit_all.xls',
             'pages': (ClinicCapitationDiseaseSingleVisitAllPage, ),
             'title': u'поликлиника фин-ние по подушевому нормативу '
                      u'(посещения разовые в связи с заболеванием) перв.мед.помощь'},

            {'pattern': 'clinic_capitation_disease_treatment_primary.xls',
             'pages': (ClinicCapitationDiseaseTreatmentPrimaryPage, ),
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

            {'pattern': 'thrombolysis.xls',
             'pages': (ThrombolysisAcuteCarePage, ),
             'title':  u'СМП вызов с проведением тромболизиса'},

            {'pattern': 'integrated_prenatal_diagnosis.xls',
             'pages': (IntegratedPrenatalDiagnosisPage, ),
             'title':  u'сведения об объемах и стоимости комплексной пренатальной (дороовой) диагностики '
                       u'при сроке беременности 11-14 недель'},

            {'pattern': 'screening_ultrasound.xls',
             'pages': (ScreeningUltrasoundPage, ),
             'title':  u'сведения об объемах и стоимости скринингового ультразвукового исследования '
                       u'при сроке беременности 18-21 неделя'},

            {'pattern': 'ambulance_visit_nursing_staff.xls',
             'pages': (AmbulanceVisitNursingStaffPage, ),
             'title': u'сведения об объемах и стоимости посещений к среднему мед.персоналу (неотложная форма)'},

            {'pattern': 'fluorography.xls',
             'pages': (FluorographyPage, ),
             'title':  u'флюорография'},

            {'pattern': 'hospital_medical_rehabilitation.xls',
             'pages': (HospitalMedRehabilitationPage, ),
             'title': u'круглосуточный стационар (мед.реабилитация по КСГ)'},

            {'pattern': 'day_hospital_medical_rehabilitation.xls',
             'pages': (DayHospitalMedRehabilitationPage, ),
             'title': u'дневной стационар (мед.реабилитация по КСГ)'},
        )

        reports_desc_in_part = (
            {'page': DayHospitalPrimaryInPartPage,
             'pattern_path': 'day_hospital',
             'parts': [{'pattern': 'day_hospital_primary_1_part.xls',
                        'title': u'дневной стационар Первичная м.п. 1 часть'},
                       {'pattern': 'day_hospital_primary_2_part.xls',
                        'title': u'дневной стационар Первичная м.п. 2 часть'},
                       {'pattern': 'day_hospital_primary_3_part.xls',
                        'title': u'дневной стационар Первичная м.п. 3 часть'}]},

            {'page': DayHospitalSpecialInPartPage,
             'pattern_path': 'day_hospital',
             'parts': [{'pattern': 'day_hospital_special_1_part.xls',
                        'title': u'дневной стационар Специализированная м.п. 1 часть'},
                       {'pattern': 'day_hospital_special_2_part.xls',
                        'title': u'дневной стационар Специализированная м.п. 2 часть'},
                       {'pattern': 'day_hospital_special_3_part.xls',
                        'title': u'дневной стационар Специализированная м.п. 3 часть'}]},
            {'page': HospitalInPartPage,
             'pattern_path': 'hospital',
             'parts': [{'pattern': 'hospital_1_part.xls',
                        'title': u'круглосуточный стационар 1 часть'},
                       {'pattern': 'hospital_2_part.xls',
                        'title': u'круглосуточный стационар 2 часть'},
                       {'pattern': 'hospital_3_part.xls',
                        'title': u'круглосуточный стационар 3 часть'}]},
        )

        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )

        print u'будет сделано %s актов...' % len(reports_desc)

        for desc in reports_desc:
            print desc['title']
            report = Report('order146/' + desc['pattern'])
            for page in desc['pages']:
                report.add_page(page())
            parameters.report_name = desc['title']
            report.print_pages(parameters)
            print

        '''

        for desc in reports_desc_in_part:
            page_obj = desc['page']()
            page_obj.calculate(parameters)
            for i, part in enumerate(desc['parts']):
                page_obj.set_part_number(i+1)
                report = Report('order146/' + desc['pattern_path']+'/'+part['pattern'])
                report.add_page(page_obj)
                parameters.report_name = part['title']
                report.print_pages(parameters)
        '''
