#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.db import connection
from main.funcs import dictfetchall
from tfoms.func import YEAR, PERIOD
from main.models import Fluorography
from datetime import datetime


def get_insurance_policy(last_name, first_name, middle_name, birthdate, policy_number, policy_series):
    query = """
    with patient_item AS (
      select upper(%(last_name)s) :: TEXT  AS last_name, upper(%(first_name)s) :: TEXT  AS first_name,
      upper(%(middle_name)s) :: TEXT as middle_name,
      %(policy_number)s :: TEXT as insurance_policy_number, %(policy_series)s :: TEXT as insurance_policy_series,
      %(birthdate)s :: DATE AS birthdate, '':: TEXT AS snils
    )

    select max(version_id_pk) AS policy_id
    from insurance_policy
                where id = (
                    select insurance_policy.id
                    from patient_item p2
                        JOIN insurance_policy
                            on version_id_pk = (
                                CASE
                                when char_length(p2.insurance_policy_number) <= 6 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            series = p2.insurance_policy_series
                                            and number = trim(leading '0' from p2.insurance_policy_number)
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))

                                when char_length(p2.insurance_policy_number) between 7 and 8 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            series = p2.insurance_policy_series
                                            and number = p2.insurance_policy_number
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))

                                when char_length(p2.insurance_policy_number) = 9 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select id from insurance_policy where
                                            number = p2.insurance_policy_number
                                        order by stop_date DESC NULLS FIRST
                                        LIMIT 1
                                    ))

                                when char_length(p2.insurance_policy_number) = 16 THEN
                                    (select max(version_id_pk) from insurance_policy where id = (
                                        select insurance_policy.id from insurance_policy
                                            join person
                                                on insurance_policy.person_fk = person.version_id_pk
                                                    and (
                                                        (person.last_name = p2.last_name
                                                            and person.first_name = p2.first_name
                                                            and person.middle_name = p2.middle_name
                                                            and person.birthdate = p2.birthdate)
                                                        or

                                                        ((
                                                            (person.first_name = p2.first_name
                                                            and person.middle_name = p2.middle_name)
                                                            or (person.last_name = p2.last_name
                                                            and person.first_name = p2.first_name
                                                            ) or (person.last_name = p2.last_name
                                                            and person.middle_name = p2.middle_name)
                                                        ) and person.birthdate = p2.birthdate)
                                                        or (
                                                            person.last_name = p2.last_name
                                                            and person.first_name = p2.first_name
                                                            and person.middle_name = p2.middle_name
                                                        ) or (
                                                            regexp_replace(regexp_replace((person.last_name || person.first_name || person.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g') = regexp_replace(regexp_replace((p2.last_name || p2.first_name || p2.middle_name), 'Ё', 'Е' , 'g'), ' ', '' , 'g')
                                                        )
                                                    )

                                        where
                                            enp = p2.insurance_policy_number
                                        order by stop_date desc NULLS FIRST
                                        LIMIT 1
                                    ))
                                else
                                    NULL
                                end
                         )

                        join person
                            on insurance_policy.person_fk = person.version_id_pk
                                and (
                                    (
                                        (
                                            p2.first_name = person.first_name
                                            or p2.middle_name = person.middle_name
                                            or p2.last_name = person.last_name
                                        ) and p2.birthdate = person.birthdate
                                    ) or (
                                        p2.first_name = person.first_name
                                        and p2.middle_name = person.middle_name
                                    ) or (p2.snils = person.snils)
                                )
                    where ((insurance_policy.stop_date is nuLL) or (insurance_policy.stop_date > '2011-01-01'))
                    order by insurance_policy.version_id_pk DESC
                    limit 1
               ) and is_active
    """
    cursor = connection.cursor()
    cursor.execute(query, dict(last_name=last_name, first_name=first_name,
                               middle_name=middle_name, birthdate=birthdate,
                               policy_number=policy_number,
                               policy_series=policy_series))
    data = dictfetchall(cursor)
    if data:
        return data[0]['policy_id']
    return None


def get_attachment(policy_id):
    query = """
        SELECT DISTINCT  att_org.code as attach_code
        FROM insurance_policy i
            JOIN person
                ON person.version_id_pk = (
                    SELECT version_id_pk
                    FROM person WHERE id = (
                        SELECT id FROM person
                        WHERE version_id_pk = i.person_fk) AND is_active)
            LEFT JOIN attachment
              ON attachment.id_pk = (
                  SELECT MAX(id_pk)
                  FROM attachment
                  WHERE person_fk = person.version_id_pk AND status_fk = 1
                     AND attachment.date <= (format('%%s-%%s-%%s', %(year)s, %(period)s, '01')::DATE) AND attachment.is_active)
            LEFT JOIN medical_organization att_org
              ON (att_org.id_pk = attachment.medical_organization_fk
                  AND att_org.parent_fk IS NULL)
                  OR att_org.id_pk = (
                     SELECT parent_fk FROM medical_organization
                     WHERE id_pk = attachment.medical_organization_fk
                  )
             where i.version_id_pk = %(policy_id)s
        """
    cursor = connection.cursor()
    cursor.execute(query, dict(policy_id=policy_id, year=YEAR, period=PERIOD))
    data = dictfetchall(cursor)
    if data:
        return data[0]['attach_code']
    return None


class Command(BaseCommand):
    def handle(self, *args, **options):
        reporting_date = datetime.strptime('01-%s-%s' % (PERIOD, YEAR), '%d-%m-%Y')
        for row in open(u'ФЛГ за июнь.csv'):
            data = row.replace('\n', '').split(';')
            sk = data[1]
            policy_value = data[2]
            policy_data = policy_value.split(' ')
            if len(policy_data) == 2:
                policy_series = policy_data[0]
                policy_number = policy_data[1]
            else:
                policy_series = ''
                policy_number = policy_data[0]
            last_name = data[3]
            first_name = data[4]
            middle_name = data[5]
            gender = int(data[6])
            birthdate_value = data[7]
            birthdate_data = birthdate_value.split('.')
            birthdate = '%s-%s-%s' % (birthdate_data[2], birthdate_data[1], birthdate_data[0])

            start_date_value = data[9]
            start_date_data = start_date_value.split('.')
            start_date = '%s-%s-%s' % (start_date_data[2], start_date_data[1], start_date_data[0])

            policy_id = get_insurance_policy(last_name=last_name, first_name=first_name, middle_name=middle_name,
                                             birthdate=birthdate, policy_number=policy_number,
                                             policy_series=policy_series)

            attachment_code = get_attachment(policy_id)

            Fluorography.objects.create(
                first_name=first_name,
                last_name=last_name,
                middle_name=middle_name,
                birthdate=birthdate,
                gender_id=gender,
                insurance_policy_series=policy_series,
                insurance_policy_number=policy_number,
                start_date=start_date,
                insurance_policy=policy_id,
                attachment_code=attachment_code,
                start_date=reporting_date
            )
