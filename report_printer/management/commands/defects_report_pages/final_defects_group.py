#! -*- coding: utf-8 -*-

from report_printer.libs.excel_loader import XlsxExcelLoader, XlsExcelLoader
from report_printer.libs.excel_style import VALUE_STYLE
from report_printer.libs.page import ReportPage

import os
import re


class FinalDefectsGroupPage(ReportPage):
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

    DEFECTS_AREA_GROUP = {
        u'Областные': {'mo': ('280003', '280005', '280043', '280013', '280018', '280054'), 'total': None},
        u'г. Благовещенск': {'mo': ('280026', '280036', '280085', '280038', '280066', '280064', '280069',
                                    '280004', '280082', '280083', '280088', '280091', '280093', '280096',
                                    '280112', '280113', '280107', '280116'), 'total': None},
        u'г. Белогорск': {'mo': ('280017', '280065', '280010', '280110', '280117', '280118'), 'total': None},
        u'г. Свободный': {'mo': ('280001', '280052', '280076'), 'total': None},
        u'г. Райчихинск': {'mo': ('280075', ), 'total': None},
        u'(пгт)Прогресс': {'mo': ('280019', ), 'total': None},
        u'Архаринский район': {'mo': ('280024', ), 'total': None},
        u'Бурейский район': {'mo': ('280068', ), 'total': None},
        u'Завитинский район': {'mo': ('280067', '280022', ), 'total': None},
        u'г. Зея': {'mo': ('280084', '280070', ), 'total': None},
        u'Магдагачинский район': {'mo': ('280029', '280037', ), 'total': None},
        u'Серышевский район': {'mo': ('280078',), 'total': None},
        u'Сковородинский район': {'mo': ('280059', '280074', '280061'), 'total': None},
        u'г.Тында': {'mo': ('280027', '280041', '280023', '280040'), 'total': None},
        u'Селемджинский район': {'mo': ('280025', '280015', ), 'total': None},
        u'г. Шимановск': {'mo': ('280012', '280009', ), 'total': None},
        u'Ивановский район': {'mo': ('280007', ), 'total': None},
        u'Константиновский район': {'mo': ('280002', ), 'total': None},
        u'Мазановский район': {'mo': ('280039', ), 'total': None},
        u'Ромненский район': {'mo': ('280071', ), 'total': None},
        u'Тамбовский район': {'mo': ('280080', ), 'total': None},
        u'Октябрьский район': {'mo': ('280053', ), 'total': None},
        u'Михайловский район': {'mo': ('280020', ), 'total': None},
    }

    def __init__(self):
        self.data = None
        self.page_number = 0

    def calculate(self, parameters):
        self.data = None
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
                for reg in FinalDefectsGroupPage.DEFECTS_AREA_GROUP:
                    if mo_code in FinalDefectsGroupPage.DEFECTS_AREA_GROUP[reg]['mo']:
                        region = reg
                        break

                if not region:
                    print u'НЕ НАШЕЛ РЕГИОН', mo_code
                if FinalDefectsGroupPage.DEFECTS_AREA_GROUP[region]['total']:
                    FinalDefectsGroupPage.DEFECTS_AREA_GROUP[region]['total'] = calculate_sum_data(
                        FinalDefectsGroupPage.DEFECTS_AREA_GROUP[region]['total'],
                        sum_by_term)
                else:
                    FinalDefectsGroupPage.DEFECTS_AREA_GROUP[region]['total'] = sum_by_term
                counter += 1

            else:
                print u'НЕ ПОДОШЕЛ', file_from_dir
        print counter

    def print_page(self, sheet, parameters):
        sheet.set_style(VALUE_STYLE)
        row_position = 5
        for region in FinalDefectsGroupPage.DEFECTS_AREA_GROUP_KEY:
            data = FinalDefectsGroupPage.DEFECTS_AREA_GROUP[region]['total']
            if data:
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

