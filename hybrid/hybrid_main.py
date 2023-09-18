import os
import re
import shutil
from typing import List, Optional

import util
from hybrid import results
from hybrid.clean import clean
from hybrid.dynamic import StringReturnDynamicLogProcessingStrategy, dynamic_log_processing_strategy_factory
from hybrid.flowdroid import activate_flowdroid
from hybrid.hybrid_config import HybridAnalysisConfig, get_default_hybrid_analysis_config
from hybrid.results import HybridAnalysisResult
from intercept import intercept_main
from intercept.intercept_config import get_default_intercept_config

from util import logger, input
from util.input import InputApkModel, InputApksModel

logger = logger.get_logger('hybrid', 'hybrid_main')

def main(hybrid_config, do_clean=True):
    if do_clean:
        clean(hybrid_config)

    results.HybridAnalysisResult.experiment_start(hybrid_config)

    dysta(hybrid_config, do_clean)

    results.HybridAnalysisResult.experiment_end(hybrid_config)


def dysta(hybrid_config: HybridAnalysisConfig, do_clean):

    # dynamic pass
    # TODO: I should setup the configs so that this step is unnecessary
    hybrid_config.intercept_config.logs_path = hybrid_config.dynamic_pass_logs_path
    # TODO: Should be able to skip specific APKs if there's already a result for them.
    intercept_main.main(hybrid_config.intercept_config, do_clean=do_clean)

    # TODO: need to handle list of input_apks, and apk_groups
    input_apks: List[input.InputApkModel] = hybrid_config.intercept_config.input_apks.input_apks

    for input_apk in input_apks:
        _dysta_on_apk(hybrid_config, input_apk)


def _dysta_on_apk(hybrid_config: HybridAnalysisConfig, apk: InputApkModel):
    unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
    flowdroid_first_pass_logs_path = hybrid_config.flowdroid_first_pass_logs_path
    flowdroid_second_pass_logs_path = hybrid_config.flowdroid_second_pass_logs_path

    apk_name = apk.apk_name

    apk_path = apk.apk_path

    # flowdroid 1st pass
    result_log_name = activate_flowdroid(hybrid_config, apk_path, apk_name,
                                         unmodified_source_and_sink_path,
                                         flowdroid_first_pass_logs_path)

    # uses same result_log_name as intercept TODO: fix this nonobvious dependency
    dynamic_log_path = os.path.join(hybrid_config.dynamic_pass_logs_path,
                                    result_log_name)

    if not os.path.isfile(dynamic_log_path):
        results.HybridAnalysisResult.report_error(hybrid_config, apk_name,
                                                  "No record of Dynamic Run")
        return None

    # strategy = StringReturnDynamicLogProcessingStrategy()
    strategy = dynamic_log_processing_strategy_factory(hybrid_config)

    new_sources = strategy.sources_from_log(hybrid_config, dynamic_log_path,
                                            apk_name)

    new_source_sink_path = strategy.source_sink_file_from_sources(
        hybrid_config, new_sources, apk_name)

    # flowdroid 2nd pass
    activate_flowdroid(hybrid_config,
                       apk_path, apk_name,
                       new_source_sink_path,
                       flowdroid_second_pass_logs_path)

def flowdroid_on_apks(hybrid_config: HybridAnalysisConfig, input_apks: InputApksModel, use_individual_source_sink_file=False):

    if input_apks.input_apks is None:
        raise NotImplementedError()

    for input_apk in input_apks.input_apks:
        if use_individual_source_sink_file:
            source_and_sink_path = os.path.join(
                hybrid_config.modified_source_sink_directory,
                input_apk.apk_name + "source-and-sinks.txt"
            )
        else:
            source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
        result_log_name = activate_flowdroid(hybrid_config,
                                             input_apk.apk_path,
                                             input_apk.apk_name,
                                             source_and_sink_path,
                                             hybrid_config.flowdroid_misc_logs_path)


        num_leaks = HybridAnalysisResult._count_leaks_in_flowdroid_log(
            os.path.join(hybrid_config.flowdroid_misc_logs_path, result_log_name))

        if num_leaks is not None:
            logger.info(f"In apk {input_apk.apk_name} flowdroid found {num_leaks} leaks")
        else:
            pass


if __name__ == '__main__':
    print(len(input.input_apks_from_list(
        "data/input-apk-lists/common-false-neg-RP.txt")))

