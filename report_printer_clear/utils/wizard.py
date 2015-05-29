from report_printer_clear.utils.report import ReportParameters
from tfoms.func import get_mo_code, get_mo_name, change_register_status, calculate_capitation
from medical_service_register.path import REESTR_DIR, REESTR_EXP


class AutomaticReportsWizard():

    def __init__(self, report, suffix=''):
        self.report = report
        self.suffix = suffix

    def create_reports(self, registry_status):
        parameters = ReportParameters()
        organization_code = get_mo_code(registry_status)
        if registry_status in (6, 8):
            path_to_dir = REESTR_DIR
        else:
            path_to_dir = REESTR_EXP
        parameters.path_to_dir = path_to_dir % (
            parameters.registry_year,
            parameters.registry_period
        )

        while organization_code:
            parameters.organization_code = organization_code
            parameters.report_name = get_mo_name(organization_code).\
                replace('"', '').strip() + ('_'+self.suffix if self.suffix else '')
            parameters.policlinic_capitation = calculate_capitation(3, organization_code)
            parameters.ambulance_capitation = calculate_capitation(4, organization_code)
            parameters.policlinic_capitation_total = self.__calculate_total(parameters.policlinic_capitation[1])
            parameters.ambulance_capitation_total = self.__calculate_total(parameters.ambulance_capitation[1])
            self.report.print_pages(parameters)
            #change_register_status(organization_code, 6)
            organization_code = get_mo_code(registry_status)
            break

    def __calculate_total(self, capitation):
        result = 0
        for key in capitation:
            result += capitation[key]['accepted']
        return result


