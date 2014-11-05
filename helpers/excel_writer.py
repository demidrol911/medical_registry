#! -*- coding: utf-8 -*-

from decimal import Decimal
from xlrd import open_workbook
from xlsxwriter.workbook import Workbook
from os import path, listdir, remove
from shutil import move
from copy import deepcopy
from medical_service_register.settings import BASE_DIR


class ExcelWriter(Workbook):
    ### Временная директория
    TEMPORARY_DIR = BASE_DIR + r'\tmp'

    def __init__(self, target, template=None, sheet_names=[]):
        book_name = path.basename(target)
        target_dir = path.dirname(target)
        similar_names = [f_name for f_name in listdir(target_dir)
                         if f_name.__contains__(book_name) and f_name.endswith('.xlsx')]
        index_number = 0 if similar_names else -1
        for f_name in similar_names:
            f_name_parts = f_name[:-5].split('_')
            if len(f_name_parts) > 1 and f_name_parts[-1].isdigit() and int(f_name_parts[-1]) < 100:
                if index_number < int(f_name_parts[-1]):
                    index_number = int(f_name_parts[-1])
        index_number += 1
        if index_number:
            generated_name = '%s_%s.xlsx' % (book_name, index_number)
        else:
            generated_name = '%s.xlsx' % book_name
        self.name = generated_name
        self.temporary_path = '%s\%s' % (self.TEMPORARY_DIR, generated_name)
        self.target_path = '%s\%s' % (target_dir, generated_name)
        super(ExcelWriter, self).__init__(self.temporary_path)
        self.cursor = {'row': 0, 'column': 0}
        self.overall_style = {}
        self.style = {}
        self.number_precision = 2
        if template:
            template_book = open_workbook(template, formatting_info=True)
            format_info = template_book.xf_list
            colour_map = template_book.colour_map
            vert_align = {0: 'vleft', 1: 'vcenter', 2: 'vcenter', 4: 'vcenter'}
            hort_align = {0: 'left', 1: 'left', 2: 'center', 3: 'right'}
            for idx, temp_sheet in enumerate(template_book.sheets()):
                self.sheet = self.add_worksheet(sheet_names[idx]
                                                if len(sheet_names) > idx
                                                else temp_sheet.name)
                rowinfo_map = temp_sheet.rowinfo_map
                colinfo_map = temp_sheet.colinfo_map
                for cell_range in temp_sheet.merged_cells:
                    self.sheet.merge_range(cell_range[0], cell_range[2], cell_range[1]-1, cell_range[3]-1, '')
                for row_index in range(temp_sheet.nrows):
                    row_height = rowinfo_map.get(row_index).height/20 if rowinfo_map.get(row_index) else 0
                    self.sheet.set_row(row_index, row_height)
                    for column_index in range(temp_sheet.ncols):
                        col_width = colinfo_map.get(column_index).width/223 if colinfo_map.get(column_index) else 0
                        self.sheet.set_column(column_index, column_index, col_width)
                        cell = temp_sheet.cell(row_index, column_index)
                        format_cell = format_info[cell.xf_index]
                        colour_cell = colour_map[format_cell.background.pattern_colour_index]
                        colour_code = ''
                        if colour_cell:
                            r = str(hex(colour_cell[0]))[2:]
                            g = str(hex(colour_cell[1]))[2:]
                            b = str(hex(colour_cell[2]))[2:]
                            if len(r) == 1:
                                r = '0' + r
                            if len(g) == 1:
                                g = '0' + g
                            if len(b) == 1:
                                b = '0' + b
                            colour_code = '#%s%s%s' % (r, g, b)
                        font_cell = template_book.font_list[format_cell.font_index]
                        self.style = {'top': format_cell.border.top_line_style,
                                      'bottom': format_cell.border.bottom_line_style,
                                      'left': format_cell.border.left_line_style,
                                      'right': format_cell.border.right_line_style,
                                      'text_wrap': format_cell.alignment.text_wrapped,
                                      'font_name': font_cell.name, 'font_size': font_cell.height/20,
                                      'bold': font_cell.bold, 'italic': font_cell.italic,
                                      'valign': vert_align[format_cell.alignment.vert_align],
                                      'align': hort_align[format_cell.alignment.hor_align]}
                        if colour_code:
                            self.style['fg_color'] = colour_code
                        self.set_cursor(row_index, column_index)
                        self.style_obj = self.add_format(self.style)
                        value = int(cell.value) \
                            if unicode(cell.value).replace('.', '').isdigit() \
                            else cell.value
                        self.write_cell(value)
        else:
            self.sheet = self.add_worksheet()
        self.set_sheet(0)
        self.set_cursor(0, 0)
        self.style_obj = self.add_format(self.overall_style)

    ### Записывает в ячейку укаазанное значение
    def write_cell(self, value, increment=None, size=0):
        if isinstance(value, Decimal) or isinstance(value, float):
                #and value != round(value, 0):
            self.set_style_property('num_format', '0.'+'0'*self.number_precision)
            value_cell = round(value, self.number_precision)
        else:
            self.set_style_property('num_format', '0')
            value_cell = value
        if size:
            self.sheet.merge_range(self.cursor['row'], self.cursor['column'],
                                   self.cursor['row'], self.cursor['column']+size,
                                   value_cell, self.style_obj)
        else:
            self.sheet.write(self.cursor['row'], self.cursor['column'], value_cell, self.style_obj)
        if increment == 'r':
            self.cursor['row'] += 1
            self.cursor['column'] = 0
        elif increment == 'c':
            self.cursor['column'] += size + 1
        elif increment == 'rc':
            self.cursor['row'] += 1
            self.cursor['column'] += 1

    ### Устанаавливает количество отображаемых знаков после запятой для чисел
    def set_number_precision(self, prec):
        self.number_precision = prec

    ### Устанавливает текущий лист
    def set_sheet(self, index):
        self.sheet = self.worksheets()[index]

    ### Устанавливает основной стиль, который применяется ко всей книге
    def set_overall_style(self, style_dict={}):
        self.overall_style = deepcopy(style_dict)
        self.style = deepcopy(style_dict)
        self.style_obj = self.add_format(self.style)

    ### Устанавливает дополнительный стиль
    def set_style(self, style_dict={}):
        self.style = deepcopy(self.overall_style)
        for property_key, value in style_dict.items():
            self.style[property_key] = value
        self.style_obj = self.add_format(self.style)

    ### Устанавливает дополнительное свойство стиля
    def set_style_property(self, key, value):
        self.style[key] = value
        self.style_obj = self.add_format(self.style)

    ### Устанавливает адрес текущей ячейки
    def set_cursor(self, row_index, column_index):
        self.cursor['row'] = row_index
        self.cursor['column'] = column_index

    ### Закрывает книгу
    def close(self):
        super(ExcelWriter, self).close()
        move(self.temporary_path, self.target_path)

    ### Переход на новую строку
    def row_inc(self):
        self.cursor['row'] += 1
        self.cursor['column'] = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        super(ExcelWriter, self).close()
        if exc_type and path.exists(self.temporary_path):
            remove(self.temporary_path)
        else:
            move(self.temporary_path, self.target_path)