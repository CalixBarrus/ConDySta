

import pytest

from experiment.common import load_logcat_files_batch, subset_setup_generic
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks



@pytest.mark.parametrize("benchmark_name, logcat_files_directory, expected_da_results",
    [
        ("fossdroid", "tests/data-persistent/mock_da_results/fossdroid", 1),
        ("gpbench", "tests/data-persistent/mock_da_results/gpbench", 1),
    ],)
def test_load_logcat_files_batch_smoke(benchmark_name, logcat_files_directory, expected_da_results):

    file_paths = get_wild_benchmarks(benchmark_name)[0]
    file_paths = subset_setup_generic(file_paths, "full")

    df = LoadBenchmark(file_paths).execute()
    input_identifier = "Input Model"
    
    load_logcat_files_batch(logcat_files_directory, input_identifier, df, output_col="logcat_file")

    assert sum(df["logcat_file"] != "") == expected_da_results
