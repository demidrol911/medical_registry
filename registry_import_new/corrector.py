#! -*- coding: utf-8 -*-


def correct(item, parent_key=''):
    new_item = {}
    for key in item:
        value = item[key]
        if isinstance(value, dict):
            new_item[key] = correct(value, key)
            if key in ('USL', 'SLUCH'):
                new_item[key] = [correct(value, key)]
            else:
                new_item[key] = correct(value, key)
        elif isinstance(value, list):
            new_item[key] = []
            for v in value:
                if isinstance(v, dict):
                    new_item[key].append(correct(v, key))
                else:
                    new_item[key].append(v)
        else:
            new_item[key] = value

        # Корректирвка кодов услуг
        if parent_key == 'USL' and key == 'CODE_USL':
            new_item[key] = new_item[key].rjust(6, '0')

        # Корректировка отделений
        elif parent_key in ('USL', 'SLUCH') and key == 'PODR':
            division = (new_item[key] or '')[:3]
            if division and len(division) < 3:
                new_item[key] = ('0'*(3-len(division))) + division
    return new_item


