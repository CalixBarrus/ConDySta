import os
from typing import Dict, List, Tuple

import numpy as np

from experiment import external_path
from experiment.load_benchmark import get_droidbench_files_paths3, get_fossdroid_files, get_gpbench_files, get_wild_benchmarks
from experiment.common import benchmark_df_from_benchmark_directory_path, flowdroid_setup_generic, get_flowdroid_file_paths, load_logcat_files_batch, observation_arguments_default, recent_experiment_directory_path, setup_additional_directories, setup_dirs_with_ic3, setup_experiment_dir, subset_setup_generic
from experiment.flowdroid_experiment import experiment_setup, experiment_setup_and_save_csv_fixme, filtering_flowdroid_comparison, flowdroid_comparison_with_observation_processing_experiment, flowdroid_on_benchmark_df, observation_processing, parse_flowdroid_results, summary_df_for_fd_comparison
from experiment.instrument import instrument_observations_batch, rebuild_apps_no_instrumentation
from hybrid.dynamic import get_observations_from_logcat_batch
import hybrid.hybrid_config
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_paper_settings
from hybrid.ic3 import run_ic3_on_apk, run_ic3_on_apk_direct
from hybrid.log_process_fd import get_flowdroid_reported_leaks_count
from hybrid.source_sink import create_source_sink_file_ssbench
from util.input import BatchInputModel, input_apks_from_dir, InputModel
import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)



def recent_instrumented_apps_for_wild_benchmark(benchmark_files: Dict[str, str], size: str) -> str:
    # TODO: this shouldn't necessarily care about the size keyword? It throws an error looking up "small" even if there's a recent "full"
    # Maybe this is just a usage issue tho

    # Right now, instrumented directories are named as f"instrument-{size}-{name}"
    if benchmark_files["benchmark_name"] == "fossdroid":
        instrumented_fossdroid_apks_dir_path = os.path.join(recent_experiment_directory_path(size, "instrument", "fossdroid"), "signed-apks")
        instrumented_apks_directory_path = instrumented_fossdroid_apks_dir_path
    elif benchmark_files["benchmark_name"] == "gpbench":
        instrumented_gpbench_apks_dir_path = os.path.join(recent_experiment_directory_path(size, "instrument", "gpbench"), "signed-apks")
        instrumented_apks_directory_path = instrumented_gpbench_apks_dir_path
    else: 
        assert False

    return instrumented_apks_directory_path

def recent_executions_for_wild_benchmark(benchmark_files: Dict[str, str], size: str, filter_word: str="") -> List[Tuple[Dict[str, str], str]]:
    # fossdroid_logcat_directory_path = os.path.join(recent_experiment_directory_path(size, "execution", "fossdroid"), "logcat-output")
    # gpbench_logcat_directory_path = os.path.join(recent_experiment_directory_path(size, "execution", "gpbench"), "logcat-output")

    # return [(files, fossdroid_logcat_directory_path) if files["benchmark_name"] == "fossdroid" else (files, gpbench_logcat_directory_path) for files in get_wild_benchmarks()]

    if benchmark_files["benchmark_name"] == "fossdroid":
        fossdroid_logcat_directory_path = os.path.join(recent_experiment_directory_path(size, "execution", "fossdroid", filter_word), "logcat-output")
        recent_execution_logcat_directory_path = fossdroid_logcat_directory_path
    elif benchmark_files["benchmark_name"] == "gpbench":
        gpbench_logcat_directory_path = os.path.join(recent_experiment_directory_path(size, "execution", "gpbench", filter_word), "logcat-output")
        recent_execution_logcat_directory_path = gpbench_logcat_directory_path
    else: 
        assert False

    return recent_execution_logcat_directory_path


def test_full_observation_processing():
    observation_processing_wild_benchmarks("full")

def test_small_observation_processing(filter_word=""):
    observation_processing_wild_benchmarks("small", filter_word)

