from tfoms.func import get_mo_code, get_mo_name, change_register_status
from medical_service_register.path import REESTR_DIR, REESTR_EXP


class AutomaticReportsWizard():

    def __init__(self, report, parameters):
        self.report = report
        self.parameters = parameters

    def create_reports(self, registry_status):
        organization_code = get_mo_code(registry_status)
        if registry_status in (6, 8):
            path_to_dir = REESTR_DIR
        else:
            path_to_dir = REESTR_EXP
        self.parameters.path_to_dir = path_to_dir % (
            self.parameters.registry_year,
            self.parameters.registry_period
        )

        while organization_code:
            self.parameters.organization_code = organization_code
            self.parameters.report_name = get_mo_name(organization_code).\
                replace('"', '').strip()
            self.report.print_pages(self.parameters)
            change_register_status(organization_code, 6)
            organization_code = get_mo_code(registry_status)


