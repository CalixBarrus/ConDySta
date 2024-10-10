
import os
from subprocess import CalledProcessError, TimeoutExpired
import time
from typing import Dict, List
import typing

import numpy as np

from experiment import external_path
from experiment.common import benchmark_df_base_from_batch_input_model, get_flowdroid_file_paths, format_num_secs, get_gpbench_files, setup_additional_directories, setup_dirs_with_ic3, setup_experiment_dir
from experiment.flowdroid_experiment import experiment_setup_and_teardown_temp, flowdroid_experiment, groundtruth_df_from_xml, process_results_from_fd_log_single, results_df_from_benchmark_df
import hybrid
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid, run_flowdroid_help, run_flowdroid_paper_settings, run_flowdroid_with_fdconfig
from hybrid.ic3 import run_ic3_on_apk, run_ic3_script_on_apk
from hybrid.log_process_fd import get_flowdroid_reported_leaks_count
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import create_source_sink_file_ssgpl
from util.input import BatchInputModel, InputModel, input_apks_from_dir
from util.subprocess import run_command_direct

import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)

def gpbench_main():
    # benchmark_folder_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/gpbench/apks"
    benchmark_folder_path: str = external_path.gpbench_apks_dir_path

    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    # flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"

    # android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    android_path: str = "/home/calix/.android_sdk/platforms"
    

    gpbench_dir_path: str = "/home/calix/programming/benchmarks/ggplay/apks"

    # ic3_jar_path = "/home/calix/programming/ic3/target/ic3-0.2.1-full.jar"
    # ic3_jar_path: str = "/home/calix/programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"

    ic3_script_root_path: str = "/home/calix/programming/IC3"

    ground_truth_xml_path = "/home/calix/programming/benchmarks/wild-apps/gpbench_ground_truth.xml"
    gpbench_description_path = "data/benchmark-descriptions/gpbench-info.csv"

    # single_gpbench_experiment(flowdroid_jar_path=flowdroid_jar_path, android_path=android_path, benchmark_dir_path=benchmark_folder_path, ground_truth_xml_path=ground_truth_xml_path, benchmark_description_path=gpbench_description_path)
    # gbpench_experiment_1hr_fd_configs(flowdroid_jar_path=flowdroid_jar_path, android_path=android_path, benchmark_dir_path=benchmark_folder_path, ground_truth_xml_path=ground_truth_xml_path, benchmark_description_path=gpbench_description_path)
    gpbench_experiment_test_fd_configs(flowdroid_jar_path=flowdroid_jar_path, android_path=android_path, benchmark_dir_path=benchmark_folder_path, ground_truth_xml_path=ground_truth_xml_path, benchmark_description_path=gpbench_description_path)

#### Start gpbench Settings Hierarchy

def gpbench_experiment_setup_base() -> Dict[str, typing.Any]:
    file_paths = get_gpbench_files()
    experiment_args = file_paths.copy()

    experiment_args = experiment_args | get_flowdroid_file_paths()

    flowdroid_args = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified) 
    # flowdroid_args = FlowdroidArgs.best_fossdroid_settings
    experiment_args["flowdroid_args"] = flowdroid_args
    experiment_args["always_new_experiment_directory"] = False
    experiment_args["source_sink_list_path"] = check_ssgpl_list()
    return experiment_args

