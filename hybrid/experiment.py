import util
from hybrid import hybrid_main, hybrid_config, results
# from flowdroid import run_flowdroid_batch
from hybrid.flowdroid import activate_flowdroid
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

    configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/AndroidStudio/HeapSnapshot/app/build/outputs/apk/debug")


    intercept_main.generate_smali_code(configuration)

def update_heap_snapshot_smali_files():
    """
    Decompile an apk from android studio and place some targeted smali files into
    intercept/smali-files/heap-snapshot. Replace existing files if necessary
    """
    configuration = intercept_config.get_default_intercept_config()
    configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/AndroidStudio/HeapSnapshot/app/build/outputs/apk/debug")

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

    monkey.run_apk(configuration)

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


    monkey.run_apk(configuration)


def dysta_on_droidbench():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)


    intercept_configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/research-programming" \
                      "/DroidBench/apk-pared")


    hybrid_main.main(hybrid_analysis_configuration, do_clean=False)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "../data/results/dysta-on-droidbench.csv")

def dysta_on_droidbench_folder():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    intercept_configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/research-programming/DroidBench/apk/Callbacks")

    intercept_configuration.use_monkey = False

    hybrid_main.main(hybrid_analysis_configuration)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "results/dysta-on-droidbench-CallBacks-only.csv")

def dysta_on_successful_condysta_apps():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    intercept_configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/research-programming/benchmarks/condysta-apps")

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "data/results/dysta-on-successful-condysta-apps-v3.csv")

def dysta_on_successful_condysta_apps_list():
    input_apks_list = "data/input-apk-lists/condysta-paper-apks-pared.txt"
    dysta_on_list(input_apks_list, "data/results/successful_condysta-apps-v3.csv", True)

def dysta_simple_test():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    intercept_configuration.input_apks = input.input_apks_from_dir("/Users/calix/Documents/programming/research-programming/ConDySta/data/test-apks")

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_results_to_terminal(hybrid_analysis_configuration)

def dysta_on_input_apks():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    intercept_configuration.use_monkey = True

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_results_to_terminal(hybrid_analysis_configuration)


def dysta_on_common_false_neg_apks():
    dysta_on_list("data/input-apk-lists/common-false-neg-RP-v2.txt",
                  "data/results/dysta-on-common-false-neg-RP-v2.csv")


def dysta_on_pared_flowdroid_false_neg_apks():
    dysta_on_list("data/input-apk-lists/flowdroid-false-neg-RP-v2-pared.txt",
                  "data/results/dysta-on-flowdroid-false-neg-RP-pared-with-monkey-v3"
                  ".csv"
                  ".csv", True)

def dysta_on_full_benchmark():
    dysta_on_list("data/input-apk-lists/DroidBenchExtended-and-ICCBench-pared.txt",
                  "data/results/dysta-on-DroidBenchExtended-and-ICCBench-pared-with"
                  "-monkey.csv",
                  True)


def dysta_on_list(list_path: str, results_path: str, use_monkey: bool=False):
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    intercept_configuration.use_monkey = use_monkey
    intercept_configuration.input_apks = input.input_apks_from_list(list_path)

    hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
    results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)

# def dysta_on_full_benchmark_rerun():
#     list_path = "data/input-apk-lists/DroidBenchExtended-and-ICCBench-pared.txt"
#     results_path = "data/results/dysta-on-DroidBenchExtended-and-ICCBench-pared-no" \
#                    "-monkey.csv"
#
#     intercept_configuration = intercept_config.get_default_intercept_config()
#     hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
#         intercept_configuration)
#
#     intercept_configuration.use_monkey = False
#     intercept_configuration.input_apks = input.input_apks_from_list(list_path)
#
#     hybrid_main.main(hybrid_analysis_configuration, do_clean=True)
#     results.print_csv_results_to_file(hybrid_analysis_configuration, results_path)



def flowdroid_on_instrumented_apks():
    input_apks = input.input_apks_from_dir(intercept_config.get_default_intercept_config().signed_apks_path)
    flowdroid_on_apks(input_apks, True)

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
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    use_individual_source_sink_file = False
    hybrid_analysis_configuration.unmodified_source_sink_list_path = \
        "data/sources-and-sinks/OnlyTelephony-xml-format-test.xml"

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, intercept_configuration.input_apks, use_individual_source_sink_file)


def flowdroid_on_apks(input_apks, use_individual_source_sink_file):
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    hybrid_main.flowdroid_on_apks(hybrid_analysis_configuration, input_apks, use_individual_source_sink_file)


if __name__ == '__main__':
    # decompile_android_studio_apk()
    # instrument_input_apks()
    # update_heap_snapshot_smali_files()
    # flowdroid_on_OnlyTelephony_with_testXML()
    dysta_on_input_apks()
