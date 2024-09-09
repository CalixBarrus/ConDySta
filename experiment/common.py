# from datetime import timedelta
from typing import Dict, List, Tuple
import typing
import pandas as pd
import os

from hybrid.flowdroid import FlowdroidArgs
import util.logger
logger = util.logger.get_logger_revised(__name__)

def setup_dirs_with_ic3(experiment_name, experiment_description):
    df_path, intermediate_output_dirs = setup_dirs_generic(experiment_name, experiment_description, ["ic3_output", "ic3-logs", "flowdroid-logs"])
    return df_path, *intermediate_output_dirs

    # date = str(pd.to_datetime('today').date())
    # # "YYYY-MM-DD"
    # experiment_id = date + "-" + experiment_name

    # # Setup experiment specific directories
    # experiment_dir_path = os.path.join("data", experiment_id)
    # results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    # dir_paths = []
    # for dir_name in ["ic3_output", "ic3-logs", "flowdroid-logs"]:
    #     dir_paths.append(os.path.join(experiment_dir_path, dir_name))
    # # ic3_output_dir_path = os.path.join(experiment_dir_path, "ic3-output")
    # # ic3_logs_dir_path = os.path.join(experiment_dir_path, "ic3-logs")
    # # fd_output_dir_path = os.path.join(experiment_dir_path, "flowdroid-logs")
    
    # # Make sure each directory exists
    # for dir_path in [experiment_dir_path] + dir_paths:
    #     if not os.path.isdir(dir_path):
    #         os.mkdir(dir_path)

    # # Record experiment description
    # readme_path = os.path.join(experiment_dir_path, "README.txt")
    # with open(readme_path, 'w') as file:
    #     file.write(experiment_description)

    # return results_df_path, *dir_paths

def setup_dirs(experiment_name, experiment_description):
    pass

def setup_dirs_generic(experiment_name: str, experiment_description: str, dir_names: str, always_new_experiment_directory: bool) -> Tuple[str, List[str]]:
    """
    Setup data directory for an experiment.
    Experiment is assigned and ID with the date prepended.
    Returns a path for a results dataframe to be written to.
    Returns a list of paths matching the dimension of input dir_names for use in the experiment.
    The experiment description is recorded in a README.txt.
    Setup the logger to log in the experiment directory.
    """
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

    # Setup experiment specific directories
    experiment_dir_path = os.path.join("data", "experiments", experiment_id)

    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    dir_paths = []
    for dir_name in dir_names:
        dir_paths.append(os.path.join(experiment_dir_path, dir_name))
    # ic3_output_dir_path = os.path.join(experiment_dir_path, "ic3-output")
    # ic3_logs_dir_path = os.path.join(experiment_dir_path, "ic3-logs")
    # fd_output_dir_path = os.path.join(experiment_dir_path, "flowdroid-logs")
    
    # Make sure each directory exists
    for dir_path in [experiment_dir_path] + dir_paths:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

    # Record experiment description
    readme_path = os.path.join(experiment_dir_path, "README.txt")
    with open(readme_path, 'w') as file:
        file.write(experiment_description)

    experiment_log_path = os.path.join(experiment_dir_path, f"{experiment_id}.log")
    util.logger.set_all_loggers_file_handler(experiment_log_path)

    return results_df_path, dir_paths

def setup_dirs_with_dependency_info(experiment_name: str, experiment_description: str, dir_names: List[str], dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False) -> Tuple[str, List[str]]:
    experiment_description += ('\n')
    for key, value in dependency_dict.items():
        if key in ["experiment_name", "experiment_description"]:
            # These args should already be in the experiment_description
            continue
        if key == "timeout":
            experiment_description += (f"{key}: {format_num_secs(value)}\n")
        if key == "flowdroid_args":
            experiment_description += (f"{key}: {str(value.args)}\n")
        experiment_description += (f"{key}: {value}\n")
    """
    Timeout: {format_num_secs(timeout)}
    Flowdroid run with the following args: {str(flowdroid_args)}
    """
    return setup_dirs_generic(experiment_name, experiment_description, dir_names, always_new_experiment_directory)

def setup_experiment_dir(experiment_name: str, experiment_description: str, dependency_dict: Dict[str,typing.Any], always_new_experiment_directory: bool=False):
        experiment_description += ('\n')
    for key, value in dependency_dict.items():
        if key in ["experiment_name", "experiment_description"]:
            # These args should already be in the experiment_description
            continue
        if key == "timeout":
            experiment_description += (f"{key}: {format_num_secs(value)}\n")
        if key == "flowdroid_args":
            experiment_description += (f"{key}: {str(value.args)}\n")
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

    # # Setup experiment specific directories
    # experiment_dir_path = os.path.join("data", "experiments", experiment_id)

    # results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    # dir_paths = []
    # for dir_name in dir_names:
    #     dir_paths.append(os.path.join(experiment_dir_path, dir_name))
    # ic3_output_dir_path = os.path.join(experiment_dir_path, "ic3-output")
    # ic3_logs_dir_path = os.path.join(experiment_dir_path, "ic3-logs")
    # fd_output_dir_path = os.path.join(experiment_dir_path, "flowdroid-logs")
    
    for dir_path in [experiment_dir_path]:
        if not os.path.isdir(dir_path):
            os.mkdir(dir_path)

    # Record experiment description
    readme_path = os.path.join(experiment_dir_path, "README.txt")
    with open(readme_path, 'w') as file:
        file.write(experiment_description)

    experiment_log_path = os.path.join(experiment_dir_path, f"{experiment_id}.log")
    util.logger.set_all_loggers_file_handler(experiment_log_path)

    return experiment_id, experiment_dir_path


def flowdroid_experiment_generic(**kwargs):
    pass



def format_num_secs(secs: int) -> str:
    td = pd.Timedelta(seconds=secs)
    td = td.round('s')
    td.seconds // 60
    
    return f"{td.seconds // (60 * 60)}:{(td.seconds % (60 * 60)) // 60}:{td.seconds % (60)}"

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