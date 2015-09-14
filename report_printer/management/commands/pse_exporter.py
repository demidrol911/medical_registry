#! -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from medical_service_register.path import REESTR_PSE, BASE_DIR
from tfoms import func
from shutil import copy2
from helpers.correct import date_correct
from dbfpy import dbf
import os

### Экспорт реестра в PSE файла
# (P - файл пациентов, S - файл услуг, E - файл ошибок)
class Command(BaseCommand):
    def handle(self, *args, **options):
        mo = args[0]
        status = args[1]
        print u'Выгрузка в PSE файлы...'
        target_dir = REESTR_PSE #os.path.join(REESTR_PSE, '280001')
        templates_path = '%s/templates/dbf_pattern' % BASE_DIR
        services = func.get_services(mo, is_include_operation=True)
        patients = func.get_patients(mo)
        sanctions = func.get_sanctions(mo)

        # Группировка услуг по прикреплённым больницам
        services_group = {}
        for index, service in enumerate(services):
            if service['department'] not in services_group:
                services_group[service['department']] = []
            if service['group'] == 27 or service['code'] in ('A06.10.006', 'A06.12.031'):
                pass
            else:
                services_group[service['department']].append(index)

        for department in services_group:
            concomitant_diseases = func.get_concomitant_disease(department)
            rec_id = 1
            unique_patients = []
            copy2('%s/template_p.dbf' % templates_path,
                  '%s/p%s.dbf' % (target_dir, department))
            copy2('%s/template_s.dbf' % templates_path,
                  '%s/s%s.dbf' % (target_dir, department))
            copy2('%s/template_e.dbf' % templates_path,
                  '%s/e%s.dbf' % (target_dir, department))
            p_file = dbf.Dbf('%s/p%s.dbf' % (target_dir, department))
            s_file = dbf.Dbf('%s/s%s.dbf' % (target_dir, department))
            e_file = dbf.Dbf('%s/e%s.dbf' % (target_dir, department))

            for index in services_group[department]:
                service = services[index]
                patient = patients[service['patient_id']]

                #Записываем данные услуги в S-файл
                s_rec = s_file.newRecord()
                s_rec['RECID'] = rec_id
                s_rec['MCOD'] = service['department']
                police = ' '.join([patient['policy_series'] or '99',
                                   patient['policy_number'] or ''])
                s_rec['SN_POL'] = police.encode('cp866')
                s_rec['C_I'] = service['anamnesis_number'].encode('cp866')
                s_rec['OTD'] = service['division_code'] or ''
                s_rec['COD'] = float(service['code'])
                #s_rec['TIP'] = ''
                s_rec['D_BEG'] = date_correct(service['start_date'], service['id'], 'start_date')
                s_rec['D_U'] = date_correct(service['end_date'], service['id'], 'end_date')
                s_rec['K_U'] = service['quantity'] or 1
                s_rec['DS'] = (service['basic_disease'] or service['event_basic_disease']).encode('cp866')
                s_rec['DS2'] = (concomitant_diseases.get(service['event_id'], '')).encode('cp866')
                #s_rec['TR'] = ''
                s_rec['EXTR'] = '0'
                s_rec['PS'] = 1 if service['term'] == 1 else 0
                s_rec['BE'] = '1'
                s_rec['TN1'] = service['worker_code'].encode('cp866')
                #s_rec['TN2'] = ''
                s_rec['TARIF'] = '1'
                s_rec['KLPU'] = '1'
                s_rec['KRR'] = 1
                s_rec['UKL'] = 1
                s_rec['SK'] = 1
                s_rec['S_ALL'] = service['tariff'] or 0
                s_rec['KSG'] = (service['comment'] or '').encode('cp866')
                s_rec['D_TYPE'] = '1'
                s_rec['STAND'] = 1000
                s_rec['K_U_O'] = 100
                s_rec['SRV_PK'] = service['id']
                s_rec.store()

                # Записываем пациентов в P-файл
                if service['patient_id'] not in unique_patients:
                    p_rec = p_file.newRecord()
                    p_rec['RECID'] = rec_id
                    p_rec['MCOD'] = department
                    p_rec['SN_POL'] = police.encode('cp866')
                    p_rec['FAM'] = (patient['last_name'] or '').capitalize().encode('cp866')
                    p_rec['IM'] = (patient['first_name'] or '').capitalize().encode('cp866')
                    p_rec['OT'] = (patient['middle_name'] or '').capitalize().encode('cp866')
                    p_rec['DR'] = date_correct(patient['birthdate'])
                    p_rec['W'] = patient['gender_code']
                    #p_rec['REGS'] = 0
                    p_rec['NULN'] = ' '*20
                    p_rec['UL'] = 0
                    p_rec['DOM'] = ' '*7
                    p_rec['KOR'] = ' '*5
                    p_rec['STR'] = ' '*5
                    p_rec['KV'] = ' '*5
                    p_rec['ADRES'] = ' '*80
                    p_rec['Q'] = 'DM'
                    p_rec['KT'] = '  '
                    #p_rec['SP'] = ''
                    p_rec['VED'] = '  '
                    #p_rec['MR'] = 0
                    p_rec['D_TYPE'] = '1'
                    p_rec.store()
                    unique_patients.append(service['patient_id'])

                # Записываем ошибки в E-файл
                if sanctions.get(service['id']):
                    unique_errors = []
                    for sanction in sanctions[service['id']]:
                        if sanction['error'] not in unique_errors:
                            e_rec = e_file.newRecord()
                            e_rec['F'] = 'S'
                            e_rec['C_ERR'] = func.ERRORS[sanction['error']]['code']
                            e_rec['N_REC'] = rec_id
                            e_rec['RECID'] = rec_id
                            e_rec['MCOD'] = department
                            e_rec.store()
                            unique_errors.append(sanction['error'])
                #Ставим на стоматологических приёмах ошибку HD
                if service['subgroup'] in [12, 13, 14, 17]:
                    e_rec = e_file.newRecord()
                    e_rec['F'] = 'S'
                    e_rec['C_ERR'] = 'HD'
                    e_rec['N_REC'] = rec_id
                    e_rec['RECID'] = rec_id
                    e_rec['MCOD'] = department
                    e_rec.store()
                rec_id += 1
            p_file.close()
            s_file.close()
            e_file.close()
        func.change_register_status(mo, status)