def observation_processing_wild_benchmarks(size: str, filter_word: str=""):
    description = "test logcat processing"

    for benchmark_files in get_wild_benchmarks():
        experiment_args = subset_setup_generic(benchmark_files, size)
        ids_subset = experiment_args["ids_subset"]

        logcat_directory_path = recent_executions_for_wild_benchmark(benchmark_files, size, filter_word)
        name = benchmark_files["benchmark_name"]
        description = f"Testing observation processing on {name} benchmark"
        observation_processing_generic(logcat_directory_path, benchmark_files, f"logcat-processing-{size}-{name}", description, ids_subset)

def test_spotcheck_observation_processing(benchmark_files: Dict[str, str],  size: str, logcat_directory_path: str):

    name = benchmark_files["benchmark_name"]

    experiment_args = subset_setup_generic(benchmark_files, size)
    ids_subset = experiment_args["ids_subset"]
    # if name == "gpbench":
    #     ids_subset = pd.Series(range(1,20))
    # elif name == "fossdroid":
    #     ids_subset = None

    always_new_experiment_directory = experiment_args["always_new_experiment_directory"]

    description = f"Spot check for observation processing on {name} benchmark, for the execution in {logcat_directory_path}"
    observation_processing_generic(logcat_directory_path, benchmark_files, f"logcat-processing-spotcheck-{size}-{name}", description, ids_subset, always_new_experiment_directory)

    

def observation_processing_generic(logcat_directory_path: str, benchmark_files: Dict[str, str], experiment_name: str, experiment_description: str, ids_subset: List[int], always_new_experiment_directory: bool=False):
    experiment_args = {}
    experiment_args["experiment_name"] = experiment_name
    experiment_args["experiment_description"] = experiment_description
    experiment_args["always_new_experiment_directory"] = always_new_experiment_directory

    experiment_args["ids_subset"] = ids_subset
    experiment_args = experiment_args | benchmark_files

    experiment_args = experiment_args | observation_arguments_default(logcat_directory_path)

    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**experiment_args)

    results_df = observation_processing(experiment_dir_path, benchmark_df, **experiment_args)
    # if this were a args setup layer, this logic shouldn't be here
    results_df.to_csv(os.path.join(experiment_dir_path, "source_sink_paths.csv"))

def test_small_flowdroid_comparison_wild_benchmarks():
    flowdroid_comparison_wild_benchmarks("small")

def test_full_flowdroid_comparison_wild_benchmarks():
    flowdroid_comparison_wild_benchmarks("full")

def flowdroid_comparison_wild_benchmarks(size: str):

    for benchmark_files in get_wild_benchmarks():
        experiment_args = flowdroid_setup_generic(benchmark_files, size)

        logcat_directory_path = recent_executions_for_wild_benchmark(benchmark_files, "full", "intercept")
        experiment_args["logcat_directory_path"] = logcat_directory_path
        experiment_args["logcat_processing_strategy"] = "InstrReportReturnAndArgsDynamicLogProcessingStrategy"

        name = benchmark_files["benchmark_name"]
        experiment_args["experiment_name"] = f"flowdroid-comparison-{size}-{name}"
        description = f"Comparing flowdroid runs on {name} benchmark based on observations from {logcat_directory_path}"
        experiment_args["experiment_description"] = description

        flowdroid_comparison_with_observation_processing_experiment(**experiment_args)

        # flowdroid_comparison_generic(logcat_directory_path, benchmark_files, f"flowdroid-comparison-{size}-{name}", description, ids_subset)

def test_spot_check_flowdroid_comparison(benchmark_files: Dict[str, str], logcat_directory_path: str, ids_subset=None):
    # benchmark_files = {} # get_gpbench_files() or get_fossdroid_files()

    experiment_args = flowdroid_setup_generic(benchmark_files, "misc")
    experiment_args["timeout"] = 15 * 60
    experiment_args["ids_subset"] = ids_subset
    experiment_args["always_new_experiment_directory"] = True

    # logcat_directory_path = ""
    experiment_args["logcat_directory_path"] = logcat_directory_path
    experiment_args["logcat_processing_strategy"] = "InstrReportReturnAndArgsDynamicLogProcessingStrategy"


    name = benchmark_files["benchmark_name"]
    experiment_args["experiment_name"] = f"flowdroid-comparison-spotcheck-DELETE-{name}"
    description = f"Comparing flowdroid runs on {name} benchmark based on observations from {logcat_directory_path}"
    description += "\nSpot Check"
    experiment_args["experiment_description"] = description

    flowdroid_comparison_with_observation_processing_experiment(**experiment_args)

