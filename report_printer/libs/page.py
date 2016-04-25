#! -*- coding: utf-8 -*-
from abc import ABCMeta, abstractmethod
from main.funcs import howlong
from report_printer.libs.excel_writer import ExcelBook
from report_printer.libs.report import ReportParameters
from django.db import connection
from main.funcs import dictfetchall
from dbfpy import dbf
from pandas import DataFrame


class ReportPage():
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate(self, parameters):
        """Calculate report"""

    @abstractmethod
    def print_page(self, sheet, parameters):
        """Print report"""


class FilterReportPage:
    __metaclass__ = ABCMeta

    def __init__(self):
        self.data = None
        self.parameters = ReportParameters()
        self.current_value_stop_fields_dbf = None
        self.current_value_stop_fields_excel = None
        self.dbf_struct = self.get_dbf_struct()
        self.excel_struct = self.get_excel_struct()
        self.calculate()

    @howlong
    def calculate(self):
        self.data = None
        cursor = connection.cursor()
        cursor.execute(self.get_query(),
                       dict(year=self.parameters.registry_year,
                            period=self.parameters.registry_period))
        self.data = DataFrame.from_dict(self.prepare_data(dictfetchall(cursor)), orient='columns')
        cursor.close()

    def prepare_data(self, data):
        return data

    def print_to_excel(self, printing_into_one_file=False):
        if self.data.empty:
            print u'Нет данных'
        else:
            self.current_value_stop_fields_excel = {field: None for field in self.excel_struct['stop_fields']}
            book = None
            excel_data = self.data.sort(list(self.excel_struct['stop_fields'] + self.excel_struct['order_fields']))
            for idx, i in enumerate(excel_data.index):
                item = excel_data.loc[i]
                stop = (printing_into_one_file and idx == 0) or False
                for field in self.current_value_stop_fields_excel:
                    if item[field] != self.current_value_stop_fields_excel[field]:
                        stop = True
                        self.current_value_stop_fields_excel[field] = item[field]
                if stop:
                    if book:
                        book.__exit__(0, 0, 0)
                    if printing_into_one_file:
                        report_name = 'ALL_DATA'
                    else:
                        report_name = self.excel_struct['file_pattern'] % \
                           tuple(item[field] for field in self.excel_struct['stop_fields'])
                    book = ExcelBook(self.excel_struct['path'], report_name.replace('"', '').strip())
                    book.create_book()
                    sheet = book.get_sheet(0)
                    for field in self.excel_struct['titles'][:-1]:
                        sheet.write(field, 'c')
                    sheet.write(self.excel_struct['titles'][-1], 'r')
                self.print_item_excel(sheet, item)
            if book:
                book.__exit__(0, 0, 0)

    def print_to_dbf(self):
        if self.data.empty:
            print u'Нет данных'
        else:
            self.current_value_stop_fields_dbf = {field: None for field in self.dbf_struct['stop_fields']}
            db = None
            dbf_data = self.data.sort(list(self.dbf_struct['stop_fields'] + self.dbf_struct['order_fields']))
            for i in dbf_data.index:
                item = dbf_data.loc[i]
                stop = False
                for field in self.current_value_stop_fields_dbf:
                    if item[field] != self.current_value_stop_fields_dbf[field]:
                        stop = True
                        self.current_value_stop_fields_dbf[field] = item[field]
                if stop:
                    if db:
                        db.close()
                    report_name = self.dbf_struct['file_pattern'] % \
                        tuple(item[field] for field in self.dbf_struct['stop_fields'])
                    db = dbf.Dbf('%s/%s.dbf' % (self.dbf_struct['path'], report_name), new=True)
                    db.addField(*self.dbf_struct['titles'])
                self.print_item_dbf(db, item)
            if db:
                db.close()

    def calculate_statistic(self):
        stat_param = self.get_statistic_param()
        if 'filter' in stat_param:
            return self.data.query(stat_param['filter']).groupby(stat_param['group_by'])[stat_param['field']].nunique().reset_index()
        return self.data.groupby(stat_param['group_by'])[stat_param['field']].nunique().reset_index()

    @abstractmethod
    def get_dbf_struct(self):
        pass

    @abstractmethod
    def get_excel_struct(self):
        pass

    @abstractmethod
    def get_query(self):
        pass

    @abstractmethod
    def print_item_dbf(self, db, item):
        pass

    @abstractmethod
    def print_item_excel(self, sheet, item):
        pass

    @abstractmethod
    def get_statistic_param(self):
        pass
