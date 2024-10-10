

import os
import time
from typing import Dict, List

import pandas as pd
from experiment import external_path
from experiment.common import get_wild_benchmarks
from experiment.common import benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, format_num_secs, get_project_root_path, results_df_from_benchmark_df, setup_additional_directories, setup_experiment_dir
from hybrid import hybrid_config
from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from intercept import decode, instrument, intercept_main, keygen, rebuild, sign
from util.input import ApkModel, input_apks_from_dir

import util.logger
from util.subprocess import run_command
logger = util.logger.get_logger(__name__)


def instrument_test_wild_benchmarks_few():
    apks_subset = [1, 2]
    # apks_subset = [0]
    instrument_test_wild_benchmarks(apks_subset, "small")
    
def instrument_test_wild_benchmarks_full():
    apks_subset = None
    instrument_test_wild_benchmarks(apks_subset, "full")

def instrument_test_wild_benchmarks(apks_subset: List[int], size: str):
    # for apks_dir_path, name in [(fossdroid_apks_dir, "fossdroid"), (gpbench_apks_dir, "gpbench")]:
    for benchmark_files in get_wild_benchmarks():
        name = benchmark_files["benchmark_name"]
        apks_dir_path = benchmark_files["benchmark_dir_path"]
        description = f"Testing instrumentation on {name} benchmark"
        instrument_test_generic(benchmark_files, f"instrument-{size}-{name}", description, apks_subset)

def instrument_test_generic(benchmark_files: Dict[str, str], experiment_name: str, experiment_description: str, apks_subset: List[int]):
    instrumentation_strategy = "StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy"

    # eventually may want to support benchmark description csv
    benchmark_directory_path = benchmark_files["benchmark_dir_path"]
    always_new_experiment_directory = False

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, benchmark_files, always_new_experiment_directory)

    decoded_apks_directory_path = setup_additional_directories(experiment_dir_path, ["decoded-apks"])[0]
    # config._decoded_apks_path = decoded_apks_directory_path
    benchmark_description_csv_path = ("" if "benchmark_description_path" not in benchmark_files.keys() else benchmark_files["benchmark_description_path"])
    inputs_df = benchmark_df_from_benchmark_directory_path(benchmark_directory_path, benchmark_description_csv_path=benchmark_description_csv_path, ids_subset=apks_subset)

    results_df = results_df_from_benchmark_df(inputs_df)


    apks = [inputs_df.loc[i, "Input Model"].apk() for i in inputs_df.index]

    reinstrument = True
    if reinstrument:
        decode.decode_batch(decoded_apks_directory_path, apks, clean=reinstrument)
        t0 = time.time()
        report_smali_LOC(results_df, inputs_df, decoded_apks_directory_path, report_col="Smali LOC Before Instrumentation")

        instrument.instrument_batch(decoded_apks_directory_path, instrumentation_strategy, apks)
        report_smali_LOC(results_df, inputs_df, decoded_apks_directory_path, report_col="Smali LOC After Instrumentation")

        results_df.loc[0, "Instrumentation Time (All APKs)"] = format_num_secs(time.time() - t0)

    # debug
    results_df.to_csv(os.path.join(experiment_dir_path, experiment_id + ".csv"))
    # end debug

    rebuilt_apks_directory_path = setup_additional_directories(experiment_dir_path, ["rebuilt-apks"])[0]
    rebuild.rebuild_batch(decoded_apks_directory_path, rebuilt_apks_directory_path, apks, clean=True)
    
    keys_directory_path = setup_additional_directories(experiment_dir_path, ["keystores"])[0]
    keygen.generate_keys_batch(keys_directory_path, apks)
    
    signed_apks_directory_path = setup_additional_directories(experiment_dir_path, ["signed-apks"])[0]
    sign.assign_key_batch(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, apks, clean=True)

    results_df.to_csv(os.path.join(experiment_dir_path, experiment_id + ".csv"))

def rebuild_apps_no_instrumentation(apks_dir_path: str, experiment_name: str, experiment_description: str, ids_subset: List[int]=None):
    benchmark_df: pd.DataFrame = benchmark_df_from_benchmark_directory_path(apks_dir_path, ids_subset=ids_subset)
    experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, {})

    apks = benchmark_df["Input Model"].apply(lambda input: input.apk()).values
    intercept_main.decompile_and_rebuild_apks(apks, experiment_directory_path)


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




def update_heap_snapshot_smali_files():
    """
    Decompile an apk from android studio and place some targeted smali files into
    intercept/smali-files/heap-snapshot. Replace existing files if necessary
    """
    experiment_id, experiment_dir_path = setup_experiment_dir("decompile-heap-snapshot", 
                                                              "Intermediate result, smali code for the currently built APK of HeapSnapshot", 
                                                              {}, 
                                                              always_new_experiment_directory=True)

    decompile_path = setup_additional_directories(experiment_dir_path, ["decompiled-smali"])[0]
    # configuration = intercept_config.get_default_intercept_config()
    # configuration.input_apks = input.input_apks_from_dir("HeapSnapshot/app/build/outputs/apk/debug")

    project_root = get_project_root_path()

        
    heap_snapshot_apk_path = os.path.join(project_root, "HeapSnapshot", "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    intercept_main.generate_smali_code(heap_snapshot_apk_path, decompile_path)

    heap_snapshot_apk_name = "app-debug"
    decompiled_apk_root_path = os.path.join(decompile_path, heap_snapshot_apk_name)

    extract_decompiled_smali_code_to_heap_snapshot(decompiled_apk_root_path)


def extract_decompiled_smali_code_to_heap_snapshot(decompiled_apk_root_path: str):

    output_smali_dir = "data/intercept/smali-files/heap-snapshot"

    input_directory_prefix = "smali_classes3" 
    input_directory_suffix = "edu/utsa/sefm/heapsnapshot" 
    files = ["Snapshot.smali", "Snapshot$FieldInfo.smali"]

    dest = os.path.join(output_smali_dir,
                        input_directory_suffix)
    
    src_files = [os.path.join(decompiled_apk_root_path, input_directory_prefix,
                              input_directory_suffix, file_name) for file_name in files]

    # TODO: this might not work in some cases
    if not os.path.isdir(dest):
        run_command(["mkdir", dest])

    # overwrite the existing files
    run_command(["cp"] + src_files + [dest], verbose=True)



    
