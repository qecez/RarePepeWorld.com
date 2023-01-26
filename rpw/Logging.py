import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

import Settings

loggers = Settings.Logs['loggers']


class Logger:
    @staticmethod
    def setup_logger(logger_name, logger) -> logging.Logger:
        logger.setLevel(loggers[logger_name]['log_level'])
        file_handler = RotatingFileHandler(loggers[logger_name]['log_file'],
                                           maxBytes=10_000_000, backupCount=5, mode='a')
        file_handler.setFormatter(loggers[logger_name]['log_formatter'])
        file_handler.setLevel(loggers[logger_name]['log_level'])
        logger.addHandler(file_handler)
        logger.setLevel(loggers[logger_name]['log_level'])

        return logger

    @staticmethod
    def timestamp():
        return f"{datetime.now()}"
