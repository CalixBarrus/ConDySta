

import os
import time
from typing import List

import pandas as pd
from experiment import external_path
from experiment.common import benchmark_df_base_from_batch_input_model, format_num_secs, results_df_from_benchmark_df, setup_additional_directories, setup_experiment_dir
from hybrid import hybrid_config
from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from intercept import decode, instrument, keygen, rebuild, sign
from util.input import ApkModel, input_apks_from_dir

import util.logger
logger = util.logger.get_logger(__name__)

def instrument_test_wild_benchmarks_few():
    apks_subset = [0, 1]
    instrument_test_wild_benchmarks(apks_subset)
    
def instrument_test_wild_benchmarks_full():
    apks_subset = None
    instrument_test_wild_benchmarks(apks_subset)

def instrument_test_wild_benchmarks(apks_subset):
    fossdroid_apks_dir = external_path.fossdroid_benchmark_apks_dir_path
    gpbench_apks_dir = external_path.gpbench_apks_dir_path
    

    for apks_dir_path, name in [(fossdroid_apks_dir, "fossdroid"), (gpbench_apks_dir, "gpbench")]:
        description = f"Testing instrumentation on {name} benchmark"
        instrument_test_generic(apks_dir_path, "instrument-test-" + name, description, apks_subset)

def instrument_test_generic(apks_dir_path: str, experiment_name: str, experiment_description: str, apks_subset):
    # eventually may want to support benchmark description csv

    always_new_experiment_directory = False

    kwargs = {"apks_dir_path": apks_dir_path, "apks_subset": apks_subset}
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

    inputs_model = input_apks_from_dir(apks_dir_path)

    config: HybridAnalysisConfig = hybrid_config.get_default_hybrid_analysis_config()
    config.instrumentation_strategy = "StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy"
    decoded_apks_path = setup_additional_directories(experiment_dir_path, ["decoded-apks"])[0]
    config._decoded_apks_path = decoded_apks_path

    inputs_df = benchmark_df_base_from_batch_input_model(inputs_model)
    if apks_subset is not None:
        inputs_df = inputs_df.iloc[apks_subset]
    results_df = results_df_from_benchmark_df(inputs_df)

    apks = [inputs_df.loc[i, "Input Model"].apk() for i in inputs_df.index]

    reinstrument = True
    if reinstrument:
        decode.decode_batch(config, apks, clean=reinstrument)
        t0 = time.time()
        report_smali_LOC(results_df, inputs_df, decoded_apks_path, report_col="Smali LOC Before Instrumentation")

        instrument.instrument_batch(config, apks)
        report_smali_LOC(results_df, inputs_df, decoded_apks_path, report_col="Smali LOC After Instrumentation")

        results_df.loc[0, "Instrumentation Time (All APKs)"] = format_num_secs(time.time() - t0)

    # debug
    results_df.to_csv(os.path.join(experiment_dir_path, experiment_id + ".csv"))
    # end debug

    config._rebuilt_apks_path = setup_additional_directories(experiment_dir_path, ["rebuilt-apks"])[0]
    rebuild.rebuild_batch(config, apks, clean=False)
    
    config._keys_dir_path = setup_additional_directories(experiment_dir_path, ["keystores"])[0]
    keygen.generate_keys_batch(config, apks)
    
    config._signed_apks_path = setup_additional_directories(experiment_dir_path, ["signed-apks"])[0]
    sign.assign_key_batch(config, apks, clean=True)

    results_df.to_csv(os.path.join(experiment_dir_path, experiment_id + ".csv"))


# def results_df_from_apks_df(apks_df: pd.DataFrame) -> pd.DataFrame:
#     results_df = pd.DataFrame(apks_df["APK Name"])
#     results_df["Error Message"] = ""

#     return results_df

def report_smali_LOC(results_df: pd.DataFrame, apks_df: pd.DataFrame, decoded_apks_path: str, report_col: str):
    "return os.path.join(config._decoded_apks_path, apk.apk_name_no_suffix())"

    results_df[report_col] = 0

    for i in results_df.index:

        decoded_apk_dir_path = decoded_apk_path(decoded_apks_path, apks_df.loc[i, "Input Model"].apk())

        assert os.path.basename(decoded_apk_dir_path) == apks_df.loc[i, "Input Model"].apk().apk_name_no_suffix()

        #look for and count smali files
        smali_file_paths = []
        for smali_dir_path in instrument.DecodedApkModel.get_project_smali_directory_paths(decoded_apk_dir_path):
            smali_file_paths = instrument.DecodedApkModel.scan_for_smali_file_paths(smali_dir_path)

        """
        -JXmx256M
        -Xmx1g
        """

        for smali_file_path in smali_file_paths:
            results_df.loc[i, report_col] += count_smali_LOC(smali_file_path)

def count_smali_LOC(smali_file_path: str) -> int:
    
    count = 0
    with open(smali_file_path, 'r') as file:
        for line in file.readlines():
            if line.strip() != "":
                count += 1

    return count



    
