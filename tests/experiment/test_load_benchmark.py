



import pytest
from experiment.load_benchmark import get_wild_benchmarks
from experiment.common import benchmark_df_from_benchmark_directory_path, subset_setup_generic


@pytest.mark.parametrize("benchmark_name, expected_count", 
    [
        ("fossdroid", 30),
        ("gpbench", 19),
    ],)
def test_benchmark_df_from_benchmark_directory_path_correct_count(benchmark_name, expected_count):

    file_paths = get_wild_benchmarks(benchmark_name)[0]
    file_paths = subset_setup_generic(file_paths, "full")

    df = benchmark_df_from_benchmark_directory_path(file_paths["benchmark_dir_path"],
                                                    benchmark_description_csv_path=file_paths["benchmark_description_path"] if "benchmark_description_path" in file_paths else "",
                                                    ids_subset=file_paths["ids_subset"] if "ids_subset" in file_paths else None)
    
    assert len(df) == expected_count


