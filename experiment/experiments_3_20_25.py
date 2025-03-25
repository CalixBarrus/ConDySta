from enum import Enum
import enum
import os
import sys
from typing import List, Tuple

import pandas as pd

from experiment.benchmark_name import BenchmarkName
from experiment.common import get_experiment_name, get_flowdroid_file_paths, setup_experiment_dir
from experiment.flowdroid_experiment import flowdroid_on_benchmark_df
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.load_source_sink import get_default_source_sink_path
from hybrid.flowdroid import FlowdroidArgs
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

def rerun_fd_baseline():
    for ss_list_description in ["ss-per-scenario", "ss-full-fd-default"]:
        for benchmark in BenchmarkName:
            # params_in_name = [da_results_specifier.value] if da_results_specifier != DynamicResultsSpecifier.GPBENCH else []
            # params_in_name.append(analysis_constraints.name)
            timeout = 30 * 60 # seconds
            timeout_description = "30min-timeout"
            # timeout = 1 * 1 # seconds
            # timeout_description = "1sec-timeout"

            # ss_list_description = "ss-per-scenario"
            # ss_list_description = "ss-full-fd-default"
            ss_list_path = get_default_source_sink_path(benchmark, ss_list_description == "ss-full-fd-default")

            experiment_name = get_experiment_name(benchmark.value, "flowdroid-baseline", (0,1,1), [timeout_description, ss_list_description])

            experiment_description = """Baseline run of FD on apps
            """

            # pull out all the relevant keyword args    
            # da_results_directory = get_da_results_directory(benchmark, da_results_specifier)
            default_ss_list = get_default_source_sink_path(benchmark)

            flowdroid_kwargs = get_flowdroid_file_paths() 
            flowdroid_kwargs["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
            flowdroid_kwargs["timeout"] = timeout

            df_file_paths = get_wild_benchmarks(benchmark)[0]
            df_file_paths["source_sink_list_path"] = ss_list_path # change from default that comes with get_wild_benchmarks
            
            # Setup up workdir and documentation
            experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                                            {
                                                                            } | flowdroid_kwargs | df_file_paths)
            workdir = experiment_directory_path

            # actually construct dependencies
            df = LoadBenchmark(df_file_paths).execute()
            # harness_observations = HarnessObservations()
            
            # no source_sink_column in kwargs, so it'll look up kwargs["source_sink_list_path"]
            kwargs = flowdroid_kwargs | {"source_sink_list_path": df_file_paths["source_sink_list_path"]}

            apks_column = "" # will look up input_model.apk().apk_path()
            flowdroid_on_benchmark_df(workdir, df, flowdroid_logs_directory_name="flowdroid-logs", apk_path_column=apks_column, **kwargs)
            # run_fd_on_apks(workdir, df, da_results_directory, default_ss_list, harness_observations, flowdroid_kwargs, observation_harnessed_apks_column)

class AnalysisConstraints(Enum):
    DEPTH_0_DA_RESULTS_ONLY = enum.auto() # imitate context sensitive ConDySTA
    DISABLE_FIELD_SENSITIVITY = enum.auto() # Base objects should be tainted. Expected to have more FP than enabled field sensitivity
    FULL_CONTEXT_AND_FIELD_SENSITIVITY = enum.auto()

class DynamicResultsSpecifier(Enum):
    GPBENCH = ""
    FOSSDROID_SHALLOW = "shallow"
    FOSSDROID_INTERCEPT = "intercept"



def get_da_results_directory(benchmark_name: BenchmarkName, specifier: DynamicResultsSpecifier) -> str:
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            if specifier == DynamicResultsSpecifier.FOSSDROID_SHALLOW:
                return "data/OneDrive_1_2-7-2025/2024-10-26-execution-full-fossdroid-extendedStrList-60s/logcat-output"
            elif specifier == DynamicResultsSpecifier.FOSSDROID_INTERCEPT:
                return "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"

        case BenchmarkName.GPBENCH:
            return "data/OneDrive_1_2-7-2025/initial-results-for-xiaoyin/2024-10-21-execution-full-gpbench-manual/logcat-output"
        
def test_get_da_results_directory():
    for benchmark_name, da_result_specifier in zip([BenchmarkName.GPBENCH, BenchmarkName.FOSSDROID, BenchmarkName.FOSSDROID], DynamicResultsSpecifier):
        assert os.path.exists(get_da_results_directory(benchmark_name, da_result_specifier))

    print("Success")

def run_all_HA_experiments():
    for benchmark_name, da_result_specifier in zip([BenchmarkName.GPBENCH, BenchmarkName.FOSSDROID, BenchmarkName.FOSSDROID], DynamicResultsSpecifier):
        for analysis_constraints in AnalysisConstraints:
            setup_and_run_analysis_by_benchmark_name(benchmark_name, da_result_specifier, analysis_constraints)

def setup_and_run_analysis_by_benchmark_name(benchmark: BenchmarkName, da_results_specifier: DynamicResultsSpecifier, analysis_constraints: AnalysisConstraints):
    
    params_in_name = [da_results_specifier.value] if da_results_specifier != DynamicResultsSpecifier.GPBENCH else []
    params_in_name.append(analysis_constraints.name)
    experiment_name = get_experiment_name(benchmark.value, "SA-with-observations-harnessed", (0,1,2), params_in_name)
    experiment_description = """Static analysis with observations harnessed
    Doesn't reinstrument apks if already done in the experiment directory.
    """

    # pull out all the relevant keyword args    
    da_results_directory = get_da_results_directory(benchmark, da_results_specifier)
    default_ss_list = get_default_source_sink_path(benchmark)

    flowdroid_kwargs = get_flowdroid_file_paths() 
    flowdroid_kwargs["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
    flowdroid_kwargs["timeout"] = 3 * 60 # seconds

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    
    # Setup up workdir and documentation
    experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                                    {"da_results_directory": da_results_directory, 
                                                                     } | flowdroid_kwargs | df_file_paths)
    workdir = experiment_directory_path

    # actually construct dependencies
    df = LoadBenchmark(df_file_paths).execute()
    harness_observations = HarnessObservations()

    observation_harnessed_apks_column = "observation_harnessed_apks"

    dont_reinstrument_apks = True
    if dont_reinstrument_apks:
        df[observation_harnessed_apks_column] = df["Input Model"].apply(lambda model: hybrid_config.apk_path(os.path.join(workdir, "rebuilt_apks"), model.apk()))
        mask = ~df[observation_harnessed_apks_column].apply(os.path.exists)
        logger.debug(f"Skipping {sum(~mask)} apks that are already instrumented")
    else: 
        mask = [True] * len(df)

    harness_based_on_observations(workdir, df[mask], da_results_directory, harness_observations, observation_harnessed_apks_column)

    run_fd_on_apks(workdir, df, da_results_directory, default_ss_list, harness_observations, flowdroid_kwargs, observation_harnessed_apks_column)

if __name__ == "__main__":
    # change working directory to the root of the project
    os.chdir(os.path.join(os.path.dirname(__file__), "..", ".."))

    fd_report_basic_custom_all()