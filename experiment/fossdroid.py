import os
from subprocess import TimeoutExpired
import time
from typing import Dict, List
import typing
import xml.etree.ElementTree as ET

import pandas as pd

from experiment import external_path
from experiment.common import benchmark_df_base_from_batch_input_model, format_num_secs, get_project_root_path, setup_additional_directories, setup_dirs_with_dependency_info, setup_experiment_dir
from experiment.flowdroid_experiment import experiment_setup_and_teardown_temp, flowdroid_file_paths, flowdroid_experiment
from hybrid.flow import Flow
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig
from hybrid.log_process_fd import FlowdroidLogException, get_flowdroid_reported_leaks_count, get_flowdroid_analysis_error, get_flowdroid_memory, get_flowdroid_flows
import util.logger
from util.input import BatchInputModel, InputModel, find_apk_paths_in_dir_recursive, input_apks_from_dir
logger = util.logger.get_logger(__name__)

#### Start External File Paths Settings

def fossdroid_file_paths():
    fossdroid_benchmark_dir_path = external_path.fossdroid_benchmark_apks_dir_path
    fossdroid_ground_truth_xml_path = "/home/calix/programming/benchmarks/wild-apps/fossdroid_ground_truth.xml"

    return {
            "benchmark_dir_path":fossdroid_benchmark_dir_path, 
            "ground_truth_xml_path":fossdroid_ground_truth_xml_path, 
            }

#### End External & Data File Paths Settings

#### Start fossdroid Settings Hierarchy

def fossdroid_experiment_setup_base() -> Dict[str, typing.Any]:
    file_paths = fossdroid_file_paths() | flowdroid_file_paths()
    
    experiment_args = file_paths.copy()

    flowdroid_args = FlowdroidArgs(**FlowdroidArgs.default_settings)
    # flowdroid_args = FlowdroidArgs.best_fossdroid_settings
    experiment_args["flowdroid_args"] = flowdroid_args
    experiment_args["source_sink_list_path"] = get_fossdroid_source_sink_list_path()

    return experiment_args

def fossdroid_experiment_setup_test(**file_paths):
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["experiment_name"] = "fd-on-fossdroid-test"
    experiment_args["experiment_description"] = """
Integration test on a handful of apps.
"""
    experiment_args["ids_subset"] = pd.Series([0,1])
    experiment_args["timeout"] = 1 * 60
    experiment_args["always_new_experiment_directory"] = False
    return experiment_args

def fossdroid_experiment_setup_full(**file_paths):
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 60 * 60
    experiment_args["ids_subset"] = None
    experiment_args["experiment_name"] = "fd-on-fossdroid-default-fd"
    experiment_args["experiment_description"] = "Run FlowDroid on the full Fossdroid dataset with default FD settings"
    experiment_args["always_new_experiment_directory"] = True
    return experiment_args

def fossdroid_experiment_setup_misc(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([27])
    experiment_args["experiment_name"] = "fd-on-fossdroid-temp"
    experiment_args["experiment_description"] = ""
    experiment_args["always_new_experiment_directory"] = False
    return experiment_args

#### End fossdroid Settings Hierarchy

def fossdroid_main():
    # This rewrites the source sink list
    file_paths = fossdroid_file_paths() | flowdroid_file_paths()
    fossdroid_experiment_15min_fd_configs(**file_paths)

def fossdroid_validation_experiment():
    experiment_args = fossdroid_experiment_setup_base()

    experiment_args["timeout"] = 60 * 60 # 1 hour
    experiment_args["always_new_experiment_directory"] = False
    experiment_args["ids_subset"] = None

    fossdroid_default_csv_path = "data/benchmark-descriptions/fossdroid_config_aplength5_replication1.csv"
    fossdroid_best_csv_path = "data/benchmark-descriptions/fossdroid_config_2way2_replication1.csv"

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["experiment_name"] = f"fd-on-fossdroid-default-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with default settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_default_csv_path

    experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.best_fossdroid_settings)
    experiment_args["experiment_name"] = f"fd-on-fossdroid-best-mordahl-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with Mordahl's best DB3 settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_best_csv_path

    experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)


def single_fossdroid_experiment(**file_paths):
    # experiment_args = fossdroid_experiment_setup_misc(**file_paths)
    # experiment_args = fossdroid_experiment_setup_default_fd_full(**file_paths)
    experiment_args = fossdroid_experiment_setup_test(**file_paths)
    
    experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)


def fossdroid_experiment_15min_fd_configs(**file_paths):

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings), 
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified), 
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:
        
        experiment_args = fossdroid_experiment_setup_full(**file_paths)
        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-fossdroid-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with {settings_description_suffix}"
        experiment_args["timeout"] =  15 * 60

        experiment_setup_and_teardown_temp(flowdroid_experiment, **experiment_args)

    
# def fossdroid_experiment_generic(**kwargs):
#     flowdroid_jar_path = kwargs["flowdroid_jar_path"]
#     android_path = kwargs["android_path"]
#     benchmark_dir_path = kwargs["benchmark_dir_path"]
#     ground_truth_xml_path = kwargs["ground_truth_xml_path"]
#     benchmark_description_path = kwargs["benchmark_description_path"]

#     flowdroid_timeout_seconds = kwargs["timeout"]
#     ids_subset = kwargs["ids_subset"]
#     experiment_name = kwargs["experiment_name"]
#     experiment_description = kwargs["experiment_description"]
#     flowdroid_args = kwargs["flowdroid_args"]
#     always_new_experiment_directory = kwargs["always_new_experiment_directory"]
#     source_sink_list_path = kwargs["source_sink_list_path"]
    
#     # Things below here don't need tweaking between experiments???

#     logger.info(f"Starting experiment {experiment_name}")
    
#     experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

#     inputs_model: BatchInputModel = input_apks_from_dir(benchmark_dir_path)
#     benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_path)
#     if ids_subset is not None:
#         benchmark_df = benchmark_df.iloc[ids_subset]

#     flowdroid_logs_directory_path = setup_additional_directories(experiment_dir_path, ["flowdroid-logs"])[0]

#     ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)
#     results_df = results_df_from_benchmark_df(benchmark_df, benchmark_description_path)
    
#     for i in benchmark_df.index:
#         input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

#         output_log_path = os.path.join(flowdroid_logs_directory_path, input_model.input_identifier() + ".log") 

#         # TODO: do i need to pass specific android paths, or just the android platforms dir?
#         try: 
#             t0 = time.time()
#             run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, source_sink_list_path, flowdroid_args, output_log_path, flowdroid_timeout_seconds)
#             time_elapsed_seconds = time.time() - t0
#         except TimeoutExpired as e:
#             msg = f"Flowdroid timed out after {format_num_secs(flowdroid_timeout_seconds)} on apk {input_model.apk().apk_name}; details in " + output_log_path
#             logger.error(msg)
#             results_df.loc[i, "Error Message"] += msg
#             continue

#         process_results_from_fd_log_single(results_df, i, time_elapsed_seconds, output_log_path, input_model.apk().apk_path, ground_truth_flows_df=ground_truth_flows_df)

#     results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
#     results_df.to_csv(results_df_path)


def get_fossdroid_source_sink_list_path() -> str:
    project_root = get_project_root_path()
    return os.path.join(project_root, "data", "sources-and-sinks", "SS-from-fossdroid-ground-truth.txt")

