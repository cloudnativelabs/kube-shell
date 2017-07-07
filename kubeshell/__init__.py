__version__ = '0.0.20'
from . import logger
import logging
import logging.config
logging.config.dictConfig(logger.loggingConf)