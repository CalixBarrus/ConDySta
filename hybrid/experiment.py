import os
from typing import List

import hybrid.clean
import util
from hybrid import hybrid_main, hybrid_config, results
# from flowdroid import run_flowdroid_batch
from hybrid.hybrid_config import HybridAnalysisConfig
from intercept import intercept_config, intercept_main, monkey
from intercept.instrument import extract_decompiled_smali_code
from util import input


# def flowdroid_on_droidbench():
#     """
#     Run default flowdroid on all droidbench apps
#     """
#
#     droidbench_path = "/Users/calix/Documents/programming/research-programming/DroidBench/apk"
#     source_and_sink_path = "SourcesAndSinks.txt"
#     experiment_output = "logs/plain-droidbench-logs"
#
#     run_flowdroid_batch(droidbench_path, source_and_sink_path,
#                         experiment_output,
#                         recursive=True)
from util.zip import zip_dir


def instrument_and_run_droidbench():
    """
    Instrument and then run each droidbench app
    """
    # droidbench_path = "/Users/calix/Documents/CodingProjects/research/DroidBench/apk"
    droidbench_path = "/Users/calix/Documents/programming/research-programming" \
                      "/DroidBench/apk/FieldAndObjectSensitivity"
    experiment_output = "logs/dynamic-droidbench-logs"

    configuration = intercept_config.get_default_intercept_config()

    # configuration.input_apks_path = droidbench_path
    configuration.is_recursive_on_input_apks_path = True
    configuration.logs_path = experiment_output
    configuration.seconds_to_test = .5

    intercept_main.main(configuration, do_clean=True)


def decompile_android_studio_apk():
    """
    Decompile an apk from android studio.
    """
    configuration = intercept_config.get_default_intercept_config()

    configuration.input_apks = input.input_apks_from_dir(
        "/Users/calix/Documents/programming/AndroidStudio/HeapSnapshot/app/build/outputs/apk/debug")

    intercept_main.generate_smali_code(configuration)


def update_heap_snapshot_smali_files():
    """
    Decompile an apk from android studio and place some targeted smali files into
    intercept/smali-files/heap-snapshot. Replace existing files if necessary
    """
    configuration = intercept_config.get_default_intercept_config()
    configuration.input_apks = input.input_apks_from_dir("HeapSnapshot/app/build/outputs/apk/debug")

    intercept_main.generate_smali_code(configuration)

    extract_decompiled_smali_code(configuration)


def decompile_input_apks():
    configuration = intercept_config.get_default_intercept_config()

    intercept_main.generate_smali_code(configuration)


def instrument_input_apks():
    configuration = intercept_config.get_default_intercept_config()

    intercept_main.instrument_apps(configuration, do_clean=True)


def recompile_manually_modified_smalis():
    """
    Recompile whatever smalis are currently in the decoded-apks directory
    """
    configuration = intercept_config.get_default_intercept_config()
    intercept_main.rebuild_smali_code(configuration)


def manually_run_app():
    """
    Start up an app for a minute with the same logging setup as automatic
    experiments
    """
    configuration = intercept_config.get_default_intercept_config()

    configuration.use_monkey = True
    configuration.seconds_to_test_each_app = 2

    # configuration.signed_apks_path = \
    #     "/Users/calix/Documents/programming/research-programming/ConDySta" \
    #     "/input-apks"

    monkey.run_apks(configuration)


def instrument_and_run_apps_manually():
    configuration = intercept_config.get_default_intercept_config()

    droidbench_subdir_path = "/Users/calix/Documents/programming/research-programming" \
                             "/DroidBench/apk/FieldAndObjectSensitivity"

    configuration.input_apks_path = droidbench_subdir_path
    configuration.use_monkey = False
    configuration.seconds_to_test_each_app = 5

    intercept_main.main(configuration, do_clean=True)


def recompile_and_run_with_no_instrumentation():
    configuration = intercept_config.get_default_intercept_config()

    configuration.use_monkey = False
    configuration.seconds_to_test_each_app = 5

    intercept_main.generate_smali_code(configuration, do_clean=False)
    intercept_main.rebuild_smali_code(configuration)

    monkey.run_apks(configuration)


def dysta_on_droidbench():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming" \
        "/DroidBench/apk-pared")

    hybrid_main.main(hybrid_analysis_configuration, do_clean=False)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "../data/results/dysta-on-droidbench.csv")


def dysta_on_droidbench_folder():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming/DroidBench/apk/Callbacks")

    hybrid_analysis_configuration.use_monkey = False

    hybrid_main.main(hybrid_analysis_configuration)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "results/dysta-on-droidbench-CallBacks-only.csv")


def dysta_on_successful_condysta_apps():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming/benchmarks/condysta-apps")

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "data/results/dysta-on-successful-condysta-apps-v3.csv")


def dysta_on_successful_condysta_apps_list():
    input_apks_list = "data/input-apk-lists/condysta-paper-apks-pared.txt"
    dysta_on_list(input_apks_list, "data/results/successful_condysta-apps-v3.csv", True)


