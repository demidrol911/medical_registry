from general import MedicalServiceTypePage


class ClinicAllPrimary(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query()
        return query

    def get_output_order_fields(self):
        pass


class ClinicAllSpec(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query()
        return query

    def get_output_order_fields(self):
        pass


class ClinicAll(MedicalServiceTypePage):

    def __init__(self):
        self.data = None
        self.page_number = 0

    def get_query(self):
        query = MedicalServiceTypePage.get_general_query()
        return query

    def get_output_order_fields(self):
        pass
