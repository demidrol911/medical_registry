#! -*- coding: utf-8 -*-
from django.db import connection

from medical_service_register.path import REESTR_EXP, BASE_DIR
from report_printer.const import MONTH_NAME, ACT_CELL_POSITION
from report_printer.excel_style import VALUE_STYLE, PERIOD_VALUE_STYLE
from helpers.excel_writer import ExcelWriter


ACT_PATH = ur'{dir}\{title}_{month}_{year}'
TEMP_PATH = ur'{base}\templates\excel_pattern\end_of_month\{template}.xls'

DIVISION_1 = 0
DIVISION_2 = 1
DIVISION_1_2 = 2
DIVISION_ALL_1_2 = 3


def get_division_by(column_division, index):
    for column in column_division:
        if index in column:
            return column_division[column]


def run_sql(query):
    cursor_query = connection.cursor()
    cursor_query.execute(query)
    data = {}
    for row in cursor_query.fetchall():
        mo = row[0]
        division = row[1]
        if mo not in data:
            data[mo] = {}
        if division not in data[mo]:
            data[mo][division] = []
        last_pos = 2
        for cur_pos in xrange(5, len(row)+1, 3):
            data[mo][division].append(row[last_pos: cur_pos])
            last_pos = cur_pos
    cursor_query.close()
    return data


def print_act(year, period, data):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=data['title'],
        month=MONTH_NAME[period],
        year=year
    )
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=data['pattern'])
    print data['title']

    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], MONTH_NAME[period]]) as act_book:

        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        for sheet, data_query in enumerate(data['data']):
            if data_query.get('next', True):
                block_index = 2
                act_book.set_sheet(sheet)
            else:
                block_index = act_book.cursor['column']
            data_sum = run_sql(data_query['structure'][0].format(year=year, period=period))
            for mo_code in data_sum:
                row_index = ACT_CELL_POSITION[mo_code]
                act_book.set_cursor(row_index, block_index)
                for division in data_query['structure'][1]:
                    division_by = get_division_by(data_query['structure'][2], division)
                    column_len = get_division_by(data_query['column_length'], division)
                    data_divisions = data_sum[mo_code].get(division, [(0, 0, 0), ]*column_len)
                    for data_division in data_divisions[: column_len]:
                        if division_by == DIVISION_1:
                            act_book.write_cell(data_division[1], 'c')
                        elif division_by == DIVISION_2:
                            act_book.write_cell(data_division[2], 'c')
                        elif division_by == DIVISION_1_2:
                            act_book.write_cell(data_division[1], 'c')
                            act_book.write_cell(data_division[2], 'c')
                        elif division_by == DIVISION_ALL_1_2:
                            act_book.write_cell(data_division[0], 'c')
                            act_book.write_cell(data_division[1], 'c')
                            act_book.write_cell(data_division[2], 'c')
                    act_book.cursor['column'] += data_query.get('separator', {}).get(division, 0)


