import os

from intercept import intercept_config
from intercept.intercept_config import InterceptConfig

from util import logger

logger = logger.get_logger('intercept', 'clean')


def clean(config: InterceptConfig):
    logger.info("Cleaning intercept files")

    decoded_apks_path = config.decoded_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path
    key_path = config.key_path
    signed_apks_path = config.signed_apks_path
    logs_path = config.logs_path

    for folder in [rebuilt_apks_path, signed_apks_path]:
        cmd = f'rm {os.path.join(folder, "*.apk")}'
        logger.debug(cmd)
        os.system(cmd)

    cmd = f'rm {os.path.join(key_path, "*.keystore")}'
    logger.debug(cmd)
    os.system(cmd)

    cmd = f'rm {os.path.join(signed_apks_path, "*.idsig")}'
    logger.debug(cmd)
    os.system(cmd)

    cmd = f'rm {os.path.join(logs_path, "*.log")}'
    logger.debug(cmd)
    os.system(cmd)

    # For the smali code,
    # remove the whole directory and replace the root in order to avoid a
    # confirmation prompt.
    cmd = 'rm -rf {}'.format(decoded_apks_path)
    logger.debug(cmd)
    os.system(cmd)

    cmd = 'mkdir {}'.format(decoded_apks_path)
    logger.debug(cmd)
    os.system(cmd)


def setup_folders(config):
    decoded_apks_path = config.decoded_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path
    key_path = config.key_path
    signed_apks_path = config.signed_apks_path
    logs_path = config.logs_path

    directory_list = [decoded_apks_path, rebuilt_apks_path, key_path,
                      signed_apks_path, logs_path]
    for directory in directory_list:
        if not os.path.exists(directory):
            cmd = "mkdir {}".format(directory)
            print(cmd)
            os.system(cmd)


if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    clean(configuration)

    # setup_folders()
