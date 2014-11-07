# -*- coding: utf-8 -*-

from validator.collection import Collection
from validator.field import Field
from validator.rules import Regex, IsInList, IsLengthBetween, IsRequired

ERROR_MESSAGES = {
    'length exceeded': (u'904;Количество символов в поле не соответствует '
                        u'регламентированному.'),
    'missing value': u'902;Отсутствует обязательное значение.',
    'wrong value': u'904;Значение не соответствует справочному.',
    'wrong format': (u'904;Формат значения не соответствует '
                     u'регламентированному.'),
}


class MyCollection(Collection):
    def get_dict(self):
        results = {}
        for field in self.fields:
            results[field.title] = field.value

        return results


def get_person_patient_validation(item):
    patient = MyCollection().append([
        Field('uid', item['ID_PAC'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(0, 36,
                            error=ERROR_MESSAGES['length exceeded']),
        ]),
        Field('last_name', item['FAM'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'], ),
        ]),
        Field('first_name', item['IM'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('middle_name', item['OT'] or '').append([
            IsLengthBetween(0, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('birthdate', item['DR'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['wrong format'],),
        ]),
        Field('gender', item['W'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(['1', '2'], ERROR_MESSAGES['length exceeded']),
        ]),
        Field('agent_last_name', item['FAM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_first_name', item['IM_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_middle_name', item['OT_P'] or '').append([
            IsLengthBetween(1, 40,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True),
        ]),
        Field('agent_birthdate', item['DR_P'] or '').append([
            Regex('\d{4}-\d{2}-\d{2}',
                  error=ERROR_MESSAGES['length exceeded'],
                  pass_on_blank=True),
        ]),
        Field('agent_gender', item['W_P'] or '').append([
            IsInList(['0', '1', '2'], error=ERROR_MESSAGES['wrong value'],
                     pass_on_blank=True),
        ]),
        # Field('person_id_type', item['DOCTYPE'] or '').append([
        # IsInList([str(i) for i in range(0, 100)], error=u'904,Значение не соответствует справочному.', pass_on_blank=True),
        #]),
        Field('person_id_series', item['DOCSER'] or '').append([
            IsLengthBetween(1, 10,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('person_id_number', item['DOCNUM'] or '').append([
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        #Field('snils', item['SNILS'] or '').append([
        #    IsLength(14, error=u'904,Неверное количество символов.', pass_on_blank=True)
        #]),
    ])

    return patient


def get_policy_patient_validation(item):
    policy = MyCollection().append([
        Field('newborn_code', item['NOVOR'] or '').append([
            Regex('[12]\d{2}\d{2}\d{2}[1-99]',
                  error=ERROR_MESSAGES['wrong format'],
                  pass_on_blank=True)
        ]),
        Field('insurance_policy_type', item['VPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsInList(['1', '2', '3'],
                     error=ERROR_MESSAGES['wrong value']),
        ]),
        Field('insurance_policy_series', item['SPOLIS'] or '').append([
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'],
                            pass_on_blank=True)
        ]),
        Field('insurance_policy_number', item['NPOLIS'] or '').append([
            IsRequired(error=ERROR_MESSAGES['missing value']),
            IsLengthBetween(1, 20,
                            error=ERROR_MESSAGES['length exceeded'], )
        ]),

    ])

    return policy