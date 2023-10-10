import logging
import logging.config
import os


def get_logger(package_name: str, module_name: str):
    # logging_conf_path = "~/Documents/programming/research-programming/ConDySta/data/logger/logging.conf"
    # TODO: path should get abstracted into config
    # TODO: how to get logging.config.fileconfig to think it's in the project root, not the hybrid dir?
    logging_conf_path = "data/logger/logging.conf"
    if not os.path.isfile(logging_conf_path):
        raise AssertionError(f"Logging config file not found at {logging_conf_path}")
    logging.config.fileConfig(logging_conf_path)

    # [logger_name].[name of child logger]
    logger = logging.getLogger(f"default.{package_name}.{module_name}")
    return logger