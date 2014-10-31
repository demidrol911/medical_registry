#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from pandas import DataFrame
from pandas.compat import OrderedDict
from helpers.excel_writer import ExcelWriter
from tfoms.management.commands import register_function
from medical_service_register.path import REESTR_EXP, BASE_DIR
from helpers.excel_style import VALUE_STYLE, PERIOD_VALUE_STYLE
from helpers.const import MONTH_NAME, ACT_CELL_POSITION
import time


class Act():

    DIVISION_BY_GENDER = "GENDER"
    DIVISION_BY_AGE = "AGE"
    AVAILABLE_FIELDS = {'patient_id': 'patients', 'id': 'services',
                        'tariff': 'tariff', 'accepted_payment': 'accepted_payment',
                        'index07': 'index07', 'quantity_days': 'days'}
    ACT_PATH = ur'{dir}\{title}_{month}_{year}'
    TEMP_PATH = ur'{base}\templates\excel_pattern\end_of_month\{template}.xls'

    def __init__(self):
        self.title = ''
        self.pattern = ''
        self.sum = []
        self.columns = {}
        self.separator = {}
        self.method_rules = None
        self.function = OrderedDict()

    @staticmethod
    def nulldataframe(source):
        return DataFrame([[0, ]*source.columns.size]*source.index.size,
                         columns=source.columns, index=source.index)

    @staticmethod
    def rename(service_df):
        field_map_gen = {}
        for key, value in Act.AVAILABLE_FIELDS.iteritems():
            field_map_gen[key] = value+'_2'
            field_map_gen[key+'_x'] = value+'_1'
            field_map_gen[key+'_y'] = value+'_all'
        return service_df.rename(columns=field_map_gen)

    @staticmethod
    def calculate(service_df, condition, division, func, all_column=False):

        services = service_df[condition]

        if division:
            if division == Act.DIVISION_BY_AGE:
                services1 = services[services.code.str.startswith('0')]
                services2 = services[services.code.str.startswith('1')]
            elif division == Act.DIVISION_BY_GENDER:
                services1 = services[services.gender == 2]
                services2 = services[services.gender == 1]

            res1 = services1.groupby('mo_code').agg(func)
            res2 = services2.groupby('mo_code').agg(func)

            if res1.empty and not res2.empty:
                res1 = Act.nulldataframe(res2)
            elif res2.empty and not res1.empty:
                res2 = Act.nulldataframe(res1)
            elif res1.empty and res2.empty:
                empty_frame = DataFrame()
                idx = 0
                if all_column:
                    for key in func:
                        empty_frame.insert(idx, key+'_y', [])
                        idx += 1

                for key in func:
                    empty_frame.insert(idx, key+'_x', [])
                idx += 1

                for key in func:
                    empty_frame.insert(idx, key, [])
                    idx += 1
                return empty_frame

            if all_column:
                res_by_div = res1.join(res2, how='outer', lsuffix='_x')
                res = services.groupby('mo_code').agg(func)
                return Act.rename(res.join(res_by_div, how='outer', lsuffix='_y').fillna(0))
            else:
                return Act.rename(res1.join(res2, how='outer', lsuffix='_x').fillna(0))
        else:
            return Act.rename(services.groupby('mo_code').agg(func).fillna(0))

    def get_column_info(self, idx):
        for key in self.columns:
            if idx in key:
                return self.columns[key]

    def calculate_all(self, service_df):
        rules = self.method_rules(service_df) if self.method_rules else []
        sum_list = []
        for idx, rule in enumerate(rules):
            column_info = self.get_column_info(idx)
            df = Act.calculate(service_df, rule['con'],
                               column_info['division'],
                               rule['func'],
                               all_column=column_info['all_column'])
            sum_list.append(df)
        if self.sum:
            for idx, _ in enumerate(self.sum):
                if not sum_list[idx].empty:
                    if not self.sum[idx].empty:
                        self.sum[idx] = self.sum[idx].append(sum_list[idx])
                    else:
                        self.sum[idx] = sum_list[idx]
        else:
            self.sum = sum_list

    def print_excel(self, year, period):
        target_dir = REESTR_EXP % (year, period)
        act_path = Act.ACT_PATH.format(
            dir=target_dir,
            title=self.title,
            month=MONTH_NAME[period],
            year=year
        )
        temp_path = Act.TEMP_PATH.format(
            base=BASE_DIR,
            template=self.pattern)
        print self.title
        with ExcelWriter(act_path,
                         template=temp_path,
                         sheet_names=[MONTH_NAME[period], ]) as act_book:
            act_book.set_overall_style({'font_size': 11, 'border': 1})
            act_book.set_cursor(4, 2)
            act_book.set_style(PERIOD_VALUE_STYLE)
            act_book.write_cell(u'за %s %s года' % (MONTH_NAME[period], year))
            act_book.set_style(VALUE_STYLE)
            block_index = 2
            for idx, data in enumerate(self.sum):
                if not data.empty:
                    column_info = self.get_column_info(idx)
                    total_sum = data.sum()
                    for index, values in data.iterrows():
                        row = ACT_CELL_POSITION[str(index)]
                        act_book.set_cursor(row, block_index)
                        for name in column_info['column']:
                            if column_info['all_column']:
                                act_book.write_cell(values[name+'_all'], 'c')
                            if column_info['division']:
                                act_book.write_cell(values[name+'_1'], 'c')
                                act_book.write_cell(values[name+'_2'], 'c')
                            else:
                                act_book.write_cell(values[name+'_2'], 'c')
                    act_book.set_cursor(101, block_index)
                    for name in column_info['column']:
                        if column_info['all_column']:
                            act_book.write_cell(total_sum[name+'_all'], 'c')
                        if column_info['division']:
                            act_book.write_cell(total_sum[name+'_1'], 'c')
                            act_book.write_cell(total_sum[name+'_2'], 'c')
                        else:
                            act_book.write_cell(total_sum[name+'_2'], 'c')
                block_index += (data.columns.size + self.separator.get(idx, 0))


