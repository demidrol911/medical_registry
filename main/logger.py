import logging
import os
from medical_service_register.path import LOGGING_DIR


def get_logger(name):
    logger_name = ''
    name_part = name.split('.')
    if len(name_part) > 0:
        logger_name = name_part[-1]

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(os.path.join(LOGGING_DIR, 'registry_processing.log'))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
