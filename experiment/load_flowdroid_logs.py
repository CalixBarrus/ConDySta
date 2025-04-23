from hybrid import hybrid_config
from util.input import InputModel


import pandas as pd


import os


def load_flowdroid_logs_batch(fd_experiment_directory: str, df: pd.DataFrame, output_column: str="") -> pd.DataFrame:
    # Expects "Input Model" column in df
    # operates both in place and returns the input df

    if output_column == "":
        output_column = "fd_log_path"

    # append flowdroid-logs to the experiment directory if not already there
    target_dir_base_name = "flowdroid-logs"
    if not os.path.basename(fd_experiment_directory) == target_dir_base_name:
        fd_experiment_directory = os.path.join(fd_experiment_directory, target_dir_base_name)
    assert os.path.exists(fd_experiment_directory), f"Flowdroid experiment directory does not exist: {fd_experiment_directory}"

    x: InputModel
    df[output_column] = df["Input Model"].apply(lambda x: hybrid_config.flowdroid_logs_path(fd_experiment_directory, x))


    return df