# Диспансеризация детей - сирот без попечения родителей
def exam_children_without_care():
    act = Act()
    act.title = u'Диспансеризация несовершеннолетних (без попечения родителей)'
    act.pattern = 'examination_children_without_care'
    age_group_column = ('patients', 'services', 'tariff', 'index07', 'accepted_payment')
    spec_group_column = ('patients', 'services')

    act.columns = {
        (0, 1, 2, 3, 4, 5): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': False},
        (6, 8): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
        (7, ): {
            'column': spec_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
    }

    act.separator[6] = 1
    act.separator[7] = 2

    def get_rules(service_df):
        age_group = OrderedDict(
            [('patient_id', 'nunique'), ('id', 'count'),
             ('tariff', 'sum'), ('index07', 'sum'), ('accepted_payment', 'sum')])
        spec_group = OrderedDict([('patient_id', 'nunique'), ('id', 'count')])
        rules = [
            {'con': service_df.code.isin(['119220', '119221']), 'func': age_group},
            {'con': service_df.code.isin(['119222', '119223']), 'func': age_group},
            {'con': service_df.code.isin(['119224', '119225']), 'func': age_group},
            {'con': service_df.code.isin(['119226', '119227']), 'func': age_group},
            {'con': service_df.code.isin(['119228', '119229']), 'func': age_group},
            {'con': service_df.code.isin(['119230', '119231']), 'func': age_group},
            {'con': service_df.code.isin(
                ['119220', '119221',
                 '119222', '119223',
                 '119224', '119225',
                 '119226', '119227',
                 '119228', '119229',
                 '119230', '119231']), 'func': age_group},
            {'con': (service_df.group == 13) & (service_df.subgroup == 10), 'func': spec_group},
            {'con': service_df.code.isin(
                ['119220', '119221',
                 '119222', '119223',
                 '119224', '119225',
                 '119226', '119227',
                 '119228', '119229',
                 '119230', '119231']) |
                ((service_df.group == 13) & (service_df.subgroup == 10)), 'func': age_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


 # Диспансеризация детей - сирот в трудной жизненной ситуации
def exam_children_difficult_situation():
    act = Act()
    act.title = u'Диспансеризация несовершеннолетних (в трудной жизненной ситуации)'
    act.pattern = 'examination_children_difficult_situation'
    age_group_column = ('patients', 'services', 'tariff', 'index07', 'accepted_payment')
    spec_group_column = ('patients', 'services')

    act.columns = {
        (0, 1, 2, 3, 4, 5): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': False},
        (6, 8): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
        (7, ): {
            'column': spec_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
    }

    act.separator[6] = 1
    act.separator[7] = 2

    def get_rules(service_df):
        age_group = OrderedDict(
            [('patient_id', 'nunique'), ('id', 'count'),
             ('tariff', 'sum'), ('index07', 'sum'), ('accepted_payment', 'sum')])
        spec_group = OrderedDict([('patient_id', 'nunique'), ('id', 'count')])
        rules = [
            {'con': service_df.code.isin(['119020', '119021']), 'func': age_group},
            {'con': service_df.code.isin(['119022', '119023']), 'func': age_group},
            {'con': service_df.code.isin(['119024', '119025']), 'func': age_group},
            {'con': service_df.code.isin(['119026', '119027']), 'func': age_group},
            {'con': service_df.code.isin(['119028', '119029']), 'func': age_group},
            {'con': service_df.code.isin(['119030', '119031']), 'func': age_group},
            {'con': service_df.code.isin(
                ['119020', '119021',
                 '119022', '119023',
                 '119024', '119025',
                 '119026', '119027',
                 '119028', '119029',
                 '119030', '119031']), 'func': age_group},
            {'con': (service_df.group == 12) & (service_df.subgroup == 9), 'func': spec_group},
            {'con': service_df.code.isin(
                ['119020', '119021',
                 '119022', '119023',
                 '119024', '119025',
                 '119026', '119027',
                 '119028', '119029',
                 '119030', '119031']) |
                ((service_df.group == 12) & (service_df.subgroup == 9)), 'func': age_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Профосмотры несовешеннолетних
def prev_exam_children():
    act = Act()
    act.title = u'Профилактический медицинский осмотр несовершеннолетних'
    act.pattern = 'preventive_medical_examination'
    age_group_column = ('patients', 'services', 'tariff', 'index07', 'accepted_payment')
    spec_group_column = ('patients', 'services')

    act.columns = {
        (0, 1, 2, 3, 4, 5): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': False},
        (6, 8): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
        (7, ): {
            'column': spec_group_column,
            'division': Act.DIVISION_BY_GENDER,
            'all_column': True},
    }

    act.separator[6] = 2
    act.separator[7] = 2

    def get_rules(service_df):
        age_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index][service_df.tariff > 0]
                                          [['code', 'patient_id']].drop_duplicates())),
             ('id', 'count'),
             ('tariff', 'sum'), ('index07', 'sum'), ('accepted_payment', 'sum')])
        spec_group = OrderedDict([('patient_id', 'nunique'), ('id', 'count')])
        rules = [
            {'con': service_df.code.isin(['119080', '119081']),
             'func': age_group},
            {'con': service_df.code.isin(['119082', '119083']),
             'func': age_group},
            {'con': service_df.code.isin(['119084', '119085']),
             'func': age_group},
            {'con': service_df.code.isin(['119086', '119087']),
             'func': age_group},
            {'con': service_df.code.isin(['119088', '119089']),
             'func': age_group},
            {'con': service_df.code.isin(['119090', '119091']),
             'func': age_group},
            {'con': service_df.code.isin(
                ['119080', '119081',
                 '119082', '119083',
                 '119084', '119085',
                 '119086', '119087',
                 '119088', '119089',
                 '119090', '119091']),
             'func': age_group},
            {'con': (service_df.group == 11) & (service_df.subgroup == 8),
             'func': spec_group},
            {'con': service_df.code.isin(
                ['119080', '119081',
                 '119082', '119083',
                 '119084', '119085',
                 '119086', '119087',
                 '119088', '119089',
                 '119090', '119091']) |
                ((service_df.group == 11) & (service_df.subgroup == 8)),
             'func': age_group}

        ]
        return rules

    act.method_rules = get_rules
    return act


#СМП финансирование по подушевому нормативу (кол-во, основной тариф)'
def acute_care():
    act = Act()
    act.title = u'СМП финансирование по подушевому нормативу (кол-во, основной тариф)'
    act.pattern = 'acute_care'
    age_group_column = ('patients', 'services', 'tariff')

    act.columns = {
        (0, 1, 2, 3, 4): {
            'column': age_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        age_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
                                          [['code_division', 'patient_id', 'is_children']].drop_duplicates())),
             ('id', 'count'),
             ('tariff', 'sum')])
        rules = [
            {'con': service_df.code_division == 456,
             'func': age_group},
            {'con': service_df.code_division == 455,
             'func': age_group},
            {'con': service_df.code_division == 457,
             'func': age_group},
            {'con': service_df.code_division == 458,
             'func': age_group},
            {'con': service_df.code_division.isin([456, 455, 457, 458]),
             'func': age_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Периодический медосмотр несовершеннолетних
def period_exam_children():
    act = Act()
    act.title = u'Периодический медицинский осмотр несовершеннолетних'
    act.pattern = 'periodic_medical_examination'
    age_group_column = ('patients', 'services', 'tariff', 'index07', 'accepted_payment')

    act.columns = {
        (0, ): {
            'column': age_group_column,
            'division': None,
            'all_column': False},
    }

    def get_rules(service_df):
        group = OrderedDict(
            [('patient_id', 'nunique'), ('id', 'count'),
             ('tariff', 'sum'), ('index07', 'sum'), ('accepted_payment', 'sum')])
        rules = [
            {'con': service_df.code == '119151',
             'func': group},
        ]
        return rules

    act.method_rules = get_rules
    return act


# Предварительные медосмотры несовершеннолетних
def prelim_exam_children():
    act = Act()
    act.title = u'Предварительный медицинский осмотр несовершеннолетних'
    act.pattern = 'preliminary_medical_examination'
    age_group_column = ('patients', 'services', 'tariff', 'index07', 'accepted_payment')
    spec_group_column = ('patients', 'services')

    act.columns = {
        (0, 1, 2, 3, 5): {
            'column': age_group_column,
            'division': None,
            'all_column': False},
        (4, ): {
            'column': spec_group_column,
            'division': None,
            'all_column': False},
    }

    act.separator[3] = 1
    act.separator[4] = 2

    def get_rules(service_df):
        rec_group = OrderedDict(
            [('patient_id', 'nunique'), ('id', 'count'),
             ('tariff', 'sum'), ('index07', 'sum'), ('accepted_payment', 'sum')])
        spec_group = OrderedDict(
            [('patient_id', 'nunique'), ('id', 'count')])
        rules = [
            {'con': service_df.code == '119101',
             'func': rec_group},
            {'con': service_df.code == '119119',
             'func': rec_group},
            {'con': service_df.code == '119120',
             'func': rec_group},
            {'con': service_df.code.isin(['119101', '119119', '119120']),
             'func': rec_group},
            {'con': (service_df.group == 15) & (service_df.subgroup == 11),
             'func': spec_group},
            {'con': service_df.code.isin(
                ['119101', '119119', '119120']) |
                ((service_df.group == 15) & (service_df.subgroup == 11)),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар (численность лиц)
def day_hospital_patients():
    act = Act()
    act.title = u'Дневной стационар (численность лиц)'
    act.pattern = 'day_hospital_patients'
    profile_group_column = ('patients', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
            [['division_term', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates()))])
        total_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
            [['group', 'division_term', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates()))])
        general_con = service_df.group.isnull() & service_df.division_term.isin([10, 11])
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
            {'con': service_df.group == 17,
             'func': rec_group},
            {'con': (general_con & (service_df.term == 2)) | (service_df.group.isin([28, 17])),
             'func': total_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар (выбывшие больные)
def day_hospital_services():
    act = Act()
    act.title = u'Дневной стационар (выбывшие больные)'
    act.pattern = 'day_hospital_services'
    profile_group_column = ('services', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('id', 'nunique')])
        general_con = service_df.group.isnull() & service_df.division_term.isin([10, 11])
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
            {'con': service_df.group == 17,
             'func': rec_group},
            {'con': (general_con & (service_df.term == 2)) | (service_df.group.isin([28, 17])),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар (пациенто-дни)
def day_hospital_days():
    act = Act()
    act.title = u'Дневной стационар (пациенто-дни)'
    act.pattern = 'day_hospital_days'
    profile_group_column = ('days', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('quantity_days', 'sum')])
        general_con = service_df.group.isnull() & service_df.division_term.isin([10, 11])
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
            {'con': service_df.group == 17,
             'func': rec_group},
            {'con': (general_con & (service_df.term == 2)) | (service_df.group.isin([28, 17])),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар (стоимость)
def day_hospital_cost():
    act = Act()
    act.title = u'Дневной стационар (стоимость)'
    act.pattern = 'day_hospital_cost'
    profile_group_column = ('accepted_payment', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('accepted_payment', 'sum')])
        general_con = service_df.group.isnull() & service_df.division_term.isin([10, 11])
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
            {'con': service_df.group == 17,
             'func': rec_group},
            {'con': (general_con & (service_df.term == 2)) | (service_df.group.isin([28, 17])),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар свод
def day_hospital():
    act = Act()
    act.title = u'Дневной стационар свод'
    act.pattern = 'day_hospital'
    group_column = ('patients', 'services', 'days', 'accepted_payment', )

    act.columns = {
        (0, 1, ): {
            'column': group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True}
    }

    act.separator[0] = 2

    def get_rules(service_df):
        rec_group = OrderedDict([
            ('patient_id', lambda x: len(service_df.ix[x.index]
             [['division_term', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates())),
            ('id', 'nunique'), ('quantity_days', 'sum'), ('accepted_payment', 'sum')])
        general_con = (service_df.group.isnull() &
                       (service_df.term == 2) &
                       service_df.division_term.isin([10, 11]))
        rules = [
            {'con': general_con | (service_df.group == 17),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар на дому (численность лиц)
def day_hospital_home_patients():
    act = Act()
    act.title = u'Дневной стационар на дому (численность лиц)'
    act.pattern = 'day_hospital_home_patients'
    profile_group_column = ('patients', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
            [['tariff_profile', 'patient_id', 'is_children']].drop_duplicates()))])
        total_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
            [['group', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates()))])
        null_group = OrderedDict([('patient_id', lambda x: 0)])
        general_con = service_df.group.isnull() & (service_df.division_term == 12)
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': null_group},
            {'con': service_df.group == 17,
             'func': null_group},
            {'con': general_con & (service_df.term == 2),
             'func': total_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар на дому (стоимость)
def day_hospital_home_cost():
    act = Act()
    act.title = u'Дневной стационар на дому (стоимость)'
    act.pattern = 'day_hospital_home_cost'
    profile_group_column = ('accepted_payment', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('accepted_payment', 'sum')])
        null_group = OrderedDict([('accepted_payment', lambda x: 0)])
        general_con = service_df.group.isnull() & (service_df.division_term == 12)
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': null_group},
            {'con': service_df.group == 17,
             'func': null_group},
            {'con': general_con & (service_df.term == 2),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар на дому (выбывшие больные)
def day_hospital_home_services():
    act = Act()
    act.title = u'Дневной стационар на дому (выбывшие больные)'
    act.pattern = 'day_hospital_home_services'
    profile_group_column = ('services', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('id', 'nunique')])
        null_group = OrderedDict([('id', lambda x: 0)])
        general_con = service_df.group.isnull() & (service_df.division_term == 12)
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': null_group},
            {'con': service_df.group == 17,
             'func': null_group},
            {'con': general_con & (service_df.term == 2),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар на дому (пациенто-дни)
def day_hospital_home_days():
    act = Act()
    act.title = u'Дневной стационар на дому (пациенто-дни)'
    act.pattern = 'day_hospital_home_days'
    profile_group_column = ('days', )
    act.columns = {
        (0, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': False},
        (1, 2, 3, 5, 11, 16): {
            'column': profile_group_column,
            'division': None,
            'all_column': False},
        (17, ): {
            'column': profile_group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('quantity_days', 'sum')])
        null_group = OrderedDict([('quantity_days', lambda x: 0)])
        general_con = service_df.group.isnull() & (service_df.division_term == 12)
        rules = [
            {'con': general_con & (service_df.tariff_profile == 39),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 40),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 41),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 42),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 43),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 44),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 45),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 46),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 47),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 48),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 49),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 50),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 51),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 52),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 53),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': null_group},
            {'con': service_df.group == 17,
             'func': null_group},
            {'con': general_con & (service_df.term == 2),
             'func': rec_group}
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар на дому свод
def day_hospital_home():
    act = Act()
    act.title = u'Дневной стационар на дому свод'
    act.pattern = 'day_hospital_home'
    group_column = ('patients', 'services', 'days', 'accepted_payment', )

    act.columns = {
        (0, 1, ): {
            'column': group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True}
    }

    act.separator[0] = 2

    def get_rules(service_df):
        rec_group = OrderedDict([
            ('patient_id', lambda x: len(service_df.ix[x.index]
             [['division_term', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates())),
            ('id', 'nunique'), ('quantity_days', 'sum'), ('accepted_payment', 'sum')])
        rules = [
            {'con': service_df.group.isnull() &
                (service_df.term == 2) &
                (service_df.division_term == 12),
             'func': rec_group},
        ]
        return rules

    act.method_rules = get_rules
    return act


# Дневной стационар свод + на дому свод
def day_hospital_all():
    act = Act()
    act.title = u'Дневной стационар свод + на дому свод'
    act.pattern = 'day_hospital_all'
    group_column = ('patients', 'services', 'days', 'accepted_payment', )

    act.columns = {
        (0, 1, ): {
            'column': group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True}
    }

    act.separator[0] = 2

    def get_rules(service_df):
        rec_group = OrderedDict([
            ('patient_id', lambda x: len(service_df.ix[x.index]
             [['division_term', 'tariff_profile', 'patient_id', 'is_children']].drop_duplicates())),
            ('id', 'nunique'), ('quantity_days', 'sum'), ('accepted_payment', 'sum')])
        general_con = (service_df.group.isnull() &
                       (service_df.term == 2) &
                       service_df.division_term.isin([10, 11, 12]))
        rules = [
            {'con': general_con | (service_df.group == 17),
             'func': rec_group},
            {'con': service_df.group == 28,
             'func': rec_group},
        ]
        return rules

    act.method_rules = get_rules
    return act


# Круглосуточный стационар ВМП
def hospital_hmc():
    act = Act()
    act.title = u'Круглосуточный стационар ВМП'
    act.pattern = 'hospital_hmc'
    group_column = ('patients', 'services', 'days', 'accepted_payment', )
    act.columns = {
        (0, 1, 2, 3, 4, 5, 6, 7, 8, ): {
            'column': group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict(
            [('patient_id', lambda x: len(service_df.ix[x.index]
            [['tariff_profile', 'patient_id', 'is_children']].drop_duplicates())),
                ('id', 'nunique'), ('quantity_days', 'sum'),
                ('accepted_payment', 'sum')])
        general_con = (service_df.term == 1) & (service_df.group == 20)
        rules = [
            {'con': general_con & (service_df.tariff_profile == 56),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 57),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 58),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 59),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 60),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 63),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 61),
             'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 62),
             'func': rec_group},
            {'con': general_con,
             'func': rec_group},
        ]
        return rules

    act.method_rules = get_rules
    return act


