import os
from subprocess import TimeoutExpired
import time
from typing import Dict, List
import typing
import xml.etree.ElementTree as ET

import pandas as pd

from experiment import external_path
from experiment.common import benchmark_df_base_from_batch_input_model, format_num_secs, groundtruth_df_from_xml, process_results_from_fd_log_single, results_df_from_benchmark_df, setup_additional_directories, setup_dirs_with_dependency_info, setup_experiment_dir
from hybrid.flow import Flow
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig
from hybrid.log_process_fd import FlowdroidLogException, get_reported_num_leaks_in_flowdroid_log, get_analysis_error_in_flowdroid_log, get_flowdroid_memory, get_flows_in_flowdroid_log
from hybrid.source_sink import format_source_sink_signatures
import util.logger
from util.input import BatchInputModel, InputModel, find_apk_paths_in_dir_recursive, input_apks_from_dir
logger = util.logger.get_logger(__name__)

def get_file_paths():
    # flowdroid_jar_path = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_jar_path = "/home/calix/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    android_platforms_dir_path = "/home/calix/.android_sdk/platforms"
    fossdroid_benchmark_dir_path = external_path.fossdroid_benchmark_apks_dir_path
    fossdroid_ground_truth_xml_path = "/home/calix/programming/benchmarks/wild-apps/fossdroid_ground_truth.xml"

    # source_sink_list_from_df(df_from_groundtruth_xmls(fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path), get_fossdroid_source_sink_list_path())
    file_paths = {"flowdroid_jar_path": flowdroid_jar_path, 
                  "android_path": android_platforms_dir_path,
                  "fossdroid_dir_path": fossdroid_benchmark_dir_path, 
                  "fossdroid_ground_truth_xml_path": fossdroid_ground_truth_xml_path}
    
    return file_paths

def fossdroid_main():
    # This rewrites the source sink list
    # source_sink_list_from_df(df_from_groundtruth_xmls(fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path), get_fossdroid_source_sink_list_path())

    file_paths = get_file_paths()
    # single_fossdroid_experiment(flowdroid_jar_path=flowdroid_jar_path, android_path=android_platforms_dir_path, fossdroid_dir_path=fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path=fossdroid_ground_truth_xml_path)
    fossdroid_experiment_15min_fd_configs(**file_paths)

def fossdroid_validation_experiment():
    file_paths = get_file_paths()
    experiment_args = fossdroid_experiment_setup_base(**file_paths)

    experiment_args["timeout"] = 60 * 60 # 1 hour
    experiment_args["always_new_experiment_directory"] = False
    experiment_args["ids_subset"] = None

    fossdroid_default_csv_path = "data/benchmark-descriptions/fossdroid_config_aplength5_replication1.csv"
    fossdroid_best_csv_path = "data/benchmark-descriptions/fossdroid_config_2way2_replication1.csv"

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["experiment_name"] = f"fd-on-fossdroid-default-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with default settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_default_csv_path
    fossdroid_experiment_generic(**experiment_args)

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.best_fossdroid_settings)
    experiment_args["experiment_name"] = f"fd-on-fossdroid-best-mordahl-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with Mordahl's best DB3 settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_best_csv_path
    fossdroid_experiment_generic(**experiment_args)


def single_fossdroid_experiment(**file_paths):
    # experiment_args = fossdroid_experiment_setup_misc(**file_paths)
    # experiment_args = fossdroid_experiment_setup_default_fd_full(**file_paths)
    experiment_args = fossdroid_experiment_setup_test(**file_paths)
    
    fossdroid_experiment_generic(**experiment_args)

def fossdroid_experiment_15min_fd_configs(**file_paths):

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings), 
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified), 
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:
        
        experiment_args = fossdroid_experiment_setup_default_fd_full(**file_paths)
        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-fossdroid-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with {settings_description_suffix}"
        experiment_args["timeout"] =  15 * 60
        fossdroid_experiment_generic(**experiment_args)


def fossdroid_experiment_setup_base(**file_paths) -> Dict[str, typing.Any]:
    # No file names in this layer, but I want this function to eventually allow wierd automation of tweaking some experiment args. (test experiments, run different FD versions/SS lists in serial, etc.)
    # This should NOT be called by fossdroid_main, rather right some functions to handle these
    # print(file_paths)
    assert list(file_paths.keys()) == ["flowdroid_jar_path", "android_path", "fossdroid_dir_path", "fossdroid_ground_truth_xml_path"]
    
    experiment_args = file_paths.copy()
    # experiment_name = "fd-on-fossdroid-best-fdmini2"
    # experiment_args["experiment_name"] = experiment_name

    timeout = 1 * 60
    # timeout = 15 * 60
    # timeout = 2 * 60 * 60
    experiment_args["timeout"] = timeout


    ids_subset = pd.Series([0,1])
    # ids_subset = None
    experiment_args["ids_subset"] = ids_subset

    flowdroid_args = FlowdroidArgs(**FlowdroidArgs.default_settings)
    # flowdroid_args = FlowdroidArgs.best_fossdroid_settings
    experiment_args["flowdroid_args"] = flowdroid_args

    experiment_args["always_new_experiment_directory"] = False

    experiment_args["benchmark_description_path"] = ""

    return experiment_args

