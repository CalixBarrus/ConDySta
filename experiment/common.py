# from datetime import timedelta
from typing import Dict, List, Tuple
import typing
import pandas as pd
import os

from hybrid.flowdroid import FlowdroidArgs
from util.input import ApkModel, BatchInputModel, InputModel, input_apks_from_dir

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

    experiment_directory_path = os.path.join("data", "experiments", experiment_id)    
    for dir_path in [os.path.join("data"), os.path.join("data", "experiments"), experiment_directory_path]:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

    # Record experiment description
    readme_path = os.path.join(experiment_directory_path, "README.txt")
    with open(readme_path, 'w') as file:
        file.write(experiment_description)

    experiment_log_path = os.path.join(experiment_directory_path, f"{experiment_id}.log")
    util.logger.set_all_loggers_file_handler(experiment_log_path)

    return experiment_id, experiment_directory_path

def setup_additional_directories(experiment_dir_path: str, dir_names: List[str], always_new_directory: bool=False) -> List[str]:
    # TODO: this should probably not act on lists; that's not any of the use cases I'm coding right now
    # setup new directories in the experiment directory. If a directory name is already taken, create and return one with a slightly tweaked name.
    dir_paths = []
    for dir_name in dir_names:
        dir_path = os.path.join(experiment_dir_path, dir_name)


        if not always_new_directory and os.path.isdir(dir_path):
            dir_paths.append(dir_path)
            continue
        elif always_new_directory and os.path.isdir(dir_path):
            available_directory_name = next_available_directory_name(experiment_dir_path, dir_name)
            dir_path = os.path.join(experiment_dir_path, available_directory_name)
            
        os.mkdir(dir_path)
        dir_paths.append(dir_path)
    
    return dir_paths

def next_available_directory_name(base_directory_path: str, new_directory_name: str):
    file_names = os.listdir(base_directory_path)
    
    if new_directory_name not in file_names:
        available_directory_name = new_directory_name
    else:
        modified_directory_name = new_directory_name
        # if more than 20 dirs, just keep overwriting the original dir
        for i in range(0,20):
            if new_directory_name + str(i) not in file_names:
                logger.info(f"Replacing directory {new_directory_name} with {new_directory_name + str(i)}")
                modified_directory_name = new_directory_name + str(i)
                break

        available_directory_name = modified_directory_name

    return available_directory_name
    

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

def benchmark_df_from_benchmark_directory_path(benchmark_directory_path: str, benchmark_description_csv_path: str="", ids_subset: pd.Series=None):

    inputs_model = input_apks_from_dir(benchmark_directory_path)
    benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=benchmark_description_csv_path)
    if ids_subset is not None:
        benchmark_df = benchmark_df.loc[ids_subset]

    return benchmark_df

def benchmark_df_base_from_batch_input_model(inputs_model: BatchInputModel, benchmark_description_csv_path: str=""):

    inputs = inputs_model.ungrouped_inputs
    # inputs = inputs_model.ungrouped_inputs + inputs_model.grouped_inputs

    benchmark_df = pd.DataFrame({"Benchmark ID": list(range(len(inputs))),
                    "Input Model": inputs})
    assert (benchmark_df.index == benchmark_df["Benchmark ID"]).all()

    for i in benchmark_df.index:
        benchmark_df.loc[i, "Input Model"].benchmark_id = i # type: ignore

    if benchmark_description_csv_path != "":

        description_df = description_df_from_path(benchmark_description_csv_path)

        # if "AppID" in description_df.columns:
        #     description_df = description_df.set_index(description_df["AppID"])
        # else: 
        #     description_df["AppID"] = description_df.index

        # Change the Benchmark IDs to match the AppID's from the description.
        if os.path.basename(benchmark_description_csv_path) == "gpbench-info.csv":
            # Join on description_df["AppName"], where a given apk_name is [AppID].[AppName].apk
            description_df_apk_names = description_df["AppID"].astype(str) + "." + description_df["AppName"] + ".apk"
        else: 
            description_df_apk_names = description_df["apk"].apply(lambda path: os.path.basename(path))
            # logger.debug(description_df_apk_names)

        for i in benchmark_df.index:
            model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

            mask = description_df_apk_names == model.apk().apk_name 
            assert sum(mask) == 1
            # logger.debug(f"{str(i)}, {str(description_df[mask]["AppID"].iloc[0])}")
            benchmark_df.loc[i, "Benchmark ID"] = description_df[mask]["AppID"].iloc[0]
            model.benchmark_id = description_df[mask]["AppID"].iloc[0]

        benchmark_df = benchmark_df.set_index("Benchmark ID")
        benchmark_df["Benchmark ID"] = benchmark_df.index

    benchmark_df.sort_index(inplace=True)

    return benchmark_df

def description_df_from_path(benchmark_description_path: str):
    description_df = pd.read_csv(benchmark_description_path, header=0)

    if "AppID" in description_df.columns:
        description_df = description_df.set_index(description_df["AppID"])
    else: 
        description_df["AppID"] = description_df.index

    return description_df

def get_project_root_path() -> str:

    return os.path.dirname(os.path.dirname(__file__))


def modified_source_sink_path(modified_source_sink_directory_path: str, input_model: InputModel, grouped_apk_idx: int=-1, is_xml: bool=False):
    # modified_source_sink_directory = 
    return os.path.join(
        modified_source_sink_directory_path, input_model.input_identifier(grouped_apk_idx) + "source-sinks") + (".xml" if is_xml else ".txt")


def results_df_from_benchmark_df(benchmark_df: pd.DataFrame, benchmark_description_path: str="") -> pd.DataFrame:
    # Sets up new dataframe with index, Benchmark ID column, and APK Name column that match up with the benchmark_df.
    # Results data frames start with an empty Error Message column

    results_df = benchmark_df[["Benchmark ID"]]
    results_df["APK Name"] = ""
    for i in benchmark_df.index:
        results_df.loc[i, "APK Name"] = benchmark_df.loc[i, "Input Model"].apk().apk_name # type: ignore

    results_df["Error Message"] = ""

    if benchmark_description_path != "":
        description_df = description_df_from_path(benchmark_description_path)
        # print(f"{description_df.index}, {results_df.index}")
        # assert  == 

        if os.path.basename(benchmark_description_path) == "gpbench-info.csv":
            cols_to_copy = ["UBC # of Expected Flows", "UBC FlowDroid v2.7.1 Detected Flows"]
        elif os.path.basename(benchmark_description_path) == "fossdroid_config_aplength5_replication1.csv" or os.path.basename(benchmark_description_path) == "fossdroid_config_2way2_replication1.csv":
            cols_to_copy = ["num_flows", "time", "total_TP", "detected_TP", "total_FP", "detected_FP"]
        else:
            raise NotImplementedError()

        results_df[cols_to_copy] = description_df[cols_to_copy]

    return results_df


