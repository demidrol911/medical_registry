# -*- coding: utf-8 -*-

from main.data_cache import (
    DISEASES, CODES, KIND_TERM_DICT, ADULT_EXAMINATION_COMMENT_PATTERN,
    ADULT_PREVENTIVE_COMMENT_PATTERN, OLD_ADULT_EXAMINATION,
    NEW_ADULT_EXAMINATION, EXAMINATION_HEALTH_GROUP_EQUALITY)

from main.funcs import safe_int

from datetime import datetime
import re


def is_disease_has_precision(field_value):
    disease = DISEASES.get(field_value, None)

    if disease and disease.is_precision:
        return False

    return True


def is_service_corresponds_registry_type(field_value, registry_type):
    service = CODES.get(field_value)
    if registry_type == 1 and \
            service.group_id in list(range(6, 17)) + [20, 25, 26]:
        return False
    elif registry_type == 2 and \
            service.group_id != 20:
        return False
    elif registry_type in list(range(3, 11)) and \
            service.group_id not in list(range(6, 17) + [25, 26]):
        return False

    return True


def is_event_kind_corresponds_term(kind, term):
    kinds = KIND_TERM_DICT.get(term, [])

    if not kinds or not term:
        return True

    if kind in kinds:
        return True

    return False


def is_examination_result_matching_comment(examination_result, event_comment):
    pattern = re.compile(ADULT_EXAMINATION_COMMENT_PATTERN)
    matching = pattern.match(event_comment)
    result = EXAMINATION_HEALTH_GROUP_EQUALITY[examination_result]

    if examination_result in ['1', '2', '3', '4', '5', '31', '32']:
        if matching.group('health_group') != result and matching.group('second_level') != '0':
            return False

    elif examination_result in ['11', '12', '13', '14', '15']:
        if matching.group('health_group') != result and matching.group('second_level') != '1':
            return False

    return True


def is_service_code_matching_hitech_method(code, method):
    if safe_int(code[-3:]) != safe_int(method):
        return False

    return True


def is_service_children_profile_matching_event_children_profile(
        service_children_profile, event_children_profile):
    if event_children_profile != service_children_profile:
        return False

    return True


def is_expired_service(code, event_end_date):
    try:
        event_date = datetime.strptime(event_end_date, '%Y-%m-%d').date()
    except:
        return False

    control_date = datetime.strptime('2015-04-01', '%Y-%m-%d').date()

    if code in OLD_ADULT_EXAMINATION and event_date >= control_date:
        return False

    if code in NEW_ADULT_EXAMINATION \
            and event_date < control_date:
        return False

    return True