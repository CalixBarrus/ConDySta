

from typing import List
from experiment.common import benchmark_df_base_from_batch_input_model, setup_additional_directories, setup_experiment_dir
from hybrid.hybrid_config import apk_logcat_output_path
from intercept.install import check_device_is_ready, get_package_name, install_apk, uninstall_apk
from intercept.monkey import test_apk_monkey
from util.input import ApkModel, input_apks_from_dir

instrumented_fossdroid_apks_dir_path = "/home/calix/programming/ConDySta/data/experiments/2024-09-18-instrument-test-fossdroid/signed-apks"

instrumented_gpbench_apks_dir_path = "/home/calix/programming/ConDySta/data/experiments/2024-09-18-instrument-test-gpbench/signed-apks"


apks_subset = [0,1]
# apks_subset = None

def run_apps_for_integration_testing():

    for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
        description = f"Running instrumented apps from {name} benchmark"
        run_apps_for_integration_testing_generic(instrumented_apks_dir_path, "execution-test-" + name, description, apks_subset)

def install_apps_for_integration_testing():
    if not check_device_is_ready():
        raise AssertionError("FD Can't find devices")

    for instrumented_apks_dir_path, name in [(instrumented_fossdroid_apks_dir_path, "fossdroid"), (instrumented_gpbench_apks_dir_path, "gpbench")]:
        # description = f"Running instrumented apps from {name} benchmark"
        install_apps(instrumented_apks_dir_path, apks_subset)

    
    


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

    for i in inputs_df.index:
        
        apk_model: ApkModel = inputs_df.loc[i, "Input Model"].apk()

        # apks_df.loc[i, "APK Package Name"] = get_package_name(apk_model.apk_path)
        apk_package_name = get_package_name(apk_model.apk_path)
    
        # install_apk(apk_model.apk_path)

        test_apk_monkey(apk_package_name, seconds_to_test=10, logcat_output_path=apk_logcat_output_path(logcat_output_dir_path, inputs_df.loc[i, "Input Model"]))

        uninstall_apk(apk_package_name)


        




