from abc import ABCMeta, abstractmethod


class ReportPage():
    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate(self, parameters):
        """Calculate report"""

    @abstractmethod
    def print_page(self, sheet, parameters):
        """Print report"""

