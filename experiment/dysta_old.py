import os
from typing import List, Set, Union

from experiment.common import modified_source_sink_path
from hybrid.log_process_fd import get_flowdroid_reported_leaks_count
import intercept.clean
from hybrid import results
from hybrid.clean import clean
from hybrid.dynamic import logcat_processing_strategy_factory
from hybrid.flowdroid import run_flowdroid_config
from hybrid.hybrid_config import HybridAnalysisConfig, flowdroid_logs_path, apk_logcat_output_path, \
    flowdroid_logs_path, flowdroid_logs_path
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import SourceSink, SourceSinkSignatures, SourceSinkXML, MethodSignature
from intercept import monkey
from intercept.intercept_main import instrument_apks
from intercept.monkey import run_grouped_instrumented_apks
from util import input
from util.input import BatchInputModel

import util.logger
logger = util.logger.get_logger(__name__)

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
    input_apks = config.input_apks
    unmodified_source_sink_path = config.unmodified_source_sink_path
    logcat_processing_strategy = config.logcat_processing_strategy

    # experiment dirs:
    flowdroid_first_pass_logs_dir_path = config._flowdroid_first_pass_logs_dir_path
    flowdroid_second_pass_logs_dir_path = config._flowdroid_second_pass_logs_dir_path
    logcat_dir_path = config._logcat_dir_path
    modified_source_sink_directory_path = config._modified_source_sink_directory_path

    # Setup results Dataframe
    # TODO

    original_source_sinks = SourceSinkSignatures.from_file(unmodified_source_sink_path)

    # Instrument all apks
    instrument_apks(config, input_apks.unique_apks)

    # First handle ungrouped_apks. Afterward, handle grouped apks.
    for ungrouped_input in input_apks.ungrouped_inputs:
        apk = ungrouped_input.apk()

        # flowdroid 1st pass, use original apk and original source sink file
        run_flowdroid_config(config,
                             apk.apk_path,
                             unmodified_source_sink_path,
                             flowdroid_logs_path(flowdroid_first_pass_logs_dir_path, ungrouped_input))

        # Run instrumented apk and collect intermediate sources
        logcat_output_path = apk_logcat_output_path(logcat_dir_path, ungrouped_input)
        monkey.run_ungrouped_instrumented_apk(config, apk)
        if not os.path.isfile(logcat_output_path):
            results.HybridAnalysisResult.report_error(config, apk.apk_name, "No record of Dynamic Run")
            continue
        strategy = logcat_processing_strategy_factory(logcat_processing_strategy)
        new_sources: SourceSinkSignatures = strategy.sources_from_log(logcat_output_path)

        # new_sources_count = (new_sources - original_sources).source_count()
        # duplicate_sources_count = new_sources.source_count() - new_sources.set_minus(original_source_sinks).source_count()
        augmented_source_sink: SourceSinkSignatures = new_sources.union(original_source_sinks)


        new_source_sink_path = modified_source_sink_path(modified_source_sink_directory_path, ungrouped_input)
        augmented_source_sink.write_to_file(new_source_sink_path)
        # new_source_sink_path = strategy.source_sink_file_from_sources(unmodified_source_sink_path, modified_source_sink_directory_path, new_sources, ungrouped_input)

        # flowdroid 2nd pass, use original apk and modified source/sink file
        run_flowdroid_config(config,
                             apk.apk_path,
                             new_source_sink_path,
                             flowdroid_logs_path(flowdroid_second_pass_logs_dir_path, ungrouped_input))

    # Now, handle grouped apks
    for grouped_input in config.input_apks.grouped_inputs:

        # flowdroid 1st pass, use original apk and original source sink file
        for grouped_apk_index, apk in grouped_input.apks():
            run_flowdroid_config(config,
                                 apk.apk_path,
                                 unmodified_source_sink_path,
                                 flowdroid_logs_path(flowdroid_first_pass_logs_dir_path, grouped_input, grouped_apk_index))

    run_grouped_instrumented_apks(config, input_apks.grouped_inputs)

    strategy = logcat_processing_strategy_factory(logcat_processing_strategy)
    for grouped_input in input_apks.grouped_inputs:
        for grouped_apk_index, apk in grouped_input.apks():
            logcat_output_path = apk_logcat_output_path(logcat_dir_path, grouped_input, grouped_apk_index)
            new_sources: SourceSink = strategy.sources_from_log(logcat_output_path)

            augmented_source_sink: SourceSinkSignatures = new_sources.union(original_source_sinks)
            new_source_sink_path = modified_source_sink_path(modified_source_sink_directory_path, grouped_input, grouped_apk_index)
            augmented_source_sink.write_to_file(new_source_sink_path)

            # flowdroid 2nd pass, use original apk and modified source/sink file
            run_flowdroid_config(config,
                                 apk.apk_path,
                                 new_source_sink_path,
                                 flowdroid_logs_path(flowdroid_second_pass_logs_dir_path, grouped_input, grouped_apk_index))


def flowdroid_on_apks(hybrid_config: HybridAnalysisConfig, input_apks: BatchInputModel,
                      use_individual_source_sink_file=False):
    flowdroid_first_pass_logs_directory_path = hybrid_config._flowdroid_first_pass_logs_dir_path

    # We assume we aren't dealing with grouped inputs
    for ungrouped_input in input_apks.ungrouped_inputs:
        if use_individual_source_sink_file:
            source_and_sink_path = os.path.join(
                hybrid_config._modified_source_sink_directory_path,
                ungrouped_input.apk().apk_name + "source-and-sinks.txt"
            )
        else:
            source_and_sink_path = hybrid_config.unmodified_source_sink_path

        
        run_flowdroid_config(hybrid_config,
                             ungrouped_input.apk().apk_path,
                             source_and_sink_path,
                             flowdroid_logs_path(flowdroid_first_pass_logs_directory_path, ungrouped_input))


        num_leaks = get_flowdroid_reported_leaks_count(
            flowdroid_logs_path(flowdroid_first_pass_logs_directory_path, ungrouped_input))

        if num_leaks is not None:
            logger.info(f"In input {ungrouped_input.input_identifier()} flowdroid found {num_leaks} leaks")
        else:
            pass


if __name__ == '__main__':
    pass
