#! -*- coding: utf-8 -*-
from report_printer.libs.page import ReportPage
from main.models import MedicalOrganization


class TargetedExpertisePage(ReportPage):
    def __init__(self, dead_data, overdued_data, doubled_data):
        self.dead_patient_data = dead_data
        self.overdued_nkd_data = overdued_data
        self.doubled_disease_data = doubled_data
        self.page_number = 0

    def calculate(self, parameters):
        pass

    def print_page(self, sheet, parameters):
        mo_names = MedicalOrganization.objects.filter(parent__isnull=True).order_by('name').values_list('name', flat=True)

        for i, mo in enumerate(mo_names):
            row = i + 3
            sheet.write_cell(row, 0, mo)

            # Умершие
            if self.dead_patient_data:
                item = self.dead_patient_data[(self.dead_patient_data['mo_name'] == mo) &
                                              (self.dead_patient_data['event_term'] == 1)]
                if not item.empty:
                    sheet.write_cell(row, 7, item['event_id'])
                item = self.dead_patient_data[(self.dead_patient_data['mo_name'] == mo) &
                                              (self.dead_patient_data['event_term'] == 2)]
                if not item.empty:
                    sheet.write_cell(row, 8, item['event_id'])

            # Укороченные - удлинённые
            if self.overdued_nkd_data:
                item = self.overdued_nkd_data[(self.overdued_nkd_data['mo_name'] == mo) &
                                              (self.overdued_nkd_data['event_term'] == 1)]
                if not item.empty:
                    sheet.write_cell(row, 5, item['service_id'])
                item = self.overdued_nkd_data[(self.overdued_nkd_data['mo_name'] == mo) &
                                              (self.overdued_nkd_data['event_term'] == 2)]
                if not item.empty:
                    sheet.write_cell(row, 6, item['service_id'])

            # Повторные
            if self.doubled_disease_data:
                item = self.doubled_disease_data[(self.doubled_disease_data['mo_name'] == mo) &
                                                 (self.doubled_disease_data['event_term'] == 1)]
                if not item.empty:
                    sheet.write_cell(row, 1, item['unique_hash'])
                item = self.doubled_disease_data[(self.doubled_disease_data['mo_name'] == mo) &
                                                 (self.doubled_disease_data['event_term'] == 2)]
                if not item.empty:
                    sheet.write_cell(row, 2, item['unique_hash'])

                item = self.doubled_disease_data[(self.doubled_disease_data['mo_name'] == mo) &
                                                 (self.doubled_disease_data['event_term'] == 3)]
                if not item.empty:
                    sheet.write_cell(row, 3, item['unique_hash'])

                item = self.doubled_disease_data[(self.doubled_disease_data['mo_name'] == mo) &
                                                 (self.doubled_disease_data['event_term'] == 4)]
                if not item.empty:
                    sheet.write_cell(row, 4, item['unique_hash'])
