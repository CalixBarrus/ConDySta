import hybrid_config
import hybrid_run
import results
# from flowdroid import run_flowdroid_batch
from intercept import intercept_config, intercept_main, monkey


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
    configuration.input_apks_path = "/Users/calix/Documents/programming/AndroidStudio/HeapSnapshot/app/build/outputs/apk/debug"

    intercept_main.generate_smali_code(configuration)

def decompile_input_apks():
    configuration = intercept_config.get_default_intercept_config()

    intercept_main.generate_smali_code(configuration)

def instrument_input_apks():
    configuration = intercept_config.get_default_intercept_config()

    intercept_main.instrument_app(configuration)

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

    configuration.use_monkey = False
    configuration.seconds_to_test_each_app = 10

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

    input_apks_path = "/Users/calix/Documents/programming/research-programming" \
                      "/DroidBench/apk-pared"
    intercept_configuration.input_apks_path = input_apks_path
    intercept_configuration.is_recursive_on_input_apks_path = True
    hybrid_analysis_configuration.input_apks_path = input_apks_path
    hybrid_analysis_configuration.is_recursive_on_input_apks_path = True

    hybrid_run.main(hybrid_analysis_configuration, do_clean=False)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "results/dysta-on-droidbench.csv")

def dysta_on_droidbench_folder():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    input_apks_path = "/Users/calix/Documents/programming/research-programming" \
                      "/DroidBench/apk/Callbacks"
    intercept_configuration.input_apks_path = input_apks_path
    intercept_configuration.is_recursive_on_input_apks_path = True
    intercept_configuration.use_monkey = False
    hybrid_analysis_configuration.input_apks_path = input_apks_path
    hybrid_analysis_configuration.is_recursive_on_input_apks_path = True

    hybrid_run.main(hybrid_analysis_configuration)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "results/dysta-on-droidbench-CallBacks-only.csv")

def dysta_on_successful_condysta_apps():
    intercept_configuration = intercept_config.get_default_intercept_config()
    hybrid_analysis_configuration = hybrid_config.get_default_hybrid_analysis_config(
        intercept_configuration)

    input_apks_path = "/Users/calix/Documents/programming/research-programming" \
                      "/benchmarks/condysta-apps"
    intercept_configuration.input_apks_path = input_apks_path
    intercept_configuration.is_recursive_on_input_apks_path = True
    hybrid_analysis_configuration.input_apks_path = input_apks_path
    hybrid_analysis_configuration.is_recursive_on_input_apks_path = True

    hybrid_run.main(hybrid_analysis_configuration, do_clean=False)

    results.print_csv_results_to_file(hybrid_analysis_configuration,
                                      "results/dysta-on-successful-condysta-apps.csv")


if __name__ == '__main__':
    dysta_on_droidbench()