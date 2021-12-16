import logging

LOG_LEVEL = logging.INFO

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)
fh = logging.FileHandler("beehive_scripts.log")
fh.setLevel(LOG_LEVEL)
logger.addHandler(fh)
