#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from dbfpy import dbf
from collections import OrderedDict
from tfoms.func import get_mo_map, get_mo_name
import os
from medical_service_register.path import PRODUCTION_OVERDUED_NKD_DBF, PRODUCTION_REPEATED_DBF
from report_printer.libs.report import Report
from report_printer.libs.page import ReportPage
from report_printer.libs.report import ReportParameters
from medical_service_register.path import REESTR_EXP
from report_printer.libs.const import MONTH_NAME


def get_30pc(count_all):
    count_30ps = count_all * 0.3
    if count_30ps - int(count_30ps) >= 0.5:
        count_30ps += 1
    count_30ps = int(count_30ps)
    return count_30ps


def select_30pc_at_hospital(is_reverse=False):
    """
    Выбирает 30% по укороченным-удлиненным в круглосуточном стационаре
    """

    overdued_nkd30_path = PRODUCTION_OVERDUED_NKD_DBF
    overdued_nkd_path = os.path.join(PRODUCTION_OVERDUED_NKD_DBF, u'все')
    shema = (
        ("COD", "C", 15),
        ("OTD", "C", 3),
        ("ERR_ALL", "C", 8),
        ("SN_POL", "C", 25),
        ("FAM", "C", 20),
        ("IM", "C", 20),
        ("OT", "C", 25),
        ("DR", "D"),
        ("DS", "C", 6),
        ("DS2", "C", 6),
        ("C_I", "C", 16),
        ("D_BEG", "D"),
        ("D_U", "D"),
        ("K_U", "N", 4),
        ("F_DOP_R", "N", 10, 2),
        ("T_DOP_R", "N", 10, 2),
        ("S_OPL", "N", 10, 2),
        ("ADRES", "C", 80),
        ("SPOS", "C", 2),
        ("GENDER", "C", 1),
        ("EMPL_NUM", "C", 16),
        ("HOSP_TYPE", "N", 2),
        ("OUTCOME", "C", 3),
    )
    hospital_outcome = ['101', '102', '103', '104']
    report_data = {}
    for filename in os.listdir(overdued_nkd_path):
        if filename.endswith('.dbf') and not filename.startswith('.'):
            dep_code = filename[1:-4]
            # Расскомментировать если нужно обработать только определённые файлы
            # if dep_code != '0111006':
            #    continue
            db = dbf.Dbf(os.path.join(overdued_nkd_path, filename))
            count_all = 0
            count_day_hospital = 0
            for rec in db:
                if rec['OUTCOME'] in hospital_outcome:
                    count_all += 1
                else:
                    count_day_hospital += 1
            db.close()

            db = dbf.Dbf(os.path.join(overdued_nkd_path, filename))
            buffer_db = []
            for rec in db:
                item = {}
                for field in shema:
                    item[field[0]] = rec[field[0]]
                buffer_db.append(item)
            db.close()

            count_30ps = get_30pc(count_all)
            report_data[dep_code] = count_30ps
            if count_30ps > 0 or count_day_hospital:
                counter = 0
                id_list = []
                for idx in (xrange(len(buffer_db)-1, -1, -1) if is_reverse else xrange(0, len(buffer_db)-1)):
                    rec = buffer_db[idx]
                    if rec['OUTCOME'] in hospital_outcome and counter < count_30ps:
                        id_list.append(idx)
                        counter += 1
                    if rec['OUTCOME'] not in hospital_outcome:
                        id_list.append(idx)

                db30 = dbf.Dbf(os.path.join(overdued_nkd30_path, filename), new=True)
                db30.addField(*shema)

                for idx in (reversed(id_list) if is_reverse else id_list):
                    rec = buffer_db[idx]
                    rec30 = db30.newRecord()
                    for field in shema:
                        rec30[field[0]] = rec[field[0]]
                    rec30.store()
                db30.close()
    print u'Выбрал 30%', overdued_nkd30_path
    return report_data


