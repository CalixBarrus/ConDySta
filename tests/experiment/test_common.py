

import pytest
from experiment import load_benchmark
from experiment.load_benchmark import get_wild_benchmarks
from experiment.common import load_logcat_files_batch, subset_setup_generic



@pytest.mark.parametrize("benchmark_name, logcat_files_directory", 
    [
        ("fossdroid", 30),
        ("gpbench", 19),
    ],)
def test_load_logcat_files_batch(benchmark_name, logcat_files_directory):

    file_paths = get_wild_benchmarks(benchmark_name)[0]
    file_paths = subset_setup_generic(file_paths, "full")

    df = load_benchmark(file_paths).execute()
    input_identifier = "Input Model"
    
    load_logcat_files_batch(logcat_files_directory, input_identifier, df, output_col="logcat_file")
