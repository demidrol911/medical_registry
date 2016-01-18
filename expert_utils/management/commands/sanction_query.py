# -*- coding: utf-8

q = u"""
select dr.fio, --Фамилия Имя Отчество,
       dr.dr, --дата рождения,
       getheap(dr.heap,'KMU') as KMU, --код услуги,
        dr.SUM_USL
        -strtofloat(getheap(dr.heap,'SUM_ALL_OMS'))
        -strtofloat(getheap(dr.heap,'SUM_ALL_FFOMS'))
        -strtofloat(getheap(dr.heap,'SUM_ALL_TFOMS')) as S_OPL, --сумма оплаченная,
       strtofloat(getheap(dr.heap,'SUM_ALL_OMS')) as S_SN,
       coalesce(
            iif(strtodate(getheap(dr.heap, 'SDATE'))='01.01.1901',null,cast(strtodate(getheap(dr.heap, 'SDATE')) as date)),
            iif(strtodate(getheap(dr.heap, 'EDATE'))='01.01.1901',null,cast(strtodate(getheap(dr.heap, 'EDATE')) as date))
       ) as startdate    , --дата начала услуги,
       coalesce(
            iif(strtodate(getheap(dr.heap, 'EDATE'))='01.01.1901',null,cast(strtodate(getheap(dr.heap, 'EDATE')) as date)),
            iif(strtodate(getheap(dr.heap, 'SDATE'))='01.01.1901',null,cast(strtodate(getheap(dr.heap, 'SDATE')) as date))
       ) as enddate    , --дата окончания услуги,
       o.number, --код ошибки по которой снимают,
       '' as period_usl, --период в котором подана услуга, (- в базе нет)
       getheap(p.heap,'CODE_MO') as code_mo, --код ЛПУ (МО) федеральный,
       trim(dr.s_pol) as s_pol, --серия/номер полиса,
       strtoint(getheap(dr.heap,'LENGTH')) as k_u, --количество услуг,
       getheap(dr.heap, 'DS') as ds, --диагноз,
       '' as tn1, --табельный номер врача (TN1), (- в базе нет)
       dr.sum_usl, --сумма предъявленная, (- вместе с доплатами по ффомс и тфомс,
       strtofloat(getheap(dr.heap,'FFOMS')) as ffoms, --федеральная доплата,
       strtofloat(getheap(dr.heap,'TFOMS')) as tfoms, --территориальная доплата,
       '' as s_ppp, --сумма оплаченная (после первой проверки), (- в базе нет)
       strtofloat(getheap(dr.heap,'SUM_BONUS')) as s_snk, --сумма санкции, (- вывожу сумму штрафа (без снятой суммы))
       '' as snils, --СНИЛС (если есть). (- в базе нет)
       d.doctype as sank_type,
       d.number as doc_number,
       d.status as STATUS,
       strtofloat(getheap(dr.heap,'SUM_ALL_TFOMS')) as S_SNT,
       strtofloat(getheap(dr.heap,'SUM_ALL_FFOMS')) as S_SNF,
       strtodate(getheap(d.heap, 'OpDate')),
       dr.number as anamnesis_number,
       p.number as lpu_number
from documents d
     inner join docrecords dr on d.id = dr.iddocument
     inner join persons p on d.idperson = p.id
     left join objects o on dr.defect = o.id
where
    cast(strtodate(getheap(d.heap, 'OpDate')) as date) between ? and ?
    and d.doctype in (5,6,7,17,19)
    and d.status >= 1100
    and (strtofloat(getheap(dr.heap,'SUM_ALL_OMS')) <> 0 or strtofloat(getheap(dr.heap,'SUM_BONUS')) <> 0)
"""