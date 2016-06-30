#! -*- coding: utf-8 -*-

from report_printer.libs.excel_loader import XlsxExcelLoader, XlsExcelLoader
from report_printer.libs.excel_style import VALUE_STYLE, TITLE_STYLE
from report_printer.libs.page import ReportPage
from tfoms.func import get_mo_name

import os
import re


class FinalDefectsMOPage(ReportPage):

    DEFECTS_AREA_GROUP = {
        u'Областные': ('280003', '280005', '280043', '280013', '280018', '280054'),
        u'г. Благовещенск': ('280026', '280036', '280085', '280038', '280066', '280064', '280069',
                             '280004', '280082', '280083', '280088', '280091', '280093', '280096',
                             '280112', '280113', '280107'),
        u'г. Белогорск': ('280017', '280065', '280010', '280110', '280117', '280118'),
        u'г. Свободный': ('280001', '280052', '280076'),
        u'г. Райчихинск': ('280075', ),
        u'(пгт)Прогресс': ('280019', ),
        u'Архаринский район': ('280024', ),
        u'Бурейский район': ('280068', ),
        u'Завитинский район': ('280067', '280022', ),
        u'г. Зея': ('280084', '280070', ),
        u'Магдагачинский район': ('280029', '280037', ),
        u'Серышевский район': ('280078',),
        u'Сковородинский район': ('280059', '280074', '280061'),
        u'г.Тында': ('280027', '280041', '280023', '280040'),
        u'Селемджинский район': ('280025', '280015', ),
        u'г. Шимановск': ('280012', '280009', ),
        u'Ивановский район': ('280007', ),
        u'Константиновский район': ('280002', ),
        u'Мазановский район': ('280039', ),
        u'Ромненский район': ('280071', ),
        u'Тамбовский район': ('280080', ),
        u'Октябрьский район': ('280053', ),
        u'Михайловский район': ('280020', ),
    }

    DEFECTS_AREA_GROUP_KEY = (
        u'Областные',
        u'г. Благовещенск',
        u'г. Белогорск',
        u'г. Свободный',
        u'г. Райчихинск',
        u'(пгт)Прогресс',
        u'Архаринский район',
        u'Бурейский район',
        u'Завитинский район',
        u'г. Зея',
        u'Магдагачинский район',
        u'Серышевский район',
        u'Сковородинский район',
        u'г.Тында',
        u'Селемджинский район',
        u'г. Шимановск',
        u'Ивановский район',
        u'Константиновский район',
        u'Мазановский район',
        u'Ромненский район',
        u'Тамбовский район',
        u'Октябрьский район',
        u'Михайловский район'
    )

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = {}
        path_to_dir = u'c:/work/defects'
        border = {'top': 6, 'bottom': 45, 'left': 3, 'right': 34}
        counter = 0
        unique_mo_names = []
        filename_pattern = re.compile(ur'^(?P<mo>[\D1234]+?)(?:_?)(?P<sequence_number>\d?)\.(?P<ext>xlsx|xls)$')
        for file_from_dir in os.listdir(path_to_dir):
            filename_match = filename_pattern.match(file_from_dir)
            if filename_match:
                mo_name = filename_match.group('mo')
                if mo_name not in unique_mo_names:
                    unique_mo_names.append(mo_name)
                else:
                    print u'ДУБЛИКАТ', mo_name
                    break
                print file_from_dir, mo_name
                if filename_match.group('ext') == 'xlsx':
                    excel_loader = XlsxExcelLoader(os.path.join(path_to_dir, file_from_dir))
                elif filename_match.group('ext') == 'xls':
                    excel_loader = XlsExcelLoader(os.path.join(path_to_dir, file_from_dir))
                sum_by_term = excel_loader.load(0, border)
                mo_code = excel_loader.get_cell(0, 4, 1)[0:6]

                region = None
                for reg in FinalDefectsMOPage.DEFECTS_AREA_GROUP:
                    if mo_code in FinalDefectsMOPage.DEFECTS_AREA_GROUP[reg]:
                        region = reg
                        break

                if not region:
                    print u'НЕ НАШЕЛ РЕГИОН', mo_code

                self.data[mo_code] = sum_by_term
                counter += 1

            else:
                print u'НЕ ПОДОШЕЛ', file_from_dir
        print counter

    def print_page(self, sheet, parameters):
        row_position = 5
        for region in FinalDefectsMOPage.DEFECTS_AREA_GROUP_KEY:
            for mo_code in FinalDefectsMOPage.DEFECTS_AREA_GROUP[region]:
                data = self.data[mo_code]
                sheet.set_position(row_position - 1, 0)
                sheet.set_style(TITLE_STYLE)
                sheet.write(get_mo_name(mo_code), 'r')
                if data:
                    sheet.set_style(VALUE_STYLE)
                    for idx, item in enumerate(data):
                        sheet.set_position(row_position, 2)
                        for value in item:
                            sheet.write(value, 'c')
                        row_position += 1
                else:
                    row_position += 40
                row_position += 1


def calculate_sum_data(sum_data, data):
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            sum_data[i][j] += value
    return sum_data