def select_30pc_at_clinic(is_reverse=False):
    """
    Выбирает 30% по повторным по поликлинике
    """

    repeated30_path = PRODUCTION_REPEATED_DBF
    repeated_path = os.path.join(PRODUCTION_REPEATED_DBF, u'все')
    stat_by_mo, stat_by_amb, stat_amb = get_statistics(repeated_path)
    shema = (
        ("COD", "C", 15),
        ("OTD", "C", 3),
        ("ERR_ALL", "C", 8),
        ("SN_POL", "C", 25),
        ("FAM", "C", 20),
        ("IM", "C", 20),
        ("OT", "C", 25),
        ("DR", "D"),
        ("DS", "C", 6),
        ("DS2", "C", 6),
        ("C_I", "C", 16),
        ("D_BEG", "D"),
        ("D_U", "D"),
        ("K_U", "N", 4),
        ("F_DOP_R", "N", 10, 2),
        ("T_DOP_R", "N", 10, 2),
        ("S_OPL", "N", 10, 2),
        ("ADRES", "C", 80),
        ("SPOS", "C", 2),
        ("GENDER", "C", 1),
        ("EMPL_NUM", "C", 16),
        ("HOSP_TYPE", "N", 2),
        ("OUTCOME", "C", 3),
        ("IDCASE", "C", 16),
        ("IDSERV", "C", 16),
        ("ISREPEATED", "N", 2),
    )
    report_data = {}
    for mo_code in stat_by_mo:
        # Расскомментировать если нужно обработать только определённую больницу
        # if mo_code != '280026':
        #    continue
        is_include_amb = False
        for dep_code, count_all, services in stat_by_mo[mo_code]:
            count30ps_amb = get_30pc(stat_amb.get(mo_code, 0))
            count30ps_dep = get_30pc(count_all)
            if not is_include_amb and count30ps_amb + count30ps_dep < len(services):
                is_include_amb = True
                count30ps_dep += count30ps_amb
            if count30ps_dep > 0:
                report_data[dep_code] = count30ps_dep
                db = dbf.Dbf(os.path.join(repeated_path, u't%s - Поликлиника.dbf' % dep_code))
                db30 = dbf.Dbf(os.path.join(repeated30_path, u't%s - Поликлиника.dbf' % dep_code), new=True)
                db30.addField(*shema)
                services30ps = {}
                lenght_all = len(services.keys())
                for u_hash in (list(services.keys()[lenght_all-count30ps_dep:lenght_all]) if is_reverse else list(services.keys()[:count30ps_dep])):
                        services30ps[u_hash] = services[u_hash]
                for rec in db:
                    unique_hash = '%s %s %s %s %s' % (rec['FAM'], rec['IM'], rec['OT'],
                                                      rec['DR'], rec['DS'])
                    serv = services30ps.get(unique_hash, None)
                    if serv and (rec['IDCASE'] == serv[0] or rec['IDCASE'] == serv[1]):
                        rec30 = db30.newRecord()
                        for field in shema:
                            rec30[field[0]] = rec[field[0]]
                        rec30.store()
                db30.close()
            db.close()
    print u'Выбрал 30%', repeated30_path
    return report_data


def get_statistics(repeated_path):
    """
    Собирает статистику по повторным в поликлинике
    """

    mo_map = get_mo_map()
    stat_by_mo = {}
    stat_by_amb = {}
    stat_amb = {}
    for filename in os.listdir(repeated_path):
        if filename.endswith('.dbf') and not filename.startswith('.') and filename.__contains__(u'Поликлиника'):
            dep_code = filename.replace(u' - Поликлиника', '')[1:-4]
            mo_code = mo_map[dep_code]
            db = dbf.Dbf(os.path.join(repeated_path, filename))
            count_all = 0
            services = OrderedDict()
            first = None
            second = None
            current_unique_hash = None
            for rec in db:
                if rec['S_OPL'] > 0:
                    unique_hash = '%s %s %s %s %s' % (rec['FAM'], rec['IM'], rec['OT'],
                                                      rec['DR'], rec['DS'])
                    if not first:
                        first = rec['IDCASE']
                        current_unique_hash = unique_hash
                    else:
                        if current_unique_hash and current_unique_hash == unique_hash:
                            if not second:
                                second = rec['IDCASE']
                                services[unique_hash] = (first, second)
                                first = None
                                second = None
                                current_unique_hash = None
                        elif current_unique_hash and current_unique_hash != unique_hash:
                            first = rec['IDCASE']
                            second = None
                            current_unique_hash = unique_hash
                    count_all += 1
            count_all /= 2
            db.close()
            current_dep = (dep_code, count_all, services)

            if is_not_included_department(dep_code):
                if mo_code not in stat_by_amb:
                    stat_by_amb[mo_code] = []
                if mo_code not in stat_amb:
                    stat_amb[mo_code] = 0
                stat_amb[mo_code] += count_all
                stat_by_amb[mo_code].append(current_dep)
            else:
                if mo_code not in stat_by_mo:
                    stat_by_mo[mo_code] = []
                stat_by_mo[mo_code].append(current_dep)
                if len(stat_by_mo[mo_code]) > 2:
                    last = stat_by_mo[mo_code][-1]
                    pre_last = stat_by_mo[mo_code][-2]
                    if last[2] > pre_last[2]:
                        stat_by_mo[mo_code][-1] = pre_last
                        stat_by_mo[mo_code][-2] = last

    return stat_by_mo, stat_by_amb, stat_amb


