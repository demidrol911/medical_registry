#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from report_printer.func import print_act_2
from tfoms.func import (get_mo_register,
                        calculate_capitation_tariff)


### Подушевое по поликлинике
def capitation_amb_care(year, period):
    """
    Подушевое по поликлинике
    """
    result_data = {}
    for mo_code in get_mo_register(year, period):
        capitation_tariff = calculate_capitation_tariff(3, year, period, mo_code)
        result_data[mo_code] = [0, ]*24
        result_data[mo_code][1] = capitation_tariff['male']['population']['adult']
        result_data[mo_code][2] = capitation_tariff['female']['population']['adult']
        result_data[mo_code][3] = capitation_tariff['male']['population']['children']
        result_data[mo_code][4] = capitation_tariff['female']['population']['children']
        result_data[mo_code][0] = result_data[mo_code][1]+result_data[mo_code][2] + \
            result_data[mo_code][3]+result_data[mo_code][4]

        result_data[mo_code][5] = capitation_tariff['male']['tariff']['adult']
        result_data[mo_code][6] = capitation_tariff['male']['tariff']['children']

        result_data[mo_code][8] = capitation_tariff['male']['population_tariff']['adult']
        result_data[mo_code][9] = capitation_tariff['female']['population_tariff']['adult']
        result_data[mo_code][10] = capitation_tariff['male']['population_tariff']['children']
        result_data[mo_code][11] = capitation_tariff['female']['population_tariff']['children']
        result_data[mo_code][7] = result_data[mo_code][8]+result_data[mo_code][9] + \
            result_data[mo_code][10]+result_data[mo_code][11]

        result_data[mo_code][12] = capitation_tariff['male']['coefficient_value']['adult']-1 \
            if capitation_tariff['male']['coefficient_value']['adult'] else 0
        result_data[mo_code][13] = capitation_tariff['male']['coefficient_value']['children']-1 \
            if capitation_tariff['male']['coefficient_value']['children'] else 0

        result_data[mo_code][15] = capitation_tariff['male']['coefficient']['adult']
        result_data[mo_code][16] = capitation_tariff['female']['coefficient']['adult']
        result_data[mo_code][17] = capitation_tariff['male']['coefficient']['children']
        result_data[mo_code][18] = capitation_tariff['female']['coefficient']['children']
        result_data[mo_code][14] = result_data[mo_code][15]+result_data[mo_code][16] + \
            result_data[mo_code][17]+result_data[mo_code][18]

        result_data[mo_code][20] = capitation_tariff['male']['accepted_payment']['adult']
        result_data[mo_code][21] = capitation_tariff['female']['accepted_payment']['adult']
        result_data[mo_code][22] = capitation_tariff['male']['accepted_payment']['children']
        result_data[mo_code][23] = capitation_tariff['female']['accepted_payment']['children']
        result_data[mo_code][19] = result_data[mo_code][20]+result_data[mo_code][21] + \
            result_data[mo_code][22]+result_data[mo_code][23]

    return [{'title': u'Подушевой норматив (амбулаторная помощь)',
             'pattern': 'capitation_ambulatory_care',
             'sum': [{'query': result_data, 'separator_length': 0, 'len': 24}]}]


### Подушевое по скорой помощи
def capitation_acute_care(year, period):
    """
    Подушевое по скорой помощи
    """
    result_data = {}
    for mo_code in get_mo_register(year, period):
        capitation_tariff = calculate_capitation_tariff(4, year, period, mo_code)
        result_data[mo_code] = [0, ]*11
        result_data[mo_code][1] = capitation_tariff['male']['population']['adult']
        result_data[mo_code][2] = capitation_tariff['female']['population']['adult']
        result_data[mo_code][3] = capitation_tariff['male']['population']['children']
        result_data[mo_code][4] = capitation_tariff['female']['population']['children']
        result_data[mo_code][0] = result_data[mo_code][1]+result_data[mo_code][2] + \
            result_data[mo_code][3]+result_data[mo_code][4]

        result_data[mo_code][5] = capitation_tariff['male']['tariff']['adult']

        result_data[mo_code][7] = capitation_tariff['male']['accepted_payment']['adult']
        result_data[mo_code][8] = capitation_tariff['female']['accepted_payment']['adult']
        result_data[mo_code][9] = capitation_tariff['male']['accepted_payment']['children']
        result_data[mo_code][10] = capitation_tariff['female']['accepted_payment']['children']
        result_data[mo_code][6] = result_data[mo_code][7]+result_data[mo_code][8] + \
            result_data[mo_code][9]+result_data[mo_code][10]

    return [{'title': u'Подушевой норматив (СМП)',
             'pattern': 'capitation_acute_care',
             'sum': [{'query': result_data, 'separator_length': 0, 'len': 11}]}]


class Command(BaseCommand):

    def handle(self, *args, **options):
        year = args[0]
        period = args[1]
        acts = [
            capitation_amb_care(year, period),
            capitation_acute_care(year, period),
        ]
        for act in acts:
            for rule in act:
                print rule['title']
                print_act_2(year, period, rule)