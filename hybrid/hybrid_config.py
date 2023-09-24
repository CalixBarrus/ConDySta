import os
from typing import List, Dict

from util.input import InputApksModel, input_apks_from_dir, InputApkModel

# TODO: I'm trying to move all assumptions about internal project directory structure
#  into this file (see the mess of functions at the end)

class HybridAnalysisConfig:
    input_apks: InputApksModel
    unmodified_source_sink_list_path: str
    modified_source_sink_directory: str
    logcat_dump_dir_path: str
    flowdroid_first_pass_logs_path: str
    flowdroid_second_pass_logs_path: str
    flowdroid_misc_logs_path: str
    android_platform_path: str
    flowdroid_jar_path: str
    target_PII: List[str]
    dynamic_log_processing_strategy: str

    # Start fields for intercept package
    decoded_apks_path: str
    instrumentation_strategy: str
    rebuilt_apks_path: str
    keys_dir_path: str
    signed_apks_path: str
    logs_path: str
    use_monkey: bool
    seconds_to_test_each_app: int
    monkey_rng_seed: int
    # End fields for intercept package

    results_dir_path: str
    data_dir_path: str

    # For use by results.py
    results_dict: Dict

    def __init__(self,
                 input_apks: InputApksModel,
                 unmodified_source_sink_list_path,
                 modified_source_sink_directory,
                 logcat_dump_dir_path,
                 flowdroid_first_pass_logs_path,
                 flowdroid_second_pass_logs_path,
                 flowdroid_misc_logs_path,
                 android_platform_path,
                 flowdroid_jar_path,
                 target_PII,
                 dynamic_log_processing_strategy,

                 decoded_apks_path: str,
                 instrumentation_strategy: str,
                 rebuilt_apks_path: str,
                 keys_dir_path: str,
                 signed_apks_path: str,
                 logs_path: str,
                 use_monkey: bool,
                 seconds_to_test_each_app: int,
                 monkey_rng_seed: int,

                 results_dir_path: str,
                 data_dir_path: str,
                 ):
        self.input_apks = input_apks
        self.unmodified_source_sink_list_path = unmodified_source_sink_list_path
        self.modified_source_sink_directory = modified_source_sink_directory
        self.logcat_dump_dir_path = logcat_dump_dir_path
        self.flowdroid_first_pass_logs_path = flowdroid_first_pass_logs_path
        self.flowdroid_second_pass_logs_path = flowdroid_second_pass_logs_path
        self.flowdroid_misc_logs_path = flowdroid_misc_logs_path
        self.android_platform_path = android_platform_path
        self.flowdroid_jar_path = flowdroid_jar_path
        self.target_PII = target_PII
        self.dynamic_log_processing_strategy = dynamic_log_processing_strategy

        self.decoded_apks_path = decoded_apks_path
        self.instrumentation_strategy = instrumentation_strategy
        self.rebuilt_apks_path = rebuilt_apks_path
        self.keys_dir_path = keys_dir_path
        self.signed_apks_path = signed_apks_path
        self.logs_path = logs_path
        # If True, use monkey to send random commands to the app. If False,
        # launch the app but do not send commands to it.
        self.use_monkey = use_monkey
        # About how many seconds to run a given app
        self.seconds_to_test_each_app = seconds_to_test_each_app
        self.monkey_rng_seed = monkey_rng_seed

        self.results_dir_path = results_dir_path
        self.data_dir_path = data_dir_path

def get_default_hybrid_analysis_config() -> "HybridAnalysisConfig":

    # unmodified_source_sink_list_path = "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    unmodified_source_sink_list_path = "/Users/calix/Documents/programming/research-programming/FlowDroid/soot-infoflow-android/SourcesAndSinks.txt"

    # flowdroid_snapshot_jar_path = "/Users/calix/Documents/programming/research-programming/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_compiled_jar_path = "/Users/calix/Documents/programming/research-programming/FlowDroid/soot-infoflow-cmd/target/soot-infoflow-cmd-jar-with-dependencies.jar"

    config = HybridAnalysisConfig(
        input_apks=input_apks_from_dir("data/input-apks"),
        unmodified_source_sink_list_path=unmodified_source_sink_list_path,
        modified_source_sink_directory="data/sources-and-sinks/modified",
        logcat_dump_dir_path="data/logs/logcat-dump",
        flowdroid_first_pass_logs_path="data/logs/flowdroid-first-run",
        flowdroid_second_pass_logs_path="data/logs/flowdroid-second-run",
        flowdroid_misc_logs_path="data/logs/flowdroid-misc-run",
        # intercept_config,
        android_platform_path="/Users/calix/Library/Android/sdk/platforms/",
        flowdroid_jar_path=flowdroid_compiled_jar_path,
        target_PII=get_target_PII(),
        dynamic_log_processing_strategy="InstrReportReturnAndArgsDynamicLogProcessingStrategy",

        decoded_apks_path="data/intercept/decoded-apks/",
        instrumentation_strategy="StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy",
        rebuilt_apks_path="data/intercept/rebuilt-apks/",
        keys_dir_path="data/intercept/apk-keys/",
        signed_apks_path="data/signed-apks/",
        logs_path="data/logs/",
        use_monkey=True,
        seconds_to_test_each_app=5,
        monkey_rng_seed=42,
        results_dir_path="data/results",
        data_dir_path="data",
    )
    return config


