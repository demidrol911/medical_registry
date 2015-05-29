#! -*- coding: utf-8 -*-
from decimal import Decimal

from name_generator import NameGenerator
import xlsxwriter
import os
import xlrd
import excel_converter as converter
from medical_service_register.path import EXCEL_TEMPLATE_DIR


class ExcelBook():
    path_to_dir = ''
    filename = ''
    book = None

    def __init__(self, path_to_dir, filename):
        name_gen = NameGenerator(path_to_dir)
        self.path_to_dir = path_to_dir
        self.filename = name_gen.generate_unique_name(filename+'.xlsx')
        self.fullname = os.path.join(self.path_to_dir, self.filename)

    def create_book(self, template=''):

        self.book = xlsxwriter.Workbook(self.fullname)
        if template:
            path_to_template = os.path.join(EXCEL_TEMPLATE_DIR, template)
            template_book = xlrd.open_workbook(path_to_template, formatting_info=True)
            format_map = template_book.xf_list
            colour_map = template_book.colour_map
            font_list = template_book.font_list
            for idx, temp_sheet in enumerate(template_book.sheets()):
                rowinfo_map = temp_sheet.rowinfo_map
                colinfo_map = temp_sheet.colinfo_map
                current_sheet = self.book.add_worksheet(temp_sheet.name)

                for cell_range in temp_sheet.merged_cells:
                    current_sheet.merge_range(cell_range[0], cell_range[2],
                                              cell_range[1]-1, cell_range[3]-1, '')

                for row_index in range(temp_sheet.nrows):
                    if rowinfo_map.get(row_index):
                        row_height = converter.convert_cell_height(rowinfo_map.get(row_index).height)
                    else:
                        row_height = 0
                    current_sheet.set_row(row_index, row_height)

                    for column_index in range(temp_sheet.ncols):
                        if colinfo_map.get(column_index):
                            column_width = converter.convert_cell_width(colinfo_map.get(column_index).width)
                        else:
                            column_width = 0
                        current_sheet.set_column(column_index, column_index, column_width)

                        cell = temp_sheet.cell(row_index, column_index)
                        format_cell = format_map[cell.xf_index]
                        colour_cell = colour_map[format_cell.background.pattern_colour_index]
                        font_cell = font_list[format_cell.font_index]
                        style = {
                            'top': format_cell.border.top_line_style,
                            'bottom': format_cell.border.bottom_line_style,
                            'left': format_cell.border.left_line_style,
                            'right': format_cell.border.right_line_style,
                            'text_wrap': format_cell.alignment.text_wrapped,
                            'font_name': font_cell.name,
                            'font_size': converter.convert_cell_height(font_cell.height),
                            'bold': font_cell.bold,
                            'italic': font_cell.italic,
                            'valign': converter.convert_vertical_align(format_cell.alignment.vert_align),
                            'align': converter.convert_horizontal_align(format_cell.alignment.hor_align)
                        }
                        if colour_cell:
                            style['fg_color'] = converter.convert_colour(colour_cell)

                        style_cell = self.book.add_format(style)
                        current_sheet.write(row_index, column_index, cell.value, style_cell)
        else:
            self.book.add_worksheet()

    def get_sheet(self, index):
        return ExcelSheet(self.book, index)

    def close(self):
        self.book.close()


class ExcelSheet():

    def __init__(self, book, index):
        self.book = book
        self.sheet = book.worksheets()[index]
        self.style_map = {}
        self.style = None
        self.position = {'row': 0, 'column': 0}

    def set_style(self, style_map):
        self.style_map = style_map
        self.style = self.book.add_format(self.style_map)

    def add_style(self, property_name, value):
        self.style_map[property_name] = value
        self.style = self.book.add_format(self.style_map)

    def set_position(self, row_index, column_index):
        self.position['row'] = row_index
        self.position['column'] = column_index

    def get_row_index(self):
        return self.position['row']

    def get_column_index(self):
        return self.position['column']

    def write(self, value, shift_code='', merge_len=0):
        if isinstance(value, Decimal) or isinstance(value, float):
            self.add_style('num_format', '0.'+'0'*2)
            value_cell = round(value, 2)
        else:
            self.add_style('num_format', '0')
            value_cell = value

        if merge_len:
            self.sheet.merge_range(
                self.position['row'], self.position['column'],
                self.position['row'], self.position['column'] + merge_len,
                value_cell,
                self.style
            )
            self.position['column'] += merge_len
        else:
            self.sheet.write(self.position['row'], self.position['column'], value_cell, self.style)
        if shift_code == 'rc':
            self.position['row'] += 1
            self.position['column'] += 1
        elif shift_code == 'r':
            self.position['row'] += 1
            self.position['column'] = 0
        elif shift_code == 'c':
            self.position['column'] += 1

    def write_cell(self, row_index, column_index, value):
        self.sheet.write(row_index, column_index, value, self.style)

    def hide_column(self, diapason):
        self.sheet.set_column(diapason, 20, None, {'hidden': 1})


if __name__ == '__main__':
    print u'Тест (создание книги)'
    DIR = u'C:\work'
    test_book = ExcelBook(DIR, 'test.xlsx')
    test_book.create_book('ambulance_care.xls')
    test_book.close()
