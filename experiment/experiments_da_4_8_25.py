

import os
import time
from typing import Callable, List

import pandas as pd
from experiment import batch
from experiment import common
from experiment.batch import LAST_ERROR_COLUMN, ExperimentStepException, process_as_dataframe
from hybrid import hybrid_config
from hybrid.dynamic import ExecutionObservation, LogcatLogFileModel
from intercept import instrument
from experiment.benchmark_name import BenchmarkName, lookup_benchmark_name
from experiment.common import format_num_secs, get_experiment_name, instrumentation_arguments_default, setup_additional_directories, setup_experiment_dir
from experiment.instrument import InstrumentationApproach, report_smali_LOC, setup_dynamic_value_analysis_strategies
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from intercept import decode, keygen, rebuild, sign
import intercept
from intercept.decoded_apk_model import DecodedApkModel
from intercept.install import check_device_is_ready, clean_apps_off_phone, get_package_name, install_apk
from intercept.monkey import test_apk_method_factory
from util.input import ApkModel, InputModel

import util.logger
logger = util.logger.get_logger(__name__)

def instrument_benchmark_apps_all():
    for benchmark_name, instrumentation_approach in [
        # (BenchmarkName.GPBENCH, InstrumentationApproach.SHALLOW_ARGS),
        # (BenchmarkName.FOSSDROID, InstrumentationApproach.SHALLOW_ARGS),
        (BenchmarkName.FOSSDROID, InstrumentationApproach.INTERCEPT_ARGS),
    ]:
        instrument_benchmark_apps(benchmark_name, instrumentation_approach)

def instrument_benchmark_apps(benchmark_name: BenchmarkName, instrumentation_approach: 'InstrumentationApproach'):

    benchmark_files = get_wild_benchmarks(benchmark_name)[0]

    # df_file_paths = get_wild_benchmarks(benchmark_name)[0]
    instrumentation_strategies = setup_dynamic_value_analysis_strategies(instrumentation_approach, benchmark_name)

    params_in_name = [instrumentation_approach.value]
    experiment_name = get_experiment_name(benchmark_name.value, "instrument-for-DA", (0,1,2), params_in_name, date_override="2025-04-18")
    experiment_description = """Instrument apps for subsequent dynamic analysis.
    Apps are instrumented to detect ad hoc values according to the logic in HeapSnapshot
    Additionally, selected sources are also harnessed so we know whenever they are triggered during execution. 
    In the intercept case, this source harnessing also replaces the values with different known values. 

    1.2 Fixed sources not getting loaded & instrumented
    """

    _, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                            benchmark_files | {"instrumentation_approach": instrumentation_approach.value},)


    df = LoadBenchmark(benchmark_files).execute()


    decoded_apks_directory_path = setup_additional_directories(experiment_dir_path, ["decoded-apks"])[0]

    # results_df = results_df_from_benchmark_df(benchmark_df)

    # apks = [benchmark_df.loc[i, "Input Model"].apk() for i in benchmark_df.index]
    df["Apk Model"] = df["Input Model"].apply(lambda x: x.apk())
    df["Apk Name"] = df["Input Model"].apply(lambda x: x.apk().apk_name)    
    results_df = pd.DataFrame(index=df.index, data={"Apk Name": df["Apk Name"].values})

    reinstrument = True
    if reinstrument:
        decode.decode_batch(decoded_apks_directory_path, df["Apk Model"], clean=reinstrument)
        t0 = time.time()
        
        report_smali_LOC(results_df, df, decoded_apks_directory_path, report_col="Smali LOC Before Instrumentation")

        # instrument_batch(decoded_apks_directory_path, instrumentation_strategies, df["Apk Model"])
        def instrument_timed(_decoded_apks_directory_path, _instrumenters, _apk):
            single_t0 = time.time()
            decoded_apk = DecodedApkModel(hybrid_config.decoded_apk_path(_decoded_apks_directory_path, _apk))
            decoded_apk.instrument(_instrumenters)
            return time.time() - single_t0
        instrument_timed_batch = process_as_dataframe(instrument_timed, [False, False, True], [])
        instrument_timed_batch(decoded_apks_directory_path, instrumentation_strategies, "Apk Model", input_df=df, output_col="Instrumentation Time (Seconds)")

        results_df["Instrumentation Time (Seconds)"] = df["Instrumentation Time (Seconds)"]

        report_smali_LOC(results_df, df, decoded_apks_directory_path, report_col="Smali LOC After Instrumentation")

        results_df.loc[0, "Instrumentation Time (All APKs)"] = format_num_secs(time.time() - t0)

    rebuilt_apks_directory_path, keys_directory_path, signed_apks_directory_path = setup_additional_directories(experiment_dir_path, ["rebuilt-apks", "keystores", "signed-apks"])
    rebuild.rebuild_batch(decoded_apks_directory_path, rebuilt_apks_directory_path, df["Apk Model"], clean=True)
    keygen.generate_keys_batch(keys_directory_path, df["Apk Model"])
    sign.assign_key_batch(signed_apks_directory_path, rebuilt_apks_directory_path, keys_directory_path, df["Apk Model"], clean=True)

    results_df.to_csv(os.path.join(experiment_dir_path, experiment_name + ".csv"))

