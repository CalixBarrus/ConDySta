

import os
import time
from typing import Callable, Dict, List
from experiment.benchmarks import recent_instrumented_apps_for_wild_benchmark
from experiment.common import benchmark_description_path_from_benchmark_files, benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, format_num_secs, get_fossdroid_files, get_wild_benchmarks, setup_additional_directories, setup_experiment_dir
from hybrid.hybrid_config import apk_logcat_output_path, apk_path
from intercept.install import check_device_is_ready, clean_apps_off_phone, get_package_name, install_apk, list_installed_3rd_party_apps, uninstall_apk
from intercept.monkey import _clear_logcat, _dump_logcat, force_stop_app, test_apk_manual, test_apk_method_factory, test_apk_monkey
from util.input import ApkModel, input_apks_from_dir

import util.logger
logger = util.logger.get_logger(__name__)

    # return [(instrumented_gpbench_apks_dir_path, "gpbench"), (instrumented_fossdroid_apks_dir_path, "fossdroid")]


def install_few_apps_for_integration_testing():
    apks_subset = [1, 2]
    install_apps_for_integration_testing(apks_subset, "small")

def install_all_apps_for_integration_testing():
    apks_subset = None
    install_apps_for_integration_testing(apks_subset, "full")

def install_apps_for_integration_testing(apks_subset: List[int], size: str):
    if not check_device_is_ready():
        raise AssertionError("ADB Can't find devices")

    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    for benchmark_files in get_wild_benchmarks():
        instrumented_apks_dir_path = recent_instrumented_apps_for_wild_benchmark(benchmark_files, size)

        # description = f"Running instrumented apps from {name} benchmark"
        install_apps(instrumented_apks_dir_path, benchmark_files, apks_subset)   



def install_original_fossdroid_apps(apks_subset=None):
    benchmark_files = get_fossdroid_files()
    fossdroid_apks_directory_path = benchmark_files["benchmark_dir_path"]

    install_apps(fossdroid_apks_directory_path, benchmark_files, ids_subset=apks_subset)


def monkey_test_few_apps_recording_output():
    apks_subset = [2,13]
    execute_apps_each_benchmark(apks_subset, "small", "monkey")

def monkey_test_all_apps_recording_output():
    apks_subset = None
    execute_apps_each_benchmark(apks_subset, "full", "monkey")

def manual_test_few_apps_recording_output():
    apks_subset = [1,2]
    execute_apps_each_benchmark(apks_subset, "small", "manual")

def manual_test_all_apps_recording_output():
    apks_subset = None
    execute_apps_each_benchmark(apks_subset, "full", "manual")

def test_apps_spot_check():
    pass

def execute_apps_each_benchmark(apks_subset: List[int], size_description: str, execution_input_approach: str):

    test_apk_method = test_apk_method_factory(execution_input_approach, {})

    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    for benchmark_files in get_wild_benchmarks():
        instrumented_apks_dir_path = recent_instrumented_apps_for_wild_benchmark(benchmark_files, size_description)

        name = benchmark_files["benchmark_name"]
        
        experiment_name = f"execution-{size_description}-{name}"
        description = f"Running instrumented apps from {name} benchmark"

        execute_apps_generic_experiment(instrumented_apks_dir_path, benchmark_files, experiment_name, description, apks_subset, test_apk_method)

    
    


def install_apps(apks_to_install_directory_path: str, benchmark_files: Dict[str, str], ids_subset: List[int]):

    benchmark_description_csv_path = benchmark_description_path_from_benchmark_files(benchmark_files)
    inputs_df = benchmark_df_from_benchmark_directory_path(benchmark_files["benchmark_dir_path"], benchmark_description_csv_path=benchmark_description_csv_path, ids_subset=ids_subset)

    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()
        apk_to_install_path = apk_path(apks_to_install_directory_path, apk_model)
        install_apk(apk_to_install_path)


def execute_apps_generic_experiment(apks_to_install_directory_path: str, benchmark_files: Dict[str, str], experiment_name: str, experiment_description: str, ids_subset: List[int], test_apk: Callable[[ApkModel, str], None]):
    """
    run some apps to check for run time errors due to instrumentation/recompilation
    """

    # TODO: in addition to apks_to_install_directory_path, other parameter is execution_input_approach. That dependency injection should occur inside this function, so it's args can be passed to setup_experiment_dir
    # That is, test_apk should be produce in this function according to some kwargs that get passed in.
    # combine apks_to_install_directory_path and benchmark_files?

    if not check_device_is_ready():
        raise AssertionError("ADB Can't find devices")

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {"apks_to_install_directory_path": apks_to_install_directory_path} | benchmark_files, True)

    benchmark_description_csv_path = benchmark_description_path_from_benchmark_files(benchmark_files)

    # benchmark_description_csv_path = ("" if "benchmark_description_path" in benchmark_files.keys() else benchmark_files["benchmark_description_path"])
    inputs_df = benchmark_df_from_benchmark_directory_path(benchmark_files["benchmark_dir_path"], benchmark_description_csv_path=benchmark_description_csv_path, ids_subset=ids_subset)


    logcat_output_dir_path = setup_additional_directories(experiment_dir_path, ["logcat-output"])[0]

    # Make sure all necessary apks are installed
    installed_package_names = list_installed_3rd_party_apps()
    seen_apk_packages = [] # keep track of this in case 2 Input Models refer to the same APK
    

    apks_to_skip: list[str] = []
    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()

        # This gets both the package name and apk label. 
        # TODO: the name of get_package needs to be updated, and the usages of the method needs to be standardized (?); manual apk testing has a dependency on this method's behavior.
        get_package_name(apk_model.apk_path, output_apk_model=apk_model)
        logger.debug(f"Looked up {apk_model.apk_package_name} and {apk_model.apk_application_label}")


        # install apk from specified directory (if apk with same package name is not installed already)
        if apk_model.apk_package_name not in installed_package_names and apk_model.apk_package_name not in seen_apk_packages:

            apk_to_install_path = apk_path(apks_to_install_directory_path, apk_model)

            if not os.path.isfile(apk_to_install_path):
                logger.error(f"Apk not found at {apk_to_install_path}; Check Instrumentation step. ")
                apks_to_skip.append(i)
                continue

            install_apk(apk_to_install_path)

            seen_apk_packages.append(apk_model.apk_package_name)


    for i in inputs_df.index:
        if i in apks_to_skip:
            continue

        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()
    
        # install_apk(apk_model.apk_path)
        logcat_output_path = apk_logcat_output_path(logcat_output_dir_path, inputs_df.loc[i, "Input Model"])

        t0 = time.time()
        test_apk(apk_model, logcat_output_path)

        # TODO: This should probably be in a results_df
        logger.info(f"APK {apk_model.apk_package_name} tested for {format_num_secs(int(time.time() - t0))} (wall clock time)")


def uninstall_all_3rd_party_apps():
    clean_apps_off_phone()


        




