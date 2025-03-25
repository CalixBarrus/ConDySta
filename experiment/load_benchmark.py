import os
from experiment import external_path
from experiment.benchmark_name import BenchmarkName
from experiment.common import benchmark_df_from_benchmark_directory_path, get_project_root_path, source_sink_dir_path
from experiment.paths import StepInfoInterface


import pandas as pd


from typing import Dict, List, Tuple

from hybrid.source_sink import create_source_sink_file_ssgpl


def get_fossdroid_source_sink_list_path() -> str:
    project_root = get_project_root_path()
    return os.path.join(project_root, "data", "sources-and-sinks", "SS-from-fossdroid-ground-truth.txt")

#### These are config loadouts for LoadBenchmarkInputs

def get_fossdroid_files() -> Dict[str, str]:
    fossdroid_benchmark_dir_path = external_path.fossdroid_benchmark_apks_dir_path
    fossdroid_ground_truth_xml_path = external_path.fossdroid_ground_truth_xml_path
    fossdroid_description_path = os.path.join(get_project_root_path(), "data/benchmark-descriptions/fossdroid-ids-ordering.csv")

    return {
            "benchmark_name": "fossdroid",
            "benchmark_dir_path": fossdroid_benchmark_dir_path,
            "ground_truth_xml_path": fossdroid_ground_truth_xml_path,
            "source_sink_list_path": get_fossdroid_source_sink_list_path(),
            "benchmark_description_path": fossdroid_description_path,
            }


def get_ssgpl_list_path():
    """ Generate the file path where SS-GooglePlayLogin.txt is expected. Generate it if it's not present."""
    sources_sinks_dir_path = source_sink_dir_path() # type: ignore
    ssgpl_list_path = os.path.join(sources_sinks_dir_path, "SS-GooglePlayLogin.txt")

    if not os.path.isfile(ssgpl_list_path):
        create_source_sink_file_ssgpl(ssgpl_list_path)

    return ssgpl_list_path


def get_gpbench_files() -> Dict[str,str]:
    gpbench_apks_dir_path: str = external_path.gpbench_apks_dir_path
    ground_truth_xml_path = external_path.gpbench_ground_truth_xml_path
    gpbench_description_path = os.path.join(get_project_root_path(), "data/benchmark-descriptions/gpbench-info.csv")
    return {
            "benchmark_name": "gpbench",
            "benchmark_dir_path": gpbench_apks_dir_path,
            "ground_truth_xml_path": ground_truth_xml_path,
            "benchmark_description_path": gpbench_description_path,
            "source_sink_list_path": get_ssgpl_list_path(),
            }


def get_droidbench_ss_list_path() -> str:
    # "data/sources-and-sinks/SS-Bench.txt"
    return os.path.join(get_project_root_path(), "data", "sources-and-sinks", "SS-Bench.txt")


def get_droidbench_files_paths3() -> Dict[str, str]:
    droidbench_apks_dir_path: str = external_path.droidbench_apks_dir_path
    "data/sources-and-sinks/SS-Bench.txt"
    return {
            "benchmark_name": "droidbench3",
            "benchmark_dir_path": droidbench_apks_dir_path,
            # "ground_truth_xml_path": ground_truth_xml_path, 
            # "benchmark_description_path": gpbench_description_path,
            "source_sink_list_path": get_droidbench_ss_list_path(),
            }


def get_wild_benchmarks(benchmark_name: str="") -> List[Dict[str, str]]:
    fossdroid_files: Dict[str, str] = get_fossdroid_files()
    gpbench_files: Dict[str, str] = get_gpbench_files()

    if benchmark_name == "fossdroid":
        return [fossdroid_files]
    elif benchmark_name == BenchmarkName.FOSSDROID:
        return [fossdroid_files]
    elif benchmark_name == "gpbench":
        return [gpbench_files]
    elif benchmark_name == BenchmarkName.GPBENCH:
        return [gpbench_files]
    elif benchmark_name == "all":
        return [fossdroid_files, gpbench_files]
    else:
        return [fossdroid_files]
        # return [gpbench_files]
        # return [fossdroid_files, gpbench_files]

class LoadBenchmark(StepInfoInterface):
    def __init__(self, benchmark_files: Dict[str, str]) -> None:
        super().__init__()
        self.benchmark_files = benchmark_files

    @property
    def step_name() -> str:
        return "LoadBenchmark"

    @property
    def version() -> Tuple[int]:
        raise (0,1,0)

    @property
    def concise_params() -> List[str]:
        raise NotImplementedError

    @property
    def params() -> List[str]:
        raise NotImplementedError

    def execute(self) -> pd.DataFrame:
        # Input: nothing
        # Output: df with columns "Benchmark ID", "Input Model"
        
        benchmark_files = self.benchmark_files
        benchmark_directory_path: str = benchmark_files["benchmark_dir_path"]
        benchmark_description_path = (benchmark_files["benchmark_description_path"] if "benchmark_description_path" in benchmark_files.keys() else "")
        ids_subset = (benchmark_files["ids_subset"] if "ids_subset" in benchmark_files.keys() else None)

        return benchmark_df_from_benchmark_directory_path(benchmark_directory_path, benchmark_description_path, ids_subset)



class LoadDefaultSourceSink():
    pass

    # TODO: should suck out the functionality of _get_source_sink_factory
    # for now just match up the column name

    def get_ss_list():
        # GPBench gt based list, Fossdroid gt based list, fd default ss list, super custom column prepped by ???
        pass

