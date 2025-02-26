

import os
import time
from typing import Dict, List

import pandas as pd
from experiment import external_path
from experiment.load_benchmark import get_wild_benchmarks
from experiment.batch import process_as_dataframe
from experiment.common import instrumentation_arguments_default, subset_setup_generic
from experiment.common import benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, format_num_secs, get_project_root_path, results_df_from_benchmark_df, setup_additional_directories, setup_experiment_dir
from experiment.flowdroid_experiment import experiment_setup
from experiment.paths import StepInfoInterface
from hybrid import hybrid_config
from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from hybrid.invocation_register_context import InvocationRegisterContext
from intercept import decode, instrument, intercept_main, keygen, rebuild, sign
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations, instrumentation_strategy_factory_wrapper
import intercept.smali
from util.input import ApkModel, input_apks_from_dir

import util.logger
from util.subprocess import run_command
logger = util.logger.get_logger(__name__)


def instrument_test_wild_benchmarks_few():
    instrument_test_wild_benchmarks("small")
    
def instrument_test_wild_benchmarks_full():
    instrument_test_wild_benchmarks("full")

def instrument_test_wild_benchmarks(size: str):

    # for apks_dir_path, name in [(fossdroid_apks_dir, "fossdroid"), (gpbench_apks_dir, "gpbench")]:
    for benchmark_files in get_wild_benchmarks():
        name = benchmark_files["benchmark_name"]
        # apks_dir_path = benchmark_files["benchmark_dir_path"]

        experiment_args = subset_setup_generic(benchmark_files, size)

        description = f"Testing instrumentation on {name} benchmark"
        experiment_arguments = instrument_arguments_setup_generic(experiment_args, f"instrument-{size}-{name}", description)
        instrument_experiment_generic(**experiment_arguments)

def instrument_arguments_setup_generic(benchmark_files: Dict[str, str], experiment_name: str, experiment_description: str) -> Dict[str, str]:
    # TODO This method is repeated code found elsewhere

    # instrumentation_strategy = "StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy"
    experiment_arguments = benchmark_files | instrumentation_arguments_default(benchmark_files)
    # instrumentation_strategy = experiment_arguments["instrumentation_strategy"]

    # eventually may want to support benchmark description csv
    # benchmark_directory_path = experiment_arguments["benchmark_dir_path"]
    # always_new_experiment_directory = False

    experiment_arguments["experiment_name"] = experiment_name
    experiment_arguments["experiment_description"] = experiment_description
    experiment_arguments["always_new_experiment_directory"] = False

    return experiment_arguments

# def instrument_observations_batch(instrumenter: HarnessObservations, observations: str, apk: str, decoded_apks_directory_path: str, rebuilt_apks_directory_path: str, 
#                                   input_df: pd.DataFrame, output_col="") -> pd.Series:
#     assert observations, apk in input_df.columns

#     if output_col != "":
#         if not output_col in input_df.columns:
#             input_df[output_col] = "" # or some other null value? 
#         else:
#             result_series = pd.Series(index=input_df.index)

#     for i in input_df.index:
#         result = instrument_observations_single(instrumenter, input_df.at[i, observations], input_df.at[i, apk], decoded_apks_directory_path, rebuilt_apks_directory_path)
#         if output_col != "":
#             input_df.at[i, output_col] = result
#         else:
#             result_series.at[i] = result

#     if output_col != "":
#         return None
#     else:
#         return result_series

def instrument_observations_single(instrumenter: HarnessObservations, observations: List[InvocationRegisterContext], apk: ApkModel, decoded_apks_directory_path: str, rebuilt_apks_directory_path: str) -> str:
    # # inputs
    # # experiment_dir_path = ""
    # # instrumentation_strategy = ""
    # instrumenter = HarnessObservations()
    # observations = ""
    # apk = ApkModel("") 
    # # intermediates
    # decoded_apks_directory_path = ""
    # # output
    # rebuilt_apks_directory_path = "" 

    decode.decode_apk(decoded_apks_directory_path, apk, clean=True)
    
    decoded_apk = DecodedApkModel(hybrid_config.decoded_apk_path(decoded_apks_directory_path, apk))
    instrumenter.set_observations(observations)
    decoded_apk.instrument([instrumenter])

    rebuild.rebuild_apk(decoded_apks_directory_path, rebuilt_apks_directory_path, apk, clean=True)
    # TODO: do we even need to sign them for FD to analyze them? 
    # keygen.generate_keys_batch(keys_directory_path, apks)
    # sign.assign_key_batch(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, apks, clean=True)

    return hybrid_config.apk_path(rebuilt_apks_directory_path, apk)

instrument_observations_batch = process_as_dataframe(instrument_observations_single, [False, True, True, False, False], [])

def instrument_experiment_generic(**kwargs):
    # TODO: this needs to get moved to a different file maybe (instrument_experiment??). Is this using the same setup/tear down automation as flowdroid experiments??
    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**kwargs)

    decoded_apks_directory_path = setup_additional_directories(experiment_dir_path, ["decoded-apks"])[0]

    results_df = results_df_from_benchmark_df(benchmark_df)

    instrumentation_strategy = instrumentation_strategy_factory_wrapper(**kwargs)

    apks = [benchmark_df.loc[i, "Input Model"].apk() for i in benchmark_df.index]

    reinstrument = True
    if reinstrument:
        decode.decode_batch(decoded_apks_directory_path, apks, clean=reinstrument)
        t0 = time.time()
        report_smali_LOC(results_df, benchmark_df, decoded_apks_directory_path, report_col="Smali LOC Before Instrumentation")

        instrument.instrument_batch(decoded_apks_directory_path, instrumentation_strategy, apks)
        report_smali_LOC(results_df, benchmark_df, decoded_apks_directory_path, report_col="Smali LOC After Instrumentation")



        results_df.loc[0, "Instrumentation Time (All APKs)"] = format_num_secs(time.time() - t0)

    rebuilt_apks_directory_path, keys_directory_path, signed_apks_directory_path = setup_additional_directories(experiment_dir_path, ["rebuilt-apks", "keystores", "signed-apks"])
    rebuild.rebuild_batch(decoded_apks_directory_path, rebuilt_apks_directory_path, apks, clean=True)
    keygen.generate_keys_batch(keys_directory_path, apks)
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
        for smali_dir_path in intercept.smali.DecodedApkModel.get_project_smali_directory_paths(decoded_apk_dir_path):
            smali_file_paths = intercept.smali.DecodedApkModel.scan_for_smali_file_paths(smali_dir_path)

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
                                                              always_new_experiment_directory=False)

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



    