def gpbench_experiment_setup_test(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = gpbench_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([0, 1])
    experiment_args["experiment_name"] = "fd-on-gpbench-test"
    experiment_args["experiment_description"] = "Run Flowdroid on a few Google Play Bench apps"
    return experiment_args

def gpbench_experiment_setup_full(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = gpbench_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 60 * 60
    experiment_args["ids_subset"] = pd.Series(range(1,20))
    experiment_args["experiment_name"] = "fd-on-gpbench-login"
    experiment_args["experiment_description"] = "Run Flowdroid on Google Play Bench Login Scenario"
    return experiment_args

#### End gpbench Settings Hierarchy

#### Start Actual Experiment end points

def flowdroid_on_gpbench_test():
    experiment_args = gpbench_experiment_setup_test()

    experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)


def gbpench_experiment_1hr_fd_configs():
    timeout = 60 * 60
    ids_subset = None
    gbpench_experiment_fd_configs(timeout=timeout, ids_subset=ids_subset, experiment_name_suffix="full")


def gpbench_experiment_test_fd_configs():
    timeout =  15 * 60
    ids_subset = [2,3,4,5]
    gbpench_experiment_fd_configs(timeout=timeout, ids_subset=ids_subset, experiment_name_suffix="test")


def gbpench_experiment_fd_configs(timeout=60*60, ids_subset=None, experiment_name_suffix="full"):

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings), 
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified), 
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:

        experiment_args = gpbench_experiment_setup_full()
        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-gpbench-{experiment_name_suffix}-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the {experiment_name_suffix} GP Bench dataset with {settings_description_suffix}"
        experiment_args["timeout"] = timeout
        experiment_args["ids_subset"] = ids_subset

        experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)

"""
def ic3_linux():
    android_path: str = "/usr/lib/android-sdk/platforms/"
    benchmark_dir_path: str = "/home/calix/programming/benchmarks/ggplay/apks"
    ic3_script_root_path: str = "/home/calix/programming/IC3"
    ic3_on_gpbench(android_path, benchmark_dir_path, ic3_script_root_path)
"""
 
# def ic3_on_gpbench(android_path: str, benchmark_dir_path: str, ic3_path: str):
#     experiment_name = "ic3-on-gpbench-long-timeouts"
#     experiment_description = f"""{str(pd.to_datetime('today').date())}-{experiment_name}

# Run ic3 on Google Play Bench (gpbench), login scenario.

# Using ic3 script from Junbin Zhang (UBC).
# """
    
#     results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)



#     # Get apps from icc_bench
#     # input_apks: BatchInputModel = apps_from_gpbench(benchmark_dir_path, benchmark_df)
#     inputs_model = input_apks_from_dir(benchmark_dir_path)
#     benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_path)

#     # Setup experiment df
#     benchmark_description_path = "data/benchmark-descriptions/gpbench-info.csv"
#     benchamark_df = pd.read_csv(benchmark_description_path, header=0, index_col=False)
#     benchamark_df = benchamark_df.set_index(benchamark_df["AppID"])
#     benchamark_df["Detected Flows"] = None
#     benchamark_df["Error Message"] = None
#     benchamark_df["IC3 Time"] = None
#     benchamark_df["Time Elapsed"] = None


#     benchmark_df["Input Model"] = None
#     for input_model in inputs_model.ungrouped_inputs:
#         mask = benchmark_df["AppName"].apply(lambda x: x in input_model.apk().apk_name) # type: ignore
#         # only one result should be found 
#         if mask.sum() > 1:
#             raise AssertionError("Apk Name " + input_model.apk().apk_name + " found in multiple df rows: \n" + str(benchmark_df[mask]))
#         app_id = benchmark_df[mask]["AppID"].iloc[0]
#         input_model.benchmark_id = app_id
#         benchmark_df.loc[app_id, "Input Model"] = input_model # type: ignore
#     # assign_input_gpbench_benchmark_ids(inputs_model, results_df)


#     # Only use a subset of inputs
#     mask = benchmark_df["AppID"].isin(range(1,20))
#     mask = benchmark_df["AppID"].isin([3,6,8,9,10,15,19])
#     results_df = benchmark_df[mask]
    

#     # run ic3 on each app
#     for input_model in inputs_model.ungrouped_inputs:
#         # only run apps in dataframe
#         if not input_model.benchmark_id in results_df["AppID"]:
#             continue

#         # Run ic3 to get model for app, need to record resulting model filename
#         # ic3_timeout = 4 * 60 * 60
#         ic3_timeout = 72 *  60 * 60
#         # ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")

