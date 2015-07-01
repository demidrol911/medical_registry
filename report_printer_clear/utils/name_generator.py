#! -*- coding: utf-8 -*-

from os import path, listdir
import re


class NameGenerator():

    def __init__(self, path_to_dir):
        self.path_to_dir = path_to_dir

    def generate_unique_name(self, filename):
        filename_without_ext, file_ext = path.splitext(filename)

        filename_pattern = re.compile(ur'^%s(?:_?)(?P<sequence_number>\d*?)%s$' %
                                      (filename_without_ext
                                       .replace('(', '\(')
                                       .replace(')', '\)'), file_ext))
        sequence_number = -1
        for file_from_dir in listdir(self.path_to_dir):
            filename_match = filename_pattern.match(file_from_dir)
            if filename_match:
                current_sequence_number = int(filename_match.group('sequence_number') or 0) + 1
            else:
                current_sequence_number = -1
            if sequence_number < current_sequence_number:
                sequence_number = current_sequence_number

        filename_generate_pattern = u'{filename}{sequence_number}{file_ext}'
        return filename_generate_pattern.format(
            filename=filename_without_ext,
            sequence_number='' if sequence_number == -1 else '_'+str(sequence_number),
            file_ext=file_ext
        )



