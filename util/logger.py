import logging
import logging.config
from logging.handlers import RotatingFileHandler
import os


logger_dir_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'logger')
logging_conf_path = os.path.join(logger_dir_path, 'logging.conf')
general_log_path = os.path.join(logger_dir_path, 'condysta.log')

if not os.path.isfile(logging_conf_path):
    raise AssertionError(f"Logging config file not found at {logging_conf_path}, has the project directory structure changed?")

logging.config.fileConfig(logging_conf_path)

# Setup up file handler programatically to avoid path dependencies
rotating_handler = RotatingFileHandler(general_log_path, maxBytes=1048576, backupCount=3) # 1MB
rotating_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotating_handler.setFormatter(formatter)

default_logger = logging.getLogger("default")
default_logger.addHandler(rotating_handler)


def get_logger(package_name: str, module_name: str):
    # logging_conf_path = "~/Documents/programming/research-programming/ConDySta/data/logger/logging.conf"
    # TODO: path should get abstracted into config
    # TODO: how to get logging.config.fileconfig to think it's in the project root, not the hybrid dir?

    # [logger_name].[name of child logger]
    logger = logging.getLogger(f"default.{package_name}.{module_name}")
    return logger

def get_logger_revised(file__name__: str) -> logging.Logger:

    # [logger_name].[name of child logger]
    logger = logging.getLogger(f"default.{file__name__}")
    return logger

def set_all_loggers_file_handler(log_file_path: str):
    # Create a new file handler
    file_handler = logging.FileHandler(log_file_path, 'w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    default_logger = logging.getLogger("default")
    default_logger.addHandler(file_handler)
    # TODO: make sure this actually works