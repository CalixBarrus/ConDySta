


import os
import shutil
from unittest.mock import Mock
import pytest
import experiment
from experiment.load_benchmark import LoadBenchmark
from experiment.load_benchmark import get_wild_benchmarks
from experiment.benchmark_name import BenchmarkName
from experiment.common import get_flowdroid_file_paths, subset_setup_generic
from experiment.experiments_2_10_25 import da_observation_report, harness_based_on_observations, hybrid_flow_postprocessing_single, run_fd_on_apks
import pandas as pd

import hybrid
from hybrid.flowdroid import FlowdroidArgs
from hybrid.hybrid_config import flowdroid_logs_path
from hybrid.log_process_fd import get_count_found_sources
import intercept
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

    # analysis_with_da_observations_harnessed(temp_workdir, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs)

    observation_harnessed_apks_column = "observation_harnessed_apks"

    harness_based_on_observations(temp_workdir, test_data_df, da_results_directory, harness_observations, observation_harnessed_apks_column)

    run_fd_on_apks(temp_workdir, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs, observation_harnessed_apks_column)

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

    observation_harnessed_apks_column = "observation_harnessed_apks"
    harness_based_on_observations(temp_workdir_delete_by_client, test_data_df, da_results_directory, harness_observations, observation_harnessed_apks_column)
    run_fd_on_apks(temp_workdir_delete_by_client, test_data_df, da_results_directory, default_ss_list, harness_observations, mock_flowdroid_kwargs, observation_harnessed_apks_column)

    output_log_path = flowdroid_logs_path(os.path.join(temp_workdir_delete_by_client, "flowdroid-logs"), test_data_df.at[0, "Input Model"])
    count_found_sources, _ = get_count_found_sources(output_log_path)

    assert count_found_sources > 0

    shutil.rmtree(temp_workdir_delete_by_client)


def test_hybrid_flow_postprocessing_single_smoke_and_observe_columns(mocker):
    # In this test, we want to feed the function a bunch of hand-made dataframes, and make sure all the left-joins work the way they should.
    # Use mocks so we can skip the step of parsing logs and just use hand-made dataframes

    # ["source_function", "source_enclosing_method", "source_enclosing_class", "", "", ""]
    mock_df_reported_flows = pd.DataFrame({ 
                    "source_function": ["taint1", "taint1", "taint1", "taint2", "taint2", "taint3", "taintmax", "taint_not_in_mapping"], 
                    "source_enclosing_method": ["a()", "a()", "a()", "a()", "a()", "mlem()", "mlem()", "mlem()"],
                    "source_enclosing_class": ["Foo", "Foo", "Foo", "Foo", "Foo", "Cats", "Cats", "Cats"],
                    "sink_function": ["sink1()", "sink2()", "sink1()", "sink2()", "sink1()", "sink2()", "sinkmax()", "sink_not_mapped()"],
                    "sink_enclosing_method": ["zap()", "zap()", "zap()", "zap()", "zap()", "zap()", "zapmax()", "zapmax()"],
                    "sink_enclosing_class": ["Bar", "Bar", "Bar", "Bar", "Bar", "Bar", "Bar", "Bar"],
                    })
    # cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method", "Observed Strings"]
    mock_df_observation_harness_to_string_set_map = pd.DataFrame({ 
                    "Observed Strings": [set(["secret1"]), set(["secret2"]), set(["***secret1***"]), set(["secretmax1", "secretmax2"]), set(["secret_unused"])], 
                    "Taint Function Name": ["taint1", "taint2", "taint3", "taintmax", "taint4"],
                    "Enclosing Method": ["a()", "a()", "mlem()", "mlem()", "mlem()"],
                    "Enclosing Class": ["Foo", "Foo", "Cats", "Cats", "Cats"],
                    })
    # cols = ["observed_string", "original_source_method", "scenario", "original_source_enclosing_method", "original_source_enclosing_class"]
    mock_df_observed_string_to_original_source_map = pd.DataFrame({
                    "observed_string": ["secret1", "secret1", "secret2", "secret3", "***secret1***", "***secret2***"],
                    "scenario": ["profile", "profile-observation", "profile", "profile", "intercept", "intercept"],
                    "original_source_method": ["getSecret()", "getSecret()", "", "", "getImei()", "getLocale()"],
                    "original_source_enclosing_method": ["", "kibble()", "", "", "build()", "build()"],
                    "original_source_enclosing_class": ["", "CatTown/", "", "", "CatTown/", "CatTown/"],
                    })

    # output of these are only used with other mocked functions
    # hybrid.log_process_fd.get_flowdroid_flows = Mock()
    # mocker.patch("hybrid.log_process_fd.get_flowdroid_flows")
    mocker.patch("experiment.experiments_2_10_25.get_flowdroid_flows")
    mocker.patch("experiment.experiments_2_10_25.get_observations_from_logcat_single", return_value=("", ""))
    mocker.patch("experiment.experiments_2_10_25.DecodedApkModel")
    
    # intercept.decoded_apk_model.DecodedApkModel.__init__ = Mock()

    # get_reported_fd_flows_as_df(reported_fd_flows, col_names=cols)
    mocker.patch("experiment.experiments_2_10_25.get_reported_fd_flows_as_df", return_value=mock_df_reported_flows)
    # hybrid.flow.get_reported_fd_flows_as_df = Mock(return_value=mock_df_reported_flows)
    
    # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model, observations, observed_strings)
    experiment.flow_mapping.get_observation_harness_to_string_set_map = Mock(return_value=mock_df_observation_harness_to_string_set_map)
    
    # get_observed_string_to_original_source_map(benchmark_name, logcat_file, columns=cols)
    experiment.flow_mapping.get_observed_string_to_original_source_map = Mock(return_value=mock_df_observed_string_to_original_source_map)

    # none of the args should be getting passed to functions that aren't mocked
    df = hybrid_flow_postprocessing_single(None, None, None, None, None, None)

    print(df.columns)

    # Non-empty as a sanity check that something happened
    assert len(df > 1)
    
