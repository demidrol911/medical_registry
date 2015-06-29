from report_printer_clear.utils.report import ReportParameters
from tfoms.func import get_mo_code, get_mo_name, \
    change_register_status, calculate_capitation, \
    get_partial_register
from medical_service_register.path import REESTR_DIR, REESTR_EXP


class AutomaticReportsWizard():

    def __init__(self, reports):
        self.reports = reports
        self.completed_reports = []

    def create_reports(self, registry_status):
        organization_code = get_mo_code(registry_status)
        while organization_code:
            print organization_code
            change_register_status(organization_code, 11)

            parameters = ReportParameters()
            if registry_status in (6, 8):
                path_to_dir = REESTR_DIR
            else:
                path_to_dir = REESTR_EXP
            parameters.path_to_dir = path_to_dir % (
                parameters.registry_year,
                parameters.registry_period
            )
            if registry_status == 3:
                new_status = 9
            elif registry_status == 8:
                new_status = 6
            else:
                new_status = 600
            parameters.organization_code = organization_code
            parameters.report_name = get_mo_name(organization_code).\
                replace('"', '').strip()
            parameters.partial_register = get_partial_register(organization_code)
            parameters.policlinic_capitation = calculate_capitation(3, organization_code)
            parameters.ambulance_capitation = calculate_capitation(4, organization_code)
            parameters.policlinic_capitation_total = self.__calculate_total(parameters.policlinic_capitation[1])
            parameters.ambulance_capitation_total = self.__calculate_total(parameters.ambulance_capitation[1])
            parameters.department = None

            for report in self.reports:
                report.print_pages(parameters)
                self.completed_reports.append(report.get_filename())
                print '-'*70

            for department in parameters.partial_register:
                print department
                parameters.report_name = get_mo_name(organization_code, department).\
                    replace('"', '').strip()
                parameters.partial_register = [department]
                parameters.department = department
                for report in self.reports:
                    if report.is_by_department():
                        report.print_pages(parameters)
                        print '-'*70

            change_register_status(organization_code, new_status)
            organization_code = get_mo_code(registry_status)

    def print_completed_reports(self):
        for report in self.completed_reports:
            print report

    def __calculate_total(self, capitation):
        result = 0
        for key in capitation:
            result += capitation[key].get('accepted', 0)
        return result


