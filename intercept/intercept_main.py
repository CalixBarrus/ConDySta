
import os
from typing import Union, List

from hybrid.hybrid_config import HybridAnalysisConfig
from intercept import decode, instrument, rebuild, keygen, \
    intercept_config, sign, clean, monkey

from util.input import ApkModel, BatchInputModel, InputModel

import util.logger
logger = util.logger.get_logger(__name__)

# def main(config: HybridAnalysisConfig, input: InputApksModel, do_clean=True):
#     if do_clean:
#         clean.clean(config)
#
#     instrument_code(config, input)
#
#     run_apks(config, input)


def instrument_apks(config: HybridAnalysisConfig, unique_apks: List[ApkModel], do_clean=True):
    """
    Instrument each apk in InputApksModel (once).
    Instrumented apks can be accessed from hybrid_config.signed_apk_path()
    TODO: this method fails if clean is not called by the caller (I think)
    """

    logger.info("Starting code instrumentation...")
    decode.decode_batch(config, unique_apks)
    instrument.instrument_batch(config, unique_apks)
    rebuild.rebuild_batch(config, unique_apks)
    keygen.generate_keys_batch(config, unique_apks)
    sign.assign_key_batch(config, unique_apks)
    logger.info("Code instrumentation finished.")

def run_apks(config: HybridAnalysisConfig, input: BatchInputModel):
    logger.info("Running APKs...")
    monkey.run_input_apks_model(config, input)
    logger.info("Finished running APKs.")


def generate_smali_code(config: HybridAnalysisConfig, do_clean=True):
    if do_clean:
        clean.clean(config)

    decode.decode_batch(config, config.input_apks.unique_apks)

def rebuild_smali_code(config: HybridAnalysisConfig):

    # Clean out rebuilt-apks, keys, and signed-apks.
    # TODO: should probably change clean.py so this can live in there
    for folder in [config.rebuilt_apks_path, config.signed_apks_path]:
        cmd = f'rm {os.path.join(folder, "*.apk")}'
        logger.debug(cmd)
        os.system(cmd)
    cmd = f'rm {os.path.join(config.keys_dir_path, "*.keystore")}'
    logger.debug(cmd)
    os.system(cmd)

    apks_list = config.input_apks.unique_apks

    rebuild.rebuild_batch(config, apks_list)
    keygen.generate_keys_batch(config, apks_list)
    sign.assign_key_batch(config, apks_list)



def instrument_apps(config: HybridAnalysisConfig, do_clean=True):
    logger.info("Start code instrumentation")
    if do_clean:
        clean.clean(config)

    apks_list = config.input_apks.unique_apks
    decode.decode_batch(config, apks_list)
    instrument.instrument_batch(config, apks_list)
    rebuild.rebuild_batch(config, apks_list)
    keygen.generate_keys_batch(config, apks_list)
    sign.assign_key_batch(config, apks_list)

if __name__ == '__main__':
    pass