### Распечатка нестандаотных актов
def print_act_1(year, period, data):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=data['title'],
        month=MONTH_NAME[period],
        year=year
    )
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=data['pattern'])
    print data['title']

    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], MONTH_NAME[period]]) as act_book:

        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        act_book.set_sheet(0)
        data_sum = run_sql(data['data'][0]['structure'][0].format(year=year, period=period))

        def print_division(act_book, data_division):
            act_book.write_cell(data_division[0][0], 'c')
            act_book.write_cell(data_division[0][1], 'c')
            act_book.write_cell(data_division[0][2], 'c')
            act_book.write_cell(data_division[1][0], 'c')
            act_book.write_cell(data_division[1][1], 'c')
            act_book.write_cell(data_division[1][2], 'c')
            act_book.write_cell(data_division[2][0], 'c')
            act_book.write_cell(data_division[2][1], 'c')
            act_book.write_cell(data_division[2][2], 'c')

        block_index = 2
        for mo_code, values in data_sum.iteritems():
            row_index = ACT_CELL_POSITION[mo_code]
            act_book.set_cursor(row_index, block_index)
            print_division(act_book, data_sum[mo_code].get(399, [(0, 0, 0), ]*3))
            print_division(act_book, data_sum[mo_code].get(100002, [(0, 0, 0), ]*3))
            print_division(act_book, data_sum[mo_code].get(401, [(0, 0, 0), ]*3))
            print_division(act_book, data_sum[mo_code].get(403, [(0, 0, 0), ]*3))

            complex_exam = data_sum[mo_code].get(100000, [(0, 0, 0), ]*3)
            dynamic_exam = data_sum[mo_code].get(100001, [(0, 0, 0), ]*3)

            # Численность
            act_book.write_cell(complex_exam[0][0], 'c')
            act_book.write_cell(dynamic_exam[0][0], 'c')
            act_book.write_cell(complex_exam[0][1], 'c')
            act_book.write_cell(dynamic_exam[0][1], 'c')
            act_book.write_cell(complex_exam[0][2], 'c')
            act_book.write_cell(dynamic_exam[0][2], 'c')

            # Число посещений
            act_book.write_cell(complex_exam[1][0], 'c')
            act_book.write_cell(dynamic_exam[1][0], 'c')
            act_book.write_cell(complex_exam[1][1], 'c')
            act_book.write_cell(dynamic_exam[1][1], 'c')
            act_book.write_cell(complex_exam[1][2], 'c')
            act_book.write_cell(dynamic_exam[1][2], 'c')

            # Стоимость
            act_book.write_cell(complex_exam[2][0], 'c')
            act_book.write_cell(dynamic_exam[2][0], 'c')
            act_book.write_cell(complex_exam[2][1], 'c')
            act_book.write_cell(dynamic_exam[2][1], 'c')
            act_book.write_cell(complex_exam[2][2], 'c')
            act_book.write_cell(dynamic_exam[2][2], 'c')

            print_division(act_book, data_sum[mo_code].get(443, [(0, 0, 0), ]*3))
            print_division(act_book, data_sum[mo_code].get(444, [(0, 0, 0), ]*3))

        block_index = act_book.cursor['column']+11
        data_sum = run_sql(data['data'][1]['structure'][0].format(year=year, period=period))
        for mo_code, values in data_sum.iteritems():
            row_index = ACT_CELL_POSITION[mo_code]
            act_book.set_cursor(row_index, block_index)
            data_division = data_sum[mo_code].get(100000, [(0, 0, 0), ]*2)
            act_book.write_cell(data_division[0][1], 'c')
            act_book.write_cell(data_division[1][1], 'c')
            act_book.write_cell(data_division[2][0], 'c')
            act_book.write_cell(data_division[2][1], 'c')
            act_book.write_cell(data_division[2][2], 'c')


### Устаревший метод распечатки актов
def run_sql1(year, period):
    def run(query):
        pattern_query, condition = query
        text_query = pattern_query.format(year=year, period=period,
                                          condition=condition)
        cursor = connection.cursor()
        cursor.execute(text_query)
        result_sum = {mo_data[0]: [value for value in mo_data[1:]]
                      for mo_data in cursor.fetchall()}
        cursor.close()
        return result_sum
    return lambda query: run(query)


def print_act_2(year, period, rule):
    target_dir = REESTR_EXP % (year, period)
    act_path = ACT_PATH.format(
        dir=target_dir,
        title=rule['title'],
        month=MONTH_NAME[period],
        year=year)
    temp_path = TEMP_PATH.format(
        base=BASE_DIR,
        template=rule['pattern'])
    with ExcelWriter(act_path,
                     template=temp_path,
                     sheet_names=[MONTH_NAME[period], ]) as act_book:
        act_book.set_overall_style({'font_size': 11, 'border': 1})
        act_book.set_cursor(4, 2)
        act_book.set_style(PERIOD_VALUE_STYLE)
        act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
        act_book.set_style(VALUE_STYLE)
        block_index = 2
        for condition in rule['sum']:
            result_data = condition['query']
            if result_data:
                total_sum = [0, ]*len(result_data.values()[0])
                for mo_code, value in result_data.iteritems():
                    act_book.set_cursor(ACT_CELL_POSITION[mo_code], block_index)
                    for index, cell_value in enumerate(value):
                        total_sum[index] += cell_value
                        act_book.write_cell(cell_value, 'c')
                act_book.set_cursor(101, block_index)
                for cell_value in total_sum:
                    act_book.write_cell(cell_value, 'c')
            block_index += condition['len'] + \
                condition['separator_length']