def get_instrumented_apps_directory_path(benchmark_name: BenchmarkName, instrumentation_approach: 'InstrumentationApproach'):
    match benchmark_name:
        case BenchmarkName.GPBENCH:
            assert instrumentation_approach == InstrumentationApproach.SHALLOW_ARGS
            return "data/experiments/2025-04-18_instrument-for-DA_gpbench_0.1.2_shallow-args/signed-apks"
        case BenchmarkName.FOSSDROID:
            match instrumentation_approach:
                case InstrumentationApproach.SHALLOW_ARGS:
                    return "data/experiments/2025-04-18_instrument-for-DA_fossdroid_0.1.2_shallow-args/signed-apks"
                case InstrumentationApproach.INTERCEPT_ARGS:
                    return "data/experiments/2025-04-18_instrument-for-DA_fossdroid_0.1.2_intercept-args/signed-apks"
                case _:
                    raise NotImplementedError()
        case _:
            raise NotImplementedError()

    # "data/experiments/2025-04-08_instrument-for-DA_gpbench_0.1.1_shallow-args/signed-apks"
    # "data/experiments/2025-04-09_instrument-for-DA_fossdroid_0.1.1_intercept-args/signed-apks"
    # "data/experiments/2025-04-09_instrument-for-DA_fossdroid_0.1.1_shallow-args/signed-apks"

def _4_8_25_dynamic_experiments_main():
    check_device_is_ready()
    # uninstall_all_3rd_party_apps()

    # install_apps_selected_experiment(BenchmarkName.GPBENCH, InstrumentationApproach.SHALLOW_ARGS)
    run_apps_selected_experiment(BenchmarkName.GPBENCH, InstrumentationApproach.SHALLOW_ARGS, "manual")
    uninstall_all_3rd_party_apps()

    # install_apps_selected_experiment(BenchmarkName.FOSSDROID, InstrumentationApproach.SHALLOW_ARGS)
    # run_apps_selected_experiment(BenchmarkName.FOSSDROID, InstrumentationApproach.SHALLOW_ARGS, "monkey")
    # uninstall_all_3rd_party_apps()

    # install_apps_selected_experiment(BenchmarkName.FOSSDROID, InstrumentationApproach.INTERCEPT_ARGS)
    # run_apps_selected_experiment(BenchmarkName.FOSSDROID, InstrumentationApproach.INTERCEPT_ARGS, "monkey")
    # uninstall_all_3rd_party_apps()


def install_apps_selected_experiment(benchmark, instrumentation_approach: 'InstrumentationApproach'):

    # Install apps
    # benchmark_description_csv_path = benchmark_description_path_from_benchmark_files(benchmark_files)
    # inputs_df = benchmark_df_from_benchmark_directory_path(benchmark_files["benchmark_dir_path"], benchmark_description_csv_path=benchmark_description_csv_path, ids_subset=ids_subset)
    benchmark_files = get_wild_benchmarks(benchmark)[0]
    inputs_df = LoadBenchmark(benchmark_files).execute()

    apks_to_test_directory_path = get_instrumented_apps_directory_path(benchmark, instrumentation_approach)

    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()
        apk_to_install_path = hybrid_config.apk_path(apks_to_test_directory_path, apk_model)
        if os.path.exists(apk_to_install_path):
            install_apk(apk_to_install_path)
        else:
            logger.error(f"Path {apk_to_install_path} doesn't exist")

