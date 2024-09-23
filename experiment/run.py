

import os
from typing import List
from experiment.common import benchmark_df_base_from_batch_input_model, setup_additional_directories, setup_experiment_dir
from hybrid.hybrid_config import apk_logcat_output_path
from intercept.install import check_device_is_ready, get_package_name, install_apk, list_installed_3rd_party_apps, uninstall_apk
from intercept.monkey import _clear_logcat, _dump_logcat, test_apk_monkey
from util.input import ApkModel, input_apks_from_dir

instrumented_fossdroid_apks_dir_path = "/home/calix/programming/ConDySta/data/experiments/2024-09-19-instrument-test-fossdroid/signed-apks"

instrumented_gpbench_apks_dir_path = "/home/calix/programming/ConDySta/data/experiments/2024-09-19-instrument-test-gpbench/signed-apks"





def monkey_test_few_apps_for_verify_errors():
    apks_subset = [0,1]
    apks_subset = [0]
    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid")]:
        description = f"Running instrumented apps from {name} benchmark"
        run_apps_for_integration_testing_generic(instrumented_apks_dir_path, "execution-test-small-" + name, description, apks_subset)

def monkey_test_all_apps_for_verify_errors():
    apks_subset = None
    for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid")]:
        description = f"Running instrumented apps from {name} benchmark"
        run_apps_for_integration_testing_generic(instrumented_apks_dir_path, "execution-test-full-" + name, description, apks_subset)


def install_few_apps_for_integration_testing():
    apks_subset = [0]
    if not check_device_is_ready():
        raise AssertionError("FD Can't find devices")

    # for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
    for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid")]:
        # description = f"Running instrumented apps from {name} benchmark"
        install_apps(instrumented_apks_dir_path, apks_subset)    


def record_manual_interactions():
    if not check_device_is_ready():
        raise AssertionError("FD Can't find devices")

    experiment_id, experiment_dir_path = setup_experiment_dir("manual-execution-recording", "Logcat is recording manual interaction with the phone.", {}, always_new_experiment_directory=True)

    logcat_output_dir_path = setup_additional_directories(experiment_dir_path, ["logcat-output"])[0]

    _clear_logcat()

    input("Press Any Key when finished")

    _dump_logcat(os.path.join(logcat_output_dir_path, "manual-interaction.log"))
    
    


def install_apps(apks_dir_path, apks_subset):
    inputs_model = input_apks_from_dir(apks_dir_path)
    inputs_df = benchmark_df_base_from_batch_input_model(inputs_model)

    if apks_subset is not None:
        inputs_df = inputs_df.iloc[apks_subset]

    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()

        install_apk(apk_model.apk_path)


def run_apps_for_integration_testing_generic(apks_dir_path: str, experiment_name: str, experiment_description: str, apks_subset: List[int]):
    """
    run some apps to check for run time errors due to instrumentation/recompilation
    """

    inputs_model = input_apks_from_dir(apks_dir_path)

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {"apks_dir_path": apks_dir_path}, False)

    inputs_df = benchmark_df_base_from_batch_input_model(inputs_model)

    # inputs_df["Package Name"] = ""

    if apks_subset is not None:
        inputs_df = inputs_df.iloc[apks_subset]

    logcat_output_dir_path = setup_additional_directories(experiment_dir_path, ["logcat-output"])[0]

    installed_package_names = list_installed_3rd_party_apps()
    seen_apk_packages = [] # keep track of this in case 2 Input Models refer to the same APK
    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()

        # apks_df.loc[i, "APK Package Name"] = get_package_name(apk_model.apk_path)
        apk_package_name = get_package_name(apk_model.apk_path, apk_model=apk_model)
        apk_model.apk_package_name = apk_package_name

        # install apk if not installed already
        if apk_model.apk_package_name not in installed_package_names and apk_model.apk_package_name not in seen_apk_packages:
            install_apk(apk_model.apk_path)
            seen_apk_packages.append(apk_model.apk_package_name)


    for i in inputs_df.index:
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()
    
        # install_apk(apk_model.apk_path)

        test_apk_monkey(apk_model.apk_package_name, seconds_to_test=5, logcat_output_path=apk_logcat_output_path(logcat_output_dir_path, inputs_df.loc[i, "Input Model"]))

        # uninstall_apk(apk_package_name)



        