#         android_jar_path = os.path.join(android_path, f"android-{str(results_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")

#         try:
#             t0 = time.time()
#             # icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
#             icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
#             results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
#         except CalledProcessError as e:
#             logger.error("Exception by ic3; details in " + ic3_path + "for apk " + input_model.apk().apk_name)
#             results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
#             # skip the rest of the experiment; Can't run FD properly without the ICC model
#             continue
#         except TimeoutExpired as e:
#             logger.error(f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_path)
#             results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {format_num_secs(ic3_timeout)}"
#             # skip the rest of the experiment; Can't run FD properly without the ICC model
#             continue
#         except ValueError as e:
#             logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
#             results_df.loc[input_model.benchmark_id, "Error Message"] = f"Can't find icc model: {str(e)}"
#             continue

#     print(results_df)
#     results_df.to_csv(results_df_path)


# def temp():
#     run_ic3()
#     run_fd(input)

#     run_fd()

#     interpret_observations()
#     run_fd(input)
    

# def gpbench_experiment_generic(**kwargs):
#     flowdroid_jar_path: str = kwargs["flowdroid_jar_path"]
#     android_path: str = kwargs["android_path"]
#     benchmark_dir_path: str = kwargs["benchmark_dir_path"]
#     ground_truth_xml_path = kwargs["ground_truth_xml_path"]
#     benchmark_description_path = kwargs["benchmark_description_path"]
#     # ground_truth_xml_path = ""

#     flowdroid_timeout_seconds = kwargs["timeout"] 
#     ids_subset = kwargs["ids_subset"] 
#     experiment_name = kwargs["experiment_name"] 
#     experiment_description = kwargs["experiment_description"] 
#     flowdroid_args: FlowdroidArgs = kwargs["flowdroid_args"] 
#     always_new_experiment_directory = kwargs["always_new_experiment_directory"] 
#     source_sink_list_path = kwargs["source_sink_list_path"]

#     logger.info(f"Starting experiment {experiment_name}")

#     experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

#     inputs_model = input_apks_from_dir(benchmark_dir_path)
#     benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_path)
#     if ids_subset is not None:
#         benchmark_df = benchmark_df.loc[ids_subset]

#     """
#     ic3_path: str = kwargs["ic3_path"]
#     use_model_paths_csv: bool = kwargs["use_model_paths_csv"]
#     using_ic3_script: bool = kwargs["using_ic3_script"]
#     """
#     # ic3_timeout = 4 * 60 * 60
#     ic3_timeout = 15 * 60
    
#     if "use_model_paths_csv" in kwargs.keys():
#         icc_model_path_df = pd.read_csv("/home/calix/programming/ConDySta/data/benchmark-descriptions/gpbench-icc-model-paths.csv", header=0, index_col=False)
#         icc_model_path_df = icc_model_path_df.set_index(icc_model_path_df["AppID"])
    
#     # run fd on each app
#     flowdroid_logs_directory_path = setup_additional_directories(experiment_dir_path, ["flowdroid-logs"])[0]
#     if "use_model_paths_csv" in kwargs.keys():
#         ic3_logs_dir_path, ic3_output_dir_path = setup_additional_directories(experiment_dir_path, ["ic3-logs", "ic3_output"])

#     ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)
#     results_df = results_df_from_benchmark_df(benchmark_df)
    
#     for i in benchmark_df.index:
#         input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore
        
#     #     # Run ic3 to get model for app, get file for FD
#     #     # it makes an ic3 model, or fails to do so. The resulting path needs to get passed to FD (if this thang is being used)
#     #     # These file paths are different, depending on the input. 
#     #     # inputs: params for ic3 behavior, specific input model (plus group_id, i guess, though this should only be done once per apk)
#     #     # dataframe with columns that will be used
#     #     # output: dataframe with the outputs corresponding to the input dataframe
#     #     if "use_model_paths_csv" in kwargs.keys() and kwargs["use_model_paths_csv"]:
#     #         icc_model_path = icc_model_path_df.loc[input_model.benchmark_id, "ICC Model Path"]
#     #         if not os.path.isfile(str(icc_model_path)):
#     #             results_df.loc[input_model.benchmark_id, "Error Message"] = "No ICC Model"
#     #             continue

