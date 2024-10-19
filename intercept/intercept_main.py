
import os
from typing import Union, List

from experiment.common import instrumentation_arguments_default, instrumentation_strategy_factory_wrapper, setup_additional_directories, setup_experiment_dir
from hybrid import hybrid_config
from hybrid.hybrid_config import HybridAnalysisConfig
from intercept import decode, instrument, rebuild, keygen, sign, monkey

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

    
    decoded_apks_directory_path = config._decoded_apks_path
    instrumentation_strategy_arguments = instrumentation_arguments_default()
    rebuilt_apks_directory_path = config._rebuilt_apks_path
    keys_directory_path = config._keys_dir_path
    signed_apks_directory_path = config._signed_apks_path

    decode.decode_batch(decoded_apks_directory_path, unique_apks)
    instrumentation_strategy_arguments = instrumentation_strategy_factory_wrapper(instrumentation_strategy_arguments)
    instrument.instrument_batch(decoded_apks_directory_path, instrumentation_strategy_arguments, unique_apks)
    rebuild.rebuild_batch(decoded_apks_directory_path, rebuilt_apks_directory_path, unique_apks)
    keygen.generate_keys_batch(keys_directory_path, unique_apks)
    sign.assign_key_batch(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, unique_apks)
    logger.info("Code instrumentation finished.")

def run_apks(config: HybridAnalysisConfig, input: BatchInputModel):
    logger.info("Running APKs...")
    monkey.run_input_apks_model(config, input)
    logger.info("Finished running APKs.")


def generate_smali_code(apk_path: str, decode_output_directory_path: str):
    # if do_clean:
    #     clean.clean(config)
    apk_model: ApkModel = ApkModel(apk_path)
    
    decode.decode_apk(decode_output_directory_path, apk_model, clean=True)

def decompile_and_rebuild_apks(apks: List[ApkModel], experiment_directory_path):
    clean = True

    decoded_apks_directory_path = setup_additional_directories(experiment_directory_path, ["decoded-apks"])[0]
    decode.decode_batch(decoded_apks_directory_path, apks, clean=clean)

    rebuild_smali_code(apks, experiment_directory_path, decoded_apks_directory_path)

def rebuild_smali_code(apks: List[ApkModel], experiment_directory_path: str, decoded_apks_directory_path: str):


    paths = setup_additional_directories(experiment_directory_path, ["rebuilt-apks", "keys", "signed-apks"])
    rebuilt_apks_directory_path, keys_directory_path, signed_apks_directory_path = paths[0], paths[1], paths[2]

    rebuild.rebuild_batch(decoded_apks_directory_path, rebuilt_apks_directory_path, apks)
    keygen.generate_keys_batch(keys_directory_path, apks)
    sign.assign_key_batch(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, apks)



# def instrument_apps(config: HybridAnalysisConfig, do_clean=True):
#     logger.info("Start code instrumentation")
#     if do_clean:
#         clean.clean(config)

#     apks_list = config.input_apks.unique_apks
#     decode.decode_batch(config, apks_list)
#     instrument.instrument_batch(config, apks_list)
#     rebuild.rebuild_batch(config, apks_list)
#     keygen.generate_keys_batch(config, apks_list)
#     sign.assign_key_batch(config, apks_list)

if __name__ == '__main__':
    pass