def is_not_included_department(dep_code):
    """
    Подразделения, которые не включаются в выборку
    """
    return dep_code in [
        '0328076', '0328075', '0328016', '1328082', '0310084', '0328085', '0328086', '0328001',
        '0328004', '0328002', '0328003', '1328110', '1328111', '1328115', '1328112', '0328012',
        '0310018', '0328017', '0328119', '0310050', '0328051', '0328120', '0310019', '0328009',
        '0328038', '0328036', '0328041', '0328101', '0328019', '0328096', '0328097', '0328098',
        '0328100', '0328055', '0328013', '0328014', '0328020', '0328010', '0328011', '0328015',
        '0328021', '1106021', '1118001', '1328113', '1328114', '0328018', '1307048', '0310049',
        '0310047', '0108002', '0208003', '0310072', '0310073', '0321001', '0310032', '0310096',
        '1305089', '0310092', '0321002', '0310117', '6115001', '0301063', '0309077', '1305088',
        '0313063', '0313067', '0101007', '0115025', '0121001', '0121002', '0123002'
    ]


class TargetedExpertise30pcPage(ReportPage):
    def __init__(self, clinic_result, hospital_result):
        self.data = None
        self.clinic_result = clinic_result
        self.hospital_result = hospital_result
        self.page_number = 0

    def calculate(self, parameters):
        self.data = {}
        mo_map = get_mo_map()
        for dep in self.clinic_result:
            mo_code = mo_map[dep]
            if mo_code not in self.data:
                self.data[mo_code] = {}
            if 'clinic' not in self.data[mo_code]:
                self.data[mo_code]['clinic'] = 0
            self.data[mo_code]['clinic'] += self.clinic_result[dep]

        for dep in self.hospital_result:
            mo_code = mo_map[dep]
            if mo_code not in self.data:
                self.data[mo_code] = {}
            if 'hospital' not in self.data[mo_code]:
                self.data[mo_code]['hospital'] = 0
            self.data[mo_code]['hospital'] += self.hospital_result[dep]

    def print_page(self, sheet, parameters):
        sheet.write(u'МО', 'c')
        sheet.write(u'Повторные поликлиника', 'c')
        sheet.write(u'Удл.-укороч. кругл. стационар', 'r')
        for mo_code in self.data:
            sheet.write(get_mo_name(mo_code), 'c')
            sheet.write(self.data[mo_code].get('clinic', 0), 'c')
            sheet.write(self.data[mo_code].get('hospital', 0), 'r')


class Command(BaseCommand):
    """
    Выбирает 30% экспертиз по повтрным в полклинике
    и по укороченным-удлиннённым в круглосуточном стационаре
    """

    def handle(self, *args, **options):
        if 'reverse' in args:
            clinic_result = select_30pc_at_clinic(is_reverse=True)
            hospital_result = select_30pc_at_hospital(is_reverse=True)
        else:
            clinic_result = select_30pc_at_clinic()
            hospital_result = select_30pc_at_hospital()

        # Отчёт по 30 процентам целевых экспертиз
        parameters = ReportParameters()
        parameters.path_to_dir = REESTR_EXP % (
            parameters.registry_year,
            parameters.registry_period
        )
        parameters.report_name = u'целевые 30 процентов за %s' % MONTH_NAME[parameters.registry_period]
        report = Report()
        report.add_page(TargetedExpertise30pcPage(
            clinic_result=clinic_result,
            hospital_result=hospital_result
        ))
        report.print_pages(parameters)
