import logging
import logging.config

logging.config.fileConfig('log.conf')
log = logging.getLogger('simpleExample')