def test_spot_check_flowdroid_output_processing(size: str, flowdroid_logs_directory_path: str):
    
    experiment_args = subset_setup_generic(get_gpbench_files(), size)
    name = experiment_args["benchmark_name"]

    experiment_args["experiment_name"] = f"fd-log-processing-spotcheck-{size}-{name}"
    description = f"Parse flowdroid output from {flowdroid_logs_directory_path}"
    experiment_args["experiment_description"] = description

    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**experiment_args)
    results_df = parse_flowdroid_results(experiment_dir_path, benchmark_df, flowdroid_logs_directory_path, **experiment_args)
    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)

def test_spot_check_flowdroid_comparison_output_processing(size: str, unmodified_fd_logs_path: str, augmented_fd_logs_path: str, logcat_directory_path: str):
    experiment_args = subset_setup_generic(get_gpbench_files(), size)
    name = experiment_args["benchmark_name"]

    experiment_args["experiment_name"] = f"fd-log-processing-comparison-spotcheck-{size}-{name}"
    description = f"Parse flowdroid output from {unmodified_fd_logs_path} and {augmented_fd_logs_path}"
    experiment_args["experiment_description"] = description

    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**experiment_args)

    experiment_args = experiment_args | observation_arguments_default(logcat_directory_path)    
    source_sink_files: pd.DataFrame = observation_processing(experiment_dir_path, benchmark_df, **experiment_args)

    unmodified_source_sink_results = parse_flowdroid_results(experiment_dir_path, benchmark_df, unmodified_fd_logs_path, **experiment_args)
    # print(source_sink_files["Augmented Source Sink Path"].to_string())
    benchmark_df["Source Sink Path"] = source_sink_files["Augmented Source Sink Path"]
    # benchmark_df["Augmented Source Sink Path"] = source_sink_files["Augmented Source Sink Path"]
    # logger.debug(source_sink_files.to_string())
    benchmark_df["Observed Sources Path"] = source_sink_files["Observed Sources Path"]
    augmented_source_sink_results = parse_flowdroid_results(experiment_dir_path, benchmark_df, augmented_fd_logs_path, **experiment_args)

    filtering_flowdroid_comparison(experiment_dir_path, benchmark_df, unmodified_fd_logs_path, augmented_fd_logs_path, logcat_directory_path)

    count_discovered_sources = source_sink_files["Observed Source Signatures"]
    results_df = summary_df_for_fd_comparison(unmodified_source_sink_results, augmented_source_sink_results, count_discovered_sources)

    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)

    
def test_small_flowdroid_on_wild_benchmarks():
    flowdroid_on_wild_benchmarks("small")

def test_full_flowdroid_on_wild_benchmarks():
    flowdroid_on_wild_benchmarks("full")

def flowdroid_on_wild_benchmarks(size: str):
    for benchmark_files in get_wild_benchmarks():
        experiment_args = flowdroid_setup_generic(benchmark_files, size)

        name = benchmark_files["benchmark_name"]
        experiment_args["experiment_name"] = f"flowdroid-{size}-on-{name}"
        description = f"Flowdroid on {name} benchmark"
        experiment_args["experiment_description"] = description

        experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)



def test_spot_check_flowdroid_on_wild_benchmarks(benchmark_files: Dict[str, str], logcat_directory_path: str, ids_subset=None):
    experiment_args = flowdroid_setup_generic(benchmark_files, "misc")
    experiment_args["timeout"] = 3 * 60 * 60
    experiment_args["ids_subset"] = ids_subset
    experiment_args["always_new_experiment_directory"] = True

    name = benchmark_files["benchmark_name"]
    experiment_args["experiment_name"] = f"flowdroid-spotcheck-{name}"
    description = f"Flowdroid run on {name} benchmark."
    description += "\nSpot Check"
    experiment_args["experiment_description"] = description

    # experiment_args["source_sink_list_path"] = "data/sources-and-sinks/SS-GooglePlayLogin copy.txt"
    experiment_args["source_sink_list_path"] = "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"

    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)

