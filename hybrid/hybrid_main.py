import os
from typing import List, Set, Union

from hybrid.log_process_fd import get_reported_num_leaks_in_flowdroid_log
import intercept.clean
from hybrid import results
from hybrid.clean import clean
from hybrid.dynamic import dynamic_log_processing_strategy_factory
from hybrid.flowdroid import run_flowdroid_config
from hybrid.hybrid_config import HybridAnalysisConfig, flowdroid_first_pass_logs_path, apk_logcat_dump_path, \
    flowdroid_second_pass_logs_path, flowdroid_misc_pass_logs_path
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import SourceSinkXML, MethodSignature
from intercept import monkey
from intercept.intercept_main import instrument_apks
from intercept.monkey import run_grouped_instrumented_apks
from util import input
from util.input import BatchInputModel

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
    instrument_apks(config, config.input_apks.unique_apks)

    # First handle ungrouped_apks. Afterward, handle grouped apks.
    for ungrouped_input in config.input_apks.ungrouped_inputs:
        apk = ungrouped_input.apk()

        # flowdroid 1st pass, use original apk and original source sink file
        run_flowdroid_config(config,
                             apk.apk_path,
                             config.unmodified_source_sink_list_path,
                             flowdroid_first_pass_logs_path(config, ungrouped_input))

        # Run instrumented apk and collect intermediate sources
        monkey.run_ungrouped_instrumented_apk(config, apk)
        if not os.path.isfile(apk_logcat_dump_path(config, ungrouped_input)):
            results.HybridAnalysisResult.report_error(config, apk.apk_name, "No record of Dynamic Run")
            continue
        strategy = dynamic_log_processing_strategy_factory(config)
        new_sources: Union[Set[MethodSignature], SourceSinkXML] \
            = strategy.sources_from_log(config, apk_logcat_dump_path(config, ungrouped_input), ungrouped_input)
        new_source_sink_path = strategy.source_sink_file_from_sources(config, new_sources, ungrouped_input)

        # flowdroid 2nd pass, use original apk and modified source/sink file
        run_flowdroid_config(config,
                             apk.apk_path,
                             new_source_sink_path,
                             flowdroid_second_pass_logs_path(config, ungrouped_input))

    # Now, handle grouped apks
    for grouped_input in config.input_apks.grouped_inputs:

        # flowdroid 1st pass, use original apk and original source sink file
        for grouped_apk_index, apk in grouped_input.apks():
            run_flowdroid_config(config,
                                 apk.apk_path,
                                 config.unmodified_source_sink_list_path,
                                 flowdroid_first_pass_logs_path(config, grouped_input, grouped_apk_index))

    run_grouped_instrumented_apks(config, config.input_apks.grouped_inputs)

    strategy = dynamic_log_processing_strategy_factory(config)
    for grouped_input in config.input_apks.grouped_inputs:
        for grouped_apk_index, apk in grouped_input.apks():
            new_sources: Union[Set[MethodSignature], SourceSinkXML] \
                = strategy.sources_from_log(config, apk_logcat_dump_path(config, grouped_input, grouped_apk_index),
                                            grouped_input, grouped_apk_index)

            new_source_sink_path = strategy.source_sink_file_from_sources(config, new_sources, grouped_input, grouped_apk_index)

            # flowdroid 2nd pass, use original apk and modified source/sink file
            run_flowdroid_config(config,
                                 apk.apk_path,
                                 new_source_sink_path,
                                 flowdroid_second_pass_logs_path(config, grouped_input, grouped_apk_index))


def flowdroid_on_apks(hybrid_config: HybridAnalysisConfig, input_apks: BatchInputModel,
                      use_individual_source_sink_file=False):
    # TODO: test this function

    # We assume we aren't dealing with grouped inputs
    for ungrouped_input in input_apks.ungrouped_inputs:
        if use_individual_source_sink_file:
            source_and_sink_path = os.path.join(
                hybrid_config._modified_source_sink_directory,
                ungrouped_input.apk().apk_name + "source-and-sinks.txt"
            )
        else:
            source_and_sink_path = hybrid_config.unmodified_source_sink_list_path

        run_flowdroid_config(hybrid_config,
                             ungrouped_input.apk().apk_path,
                             source_and_sink_path,
                             flowdroid_misc_pass_logs_path(hybrid_config, ungrouped_input))


        num_leaks = get_reported_num_leaks_in_flowdroid_log(
            flowdroid_misc_pass_logs_path(hybrid_config, ungrouped_input))

        if num_leaks is not None:
            logger.info(f"In input {ungrouped_input.input_identifier()} flowdroid found {num_leaks} leaks")
        else:
            pass


if __name__ == '__main__':
    pass