def dysta_simple_test():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_dir(
        "/Users/calix/Documents/programming/research-programming/ConDySta/data/test-apks")

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_results_to_terminal(hybrid_analysis_configuration)


def dysta_on_input_apks():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.use_monkey = False

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_results_to_terminal(hybrid_analysis_configuration)


def dysta_on_common_false_neg_apks():
    dysta_on_list("data/input-apk-lists/common-false-neg-RP-v2.txt",
                  "data/results/InstrReportReturnAndArgsDynamicLogProcessingStrategy/dysta-on-common-false-neg-RP-v2.csv")


def dysta_on_pared_flowdroid_false_neg_apks():
    dysta_on_list("data/input-apk-lists/flowdroid-false-neg-RP-v2-pared.txt",
                  "data/results/InstrReportReturnAndArgsDynamicLogProcessingStrategy"
                  "/dysta-on-flowdroid-false-neg-RP-pared-no-monkey-v3.csv", False)


def dysta_on_full_benchmark():
    dysta_on_list("data/input-apk-lists/DroidBenchExtended-and-ICCBench-pared.txt",
                  "data/results/dysta-on-DroidBenchExtended-and-ICCBench-pared-with"
                  "-monkey.csv",
                  True)

def dysta_on_location_group():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    location_service_path = "/Users/calix/Documents/programming/research-programming/benchmarks/DroidBenchExtended/benchmark/apks/InterAppCommunication/Location_leakage/Location_Service1.apk"
    collector_path = "/Users/calix/Documents/programming/research-programming/benchmarks/DroidBenchExtended/benchmark/apks/InterAppCommunication/Collector/Collector.apk"




def dysta_on_list(list_path: str, results_path: str, use_monkey: bool = False):
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.use_monkey = use_monkey
    hybrid_analysis_configuration.input_apks = input.input_apks_from_list(list_path)

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)

def dysta_on_input_apks_with_collector():
    raise NotImplementedError()
    # apps in DroidBenchExtended/InterAppCommunication only leak when the "Collector" apk is also running


def flowdroid_on_RP_common_false_negs():
    input_apks = input.input_apks_from_list(
        "data/input-apk-lists/common-false-neg-RP.txt")
    flowdroid_on_apks(input_apks, False)


def flowdroid_on_RP_flowdroid_false_negs():
    input_apks = input.input_apks_from_list(
        "data/input-apk-lists/flowdroid-false-neg-RP-pared.txt")
    flowdroid_on_apks(input_apks, False)


def flowdroid_on_droidbench_extended_pared():
    input_apks = input.input_apks_from_list(
        "data/input-apk-lists/droidbench-extended-pared.txt")
    flowdroid_on_apks(input_apks, False)


def flowdroid_on_full_benchmark():
    input_apks = input.input_apks_from_list(
        "data/input-apk-lists/DroidBenchExtended-and-ICCBench-pared.txt")
    flowdroid_on_apks(input_apks, False)


def flowdroid_on_OnlyTelephony_with_testXML():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    use_individual_source_sink_file = False
    hybrid_analysis_configuration.unmodified_source_sink_list_path = \
        "data/sources-and-sinks/OnlyTelephony-xml-format-test.xml"

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, hybrid_analysis_configuration.input_apks,
                                  use_individual_source_sink_file)

def flowdroid_on_input_apks():
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    use_individual_source_sink_file = False

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, hybrid_analysis_configuration.input_apks,
                                  use_individual_source_sink_file)

def flowdroid_on_apk_with_source_sink(apk_dir_path, source_sink_path):
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    use_individual_source_sink_file = False
    hybrid_analysis_configuration.unmodified_source_sink_list_path = source_sink_path

    hybrid_analysis_configuration.input_apks = input.input_apks_from_dir(apk_dir_path)

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, hybrid_analysis_configuration.input_apks,
                                  use_individual_source_sink_file)

def flowdroid_on_android_studio_apk_with_testXML():
    apk_dir_path = "/Users/calix/Documents/programming/research-programming/flowdroid-sourcesink-tests/flowdroid-sourcesink-tests-inner-class/app/build/outputs/apk/debug"
    source_sink_path = "/Users/calix/Documents/programming/research-programming/ConDySta/data/sources-and-sinks/test-source-sink.xml"
    flowdroid_on_apk_with_source_sink(apk_dir_path, source_sink_path)

def flowdroid_on_apks(input_apks, use_individual_source_sink_file):

    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, input_apks, use_individual_source_sink_file)

def export_flowdroid_callgraph_for_input_apks():
    pass

def setup_folders():

    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid.clean.setup_folders(hybrid_analysis_configuration)

