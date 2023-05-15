from typing import List

from intercept.intercept_config import InterceptConfig, get_default_intercept_config


def get_default_hybrid_analysis_config(
        intercept_config: InterceptConfig) -> "HybridAnalysisConfig":
    input_apks_path = "input-apks"
    unmodified_source_sink_list_path = "sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    modified_source_sink_directory = "sources-and-sinks"
    flowdroid_first_pass_logs_path = "logs/flowdroid-first-run"
    flowdroid_second_pass_logs_path = "logs/flowdroid-second-run"
    intercept_config = intercept_config
    android_platform_path = "/Users/calix/Library/Android/sdk/platforms/"
    flowdroid_jar_path = "/Users/calix/Documents/programming/research-programming/soot-infoflow-cmd-jar-with-dependencies.jar"
    verbose = True
    target_PII = get_target_PII()

    config = HybridAnalysisConfig(input_apks_path, unmodified_source_sink_list_path,
                                  modified_source_sink_directory,
                                  flowdroid_first_pass_logs_path,
                                  flowdroid_second_pass_logs_path,
                                  intercept_config,
                                  android_platform_path,
                                  flowdroid_jar_path,
                                  verbose,
                                  target_PII,
                                  )
    return config


class HybridAnalysisConfig:
    input_apks_path: str
    unmodified_source_sink_list_path: str
    modified_source_sink_directory: str
    flowdroid_first_pass_logs_path: str
    flowdroid_second_pass_logs_path: str
    intercept_config: InterceptConfig
    android_platform_path: str
    flowdroid_jar_path: str
    verbose: bool
    target_PII: List[str]

    def __init__(self, input_apks_path, unmodified_source_sink_list_path,
                 modified_source_sink_directory, flowdroid_first_pass_logs_path,
                 flowdroid_second_pass_logs_path,
                 intercept_config,
                 android_platform_path,
                 flowdroid_jar_path,
                 verbose,
                 target_PII,
                 ):
        self.input_apks_path = input_apks_path
        self.unmodified_source_sink_list_path = unmodified_source_sink_list_path
        self.modified_source_sink_directory = modified_source_sink_directory
        self.flowdroid_first_pass_logs_path = flowdroid_first_pass_logs_path
        self.flowdroid_second_pass_logs_path = flowdroid_second_pass_logs_path
        self.intercept_config = intercept_config
        self.android_platform_path = android_platform_path
        self.flowdroid_jar_path = flowdroid_jar_path
        self.verbose = verbose
        self.target_PII = target_PII

def get_target_PII() -> List[str]:
    # Return list of strings that should be considered Personally Identifiable
    # Information. These are strings that can only come from some call to a source
    # function (or something that should be a source function).

    mint_mobile_SIM_id = "8901240197155182897"
    target_PII = [mint_mobile_SIM_id]
    return target_PII