def fossdroid_experiment_setup_misc(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([27])
    experiment_args["experiment_name"] = "fd-on-fossdroid-temp"
    experiment_args["experiment_description"] = ""
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["always_new_experiment_directory"] = False
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

def fossdroid_experiment_setup_default_fd_full(**file_paths):
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 60 * 60
    experiment_args["ids_subset"] = None
    experiment_args["experiment_name"] = "fd-on-fossdroid-default-fd"
    experiment_args["experiment_description"] = "Run FlowDroid on the full Fossdroid dataset with default FD settings"
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["always_new_experiment_directory"] = True
    return experiment_args


def fossdroid_experiment_setup(**file_paths) -> Dict[str, typing.Any]:
    # No file names in this layer, but I want this function to eventually allow wierd automation of tweaking some experiment args. (test experiments, run different FD versions/SS lists in serial, etc.)
    assert file_paths.keys == ["flowdroid_jar_path", "android_path", "fossdroid_dir_path", "fossdroid_ground_truth_xml_path"]
    
    experiment_args = file_paths.copy()
    experiment_name = "fd-on-fossdroid-best-fdmini2"
    experiment_args["experiment_name"] = experiment_name

    # flowdroid_args = FlowdroidArgs.default_settings
    flowdroid_args = FlowdroidArgs.best_fossdroid_settings

    timeout = 1 * 60
    # timeout = 15 * 60
    # timeout = 2 * 60 * 60
    experiment_args["timeout"] = timeout


    ids_subset = pd.Series([0,1])
    # ids_subset = None
    experiment_args["ids_subset"] = ids_subset

    experiment_description = f"""
Run Flowdroid on FossDroid apps. 

Timeout: {format_num_secs(timeout)}
Flowdroid run with the following args: {str(flowdroid_args)}
"""
    flowdroid_args = FlowdroidArgs(**flowdroid_args)
    experiment_args["experiment_description"] = experiment_description    
    experiment_args["flowdroid_args"] = flowdroid_args

    return experiment_args


    
# def fossdroid_experiment(flowdroid_jar_path: str, android_path: str, fossdroid_dir_path: str, fossdroid_ground_truth_xml_path: str, default_fd_config: bool=False, best_fossdroid_fd_config: bool=False):
def fossdroid_experiment_generic(**kwargs):
    flowdroid_jar_path = kwargs["flowdroid_jar_path"]
    android_path = kwargs["android_path"]
    fossdroid_dir_path = kwargs["fossdroid_dir_path"]
    fossdroid_ground_truth_xml_path = kwargs["fossdroid_ground_truth_xml_path"]

    timeout = kwargs["timeout"]
    ids_subset = kwargs["ids_subset"]
    experiment_name = kwargs["experiment_name"]
    experiment_description = kwargs["experiment_description"]
    flowdroid_args = kwargs["flowdroid_args"]
    always_new_experiment_directory = kwargs["always_new_experiment_directory"]
    benchmark_description_path = kwargs["benchmark_description_path"]
    
    # Things below here don't need tweaking between experiments???

    logger.info(f"Starting experiment {experiment_name}")
    
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)
    

    source_sink_list_path = get_fossdroid_source_sink_list_path()

    # TODO: This isn't a general way at all to setup the results_df/apps_df
    inputs_model: BatchInputModel = input_apks_from_dir(fossdroid_dir_path)
    # For benchmark/app 'id's, take the apps alphabetically from the directory 
    benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_path)
    
    if ids_subset is not None:
        benchmark_df = benchmark_df.iloc[ids_subset]

    flowdroid_logs_dir_path = setup_additional_directories(experiment_dir_path, ["flowdroid-logs"])[0]

    ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, fossdroid_ground_truth_xml_path)
    results_df = results_df_from_benchmark_df(benchmark_df, benchmark_description_path)
    
    for i in benchmark_df.index:
        input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

        output_log_path = os.path.join(flowdroid_logs_dir_path, input_model.input_identifier() + ".log") 

        # TODO: do i need to pass specific android paths, or just the android platforms dir?
        try: 
            t0 = time.time()
            # TODO: Shouldn't have an APK Path column, thats encapsulated by input_models. 
            run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, source_sink_list_path, flowdroid_args, output_log_path, timeout)
            time_elapsed = time.time() - t0
        except TimeoutExpired as e:
            msg = f"Flowdroid timed out after {format_num_secs(timeout)} on apk {input_model.apk().apk_name}; details in " + output_log_path
            logger.error(msg)
            results_df.loc[i, "Error Message"] += msg
            continue

        process_results_from_fd_log_single(results_df, i, time_elapsed, output_log_path, input_model.apk().apk_path, ground_truth_flows_df=ground_truth_flows_df)

    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)


def get_fossdroid_source_sink_list_path() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__)) # Go back a directory
    return os.path.join(project_root, "data", "sources-and-sinks", "SS-from-fossdroid-ground-truth.txt")


def source_sink_list_from_df(df, output_file):
    # df["Source Signature"].unique().list()

    source_sink_list = format_source_sink_signatures(df["Source Signature"].unique().tolist(), df["Sink Signature"].unique().tolist())

    with open(output_file, 'w') as file:
        file.write(source_sink_list)