#     #     elif "ic3_path" in kwargs.keys():
#     #         ic3_path = kwargs["ic3_path"]
#     #         using_ic3_script = kwargs["using_ic3_script"]
#     #         if not using_ic3_script:
#     #             ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")
#     #             try:
#     #                 t0 = time.time()
#     #                 icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
                    
#     #                 results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
#     #             except CalledProcessError as e:
#     #                 logger.error("Exception by ic3; details in " + ic3_log_path + " for apk " + input_model.apk().apk_name)
#     #                 results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
#     #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
#     #                 continue
#     #             except TimeoutExpired as e:
#     #                 logger.error(f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_log_path)
#     #                 results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {format_num_secs(ic3_timeout)} "
#     #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
#     #                 continue
#     #             except ValueError as e:
#     #                 logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
#     #                 continue
#     #         else: 
#     #             android_jar_path = os.path.join(android_path, f"android-{str(benchmark_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")
#     #             try:
#     #                 t0 = time.time()
#     #                 icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
#     #                 results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
#     #             except CalledProcessError as e:
#     #                 logger.error("Exception by ic3; details in " + ic3_path + " for apk " + input_model.apk().apk_name)
#     #                 results_df.loc[i, "Error Message"] = "IC3 Exception"
#     #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
#     #                 continue
#     #             except TimeoutExpired as e:
#     #                 msg = f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_path
#     #                 logger.error(msg)
#     #                 results_df.loc[i, "Error Message"] = msg
#     #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
#     #                 continue
#     #             except ValueError as e:
#     #                 msg = f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e)
#     #                 logger.error(msg)
#     #                 results_df.loc[i, "Error Message"] += msg # type: ignore
#     #                 continue
#     #     else: 
#     #         # ic3_path is ""
#     #         icc_model_path = ""
#     #         pass

#         output_log_path = os.path.join(flowdroid_logs_directory_path, input_model.input_identifier() + ".log")
#         # # debug
#         # flowdroid_args.set_arg("outputfile", os.path.join(fd_xml_output_dir_path, input_model.input_identifier() + ".xml"))
#         # # end debug
        

#         try:
#             t0 = time.time()
#             run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, source_sink_list_path, flowdroid_args, output_log_path, flowdroid_timeout_seconds)
#             time_elapsed_seconds = time.time() - t0
#         except TimeoutExpired as e:
#             msg = f"Flowdroid timed out after {format_num_secs(flowdroid_timeout_seconds)} on apk {input_model.apk().apk_name}; details in " + output_log_path
#             logger.error(msg)
#             results_df.loc[i, "Error Message"] += msg
#             continue

#         process_results_from_fd_log_single(results_df, i, time_elapsed_seconds, output_log_path, apk_path=input_model.apk().apk_path, ground_truth_flows_df=ground_truth_flows_df)

#         # # debug
#         # ground_truth_flows_df.to_csv(os.path.join(experiment_dir_path, "groundtruth_df.csv"))
#         # # end debug

#     results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
#     results_df.to_csv(results_df_path)

def check_ssgpl_list():
    """ Generate the file path where SS-GooglePlayLogin.txt is expected. Generate it if it's not present."""
    sources_sinks_dir_path = hybrid.hybrid_config.source_sink_dir_path() # type: ignore
    ssgpl_list_path = os.path.join(sources_sinks_dir_path, "SS-GooglePlayLogin.txt")

    if not os.path.isfile(ssgpl_list_path):
        create_source_sink_file_ssgpl(ssgpl_list_path)

    return ssgpl_list_path



