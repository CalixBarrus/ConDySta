

# postprocess some flows, 
# 
# 
# reconstruct hybrid flows

# Compare with g.t. flows 

#     

import os

from experiment import common
from experiment.batch import process_as_dataframe
from experiment.benchmark_name import lookup_benchmark_name
from experiment.flow_mapping import get_observation_harness_to_observed_source_map, get_observation_harness_to_string_set_map, get_observed_source_to_original_source_map, get_observed_string_to_original_source_map
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.load_flowdroid_logs import load_flowdroid_logs_batch
from hybrid.dynamic import get_observations_from_logcat_single
from hybrid.log_process_fd import get_flowdroid_flows
from intercept.instrument import HarnessObservations
import util.logger
logger = util.logger.get_logger(__name__)

def reconstruct_hybrid_flows():

    sa_results_directory = "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY"
    sa_results_directory = os.path.join(sa_results_directory, "flowdroid-logs")

    da_results_directory = "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-outputs"

    benchmark = lookup_benchmark_name(sa_results_directory)

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    input_df = LoadBenchmark(df_file_paths).execute()

    # load fd log paths
    load_flowdroid_logs_batch(sa_results_directory, input_df, "fd_log_path")
    harnesser = ""

    # load logcat paths
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", input_df, output_col="logcat_file")

    # get flows from logs
    # pass blank apk_path since it's only used for some tag deep in the XML flow objects
    process_as_dataframe(get_flowdroid_flows, [True, False], [])("fd_log_path", "", input_df=input_df, output_col="flows_list")
    
    # get_observations_from_logcat_single(logcat_path: str, with_observed_strings: bool)
    process_as_dataframe(get_observations_from_logcat_single, [True, False], [])("logcat_file", True, input_df=input_df, output_col=["observations_list", "observed_strings_list"])
    
    # get flow mappings
    # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]])
    mappings: Series[DataFrame] = process_as_dataframe(get_observation_harness_to_string_set_map, [False, True, True, True], [])(harnesser, "readonly_decoded_apk_model", "observations_list", "observed_strings_list", input_df=input_df, output_col="")
    get_observed_string_to_original_source_map(benchmark_name: BenchmarkName, logcat_file: str="", columns: List[str]=[])

    apply_flow_mapping

    

def get_corresponing_harnesser(sa_results_directory) -> HarnessObservations:

    raise NotImplementedError()
    return HarnessObservations()


    