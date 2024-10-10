

import os
from typing import Callable, Dict, List
from experiment.benchmarks import recent_instrumented_apps_for_wild_benchmark
from experiment.common import benchmark_description_path_from_benchmark_files, benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, get_fossdroid_files, get_wild_benchmarks, setup_additional_directories, setup_experiment_dir
from hybrid.hybrid_config import apk_logcat_output_path, apk_path
from intercept.install import check_device_is_ready, clean_apps_off_phone, get_package_name, install_apk, list_installed_3rd_party_apps, uninstall_apk
from intercept.monkey import _clear_logcat, _dump_logcat, force_stop_app, test_apk_manual, test_apk_monkey
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


def monkey_test_few_apps_for_verify_errors():
    apks_subset = [1,2]
    monkey_test_for_verify_errors(apks_subset, "small")

def monkey_test_all_apps_for_verify_errors():
    apks_subset = None
    monkey_test_for_verify_errors(apks_subset, "full")

def monkey_test_for_verify_errors(apks_subset: List[int], size_description: str):
    f = lambda apk_model, logcat_output_path: test_apk_monkey(apk_model, seconds_to_test=5, logcat_output_path=logcat_output_path, force_stop_when_finished=True)
    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    for benchmark_files in get_wild_benchmarks():
        instrumented_apks_dir_path = recent_instrumented_apps_for_wild_benchmark(benchmark_files, size_description)

        name = benchmark_files["benchmark_name"]
        description = f"Running instrumented apps from {name} benchmark"
        experiment_name = f"execution-{size_description}-{name}"



        run_apps_for_integration_testing_generic(instrumented_apks_dir_path, benchmark_files, experiment_name, description, apks_subset, f)



def record_manual_interactions(output_file_name: str = ""):
    if not check_device_is_ready():
        raise AssertionError("FD Can't find devices")

    experiment_id, experiment_dir_path = setup_experiment_dir("manual-execution-recording", "Logcat is recording manual interaction with the phone.", {}, always_new_experiment_directory=False)

    logcat_output_dir_path = setup_additional_directories(experiment_dir_path, ["logcat-output"])[0]

    _clear_logcat()

    input("Press Any Key when finished")

    _dump_logcat(os.path.join(logcat_output_dir_path, ("manual-interaction.log" if output_file_name == "" else output_file_name)))
    
    


def install_apps(apks_to_install_directory_path: str, benchmark_files: Dict[str, str], ids_subset: List[int]):

    benchmark_description_csv_path = benchmark_description_path_from_benchmark_files(benchmark_files)
    inputs_df = benchmark_df_from_benchmark_directory_path(benchmark_files["benchmark_dir_path"], benchmark_description_csv_path=benchmark_description_csv_path, ids_subset=ids_subset)

    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()
        apk_to_install_path = apk_path(apks_to_install_directory_path, apk_model)
        install_apk(apk_to_install_path)


def run_apps_for_integration_testing_generic(apks_to_install_directory_path: str, benchmark_files: Dict[str, str], experiment_name: str, experiment_description: str, ids_subset: List[int], test_apk_generic: Callable[[ApkModel, str], None]):
    """
    run some apps to check for run time errors due to instrumentation/recompilation
    """

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

        # apks_df.loc[i, "APK Package Name"] = get_package_name(apk_model.apk_path)
        # apk_package_name = get_package_name(apk_model.apk_path, output_apk_model=apk_model)
        # apk_model.apk_package_name = apk_package_name
        get_package_name(apk_model.apk_path, output_apk_model=apk_model)


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


        test_apk_generic(apk_model, logcat_output_path)

        # test_apk_monkey(apk_model, seconds_to_test=5, logcat_output_path=logcat_output_path, force_stop_when_finished=True)

        # test_apk_manual(apk_model, seconds_to_test=5, logcat_output_path=logcat_output_path, force_stop_when_finished=True)

        

        # uninstall_apk(apk_package_name)

def uninstall_all_3rd_party_apps():
    clean_apps_off_phone()


        