def test_spot_check_flowdroid_on_droidbench3(size: str):
    benchmark_files = get_droidbench_files_paths3()

    experiment_args = flowdroid_setup_generic(benchmark_files, size)

    name = benchmark_files["benchmark_name"]
    experiment_args["experiment_name"] = f"flowdroid-{size}-on-{name}"
    description = f"Flowdroid on {name} benchmark"
    experiment_args["experiment_description"] = description

    experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


def flowdroid_experiment_many_fd_configs(benchmark_files: Dict[str, str], size="full"):
    benchmark_name = benchmark_files["benchmark_name"]
    # size = "full"
    experiment_args = flowdroid_setup_generic(benchmark_files, size)

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings),
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified),
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:


        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-{benchmark_name}-{size}-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the {size} {benchmark_name} dataset with Flowdroid settings: {settings_description_suffix}"



        experiment_setup_and_save_csv_fixme(flowdroid_on_benchmark_df, **experiment_args)


def test_rebuild_fossdroid_apks_small():
    file_paths = get_fossdroid_files()
    experiment_name = "rebuilt-and-unmodified-apks"
    experiment_description = "rebuild apks with no further changes"
    ids_subset = [0, 1]

    

    rebuild_apps_no_instrumentation(file_paths["benchmark_dir_path"], experiment_name, experiment_description, ids_subset)

def test_rebuild_wild_benchmarks_full():
    size = "full"
    rebuild_wild_benchmarks(size)

def test_rebuild_wild_benchmarks_several():
    size = "several"
    rebuild_wild_benchmarks(size)

def rebuild_wild_benchmarks(size: str):

    for benchmark_files in get_wild_benchmarks():
        # experiment_args = flowdroid_setup_generic(benchmark_files, size)
        experiment_args = subset_setup_generic(benchmark_files, size)

        benchmark_name = experiment_args["benchmark_name"]
        experiment_args["experiment_name"] = f"plain-rebuild-{size}-on-{benchmark_name}"
        experiment_name = experiment_args["experiment_name"]
        description = f"Plain rebuild of apps with APK Tool on {benchmark_name} benchmark"
        experiment_args["experiment_description"] = description
        experiment_description = experiment_args["experiment_description"]
        ids_subset = experiment_args["ids_subset"]

        rebuild_apps_no_instrumentation(experiment_args["benchmark_dir_path"], experiment_name, experiment_description, ids_subset)


def icc_bench_mac():
    benchmark_folder_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/benchmarks/gpbench/apks")
    # benchmark_folder_path: str = os.path.join(external_path.home_directory, "programming/benchmarks/gpbench")

    flowdroid_jar_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar")
    # flowdroid_jar_path: str = os.path.join(external_path.home_directory, "programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar")

    android_path: str = os.path.join(external_path.home_directory, "Library/Android/sdk/platforms/")
    # android_path: str = "/usr/lib/android-sdk/platforms/"

    source_sink_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt")
    # source_sink_path: str = os.path.join(external_path.home_directory, "programming/ConDySta/data/sources-and-sinks/ss-gpl.txt")

    icc_bench_dir_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/benchmarks/ICCBench20")

    ic3_jar_path = ""

    icc_bench(flowdroid_jar_path, android_path, icc_bench_dir_path, ic3_jar_path)

def icc_bench_linux():
    # benchmark_folder_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/benchmarks/gpbench/apks"
    benchmark_folder_path: str = os.path.join(external_path.home_directory, "programming/benchmarks/gpbench")

    # flowdroid_jar_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = os.path.join(external_path.home_directory, "programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar")

    # android_path: str = os.path.join(external_path.home_directory, "Library/Android/sdk/platforms/"
    android_path: str = "/usr/lib/android-sdk/platforms/"

    # source_sink_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"
    source_sink_path: str = os.path.join(external_path.home_directory, "programming/ConDySta/data/sources-and-sinks/ss-gpl.txt")

    icc_bench_dir_path: str = os.path.join(external_path.home_directory, "programming/benchmarks/ICCBench20/benchmark/apks")

    ic3_jar_path = os.path.join(external_path.home_directory, "programming/ic3/target/ic3-0.2.1-full.jar")
    # ic3_jar_path: str = os.path.join(external_path.home_directory, "programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = os.path.join(external_path.home_directory, "programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"

    icc_bench(flowdroid_jar_path, android_path, icc_bench_dir_path, ic3_jar_path)
    
