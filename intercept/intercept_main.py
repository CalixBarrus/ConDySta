# TODO: make this an entry point to call and control all the scripts in the
#  package
import os

from intercept import decode, instrument, rebuild, keygen, \
    intercept_config, sign, clean, monkey
from intercept.intercept_config import InterceptConfig

from util import logger
logger = logger.get_logger('intercept', 'intercept_main')

def main(config: InterceptConfig, do_clean=True):
    if do_clean:
        clean.clean(config)

    instrument_code(config)

    run_apks(config)

    pass

def instrument_code(config: InterceptConfig):
    logger.info("Starting code instrumentation...")
    decode.decode(config)
    instrument.instrument_main(config)
    rebuild.rebuild(config)
    keygen.generate_keys(config)
    sign.assign_key(config)
    logger.info("Code instrumentation finished.")

def run_apks(config: InterceptConfig):
    logger.info("Running APKs...")
    monkey.run_apks(config)
    logger.info("Finished running APKs.")


def generate_smali_code(config: InterceptConfig, do_clean=True):
    if do_clean:
        clean.clean(config)
    decode.decode(config)

def rebuild_smali_code(config: InterceptConfig):
    # Clean out rebuilt-apks, keys, and signed-apks.
    # TODO: should probably change clean.py so this can live in there
    for folder in [config.rebuilt_apks_path, config.signed_apks_path]:
        cmd = f'rm {os.path.join(folder, "*.apk")}'
        logger.debug(cmd)
        os.system(cmd)
    cmd = f'rm {os.path.join(config.key_path, "*.keystore")}'
    logger.debug(cmd)
    os.system(cmd)

    rebuild.rebuild(config)
    keygen.generate_keys(config)
    sign.assign_key(config)



def instrument_apps(config: InterceptConfig, do_clean=True):
    logger.info("Start code instrumentation")

    if do_clean:
        clean.clean(config)
    decode.decode(config)
    instrument.instrument_main(config)
    rebuild.rebuild(config)
    keygen.generate_keys(config)
    sign.assign_key(config)

if __name__ == '__main__':
    configuration: InterceptConfig = intercept_config.get_default_intercept_config()

    # main(configuration)
    # generate_smali_code(configuration)
    instrument_apps(configuration)