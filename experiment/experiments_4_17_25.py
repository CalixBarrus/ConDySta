

# postprocess some flows, 
# 
# 
# reconstruct hybrid flows

# Compare with g.t. flows 

#     

import os

from experiment import common
from experiment.benchmark_name import lookup_benchmark_name
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.load_flowdroid_logs import load_flowdroid_logs_batch
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

    # load logcat paths
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", input_df, output_col="logcat_file")

    

    


    