


import os
import shutil
import pytest
from experiment.load_benchmark import LoadBenchmark
from experiment.load_benchmark import get_wild_benchmarks
from experiment.benchmark_name import BenchmarkName
from experiment.common import get_flowdroid_file_paths, subset_setup_generic
from experiment.experiments_2_10_25 import analysis_with_da_observations_harnessed, da_observation_report
import pandas as pd

from hybrid.flowdroid import FlowdroidArgs
from hybrid.hybrid_config import flowdroid_logs_path
from hybrid.log_process_fd import get_count_found_sources
from intercept.instrument import HarnessObservations

@pytest.fixture
def test_data_df(benchmark_name):

    file_paths = get_wild_benchmarks(benchmark_name)[0]

    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            file_paths['ids_subset'] = [0]
        case BenchmarkName.GPBENCH:
            file_paths['ids_subset'] = [1]

    df = LoadBenchmark(file_paths).execute()

    return df


@pytest.fixture
def temp_workdir():
    relative_path = "tests/data/temp_test_output"

    if not os.path.isdir(relative_path):
        os.makedirs(relative_path)
        

    yield relative_path

    shutil.rmtree(relative_path)
    # os.removedirs(relative_path)

@pytest.fixture
def temp_workdir_delete_by_client():
    relative_path = "tests/data/temp_test_output_delete_me"

    if not os.path.isdir(relative_path):
        os.makedirs(relative_path)
    else: 
        shutil.rmtree(relative_path)
        os.makedirs(relative_path)

    yield relative_path

    # shutil.rmtree(relative_path)

@pytest.fixture
def da_observation_report_inspection_directory(benchmark_name: BenchmarkName):

    relative_path = "tests/data/da_observation_report_inspection_test_" + benchmark_name.value

    if not os.path.isdir(relative_path):
        os.makedirs(relative_path)
    else:
        shutil.rmtree(relative_path)
        os.makedirs(relative_path)

    yield relative_path

    # Don't delete after the test so it can be inspected
    # os.removedirs(relative_path)



@pytest.fixture()
def da_results_directory(benchmark_name):
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            return "tests/data-persistent/mock_da_results/fossdroid"
        case BenchmarkName.GPBENCH:
            return "tests/data-persistent/mock_da_results/gpbench"
        case _:
            assert False, "Invalid benchmark name"
        
    # if benchmark_name == "fossdroid":
    #     return "tests/data/mock_da_results/fossdroid"
    # elif benchmark_name == "gpbench":
    #     return "tests/data/mock_da_results/gpbench"
    
    

@pytest.fixture()
def default_ss_list(benchmark_name):
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            return "data/sources-and-sinks/SS-from-fossdroid-ground-truth.txt"
        case BenchmarkName.GPBENCH:
            return "data/sources-and-sinks/ss-gpl.txt"
        case _:
            assert False, "Invalid benchmark name"
            

@pytest.fixture()
def harness_observations():
    return HarnessObservations([])

@pytest.fixture()
def mock_flowdroid_kwargs():
    flowdroid_kwargs = get_flowdroid_file_paths()
    flowdroid_kwargs["timeout"] = 3 # seconds

    flowdroid_kwargs["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
    return flowdroid_kwargs


@pytest.mark.parametrize("benchmark_name",
    [
        (BenchmarkName.FOSSDROID),
        (BenchmarkName.GPBENCH),
    ],)
def test_analysis_with_da_observations_harnessed_smoke(test_data_df, benchmark_name, temp_workdir, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs):

    analysis_with_da_observations_harnessed(temp_workdir, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs)
    assert True


@pytest.mark.parametrize("benchmark_name",
    [
        (BenchmarkName.FOSSDROID),
        (BenchmarkName.GPBENCH),
    ],)
def test_da_observation_report_smoke(benchmark_name, test_data_df, da_results_directory, temp_workdir):

    da_observation_report(da_results_directory, test_data_df, temp_workdir)

@pytest.mark.parametrize("benchmark_name",
    [
        (BenchmarkName.FOSSDROID),
        (BenchmarkName.GPBENCH),
    ],)
def test_da_observation_report_manual_inspection(benchmark_name, test_data_df, da_results_directory, da_observation_report_inspection_directory):

    da_observation_report(da_results_directory, test_data_df, da_observation_report_inspection_directory)


@pytest.mark.parametrize("benchmark_name",
    [
        (BenchmarkName.FOSSDROID),
        # (BenchmarkName.GPBENCH),
    ],)
def test_analysis_with_da_observations_harnessed_fd_recognizes_inserted_sources(temp_workdir_delete_by_client, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs):
    mock_flowdroid_kwargs["timeout"] = 60
    analysis_with_da_observations_harnessed(temp_workdir_delete_by_client, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs)

    output_log_path = flowdroid_logs_path(os.path.join(temp_workdir_delete_by_client, "flowdroid-logs"), test_data_df.at[0, "Input Model"])
    count_found_sources, _ = get_count_found_sources(output_log_path)

    assert count_found_sources > 0

    shutil.rmtree(temp_workdir_delete_by_client)