def get_target_PII() -> List[str]:
    # Return list of strings that should be considered Personally Identifiable
    # Information. These are strings that can only come from some call to a source
    # function (or something that should be a source function).

    mint_mobile_SIM_id = "8901240197155182897"
    nexus_6_IMEI = "355458061189396"
    fake_gps_lat = "-3.144000"
    fake_gps_long = "-60.020000"
    target_PII = [mint_mobile_SIM_id, nexus_6_IMEI]
    return target_PII

def decoded_apk_path(config: HybridAnalysisConfig, apk: InputApkModel) -> str:
    return os.path.join(config.decoded_apks_path, apk.apk_name_no_suffix())

def rebuilt_apk_path(config: HybridAnalysisConfig, apk: InputApkModel) ->  str:
    # Rebuilt apk keeps the ".apk" suffix
    return os.path.join(config.rebuilt_apks_path, apk.apk_name)

def apk_key_path(config: HybridAnalysisConfig, apk: InputApkModel) -> str:
    return os.path.join(config.keys_dir_path, apk.apk_key_name())

def signed_apk_path(config: HybridAnalysisConfig, apk: InputApkModel) -> str:
    return os.path.join(config.signed_apks_path, apk.apk_name)

def apk_logcat_dump_path(config: HybridAnalysisConfig, apk: InputApkModel, group_id: int=-1) -> str:
    if group_id == -1:
        # APK not part of a group
        return os.path.join(config.logcat_dump_dir_path, _apk_log_file_name(apk))
    else:
        # Add a prefix to logcat dumps for runs that are part of an apk group
        return os.path.join(config.logcat_dump_dir_path, _group_prefix(group_id) + _apk_log_file_name(apk))

def flowdroid_first_pass_logs_path(config: HybridAnalysisConfig, apk: InputApkModel, group_id: int=-1) -> str:
    if group_id == -1:
        # APK not part of a group
        return os.path.join(config.flowdroid_first_pass_logs_path, _apk_log_file_name(apk))
    else:
        # Add a prefix to logcat dumps for runs that are part of an apk group
        return os.path.join(config.flowdroid_first_pass_logs_path, _group_prefix(group_id) + _apk_log_file_name(apk))

def flowdroid_second_pass_logs_path(config: HybridAnalysisConfig, apk: InputApkModel, group_id: int=-1) -> str:
    if group_id == -1:
        # APK not part of a group
        return os.path.join(config.flowdroid_second_pass_logs_path, _apk_log_file_name(apk))
    else:
        # Add a prefix to logcat dumps for runs that are part of an apk group
        return os.path.join(config.flowdroid_second_pass_logs_path, _group_prefix(group_id) + _apk_log_file_name(apk))

def flowdroid_misc_pass_logs_path(config: HybridAnalysisConfig, apk: InputApkModel) -> str:
    return os.path.join(config.flowdroid_first_pass_logs_path, _apk_log_file_name(apk))

def _group_prefix(group_id: int) -> str:
    if group_id == -1:
        return ""
    else:
        return f"group{str(group_id)}_"

def _apk_log_file_name(apk: InputApkModel) -> str:
    return apk.apk_name + ".log"

def modified_source_sink_path(config: HybridAnalysisConfig, apk_name: str, group_id: int=-1, is_xml: bool=False):
    if is_xml:
        return os.path.join(
            config.modified_source_sink_directory,
            _group_prefix(group_id) + apk_name + "source-and-sinks.xml")
    else:
        return os.path.join(
            config.modified_source_sink_directory,
            _group_prefix(group_id) + apk_name + "source-and-sinks.txt")


def data_dir_path(config: HybridAnalysisConfig):
    return config.data_dir_path

def results_csv_path(config: HybridAnalysisConfig, experiment_name: str):
    return os.path.join(config.results_dir_path, experiment_name + ".csv")