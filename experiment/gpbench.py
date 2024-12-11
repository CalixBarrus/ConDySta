
from subprocess import CalledProcessError, TimeoutExpired
import time
import typing

import numpy as np

from experiment import external_path
from experiment.LoadBenchmark import get_gpbench_files
from experiment.benchmarks import flowdroid_experiment_many_fd_configs
from experiment.common import benchmark_df_base_from_batch_input_model, flowdroid_setup_generic, format_num_secs, setup_additional_directories, setup_dirs_with_ic3
from experiment.flowdroid_experiment import experiment_setup_and_save_csv_fixme, flowdroid_on_benchmark_df, groundtruth_df_from_xml, process_fd_log_stats, results_df_from_benchmark_df
from hybrid.flowdroid import run_flowdroid, run_flowdroid_help, run_flowdroid_paper_settings, run_flowdroid_with_fdconfig
from hybrid.ic3 import run_ic3_on_apk, run_ic3_script_on_apk
from hybrid.log_process_fd import get_flowdroid_reported_leaks_count
from hybrid.results import HybridAnalysisResult
from util.input import BatchInputModel, InputModel, input_apks_from_dir
from util.subprocess import run_command_direct


import util.logger
logger = util.logger.get_logger(__name__)


#### Start Actual Experiment end points

def test_small_flowdroid_on_gpbench():
    benchmark_name = "gpbench"
    size = "small"
    experiment_args = flowdroid_setup_generic(get_gpbench_files(), size)
    experiment_args["experiment_name"] = f"fd-on-{benchmark_name}-{size}"
    experiment_args["experiment_description"] = f"Run Flowdroid on {benchmark_name} benchmark"
    # experiment_args = gpbench_experiment_setup_small()

    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


def test_gbpench_experiment_1hr_many_fd_configs():
    timeout = 60 * 60
    benchmark_files = get_gpbench_files()
    benchmark_files["timeout"] = timeout
    flowdroid_experiment_many_fd_configs(benchmark_files, size="full")


def test_gpbench_experiment_test_many_fd_configs():
    timeout =  15 * 60
    # ids_subset = [2,3,4,5]
    
    benchmark_files = get_gpbench_files()
    benchmark_files["timeout"] = timeout
    flowdroid_experiment_many_fd_configs(benchmark_files, size="small")


