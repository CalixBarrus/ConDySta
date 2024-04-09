import os
from typing import List, Set, Union

import intercept.clean
from hybrid import results
from hybrid.clean import clean
from hybrid.dynamic import dynamic_log_processing_strategy_factory
from hybrid.flowdroid import activate_flowdroid
from hybrid.hybrid_config import HybridAnalysisConfig, flowdroid_first_pass_logs_path, apk_logcat_dump_path, \
    flowdroid_second_pass_logs_path, flowdroid_misc_pass_logs_path
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import SourceSinkXML, MethodSignature
from intercept import monkey
from intercept.intercept_main import instrument_apks
from intercept.monkey import run_grouped_instrumented_apks
from util import input
from util.input import InputApksModel

from util import logger
logger = logger.get_logger('hybrid', 'hybrid_main')


def main(hybrid_config, do_clean=True):
    if do_clean:
        # todo: merge intercept clean with hybrid clean
        clean(hybrid_config)
        intercept.clean.clean(hybrid_config)

    results.HybridAnalysisResult.experiment_start(hybrid_config)

    dysta(hybrid_config)

    results.HybridAnalysisResult.experiment_end(hybrid_config)


def dysta(config: HybridAnalysisConfig):

    # TODO: Should be able to skip specific APKs if there's already a result for them.

    # Instrument all apks
    instrument_apks(config, config.input_apks)

    # First handle ungrouped_apks. Afterward, handle grouped apks.
    ungrouped_apks: List[input.InputApkModel] = config.input_apks.ungrouped_apks
    for apk in ungrouped_apks:

        # flowdroid 1st pass, use original apk and original source sink file
        activate_flowdroid(config,
                           apk.apk_path,
                           config.unmodified_source_sink_list_path,
                           flowdroid_first_pass_logs_path(config, apk))

        # Run instrumented apk and collect intermediate sources
        monkey.run_ungrouped_instrumented_apk(config, apk)
        if not os.path.isfile(apk_logcat_dump_path(config, apk)):
            results.HybridAnalysisResult.report_error(config, apk.apk_name, "No record of Dynamic Run")
            continue
        strategy = dynamic_log_processing_strategy_factory(config)
        new_sources: Union[Set[MethodSignature], SourceSinkXML] \
            = strategy.sources_from_log(config, apk_logcat_dump_path(config, apk), apk.apk_name)
        new_source_sink_path = strategy.source_sink_file_from_sources(config, new_sources, apk.apk_name)

        # flowdroid 2nd pass, use original apk and modified source/sink file
        activate_flowdroid(config,
                           apk.apk_path,
                           new_source_sink_path,
                           flowdroid_second_pass_logs_path(config, apk))


    # Now, handle grouped apks
    for apk_group in config.input_apks.input_apk_groups:

        # flowdroid 1st pass, use original apk and original source sink file
        for apk in apk_group.apks:
            activate_flowdroid(config,
                               apk.apk_path,
                               config.unmodified_source_sink_list_path,
                               flowdroid_first_pass_logs_path(config, apk, group_id=apk_group.group_id))

    run_grouped_instrumented_apks(config, config.input_apks.input_apk_groups)

    strategy = dynamic_log_processing_strategy_factory(config)
    for apk_group in config.input_apks.input_apk_groups:
        for apk in apk_group.apks:

            new_sources: Union[Set[MethodSignature], SourceSinkXML] \
                = strategy.sources_from_log(config, apk_logcat_dump_path(config, apk, group_id=apk_group.group_id), apk.apk_name, group_id=apk_group.group_id)

            new_source_sink_path = strategy.source_sink_file_from_sources(config, new_sources, apk.apk_name)

            # flowdroid 2nd pass, use original apk and modified source/sink file
            activate_flowdroid(config,
                               apk.apk_path,
                               new_source_sink_path,
                               flowdroid_second_pass_logs_path(config, apk, group_id=apk_group.group_id))

def flowdroid_on_apks(hybrid_config: HybridAnalysisConfig, input_apks: InputApksModel,
                      use_individual_source_sink_file=False):

    for input_apk in input_apks.unique_apks:
        if use_individual_source_sink_file:
            source_and_sink_path = os.path.join(
                hybrid_config.modified_source_sink_directory,
                input_apk.apk_name + "source-and-sinks.txt"
            )
        else:
            source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
        result_log_name = activate_flowdroid(hybrid_config,
                                             input_apk.apk_path,
                                             source_and_sink_path,
                                             flowdroid_misc_pass_logs_path(hybrid_config, input_apk))

        num_leaks = HybridAnalysisResult._count_leaks_in_flowdroid_log(
            os.path.join(hybrid_config.flowdroid_misc_logs_path, result_log_name))

        if num_leaks is not None:
            logger.info(f"In apk {input_apk.apk_name} flowdroid found {num_leaks} leaks")
        else:
            pass


if __name__ == '__main__':
    pass
