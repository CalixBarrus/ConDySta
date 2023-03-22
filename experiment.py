from flowdroid import activate_flowdroid_batch
from intercept import intercept_config, intercept_main, monkey


def flowdroid_on_droidbench():
    """
    Run default flowdroid on all droidbench apps
    """

    droidbench_path = "/Users/calix/Documents/CodingProjects/research/DroidBench/apk"
    source_and_sink_path = "SourcesAndSinks.txt"
    experiment_output = "logs/plain-droidbench-logs"

    activate_flowdroid_batch(droidbench_path, source_and_sink_path,
                             experiment_output,
                             recursive=True)

def instrument_and_run_droidbench():
    """
    Instrument and then run each droidbench app
    """
    droidbench_path = "/Users/calix/Documents/CodingProjects/research/DroidBench/apk"
    droidbench_path = "/Users/calix/Documents/CodingProjects/research" \
                      "/DroidBench/apk/FieldAndObjectSensitivity"
    experiment_output = "logs/dynamic-droidbench-logs"

    configuration = intercept_config.get_default_intercept_config()

    configuration.input_apks_path = droidbench_path
    configuration.is_recursive_on_input_apks_path = True
    configuration.logs_path = experiment_output
    configuration.seconds_to_test = .5

    intercept_main.main(configuration, do_clean=False)


def decompile_android_studio_apk():
    """
    Decompile an apk from android studio.
    """
    configuration = intercept_config.get_default_intercept_config()
    configuration.input_apks_path = \
        "/Users/calix/Documents/CodingProjects/AndroidStudio/ScratchActivity" \
        "/app/build/outputs/apk/debug"

    intercept_main.generate_smali_code(configuration)

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

    monkey.run_apk(configuration)

if __name__ == '__main__':
    # decompile_android_studio_apk()
    # recompile_manually_modified_smalis()
    manually_run_app()