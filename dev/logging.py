import logging
import sys

FORMATTER = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def get_console_handler():
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    return console_handler


def get_logger(logger_name: str):
    logger = logging.getLogger(name=logger_name)
    logger.setLevel(level=logging.INFO)
    logger.addHandler(hdlr=get_console_handler())
    logger.propagate = False
    return logger