# Круглосуточный стационар (число госпитализаций)
def hospital_services():
    act = Act()
    act.title = u'Круглосуточный стационар (число госпитализаций)'
    act.pattern = 'hospital_services'
    group_column = ('services', )
    act.columns = {
        (0, 2, 3, 4, 5, 6, 7, 8, 13, 14,
         16, 17, 18, 19, 20, 21, 22, 23,
         24, 25, 26, 27, 28, 29, 30, 31,
         32, 34, 36, 37, 38, 39, 40, 41,
         42, 43, 44): {'column': group_column,
                       'division': Act.DIVISION_BY_AGE,
                       'all_column': False},
        (1, 9, 10, 11, 12, 15, 33, 35, ): {
            'column': group_column,
            'division': None,
            'all_column': False},
        (45, ): {
            'column': group_column,
            'division': Act.DIVISION_BY_AGE,
            'all_column': True},
    }

    def get_rules(service_df):
        rec_group = OrderedDict([('id', 'nunique')])
        general_con = ((service_df.term == 1) & service_df.group.isnull())
        rules = [
            {'con': general_con & (service_df.tariff_profile == 1), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 2), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 3), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 4), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 5), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 6), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 7), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 8), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 9), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 10), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 37), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 11), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 36), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 12), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 13), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 38), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 14), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 15), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 16), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 17), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 18), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 19), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 20), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 21), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 22), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 23), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 24), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 25), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 26), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 27), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 28), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 29), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 30), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 31), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 32), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 33), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 34), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 35), 'func': rec_group},
            {'con': service_df.code.isin(['049021', '049023', '149021', '149023']), 'func': rec_group},
            {'con': service_df.code.isin(['049022', '149022', '049024', '149024']), 'func': rec_group},
            {'con': general_con & (service_df.tariff_profile == 64), 'func': rec_group},
            {'con': service_df.code.isin(['098951']), 'func': rec_group},
            {'con': service_df.code.isin(['098948']), 'func': rec_group},
            {'con': service_df.code.isin(['098949', '098975']), 'func': rec_group},
            {'con': service_df.code.isin(['098950']), 'func': rec_group},
            {'con': general_con | service_df.code.isin(
                ['049021', '049023', '149021', '149023',
                 '049022', '149022', '049024', '149024',
                 '098951', '098948', '098949', '098975',
                 '098950']), 'func': rec_group},
        ]
        return rules

    act.method_rules = get_rules
    return act


