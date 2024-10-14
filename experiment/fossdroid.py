from subprocess import TimeoutExpired
import time
from typing import Dict, List
import typing
import xml.etree.ElementTree as ET

import pandas as pd

from experiment import external_path
from experiment.common import benchmark_df_base_from_batch_input_model, flowdroid_setup_generic, get_flowdroid_file_paths, format_num_secs, get_fossdroid_files, get_fossdroid_source_sink_list_path, setup_additional_directories, setup_dirs_with_dependency_info, setup_experiment_dir
from experiment.flowdroid_experiment import experiment_setup_and_save_csv_fixme, flowdroid_on_benchmark_df
from hybrid.flow import Flow
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig
from hybrid.log_process_fd import FlowdroidLogException, get_flowdroid_reported_leaks_count, get_flowdroid_analysis_error, get_flowdroid_memory, get_flowdroid_flows
import util.logger
from util.input import BatchInputModel, InputModel, find_apk_paths_in_dir_recursive, input_apks_from_dir
logger = util.logger.get_logger(__name__)

#### Start fossdroid Settings Hierarchy

def flowdroid_on_fossdroid_setup_small():
    benchmark_name = "fossdroid"
    size = "small"
    experiment_args = flowdroid_setup_generic(get_fossdroid_files(), size)

    experiment_args["experiment_name"] = f"fd-on-{benchmark_name}-{size}"
    experiment_args["experiment_description"] = f"Run Flowdroid on {benchmark_name} benchmark"
    experiment_args["experiment_description"] += f" but just a handful of apps"    
    return experiment_args

def flowdroid_on_fossdroid_setup_full():
    benchmark_name = "fossdroid"
    size = "small"
    experiment_args = flowdroid_setup_generic(get_fossdroid_files(), size)

    experiment_args["experiment_name"] = f"fd-on-{benchmark_name}-{size}"
    experiment_args["experiment_description"] = f"Run Flowdroid on {benchmark_name} benchmark"
    return experiment_args

def flowdroid_on_fossdroid_setup_misc() -> Dict[str, typing.Any]:
    benchmark_name = "fossdroid"
    size = "misc"
    experiment_args = flowdroid_setup_generic(get_fossdroid_files(), size)

    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([27])
    experiment_args["experiment_name"] = "fd-on-fossdroid-temp"
    experiment_args["experiment_description"] = ""
    return experiment_args

#### End fossdroid Settings Hierarchy

def fossdroid_main():
    # This rewrites the source sink list
    file_paths = get_fossdroid_files() | get_flowdroid_file_paths()
    test_fossdroid_experiment_15min_fd_configs(**file_paths)

def test_fossdroid_validation_experiment():
    experiment_args = flowdroid_on_fossdroid_setup_misc()

    experiment_args["ids_subset"] = None

    fossdroid_default_csv_path = "data/benchmark-descriptions/fossdroid_config_aplength5_replication1.csv"
    fossdroid_best_csv_path = "data/benchmark-descriptions/fossdroid_config_2way2_replication1.csv"

    experiment_args["timeout"] = 60 * 60 # 1 hour
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)

    experiment_args["experiment_name"] = f"fd-on-fossdroid-default-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with default settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_default_csv_path

    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)

    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.best_fossdroid_settings)
    experiment_args["experiment_name"] = f"fd-on-fossdroid-best-mordahl-validation"
    experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with Mordahl's best DB3 settings, compare with Mordahl's experiment"
    experiment_args["benchmark_description_path"] = fossdroid_best_csv_path

    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


def single_fossdroid_experiment(**file_paths):
    # experiment_args = fossdroid_experiment_setup_misc(**file_paths)
    # experiment_args = fossdroid_experiment_setup_default_fd_full(**file_paths)
    experiment_args = flowdroid_on_fossdroid_setup_small(**file_paths)
    
    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


def test_fossdroid_experiment_15min_fd_configs(**file_paths):

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings), 
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified), 
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:
        
        experiment_args = flowdroid_on_fossdroid_setup_full(**file_paths)
        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-fossdroid-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with {settings_description_suffix}"
        experiment_args["timeout"] =  15 * 60

        experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