def run_apps_selected_experiment(benchmark, instrumentation_approach: 'InstrumentationApproach', execution_approach: str):

    # check that apps are installed? nah
    benchmark_files = get_wild_benchmarks(benchmark)[0]

    # execution_input_approach = "monkey"
    # execution_input_approach = "manual"
    test_apk_kwargs = {"seconds_to_test": 5}

    apks_to_test_directory_path = get_instrumented_apps_directory_path(benchmark, instrumentation_approach)

    experiment_name = get_experiment_name(benchmark.value, "execution", (0,1,1), [instrumentation_approach.value, execution_approach], date_override="")
    experiment_description = """
"""
    experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                                {"apks_to_test_directory_path": apks_to_test_directory_path, 
                                                                    } | benchmark_files | test_apk_kwargs)


    logcat_output_dir_path = setup_additional_directories(experiment_directory_path, ["logcat-output"])[0]

    inputs_df = LoadBenchmark(benchmark_files).execute()

    # takes apk models (for the apk to be TESTED!) and output path for logcat
    test_apk: Callable[ApkModel, str] = test_apk_method_factory(execution_approach, test_apk_kwargs)

    inputs_df["Apk Model"] = inputs_df["Input Model"].apply(lambda x: x.apk())
    process_as_dataframe(load_apps_single, [False, True], [])(apks_to_test_directory_path, "Apk Model", input_df=inputs_df, output_col="Instrumented Apk Model")


    mask = inputs_df[LAST_ERROR_COLUMN] == ""
    inputs_df["Instrumented APK Path"] = inputs_df[mask]["Instrumented Apk Model"].apply(lambda x: hybrid_config.apk_path(apks_to_test_directory_path, x))
    # get_package_name(apk_path, output_apk_model: ApkModel=None)
    process_as_dataframe(get_package_name, [True, True], [])("Instrumented APK Path", "Instrumented Apk Model", input_df=inputs_df, output_col="")

    inputs_df.drop(columns=["Instrumented APK Path"], inplace=True)

    
    # test_apk(apk_model, logcat_output_path)
    def timed_test_apk(apk_model: ApkModel, logcat_output_path: str):
        t0 = time.time()
        test_apk(apk_model, logcat_output_path)
        return time.time() - t0
    
    process_as_dataframe(hybrid_config.apk_logcat_output_path, [False, True], [False])(logcat_output_dir_path, "Input Model", input_df=inputs_df, output_col="Logcat Output Path")
    process_as_dataframe(timed_test_apk, [True, True], [])("Instrumented Apk Model", "Logcat Output Path", input_df=inputs_df, output_col="Test Time (Seconds)")

    # TODO: This should probably be in a results_df
    # logger.info(f"APK {apk_model.apk_package_name} tested for {format_num_secs(int(time.time() - t0))} (wall clock time)")

    inputs_df["Apk Name"] = inputs_df["Input Model"].apply(lambda x: x.apk().apk_name)
    # inputs_df["Test Time (Seconds)"] = inputs_df["Test Time (Seconds)"].apply(lambda x: format_num_secs(int(x)))
    report_cols = ["Apk Name", "Test Time (Seconds)", "Logcat Output Path", batch.LAST_ERROR_COLUMN]
    inputs_df[report_cols].to_csv(os.path.join(experiment_directory_path, f"execution-times.csv"))


# process_as_dataframe
def load_apps_single(target_apks_directory: str, original_apk_model: ApkModel) -> ApkModel:

    apk_path = hybrid_config.apk_path(target_apks_directory, original_apk_model)
    
    if not os.path.exists(apk_path):
        logger.error(f"APK {original_apk_model.apk_package_name} not found at {apk_path}")
        raise ExperimentStepException(f"APK {original_apk_model.apk_package_name} not found at {apk_path}")
    
    return ApkModel(apk_path)

def initial_observation_reports_all_executions():
    # grab for all experiments with "execution" in name

    experiments_directory = "data/experiments"

    summaries_directory = os.path.join(experiments_directory, "observation-reports")
    if not os.path.isdir(summaries_directory):
        os.makedirs(summaries_directory)

    for item in os.listdir(experiments_directory):
        if not "execution" in item:
            continue

        da_results_directory = os.path.join(experiments_directory, item, "logcat-output")

        benchmark = lookup_benchmark_name(da_results_directory)
        benchmark_files = get_wild_benchmarks(benchmark)[0]
        df = LoadBenchmark(benchmark_files).execute()
        
        common.load_logcat_files_batch(da_results_directory, "Input Model", df, output_col="logcat_file")

        df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
        summary_table = pd.DataFrame({"App Name": df["Input Model Identifier"]}, index=df.index)
 
        logcat_available = (df["logcat_file"] != "")
        summary_table["DA Available"] = logcat_available

        # instrumentation_report_details_directory, observed_intermediate_sources_details_directory, harness_source_calls_details_directory = setup_additional_directories(workdir, ["instrumentation_report_details", "observed_intermediate_sources_details", "harnessed_source_calls_details"])    

        for i in df[logcat_available].index:

            logcat_model = LogcatLogFileModel(df.at[i, "logcat_file"])
            
            instrumentation_report_tuples: List = logcat_model.scan_log_for_instrumentation_report_tuples()        
            summary_table.at[i, "Count Instrumentation Reports"] = len(instrumentation_report_tuples)

            source_calls: List = logcat_model.scan_log_for_harnessed_source_calls()
            summary_table.at[i, "Count Observed Source Calls"] = len(source_calls)

            observation = ExecutionObservation()
            list(map(observation.parse_instrumentation_result, instrumentation_report_tuples))
            tainting_invocation_contexts, contexts_strings = observation.get_tainting_invocation_contexts(with_observed_strings=True)

            summary_table.at[i, "Count Tainting Contexts"] = len(tainting_invocation_contexts)


        summary_table.to_csv(os.path.join(summaries_directory, f"{item}-summary.csv"))




def uninstall_all_3rd_party_apps():
    clean_apps_off_phone()