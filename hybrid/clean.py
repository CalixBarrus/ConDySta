import os

import intercept.clean
from hybrid.hybrid_config import HybridAnalysisConfig

from util import logger

logger = logger.get_logger('hybrid', 'clean')


def clean(config: HybridAnalysisConfig):
    logger.info("Cleaning hybrid files...")

    flowdroid_first_pass_logs_path = config.flowdroid_first_pass_logs_path
    flowdroid_second_pass_logs_path = config.flowdroid_second_pass_logs_path

    modified_source_sink_directory = config.modified_source_sink_directory

    for folder in [flowdroid_first_pass_logs_path, flowdroid_second_pass_logs_path]:
        cmd = f'rm {os.path.join(folder, "*.log")}'
        logger.debug(cmd)
        os.system(cmd)

    cmd = f'rm {os.path.join(modified_source_sink_directory, "*.txt")}'
    logger.debug(cmd)
    os.system(cmd)


def setup_folders(config: HybridAnalysisConfig):
    flowdroid_first_pass_logs_path = config.flowdroid_first_pass_logs_path
    flowdroid_second_pass_logs_path = config.flowdroid_second_pass_logs_path
    modified_source_sink_directory = config.modified_source_sink_directory

    for folder in [flowdroid_first_pass_logs_path, flowdroid_second_pass_logs_path, modified_source_sink_directory]:
        cmd = f'mkdir {folder}'
        logger.debug(cmd)
        os.system(cmd)

    intercept.clean.setup_folders(config.intercept_config)

