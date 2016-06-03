#! -*- coding: utf-8 -*-

import re
from collections import defaultdict
from datetime import datetime

"""
valid.py

A library for validating that dictionary
values fit inside of certain sets of parameters.

Author: Samuel Lucidi <slucidi@newstex.com>

"""

__version__ = "0.8.0"


def _isstr(s):
    return isinstance(s, str)


def _in(collection, pass_on_blank=True):
    def in_lambda(value):
        if not value and pass_on_blank:
            return True
        return value in collection

    in_lambda.collection = collection
    in_lambda.err_message = u'904;Значение не соответствует справочному.'
    return in_lambda


def _not(validator):
    def not_lambda(value):
        result = validator(value)
        not_lambda.err_message = getattr(validator, "not_message", "failed validation")
        not_lambda.not_message = getattr(validator, "err_message", "failed validation")
        return not result

    return not_lambda


def _range(start, end, inclusive=True):
    def range_lambda(value):
        if inclusive:
            return start <= value <= end
        else:
            return start < value < end

    range_lambda.start = start
    range_lambda.end = end
    range_lambda.err_message = u"значение должено попадать в интервал %s и %s" % (start, end)
    return range_lambda


def _equals(obj):
    def eq_lambda(value):
        return value == obj

    eq_lambda.value = obj
    eq_lambda.err_message = u"значение должено быть равено %r" % obj
    return eq_lambda


def _blank():
    def blank_lambda(value):
        return value == ""

    blank_lambda.err_message = u"значение должено быть пустой строкой"
    return blank_lambda


def _truthy():
    def truth_lambda(value):
        if value:
            return True
        else:
            return False

    truth_lambda.err_message = u"значение должено быть эквивалентно истине"
    return truth_lambda


def _required():
    def required_lambda(field, dictionary):
        return field in dictionary  # and dictionary[field]

    required_lambda.err_message = u'902;Отсутствует обязательное значение.'
    return required_lambda


def _instance_of(base_class):
    def instanceof_lambda(value):
        return isinstance(value, base_class)

    instanceof_lambda.base_class = base_class
    instanceof_lambda.err_message = u"значение должено быть экземляром класса %s или его подклассов" % base_class.__name__
    return instanceof_lambda


def _subclass_of(base_class):
    def subclassof_lambda(class_):
        return issubclass(class_, base_class)

    subclassof_lambda.base_class = base_class
    subclassof_lambda.err_message = u"Класс должен быть подклассом of %s" % base_class.__name__
    return subclassof_lambda


def _pattern(pattern, pass_on_blank=False):
    compiled = re.compile(pattern)

    def pattern_lambda(value):
        if not value and pass_on_blank:
            return True
        if value is None:
            return False
        return compiled.match(value)

    pattern_lambda.pattern = pattern
    pattern_lambda.err_message = u'904;Формат значения не соответствует регламентированному.'
    return pattern_lambda


def _then(validation):
    def then_lambda(dictionary):
        return validate(validation, dictionary)

    return then_lambda


def _if(validator_lambda, then_lambda):
    def if_lambda(value, dictionary):
        conditional = False
        dependent = None
        if validator_lambda(value):
            conditional = True
            dependent = then_lambda(dictionary)
        return conditional, dependent
    return if_lambda


def _length(minimum, maximum=0, pass_on_blank=False):
    if not minimum and not maximum:
        raise ValueError("Length must have a non-zero minimum or maximum parameter.")
    if minimum < 0 or maximum < 0:
        raise ValueError("Length cannot have negative parameters.")

    def length_lambda(value):
        if not value and pass_on_blank:
            return True

        if getattr(value, '__len__', None):
            if maximum:
                return minimum <= len(value) <= maximum
            else:
                return minimum == len(value)
        else:
            return False

    length_lambda.err_message = u'904;Количество символов в поле не соответствует регламентированному.'
    return length_lambda


def _contains(contained):
    def contains_lambda(value):
        return contained in value

    contains_lambda.err_message = u"Значение должно содержать {0}".format(contained)
    return contains_lambda


def _isdate():
    def isdate_lambda(value):
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except TypeError:
            return False
        return True

    isdate_lambda.err_message = u'904;Значение не является датой'
    return isdate_lambda


def validate(rules, data):
    errors = defaultdict(list)
    for key in rules:
        value = data.get(key, '')
        rules_list = rules[key] if type(rules[key]) == list else [rules[key]]
        for rule in rules_list:
            if getattr(rule, '__name__', '') == '_required':
                required = rule()
                if not required(key, data):
                    errors[key].append(required.err_message)
            else:
                if type(value) == dict:
                    nested_errors = validate(rule, data[key])
                    if nested_errors:
                        errors[key].append(nested_errors)
                elif type(value) == list:
                    for v in value:
                        if not rule(v):
                            errors[key].append(rule.err_message)
                            break
                else:
                    if not rule(value):
                        errors[key].append(rule.err_message)
    return dict(errors)


if __name__ == '__main__':
    pet = {
        "name": ["fuzzy", "whiskers", ],
        "type": "cat"
    }
    cat_name_rules = {
        "name": [_in(["fuzzy", "tiger"])]
    }

    print validate(cat_name_rules, pet)
