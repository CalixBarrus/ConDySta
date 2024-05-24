import os
from typing import List, Dict

from util.input import BatchInputModel, input_apks_from_dir, ApkModel, InputModel


# TODO: I'm trying to move all assumptions about internal project directory structure
#  into this file (see the mess of functions at the end)

class HybridAnalysisConfig:
    input_apks: BatchInputModel
    unmodified_source_sink_list_path: str



    android_platform_path: str
    flowdroid_jar_path: str

    dynamic_log_processing_strategy: str

    target_PII: List[str]

    # Start fields for intercept package

    instrumentation_strategy: str

    use_monkey: bool
    seconds_to_test_each_app: int
    monkey_rng_seed: int
    # End fields for intercept package

    results_dir_path: str
    data_dir_path: str

    # For use by results.py
    results_dict: Dict

    # Internal project directory structure
    _modified_source_sink_directory: str
    _logcat_dump_dir_path: str
    _flowdroid_first_pass_logs_path: str
    _flowdroid_second_pass_logs_path: str
    _flowdroid_misc_logs_path: str
    # Just for intercept package
    _decoded_apks_path: str
    _rebuilt_apks_path: str
    _keys_dir_path: str
    _signed_apks_path: str
    _logs_path: str

    def __init__(self,
                 input_apks: BatchInputModel,
                 unmodified_source_sink_list_path,

                 android_platform_path,
                 flowdroid_jar_path,
                 target_PII,
                 dynamic_log_processing_strategy,

                 instrumentation_strategy: str,
                 use_monkey: bool,
                 seconds_to_test_each_app: int,
                 monkey_rng_seed: int,

                 results_dir_path: str,
                 data_dir_path: str,
                 ):
        self.input_apks = input_apks
        self.unmodified_source_sink_list_path = unmodified_source_sink_list_path


        self.android_platform_path = android_platform_path
        self.flowdroid_jar_path = flowdroid_jar_path
        self.target_PII = target_PII
        self.dynamic_log_processing_strategy = dynamic_log_processing_strategy

        self.instrumentation_strategy = instrumentation_strategy

        # If True, use monkey to send random commands to the app. If False,
        # launch the app but do not send commands to it.
        self.use_monkey = use_monkey
        # About how many seconds to run a given app
        self.seconds_to_test_each_app = seconds_to_test_each_app
        self.monkey_rng_seed = monkey_rng_seed

        self.results_dir_path = results_dir_path
        self.data_dir_path = data_dir_path

    def _setup_internal_dirs(self):
        """
        Setup fields that define the internal structure of project data. This should include all directories that have no
        need to be client facing.
        """
        self._signed_apks_path = "data/signed-apks/"

        self._decoded_apks_path = "data/intercept/decoded-apks/"
        self._rebuilt_apks_path = "data/intercept/rebuilt-apks/"
        self._keys_dir_path = "data/intercept/apk-keys/"

        self._modified_source_sink_directory = "data/sources-and-sinks/modified"

        self._logs_path = "data/logs/"
        self._logcat_dump_dir_path = "data/logs/logcat-dump"
        self._flowdroid_first_pass_logs_path = "data/logs/flowdroid-first-run"
        self._flowdroid_second_pass_logs_path = "data/logs/flowdroid-second-run"
        self._flowdroid_misc_logs_path = "data/logs/flowdroid-misc-run"

def get_default_hybrid_analysis_config() -> "HybridAnalysisConfig":

    # unmodified_source_sink_list_path = "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    # unmodified_source_sink_list_path = "FlowDroid/soot-infoflow-android/SourcesAndSinks.txt"
    unmodified_source_sink_list_path = ""

    flowdroid_compiled_jar_path = "FlowDroid/soot-infoflow-cmd/target/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_compiled_jar_path = ""

    # android_platform_path = "~/Library/Android/sdk/platforms/"
    android_platform_path = ""

    config = HybridAnalysisConfig(
        input_apks=input_apks_from_dir("data/input-apks"),

        unmodified_source_sink_list_path=unmodified_source_sink_list_path,
        android_platform_path=android_platform_path,
        flowdroid_jar_path=flowdroid_compiled_jar_path,

        target_PII=get_target_PII(),
        dynamic_log_processing_strategy="InstrReportReturnAndArgsDynamicLogProcessingStrategy",

        instrumentation_strategy="StaticFunctionOnInvocationArgsAndReturnsInstrumentationStrategy",
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

def decoded_apk_path(config: HybridAnalysisConfig, apk: ApkModel) -> str:
    return os.path.join(config._decoded_apks_path, apk.apk_name_no_suffix())

def rebuilt_apk_path(config: HybridAnalysisConfig, apk: ApkModel) ->  str:
    # Rebuilt apk keeps the ".apk" suffix
    return os.path.join(config._rebuilt_apks_path, apk.apk_name)

def apk_key_path(config: HybridAnalysisConfig, apk: ApkModel) -> str:
    return os.path.join(config._keys_dir_path, apk.apk_key_name())

def signed_apk_path(config: HybridAnalysisConfig, apk: ApkModel) -> str:
    return os.path.join(config._signed_apks_path, apk.apk_name)

def apk_logcat_dump_path(config: HybridAnalysisConfig, apk: InputModel, grouped_apk_idx: int=-1) -> str:
    return os.path.join(config._logcat_dump_dir_path, _apk_log_file_name(apk.input_identifier(grouped_apk_idx)))

def flowdroid_first_pass_logs_path(config: HybridAnalysisConfig, apk: InputModel, grouped_apk_idx: int=-1) -> str:
    return os.path.join(config._flowdroid_first_pass_logs_path, _apk_log_file_name(apk.input_identifier(grouped_apk_idx)))

def flowdroid_second_pass_logs_path(config: HybridAnalysisConfig, apk: InputModel, grouped_apk_idx: int=-1) -> str:
    return os.path.join(config._flowdroid_second_pass_logs_path, _apk_log_file_name(apk.input_identifier(grouped_apk_idx)))

def flowdroid_misc_pass_logs_path(config: HybridAnalysisConfig, apk: InputModel) -> str:
    return os.path.join(config._flowdroid_first_pass_logs_path, _apk_log_file_name(apk.input_identifier()))

def _apk_log_file_name(identifier: str) -> str:
    return identifier + ".log"

# TODO: fix usages
def modified_source_sink_path(config: HybridAnalysisConfig, input_model: InputModel, grouped_apk_idx: int=-1, is_xml: bool = False):

    return os.path.join(
        config._modified_source_sink_directory,
        input_model.input_identifier(grouped_apk_idx) + "source-and-sinks") + (".xml" if is_xml else ".txt")


def data_dir_path(config: HybridAnalysisConfig):
    return config.data_dir_path

def results_csv_path(config: HybridAnalysisConfig, experiment_name: str):
    return os.path.join(config.results_dir_path, experiment_name + ".csv")