
import os
import pytest
from experiment.LoadBenchmark import get_fossdroid_files
from experiment.common import benchmark_df_from_benchmark_directory_path, flowdroid_setup_generic
from experiment.flowdroid_experiment import experiment_setup, flowdroid_on_benchmark_df

@pytest.fixture
def work_directory():

    work_directory = "tests/data/workdir"

    yield work_directory

@pytest.fixture
def flowdroid_logs(work_directory):

    yield os.path.join(work_directory, "flowdroid-logs")

def test_flowdroid_on_benchmark_df_smoke(work_directory, flowdroid_logs):

    
    fossdroid_files = get_fossdroid_files() #TODO: this should iterate over between fossdroid, gpbench-L, gpbench-M
    df = []
    kwargs = flowdroid_setup_generic(fossdroid_files, "small") 

    # experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**kwargs)
    benchmark_dir_path = kwargs["benchmark_dir_path"]
    benchmark_description_path = kwargs["benchmark_description_path"]
    ids_subset = kwargs["ids_subset"]
    df = benchmark_df_from_benchmark_directory_path(benchmark_dir_path, benchmark_description_csv_path=benchmark_description_path, ids_subset=ids_subset)
    
    flowdroid_on_benchmark_df(experiment_dir_path=work_directory, benchmark_df=df, flowdroid_logs_directory_name=flowdroid_logs, **kwargs)