# def setup_dirs(experiment_name, experiment_description):
#     date = str(pd.to_datetime('today').date())
#     # "YYYY-MM-DD"
#     experiment_id = date + "-" + experiment_name

#     # Setup experiment specific directories
#     experiment_dir_path = os.path.join("data", experiment_id)
#     results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
#     ic3_output_dir_path = os.path.join(experiment_dir_path, "ic3-output")
#     ic3_logs_dir_path = os.path.join(experiment_dir_path, "ic3-logs")
#     fd_output_dir_path = os.path.join(experiment_dir_path, "flowdroid-logs")
#     # Make sure each directory exists
#     for dir_path in [experiment_dir_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path]:
#         if not os.path.isdir(dir_path):
#             os.mkdir(dir_path)

#     # Record experiment description
#     readme_path = os.path.join(experiment_dir_path, "README.txt")
#     with open(readme_path, 'w') as file:
#         file.write(experiment_description)

#     return results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path

def droidbench_linux():
    benchmark_folder_path: str = os.path.join(external_path.home_directory, "programming/benchmarks/DroidBenchExtended")

    # flowdroid_jar_path: str = os.path.join(external_path.home_directory, "Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = os.path.join(external_path.home_directory, "programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar")

    android_path: str = "/usr/lib/android-sdk/platforms/"

    source_sink_path: str = os.path.join(external_path.home_directory, "programming/ConDySta/data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt")

    droidbench_dir_path: str = os.path.join(external_path.home_directory, "programming/benchmarks/DroidBenchExtended/benchmark/apks")

    droidbench(flowdroid_jar_path, android_path, source_sink_path, droidbench_dir_path)

def icc_bench(flowdroid_jar_path: str, android_path: str, icc_bench_dir_path: str, ic3_jar_path):

    experiment_name = "fd-on-iccbench-compiled-ic3"
    experiment_description = """
Run Flowdroid on ICC Bench using same settings as zhang_2021_gpbench
"""

    results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)

    ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         icc_model_path,
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_flowdroid_reported_leaks_count(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)


def icc_bench_no_ic3(flowdroid_jar_path: str, android_path: str, icc_bench_dir_path: str, ic3_jar_path):

    date = str(pd.to_datetime('today').date())
    # "YYYY-MM-DD"

    experiment_name = "fd-on-iccbench-no-ic3"
    experiment_description = """
    Run Flowdroid on ICC Bench using same settings as zhang_2021_gpbench, less the icc model from ic3.
"""

    results_df_path, _, _, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)

    ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        # ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        # icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         "",
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_flowdroid_reported_leaks_count(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)


def droidbench(flowdroid_jar_path: str, android_path: str, droidbench_dir_path: str, source_sink_path: str):

    experiment_name = "fd-on-droidbench-subset"
    experiment_description = """
Run Flowdroid on a subset of Droidbench apps
"""

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {})
    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    fd_output_dir_path = setup_additional_directories(experiment_dir_path, ['flowdroid_logs'])[0]


    # ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         icc_model_path,
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_flowdroid_reported_leaks_count(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)

def icc_bench_apk_names() -> List[str]:
    return [
        "icc_explicit_nosrc_nosink.apk",
        "icc_explicit_nosrc_sink.apk",
        "icc_explicit_src_nosink.apk",
        "icc_explicit_src_sink.apk",
        "icc_explicit1.apk",
        "icc_implicit_nosrc_nosink.apk",
        "icc_implicit_nosrc_sink.apk",
        "icc_implicit_src_nosink.apk",
        "icc_implicit_src_sink.apk",
        "icc_implicit_action.apk",
        "icc_intentservice.apk",
        "icc_stateful.apk",

        "icc_dynregister1.apk",
        "icc_dynregister2.apk",
        "icc_implicit_category.apk",
        "icc_implicit_data1.apk",
        "icc_implicit_data2.apk",
        "icc_implicit_mix1.apk",
        "icc_implicit_mix2.apk",

        "icc_rpc_comprehensive.apk",

        "rpc_localservice.apk",
        "rpc_messengerservice.apk",
        "rpc_remoteservice.apk",
        "rpc_returnsensitive.apk",
    ]

