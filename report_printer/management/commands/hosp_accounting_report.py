#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.libs.report import Report, ReportParameters
from hosp_accounting.free_places import FreePlacesCountPage
from hosp_accounting.sender_statistic import SenderStatisticPage
from hosp_accounting.reciever_statistic import ReceiverStatisticPage, AllInfoStatisticPage
from hosp_accounting.patients_amount import SenderHospPatientsAmountPage, ReceiverHospPatientsAmountPage, \
    HospPatientsAmountPage
from hosp_accounting.info_by_mo import InfoByMoPage
from hosp_accounting.submitted_figures import SubmittedFiguresPage
from hosp_accounting.anul import AnulPage


class Command(BaseCommand):

    def handle(self, *args, **options):

        parameters = ReportParameters()
        parameters.path_to_dir = u'T:\Куракса\НОВЫЕ ДАННЫЕ по И.С\июнь'
        parameters.start_date = '2016-06-24'
        parameters.end_date = '2016-06-24'
        parameters.hosp_start = '2016-01-01'
        parameters.hosp_end = '2016-01-20'

        reports_desc = (
            {'pattern': 'free_places.xls',
             'pages': (FreePlacesCountPage, ),
             'title':  u'УГ Количество свободных мест по больницам за %s' % parameters.end_date},

            {'pages': (SenderStatisticPage, ),
             'title':  u'УГ Отправитель статистика с %s по %s'
                       % (parameters.start_date, parameters.end_date)},

            {'pages': (ReceiverStatisticPage, ),
             'title':  u'УГ Получатель статистика с %s по %s'
                       % (parameters.start_date, parameters.end_date)},

            {'pattern': 'all_info_statistic.xls',
             'pages': (AllInfoStatisticPage, ),
             'title': u'УГ статистика всей информации c %s по %s'
                      % (parameters.start_date, parameters.end_date)},

            {'pattern': 'patients_amount.xls',
             'pages': (ReceiverHospPatientsAmountPage, SenderHospPatientsAmountPage),
             'title': u'УГ Количетсво госпитализированных пациентов отправитель-получатель c %s по %s'
                      % (parameters.hosp_start, parameters.hosp_end)},

            {'pages': (HospPatientsAmountPage, ),
             'title': u'УГ Количетсво госпитализированных пациентов c %s по %s'
                      % (parameters.hosp_start, parameters.hosp_end)},

            {'pages': (InfoByMoPage, ),
             'title': u'УГ информация по больницам с %s по %s'
                      % (parameters.start_date, parameters.end_date)},

            {'pages': (SubmittedFiguresPage, ),
             'title': u'УГ поданные цифры с %s по %s'
                      % (parameters.start_date, parameters.end_date)},

            {'pages': (AnulPage, ),
             'title': u'аннулированные за %s' % (parameters.start_date, )},
        )

        reports_desc = (
            {'pages': (AnulPage, ),
             'title': u'аннулированные за %s' % (parameters.start_date, )},

            {'pages': (SubmittedFiguresPage, ),
             'title': u'поданные цифры за %s'
                      % (parameters.start_date, )},
        )

        for desc in reports_desc:
            print desc['title']
            if desc.get('pattern', None):
                report = Report('hosp_accounting/' + desc['pattern'])
            else:
                report = Report()
            for page in desc['pages']:
                report.add_page(page())
            parameters.report_name = desc['title']
            report.print_pages(parameters)
            print



