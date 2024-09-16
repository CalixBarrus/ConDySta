# from datetime import timedelta
from typing import Dict, List, Tuple
import typing
import pandas as pd
import os
import xml.etree.ElementTree as ET

from hybrid.flow import Flow, compare_flows
from hybrid.flowdroid import FlowdroidArgs
from hybrid.log_process_fd import FlowdroidLogException, get_analysis_error_in_flowdroid_log, get_flowdroid_memory, get_flows_in_flowdroid_log, get_reported_num_leaks_in_flowdroid_log
from util.input import ApkModel, BatchInputModel, InputModel

import util.logger
logger = util.logger.get_logger(__name__)

def setup_dirs_with_ic3(experiment_name, experiment_description):
    # TODO: refactor this out
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {})
    dir_names = ["ic3_output", "ic3-logs", "flowdroid-logs"]
    df_path =  os.path.join(experiment_dir_path, experiment_id + ".csv")
    return df_path, *setup_additional_directories(experiment_dir_path, dir_names)

def setup_dirs_with_dependency_info(experiment_name: str, experiment_description: str, dir_names: List[str], dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False) -> Tuple[str, List[str]]:
    # TODO: refactor this out
    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict, always_new_experiment_directory)

    df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    return df_path, setup_additional_directories(experiment_dir_path, dir_names)

def setup_experiment_dir(experiment_name: str, experiment_description: str, dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False) -> Tuple[str, str]:
    experiment_description += ('\n')
    for key, value in dependency_dict.items():
        if key in ["experiment_name", "experiment_description"]:
            # These args should already be in the experiment_description
            continue
        if key == "timeout":
            experiment_description += (f"{key}: {format_num_secs(value)}\n")
            continue
        if key == "flowdroid_args":
            experiment_description += (f"{key}: {str(value.args)}\n")
            continue
        experiment_description += (f"{key}: {value}\n")

    date = str(pd.to_datetime('today').date())
    # "YYYY-MM-DD"
    experiment_id = date + "-" + experiment_name

    if always_new_experiment_directory:
        # Check experiment directory for items of form expriment_id[n], and find the next n for which there is no directory
        experiment_names = os.listdir(os.path.join("data", "experiments"))
        if experiment_id in experiment_names:
            # if more than 20 dirs, just keep overwriting the original dir
            for i in range(0,20):
                if experiment_id + str(i) not in experiment_names:
                    logger.info(f"Replacing experiment_id {experiment_id} with {experiment_id + str(i)}")
                    experiment_id = experiment_id + str(i)
                    break

    experiment_dir_path = os.path.join("data", "experiments", experiment_id)    
    for dir_path in [os.path.join("data"), os.path.join("data", "experiments"), experiment_dir_path]:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

    # Record experiment description
    readme_path = os.path.join(experiment_dir_path, "README.txt")
    with open(readme_path, 'w') as file:
        file.write(experiment_description)

    experiment_log_path = os.path.join(experiment_dir_path, f"{experiment_id}.log")
    util.logger.set_all_loggers_file_handler(experiment_log_path)

    return experiment_id, experiment_dir_path

def setup_additional_directories(experiment_dir_path: str, dir_names: List[str]) -> List[str]:
    dir_paths = []
    for dir_name in dir_names:
        dir_path = os.path.join(experiment_dir_path, dir_name)
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)
        dir_paths.append(dir_path)
    
    return dir_paths

# def flowdroid_experiment_generic(**kwargs):
#     pass

def format_num_secs(secs: int) -> str:
    td = pd.Timedelta(seconds=secs)
    td = td.round('s')
    
    return f"{td.seconds // (60 * 60)}h{(td.seconds % (60 * 60)) // 60}m{td.seconds % (60)}s"

def find_xml_paths_in_dir_recursive(dir_path: str) -> List[str]:
    """ Recursively traverse the target directory and it's children. Return all apks
        discovered. """
    result = []

    for item in os.listdir(dir_path):
        new_path = os.path.join(dir_path, item)

        if new_path.endswith(".xml"):
            result.append(new_path)
        elif os.path.isdir(new_path):
            result += find_xml_paths_in_dir_recursive(new_path)
    return result

def process_results_from_fd_log_single(results_df: pd.DataFrame, i: int, time_elapsed, output_log_path, apk_path, ground_truth_flows_df=None):

    if "Time Elapsed" not in results_df.columns:
        results_df["Time Elapsed"] = ""
    results_df.loc[i, "Time Elapsed"] = format_num_secs(time_elapsed)

    if "Max Reported Memory Usage" not in results_df.columns:
        results_df["Max Reported Memory Usage"] = ""
    results_df.loc[i, "Max Reported Memory Usage"] = get_flowdroid_memory(output_log_path)

    analysis_error = get_analysis_error_in_flowdroid_log(output_log_path)
    if analysis_error != "":
        results_df.loc[i, "Error Message"] += analysis_error # type: ignore
        logger.error(analysis_error)

    if "Reported Flowdroid Flows" not in results_df.columns:
        results_df["Reported Flowdroid Flows"] = ""
    try: 
        reported_num_leaks = get_reported_num_leaks_in_flowdroid_log(output_log_path)
    except FlowdroidLogException as e:
        logger.error(e.msg)
        results_df.loc[i, "Error Message"] += e.msg # type: ignore
        return

    if reported_num_leaks is None:
        msg = "Flowdroid Irregularity, review log at " + output_log_path
        results_df.loc[i, "Error Message"] = msg
        logger.error(msg)
        return

    results_df.loc[i, "Reported Flowdroid Flows"] = reported_num_leaks

    if ground_truth_flows_df is None: 
        return 
    
    for col in ["TP", "FP", "TN", "FN", "Flows Not Evaluated"]:
        if col not in results_df.columns:
            results_df[col] = ""

    detected_flows = get_flows_in_flowdroid_log(output_log_path, apk_path)

    # deduplicate FD flows
    original_length = len(detected_flows)
    detected_flows = list(set(detected_flows))
    if len(detected_flows) != original_length:
        logger.warn(f"Flowdroid reported {original_length - len(detected_flows)} duplicate flows for app {results_df.loc[i, 'APK Name']}")

    tp, fp, tn, fn, inconclusive = compare_flows(detected_flows, ground_truth_flows_df, results_df.loc[i, 'APK Name'])

    results_df.loc[i, "TP"] = tp
    results_df.loc[i, "FP"] = fp
    results_df.loc[i, "TN"] = tn
    results_df.loc[i, "FN"] = fn
    results_df.loc[i, "Flows Not Evaluated"] = inconclusive

