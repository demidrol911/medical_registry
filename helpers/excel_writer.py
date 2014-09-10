#! -*- coding: utf-8 -*-

from xlrd import open_workbook
from xlsxwriter import Workbook


class ExcelWriter():

    def __init__(self, src_path, dist_path, basic_style={'font_name': 'Times New Roman', 'font_size': 10}):
        self.current_row = 0
        self.current_col = 0
        self.current_sheet = 0
        self.basic_style = basic_style
        self.current_style = None
        ver_align = {1: 'vcenter', 2: 'bottom'}
        align = {0: 'right', 1: 'left', 2: 'center'}
        src_book = open_workbook(src_path, formatting_info=True)
        self.dist_book = Workbook(dist_path)
        for src_sheet in src_book.sheets():
            dist_sheet = self.dist_book.add_worksheet(src_sheet.name)
            for cell_range in src_sheet.merged_cells:
                dist_sheet.merge_range(cell_range[0], cell_range[2], cell_range[1]-1, cell_range[3]-1, '')
            for number_row in range(src_sheet.nrows):
                dist_sheet.set_row(number_row, src_sheet.rowinfo_map[number_row].height/20)
                for number_col in range(src_sheet.ncols):
                    dist_sheet.set_column(number_col, number_col, src_sheet.colinfo_map[number_col].width/223)
                    cell = src_sheet.cell(number_row, number_col)
                    format_cell = src_book.xf_list[cell.xf_index]
                    self.set_style({'top': format_cell.border.top_line_style,
                                    'bottom': format_cell.border.bottom_line_style,
                                    'left': format_cell.border.left_line_style,
                                    'right': format_cell.border.right_line_style,
                                    'text_wrap': format_cell.alignment.text_wrapped,
                                    'valign': ver_align[format_cell.alignment.vert_align],
                                    'align': align[format_cell.alignment.hor_align]})
                    dist_sheet.write(number_row, number_col, cell.value, self.current_style)
        self.sheets = self.dist_book.worksheets()
        #self.basic_style['num_format'] = '0.00'
        self.style_dict = self.basic_style
        self.set_style(self.basic_style)

    def write_cell(self, number_row, number_column, value):
        self.sheets[self.current_sheet].write(number_row, number_column, value, self.current_style)

    def write_cell_ir(self, value):
        self.write_cell(self.current_row, self.current_col, value)
        self.current_row += 1

    def write_cell_ic(self, value):
        self.write_cell(self.current_row, self.current_col, value)
        self.current_col += 1

    def set_basic_style(self, dict_style):
        self.basic_style = dict_style
        self.set_style(self.basic_style)

    def set_style(self, dict_style={}):
        self.style_dict = {}
        for key in self.basic_style:
            self.style_dict[key] = self.basic_style[key]
        for key in dict_style:
            self.style_dict[key] = dict_style[key]
        self.current_style = self.dist_book.add_format(self.style_dict)

    def append_style(self, dict_style={}):
        for key in dict_style:
            self.style_dict[key] = dict_style[key]
        self.current_style = self.dist_book.add_format(self.style_dict)

    def merge_range(self, begin_col, end_col, value):
        self.sheets[self.current_sheet].merge_range(self.current_row, begin_col,
                                                    self.current_row, end_col,
                                                    value, self.current_style)
        self.current_row += 1

    def close(self):
        self.dist_book.close()