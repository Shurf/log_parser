__author__ = 'schrecknetuser'

import logging


class Logger:
    logging_initialized = False

    @staticmethod
    def initialize_logging():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%d-%m %H:%M:%S')
        Logger.logging_initialized = True

    @staticmethod
    def log(message):
        if not Logger.logging_initialized:
            Logger.initialize_logging()
        logging.info(message)
