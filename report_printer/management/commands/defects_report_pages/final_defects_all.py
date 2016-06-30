#! -*- coding: utf-8 -*-

from report_printer.libs.excel_loader import XlsxExcelLoader, XlsExcelLoader
from report_printer.libs.excel_style import VALUE_STYLE, TITLE_STYLE
from report_printer.libs.page import ReportPage
from tfoms.func import get_mo_name

import os
import re


class FinalDefectsAllPage(ReportPage):
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
        hospital_idx = [0, 2, 3, 4, 6]
        day_hospital_idx = [8, 10, 12]
        clinic_idx = [1, 15, 16, 17, 18, 22, 23, 25, 27, 29, 31, 32, 34, 36, 38]
        ambulance_idx = [20, 21]
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
                print file_from_dir
                if filename_match.group('ext') == 'xlsx':
                    excel_loader = XlsxExcelLoader(os.path.join(path_to_dir, file_from_dir))
                elif filename_match.group('ext') == 'xls':
                    excel_loader = XlsExcelLoader(os.path.join(path_to_dir, file_from_dir))
                sum_by_term = excel_loader.load(0, border)
                mo_code = excel_loader.get_cell(0, 4, 1)[:6]

                self.data[mo_code] = {
                    'hospital': self.calculate_total(sum_by_term, hospital_idx),
                    'day_hospital': self.calculate_total(sum_by_term, day_hospital_idx),
                    'clinic': self.calculate_total(sum_by_term, clinic_idx),
                    'ambulance': self.calculate_total(sum_by_term, ambulance_idx),
                }
                counter += 1
                print self.data[mo_code]
            else:
                print u'НЕ ПОДОШЕЛ', file_from_dir
        print counter

    def print_page(self, sheet, parameters):
        sheet.set_position(5, 0)
        for region in FinalDefectsAllPage.DEFECTS_AREA_GROUP_KEY:
            for mo_code in FinalDefectsAllPage.DEFECTS_AREA_GROUP[region]:
                data = self.data[mo_code]
                sheet.set_style(TITLE_STYLE)
                sheet.write(get_mo_name(mo_code), 'r')
                if data:
                    sheet.set_style(VALUE_STYLE)
                    self.print_row(sheet, u'стационарная', data['hospital'])
                    self.print_row(sheet, u'стационарно-замещающая', data['day_hospital'])
                    self.print_row(sheet, u'амбулаторно-поликлиническая', data['clinic'])
                    self.print_row(sheet, u'скорая помощь', data['ambulance'])

    def print_row(self, sheet, title, row_data):
        sheet.write(title, 'c')
        for item in row_data[:-1]:
            sheet.write(item, 'c')
        sheet.write(row_data[-1], 'r')

    def calculate_total(self, sum_by_term, idx_list):
        total = [0, ] * (len(sum_by_term[0]) - 2)
        for idx in idx_list:
            total[0] += sum_by_term[idx][0] + sum_by_term[idx][1]
            total[1] += sum_by_term[idx][2] + sum_by_term[idx][3]
            for jdx in xrange(2, len(total)):
                total[jdx] += sum_by_term[idx][jdx+2]
        return total