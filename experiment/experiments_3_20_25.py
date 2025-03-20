import os
import sys
from typing import List, Tuple

import pandas as pd

from experiment.benchmark_name import BenchmarkName
from experiment.common import setup_experiment_dir
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from hybrid.log_process_fd import flowdroid_time_path_from_log_path, get_count_found_sources, get_flowdroid_analysis_error, get_flowdroid_memory, get_flowdroid_reported_leaks_count, get_flowdroid_time
from util.input import InputModel


def fd_report_basic_custom_all():
    reports_dir = "data/experiments/fd_report_basic"
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)

    for benchmark, sa_results in [
        (BenchmarkName.GPBENCH, "data/experiments/2025-03-11-_SA-with-observations-harnessed_gpbench_0.1.1"),
        (BenchmarkName.FOSSDROID, "data/experiments/2025-03-11-_SA-with-observations-harnessed_fossdroid_0.1.1_intercept"),
        (BenchmarkName.FOSSDROID, "data/experiments/2025-03-11-_SA-with-observations-harnessed_fossdroid_0.1.1_shallow")]:

        fd_report_basic_runner(benchmark, sa_results, reports_dir)

def fd_report_basic_runner(benchmark: BenchmarkName, sa_results: str, results_dir: str):
    report_name = "fd_report_basic-" + os.path.basename(sa_results)

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    
    # Setup up workdir and documentation
    # experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
    #                                                                 {"sa_results": sa_results, 
    #                                                                  } | df_file_paths)
    # workdir = experiment_directory_path

    # actually construct dependencies
    df = LoadBenchmark(df_file_paths).execute()

    df = load_flowdroid_logs(sa_results, df, "fd_log_path")

    fd_report_basic_batch("fd_log_path", "Input Model", df, "Benchmark ID", ["App Name", "Sources", "Leaks", "Error", "Time", "Memory"]
                          ).to_csv(os.path.join(results_dir, f"{report_name}.csv"))

def fd_report_basic_batch(fd_log_path: str, input_model: str, input_df: pd.DataFrame, key_col: str, output_cols: List[str]) -> pd.DataFrame:
    rows = []
    for i in input_df.index:
        rows.append(fd_report_basic_single(input_df.at[i, fd_log_path],  input_df.at[i, input_model]))

        # assert len(outout_cols) == len(rows[0])

    result = pd.DataFrame(rows, columns=output_cols)
    return result
        

def fd_report_basic_single(fd_log_path: str, input_model: InputModel) -> Tuple:

    app_name = input_model.input_identifier()
    
    if not os.path.exists(fd_log_path):
        return (app_name, "", "", "No log", "", "")

    count_reported_leaks = get_flowdroid_reported_leaks_count(fd_log_path)
    if count_reported_leaks is None:
        count_reported_leaks
    flowdroid_error = get_flowdroid_analysis_error(fd_log_path)

    flowdroid_memory = get_flowdroid_memory(fd_log_path)
    flowdroid_time = get_flowdroid_time(flowdroid_time_path_from_log_path(fd_log_path))
    count_found_sources, _ = get_count_found_sources(fd_log_path)
    
    return app_name, str(count_found_sources), str(count_reported_leaks), flowdroid_error, flowdroid_time, flowdroid_memory

def load_flowdroid_logs(fd_experiment_directory: str, df: pd.DataFrame, output_column: str="") -> pd.DataFrame:

    if output_column == "":
        output_column = "fd_log_path"

    target_dir_base_name = "flowdroid-logs"
    if not os.path.basename(fd_experiment_directory) == target_dir_base_name:
        fd_experiment_directory = os.path.join(fd_experiment_directory, target_dir_base_name)

    assert os.path.exists(fd_experiment_directory), f"Flowdroid experiment directory does not exist: {fd_experiment_directory}"
    assert os.path.basename(fd_experiment_directory) == target_dir_base_name, f"Flowdroid experiment directory does not have the expected name: {fd_experiment_directory}"

    x: InputModel
    df[output_column] = df["Input Model"].apply(lambda x: os.path.join(fd_experiment_directory, x.input_identifier() + ".log"))

    return df


if __name__ == "__main__":
    # change working directory to the root of the project
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

    fd_report_basic_custom_all()