def groundtruth_df_from_xml(benchmark_df: pd.DataFrame, ground_truth_xml_path):
    tree = ET.parse(ground_truth_xml_path) 
    ground_truth_root = tree.getroot() 
    
    # assert ["Benchmark ID", "Input Model"] in benchmark_df.columns

    flow_elements = ground_truth_root.findall("flow")
    # df columns -> Flow, APK Name, APK Path, Source Signature, Sink Signature, Ground Truth Value
    flows = [Flow(element) for element in flow_elements]
    flows.sort()
    groundtruth_df = pd.DataFrame({"Flow": flows})
    # Index is set to the list index of flows
    groundtruth_df["APK Name"] = ""
    groundtruth_df["Benchmark ID"] = ""
    groundtruth_df["Source Signature"] = ""
    groundtruth_df["Sink Signature"] = ""
    groundtruth_df["Ground Truth Value"] = ""

    flows = [Flow(element) for element in flow_elements]
    flows.sort()

    for i in groundtruth_df.index:
        flow: Flow = groundtruth_df.loc[i, "Flow"] # type: ignore
        groundtruth_df.loc[i, "APK Name"] = flow.get_file()

        # Match up the flow with the corresponding Benchmark ID
        mask = benchmark_df["Input Model"].apply(lambda model: model.apk().apk_name).values == groundtruth_df.loc[i, "APK Name"]
        # logger.debug(benchmark_df["Input Model"].apply(lambda model: model.apk().apk_name).values)
        assert sum(mask) <= 1
        if sum(mask) == 1:
            groundtruth_df.loc[i, "Benchmark ID"] = benchmark_df[mask]["Benchmark ID"].iloc[0]

            groundtruth_df.loc[i, "Source Signature"] = flow.get_source_statementgeneric()
            groundtruth_df.loc[i, "Sink Signature"] = flow.get_sink_statementgeneric()
            groundtruth_df.loc[i, "Ground Truth Value"] = flow.get_ground_truth_attribute()
        else: 
            groundtruth_df.loc[i, "Benchmark ID"] = -1
    # Strip out ground truth flows not relevant to the apps in the benchmark_df
    groundtruth_df = groundtruth_df[groundtruth_df["Benchmark ID"] != -1]

    return groundtruth_df

def benchmark_df_base_from_batch_input_model(inputs_model: BatchInputModel, benchmark_description_csv_path: str=""):

    inputs = inputs_model.ungrouped_inputs
    # inputs = inputs_model.ungrouped_inputs + inputs_model.grouped_inputs

    benchmark_df = pd.DataFrame({"Benchmark ID": list(range(len(inputs))),
                    "Input Model": inputs})
    assert (benchmark_df.index == benchmark_df["Benchmark ID"]).all()

    for i in benchmark_df.index:
        benchmark_df.loc[i, "Input Model"].benchmark_id = i # type: ignore

    if benchmark_description_csv_path != "":
        description_df = pd.read_csv(benchmark_description_csv_path, header=0, index_col=False)
        description_df = description_df.set_index(description_df["AppID"])

        # Change the Benchmark IDs to match the AppID's from the description.
        # Join on description_df["AppName"], where a given apk_name is [AppID].[AppName].apk
        description_df_apk_names = description_df["AppID"].astype(str) + "." + description_df["AppName"] + ".apk"

        for i in benchmark_df.index:
            model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

            mask = description_df_apk_names == model.apk().apk_name 
            assert sum(mask) == 1
            benchmark_df.loc[i, "Benchmark ID"] = description_df[mask]["AppID"].iloc[0]
            model.benchmark_id = description_df[mask]["AppID"].iloc[0]

        benchmark_df.set_index("Benchmark ID")

    return benchmark_df

def results_df_from_benchmark_df(benchmark_df: pd.DataFrame) -> pd.DataFrame:
    results_df = benchmark_df[["Benchmark ID"]]
    results_df["APK Name"] = ""
    for i in benchmark_df.index:
        results_df.loc[i, "APK Name"] = benchmark_df.loc[i, "Input Model"].apk().apk_name # type: ignore

    results_df["Error Message"] = ""

    return results_df

    

# def apks_df_from_apk_models(apk_models: List[ApkModel]) -> pd.DataFrame:

#     apks_df = pd.DataFrame({"APK Name": [apk_model.apk_name for apk_model in apk_models],
#                             "APK Model": apk_models})

#     return apks_df

