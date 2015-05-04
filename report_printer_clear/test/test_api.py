#! -*- coding: utf-8 -*-
import openpyxl
from decimal import Decimal
import os
import re


def load(filename, parameters):
    book = openpyxl.load_workbook(filename)
    data = []
    sheet = book.worksheets[parameters.sheet_index]
    for i, row_index in enumerate(xrange(parameters.top, parameters.bottom+1)):
        row = []
        for j, column_index in enumerate(xrange(parameters.left, parameters.right+1)):
            value_original = sheet.cell(row=row_index, column=column_index).value
            if value_original:
                value = Decimal(value_original)
            else:
                value = Decimal(0)
            row.append(value)
        data.append(row)
    return data


def print_data(data):
    print len(data), len(data[0])
    for row in data:
        for value in row:
            print str(value).replace('.', ','),
        print


def get_equal_filename(path_to_dir, filename):
    filename_pattern_parse = re.compile(ur'^(?P<mo>[\D1234]+?)(?:_?)(?P<sequence_number>\d?)\.xlsx$')
    parse_match = filename_pattern_parse.match(filename)
    if parse_match:
        filename_unique = parse_match.group('mo')
    else:
        filename_unique = ''
    filename_pattern = re.compile(ur'^%s(?:_?)(?P<sequence_number>\d*?)\.xlsx$' %
                                  (filename_unique, ))

    equals_filenames = []
    for dst_filename in os.listdir(path_to_dir):
        if filename_pattern.match(dst_filename):
            equals_filenames.append(dst_filename)
    return equals_filenames


def diff(data_src, data_dst):
    is_equals = True
    for i, row_src in enumerate(data_src):
        for j, value_src in enumerate(row_src):
            if abs(value_src - data_dst[i][j]) > 0.05:
                is_equals = False
    return is_equals


class ReportLoaderParameters():

    def __init__(self):
        self.sheet_index = 0
        self.top = 0
        self.left = 0
        self.right = 0
        self.bottom = 0

if __name__ == '__main__':
    DIR_SRC = ur'C:\TEST\OLD\G2015\Period03'
    DIR_DST = ur'C:\TEST\NEW\G2015\Period03'
    parameters = ReportLoaderParameters()
    parameters.sheet_index = 0
    parameters.top = 6
    parameters.bottom = 38
    parameters.left = 3
    parameters.right = 34

    for src_filename in os.listdir(DIR_SRC):
        #print src_filename,
        equals_filenames = get_equal_filename(DIR_DST, src_filename)
        if equals_filenames:
            data_src = load(os.path.join(DIR_SRC, src_filename), parameters)
        for dst_filename in equals_filenames:
            #print '-->', dst_filename,
            data_dst = load(os.path.join(DIR_DST, dst_filename), parameters)
            is_equals = diff(data_src, data_dst)
            if is_equals:
                pass
            else:
                print src_filename, dst_filename, 'No'
            #print 'Yes' if diff(data_src, data_dst) else 'No',
        #print



    #data = load(ur'X:\REESTR\G2015\Period03\дефекты\ГБУЗ АО Ромненская больница_дефекты_1.xlsx', parameters)
    #print_data(data)