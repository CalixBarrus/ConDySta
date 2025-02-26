
import os
import shutil
import pytest
from experiment.load_benchmark import get_fossdroid_files
from experiment.common import benchmark_df_from_benchmark_directory_path, flowdroid_setup_generic
from experiment.flowdroid_experiment import experiment_setup, flowdroid_on_benchmark_df

@pytest.fixture
def work_directory():

    directory = "tests/data/workdir"

    if not os.path.isdir(directory):
        os.makedirs(directory)

    yield directory

    shutil.rmtree(directory)
    # os.removedirs(directory)


def test_flowdroid_on_benchmark_df_smoke(work_directory):

    
    fossdroid_files = get_fossdroid_files() #TODO: this should iterate over between fossdroid, gpbench-L, gpbench-M
    kwargs = flowdroid_setup_generic(fossdroid_files, "small") 

    # experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**kwargs)
    benchmark_dir_path = kwargs["benchmark_dir_path"]
    benchmark_description_path = kwargs["benchmark_description_path"]
    ids_subset = kwargs["ids_subset"]
    df = benchmark_df_from_benchmark_directory_path(benchmark_dir_path, benchmark_description_csv_path=benchmark_description_path, ids_subset=ids_subset)
    
    flowdroid_on_benchmark_df(experiment_dir_path=work_directory, benchmark_df=df, **kwargs)