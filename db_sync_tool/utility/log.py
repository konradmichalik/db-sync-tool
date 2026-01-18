#!/usr/bin/env python3

"""
Log script
"""

import logging
from db_sync_tool.utility import system

#
# GLOBALS
#

logger = None


#
# FUNCTIONS
#


def init_logger():
    """
    Initialize the logger instance
    :return:
    """
    global logger
    logger = logging.getLogger('db_sync_tool')
    logger.setLevel(logging.DEBUG)

    cfg = system.get_typed_config()
    if cfg.log_file:
        fh = logging.FileHandler(cfg.log_file)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)


def get_logger():
    """
    Return the logger instance
    :return:
    """
    if logger is None:
        init_logger()
    return logger