def improved_dysta_on_recent_FD_and_RD_common_fewer_leaks():


    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_list(
        "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks.txt")


    # hybrid_analysis_configuration.use_monkey = True
    #
    # hybrid_main.main(hybrid_analysis_configuration)
    results_path_prefix = \
        "data/results/InstrReportReturnAndArgsDynamicLogProcessingStrategy"
    # results_path = os.path.join(results_path_prefix,
    #                             "improved-dysta-on-recent-FD-fewer-leaks-with-monkey"
    #                             ".csv")
    # results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)
    #
    #
    # zip_dir("data/", ".",
    #         "improved-dysta-on-recent-FD-fewer-leaks-with-monkey-raw-data.zip")

    hybrid_analysis_configuration.use_monkey = False

    hybrid_main.main(hybrid_analysis_configuration)
    results_path = os.path.join(results_path_prefix,
                                "improved-dysta-on-recent-FD-fewer-leaks-no-monkey"
                                ".csv")
    results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)

    zip_dir("data/", ".",
            "improved-dysta-on-recent-FD-fewer-leaks-no-monkey-raw-data.zip")

def improved_dysta_on_recent_FD_and_RD_common_fewer_leaks_with_groups():


    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config()

    hybrid_analysis_configuration.input_apks = input.input_apks_from_list(
        "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks.txt")


    # hybrid_analysis_configuration.use_monkey = True
    #
    # hybrid_main.main(hybrid_analysis_configuration)
    results_path_prefix = \
        "data/results/InstrReportReturnAndArgsDynamicLogProcessingStrategy"
    # results_path = os.path.join(results_path_prefix,
    #                             "improved-dysta-on-recent-FD-fewer-leaks-with-monkey"
    #                             ".csv")
    # results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)
    #
    #
    # zip_dir("data/", ".",
    #         "improved-dysta-on-recent-FD-fewer-leaks-with-monkey-raw-data.zip")

    hybrid_analysis_configuration.use_monkey = False

    hybrid_main.main(hybrid_analysis_configuration)
    results_path = os.path.join(results_path_prefix,
                                "improved-dysta-on-recent-FD-fewer-leaks-no-monkey"
                                ".csv")
    results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)

    zip_dir("data/", ".",
            "improved-dysta-on-recent-FD-fewer-leaks-no-monkey-raw-data.zip")

def improved_dysta_on_common_leaks_with_groups():
    list_path: str = "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks.txt"
    groups_list_path: str = "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks_groups.txt"
    experiment_name: str = "improved_dysta_on_common_leaks_with_groups"

    dysta_with_groups(list_path, groups_list_path, experiment_name)


def improved_dysta_on_recent_FD_leaks_with_groups():
    list_path: str = "data/input-apk-lists/recent_FD_fewer_leaks.txt"
    groups_list_path: str = "data/input-apk-lists/recent_FD_fewer_leaks_groups.txt"
    experiment_name: str = "improved_dysta_recent_FD_leaks_with_groups"

    dysta_with_groups(list_path, groups_list_path, experiment_name)

def improved_dysta_test_list_with_groups():
    list_path: str = "data/input-apk-lists/test_list.txt"
    groups_list_path: str = "data/input-apk-lists/test_list_groups.txt"
    experiment_name: str = "test_list"

    dysta_with_groups(list_path, groups_list_path, experiment_name)


def dysta_with_groups(list_path: str, groups_list_path: str, experiment_name: str):
    # list_path: str = "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks.txt"
    # list_path: str = "data/input-apk-lists/test_list.txt"
    # groups_list_path: str = "data/input-apk-lists/recent_FD_and_RD_common_fewer_leaks_groups.txt"

    groups_lists: List[List[str]] = input.list_of_lists_from_file(groups_list_path)

    config: HybridAnalysisConfig = hybrid_config.get_default_hybrid_analysis_config()

    config.input_apks = input.input_apks_from_list_with_groups(list_path, groups_lists)

    config.use_monkey = False

    hybrid_main.main(config)

    date = "9-22-23"
    full_experiment_name = date + "-" + experiment_name + "_no_monkey"
    results.print_csv_results_to_file(config, hybrid_config.results_csv_path(config,
                                                                          full_experiment_name))
    zip_data_directory(config, full_experiment_name)


    config.use_monkey = True
    # hybrid_main.main(config, do_clean=False)
    # TODO: fix do_clean=False so it
    #  actually works
    hybrid_main.main(config)

    full_experiment_name = date + "-" + experiment_name + \
                      "_w_monkey"
    results.print_csv_results_to_file(config, hybrid_config.results_csv_path(config,
                                                                          full_experiment_name))
    zip_data_directory(config, full_experiment_name)

    # TODO: should figure out how to get everything to log properly, then dump log
    #  file with the zip


def zip_data_directory(config: HybridAnalysisConfig, experiment_name: str):
    downloads_dir_path = "/Users/calix/Downloads"
    zip_file_name = experiment_name + ".zip"

    data_dir_path = hybrid_config.data_dir_path(config)
    zip_dir(data_dir_path, downloads_dir_path, zip_file_name)

if __name__ == '__main__':
    # improved_dysta_on_recent_FD_leaks_with_groups()
    improved_dysta_test_list_with_groups()