def icc_bench_apk_benchmark_ids():
    return [
        1,
        2,
        3,
        4,
        13,
        5,
        6,
        7,
        8,
        14,
        9,
        10,

        11,
        12,
        15,
        16,
        17,
        18,
        19,

        20,

        21,
        22,
        23,
        24,
    ]

def icc_bench_ubc_config_expected_flows():
    return [
        0,
        0,
        1,
        2,
        2,
        0,
        0,
        1,
        2,
        2,
        1,
        2,

        2,
        2,
        2,
        2,
        2,
        3,
        2,

        2,

        1,
        1,
        1,
        1,
    ]

# def icc_bench_designer_expected_flows():
#     return [
#         0,
#         0,
#         0,
#         1,
#         1,
#         0,
#         0,
#         1,
#         2,
#         2,
#         1,
#         3,

#         2,
#         2,
#         2,
#         2,
#         2,
#         3,
#         2,

#         3,

#         1,
#         1,
#         1,
#         1,
#     ]

def icc_bench_FDv2_7_1_ubc_results():
    return [
        0,
        0,
        1,
        2,
        2,
        0,
        0,
        1,
        2,
        2,
        0,
        1,

        1,
        1,
        2,
        1,
        1,
        3,
        2,

        0,

        0,
        0,
        0,
        0,
    ]

def get_and_validate_icc_bench_apps(icc_bench_dir_path: str) -> BatchInputModel:

    # Expected apps and id's
    apk_names = icc_bench_apk_names()
    apk_benchmark_ids = icc_bench_apk_benchmark_ids()


    if len(apk_names) != len(apk_benchmark_ids):
        raise AssertionError(f"Mismatch between ICCBench ID's and apk names")

    input_apks = input_apks_from_dir(icc_bench_dir_path)

    # Validate results from input_apks_from_dir, and assign apks their id's.
    if len(input_apks.unique_apks) != len(apk_names):
        raise AssertionError(f"Expected {len(apk_names)} apks but found {len(input_apks.unique_apks)} in directory {icc_bench_dir_path}")

    def scan_for_apk(input_apks, apk_name) -> InputModel:
        result = None
        for model in input_apks.ungrouped_inputs:
            if model.apk().apk_name == apk_name:
                if result is not None:
                    raise AssertionError(f"Duplicate apk found {apk_name}")
                result = model
        if result is None:
            raise AssertionError(f"Apk not found {apk_name}")
        return result

    for i in range(len(apk_names)):
        # make sure an apk of this name is present, and assign that InputModel its benchmark ID
        input_model = scan_for_apk(input_apks, apk_names[i])
        input_model.benchmark_id = apk_benchmark_ids[i]

    return input_apks





def setup_icc_bench_df() -> pd.DataFrame:

    apk_benchmark_ids = icc_bench_apk_benchmark_ids()
    apk_names = icc_bench_apk_names()

    df = pd.DataFrame({"apk_name": pd.Series(apk_names, apk_benchmark_ids)})
    df.rename_axis('AppID')

    expected_flows = icc_bench_ubc_config_expected_flows()
    df["UBC Expected Flows"] = pd.Series(expected_flows, apk_benchmark_ids)

    df["Detected Flows"] = pd.Series([np.nan] * len(apk_benchmark_ids), apk_benchmark_ids)

    ubc_experiment_flows = icc_bench_FDv2_7_1_ubc_results()
    df["UBC FlowDroid v2.7.1 Detected Flows"] = pd.Series(ubc_experiment_flows, apk_benchmark_ids)

    return df



def check_ss_bench_list() -> str:
    """ Generate the file path where SS-Bench.txt is expected. Generate it if it's not present."""
    sources_sinks_dir_path = hybrid.hybrid_config.source_sink_dir_path()
    ss_bench_list_path = os.path.join(sources_sinks_dir_path, "SS-Bench.txt")

    if not os.path.isfile(ss_bench_list_path):
        create_source_sink_file_ssbench(ss_bench_list_path)

    return ss_bench_list_path