class Command(BaseCommand):

    def handle(self, *args, **options):
        #print 'Current memory usage: %iMB' % (hpy().heap().stat.size/(1024*1024))
        start = time.clock()
        year = args[0]
        period = args[1]

        mo_list = register_function.get_mo_register(year, period)

        slice_size = 5
        range_len = len(mo_list) + (0 if len(mo_list) % slice_size == 0 else slice_size)

        acts = [
            # 1 Диспансеризация детей - сирот в трудной жизненной ситуации
            exam_children_difficult_situation(),
            # 2 Диспансеризация детей - сирот без попечения родителей
            exam_children_without_care(),
            # 3 Профосмотры несовешенолетних
            prev_exam_children(),
            # 4 СМП финансирование по подушевому нормативу
            acute_care(),
            # 5 Периодический медосмотр несовершеннолетних
            period_exam_children(),
            # 6 Предварительные медосмотры несовершеннолетних
            prelim_exam_children(),
            # 7 Дневной стационар (численность лиц)
            day_hospital_patients(),
            # 8 Дневной стационар (выбывшие больные)
            day_hospital_services(),
            # 9 Дневной стационар (пациенто-дни)
            day_hospital_days(),
            # 10 Дневной стационар (стоимость)
            day_hospital_cost(),
            # 11 Дневной стационар (свод)
            day_hospital(),
            # 12 Дневной стационар на дому (численность лиц)
            day_hospital_home_patients(),
            # 13 Дневной стационар на дому (стоимость)
            day_hospital_home_cost(),
            # 14 Дневной стационар на дому (выбывшие больные)
            day_hospital_home_services(),
            # 15 Дневной стационар на дому (пациенто-дни)
            day_hospital_home_days(),
            # 16 Дневной стационар на дому свод
            day_hospital_home(),
            # 17 Дневной стационар свод + на дому свод
            day_hospital_all(),
            # 18 Круглосуточный стационар ВМП
            hospital_hmc(),
            # 19 Круглосуточный стационар (число госпитализаций)
            hospital_services()
        ]

        last_pos = 0
        for cur_pos in xrange(slice_size, range_len+1, slice_size):
            service_df_mini = register_function.get_service_df_mini(
                year, period, mo_list[last_pos: cur_pos])
            for act in acts:
                act.calculate_all(service_df_mini)
            print cur_pos,
            last_pos = cur_pos

        print 'print'
        for act in acts:
            act.print_excel(year, period)

        elapsed = time.clock() - start
        print u'Время выполнения: {0:d} мин {1:d} сек'.format(int(elapsed//60), int(elapsed % 60))

