from typing import List, Dict

from intercept.intercept_config import InterceptConfig, get_default_intercept_config


def get_default_hybrid_analysis_config(
        intercept_config: InterceptConfig) -> "HybridAnalysisConfig":
    unmodified_source_sink_list_path = "data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    modified_source_sink_directory = "data/sources-and-sinks/modified"
    dynamic_pass_logs_path = "data/logs/instrumentation-run"
    flowdroid_first_pass_logs_path = "data/logs/flowdroid-first-run"
    flowdroid_second_pass_logs_path = "data/logs/flowdroid-second-run"
    flowdroid_misc_logs_path = "data/logs/flowdroid-misc-run"
    intercept_config = intercept_config
    android_platform_path = "/Users/calix/Library/Android/sdk/platforms/"
    # flowdroid_snapshot_jar_path = "/Users/calix/Documents/programming/research-programming/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_compiled_jar_path = "/Users/calix/Documents/programming/research-programming/FlowDroid/soot-infoflow-cmd/target/soot-infoflow-cmd-jar-with-dependencies.jar"
    target_PII = get_target_PII()
    dynamic_log_processing_strategy = "InstrReportReturnAndArgsDynamicLogProcessingStrategy"


    config = HybridAnalysisConfig(unmodified_source_sink_list_path,
                                  modified_source_sink_directory,
                                  dynamic_pass_logs_path,
                                  flowdroid_first_pass_logs_path,
                                  flowdroid_second_pass_logs_path,
                                  flowdroid_misc_logs_path,
                                  intercept_config,
                                  android_platform_path,
                                  flowdroid_compiled_jar_path,
                                  target_PII,
                                  dynamic_log_processing_strategy,
                                  )
    return config


class HybridAnalysisConfig:
    # input_apks are in intercept_config
    unmodified_source_sink_list_path: str
    modified_source_sink_directory: str
    dynamic_pass_logs_path: str
    flowdroid_first_pass_logs_path: str
    flowdroid_second_pass_logs_path: str
    flowdroid_misc_logs_path: str
    intercept_config: InterceptConfig
    android_platform_path: str
    flowdroid_jar_path: str
    target_PII: List[str]
    dynamic_log_processing_strategy: str

    # For use by results.py
    results_dict: Dict

    def __init__(self,
                 unmodified_source_sink_list_path,
                 modified_source_sink_directory,
                 dynamic_pass_logs_path,
                 flowdroid_first_pass_logs_path,
                 flowdroid_second_pass_logs_path,
                 flowdroid_misc_logs_path,
                 intercept_config,
                 android_platform_path,
                 flowdroid_jar_path,
                 target_PII,
                 dynamic_log_processing_strategy,
                 ):
        self.unmodified_source_sink_list_path = unmodified_source_sink_list_path
        self.modified_source_sink_directory = modified_source_sink_directory
        self.dynamic_pass_logs_path = dynamic_pass_logs_path
        self.flowdroid_first_pass_logs_path = flowdroid_first_pass_logs_path
        self.flowdroid_second_pass_logs_path = flowdroid_second_pass_logs_path
        self.flowdroid_misc_logs_path = flowdroid_misc_logs_path
        self.intercept_config = intercept_config
        self.android_platform_path = android_platform_path
        self.flowdroid_jar_path = flowdroid_jar_path
        self.target_PII = target_PII
        self.dynamic_log_processing_strategy = dynamic_log_processing_strategy

def get_target_PII() -> List[str]:
    # Return list of strings that should be considered Personally Identifiable
    # Information. These are strings that can only come from some call to a source
    # function (or something that should be a source function).

    mint_mobile_SIM_id = "8901240197155182897"
    nexus_6_IMEI = "355458061189396"
    target_PII = [mint_mobile_SIM_id, nexus_6_IMEI]
    return target_PII
