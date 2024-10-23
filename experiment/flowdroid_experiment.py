

import os
from subprocess import TimeoutExpired
import time
from typing import Callable, List, Tuple
import xml.etree.ElementTree as ET
import pandas as pd
from experiment.common import benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, format_num_secs, logger, results_df_from_benchmark_df, setup_additional_directories, setup_experiment_dir
from hybrid.dynamic import LogcatLogFileModel, LogcatProcessingStrategy, get_selected_errors_from_logcat, logcat_processing_strategy_factory
from hybrid.flow import Flow, compare_flows
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig

from hybrid.hybrid_config import apk_logcat_output_path, flowdroid_logs_path, time_path, source_sink_file_path, text_file_path
from hybrid.log_process_fd import FlowdroidLogException, get_flowdroid_analysis_error, get_flowdroid_flows, get_flowdroid_memory, get_flowdroid_reported_leaks_count
from hybrid.source_sink import SourceSink, SourceSinkSignatures
from intercept.instrument import InstrumentationReport
from util.input import input_apks_from_dir
import util.logger
logger = util.logger.get_logger(__name__)

def experiment_setup_and_save_csv_fixme(experiment_runnable, **kwargs):
    # TODO: this function needs refactored
    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**kwargs)

    # passing all relevant kwargs to setup_experiment_dir only works if this runnable only takes stuff produced in setup + kwargs.
    # Change the stuff after this to run_and_save_result
    results_df = experiment_runnable(experiment_dir_path, benchmark_df, **kwargs)

    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)

def experiment_setup(**kwargs) -> Tuple[str, str, pd.DataFrame]:
    experiment_name = kwargs["experiment_name"] 
    experiment_description = kwargs["experiment_description"] 

    ids_subset = kwargs["ids_subset"] 
    benchmark_dir_path: str = kwargs["benchmark_dir_path"]
    benchmark_description_path = (kwargs["benchmark_description_path"] if "benchmark_description_path" in kwargs.keys() else "")
    always_new_experiment_directory = kwargs["always_new_experiment_directory"]

    logger.info(f"Starting experiment {experiment_name}")

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

    benchmark_df = benchmark_df_from_benchmark_directory_path(benchmark_dir_path, benchmark_description_csv_path=benchmark_description_path, ids_subset=ids_subset)

    return experiment_id, experiment_dir_path, benchmark_df

def flowdroid_comparison_with_observation_processing_experiment(**kwargs):

    def f(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        # takes as input kwargs["logcat_directory_path"], for now
        source_sink_files: pd.DataFrame = observation_processing(experiment_dir_path, benchmark_df, **kwargs)

        source_sink_files.to_csv(os.path.join(experiment_dir_path, "observation-processing-output.csv"))

        # kwargs["flowdroid_output_directory_name"] = "unmodified-flowdroid-logs"
        flowdroid_logs_directory_name = "unmodified-flowdroid-logs"
        unmodified_source_sink_results = flowdroid_on_benchmark_df(experiment_dir_path, benchmark_df, flowdroid_logs_directory_name=flowdroid_logs_directory_name, **kwargs)

        # kwargs["flowdroid_output_directory_name"] = "augmented-flowdroid-logs"
        flowdroid_logs_directory_name = "augmented-flowdroid-logs"
        benchmark_df["Source Sink Path"] = source_sink_files["Source Sink Path"]
        benchmark_df["Observed Sources Path"] = source_sink_files["Source Sink Path"]
        augmented_source_sink_results = flowdroid_on_benchmark_df(experiment_dir_path, benchmark_df, flowdroid_logs_directory_name=flowdroid_logs_directory_name, **kwargs)

        # TODO: compute summary & interpretation of results_df
        count_discovered_sources = source_sink_files["Discovered Sources"]
        results_df = summary_df_for_fd_comparison(unmodified_source_sink_results, augmented_source_sink_results, count_discovered_sources)
        # results_df = pd.merge(suffix_on_flowdroid_results(unmodified_source_sink_results, " Unmodified Source/Sink"), 
        #                 suffix_on_flowdroid_results(augmented_source_sink_results, " Augmented Source/Sink"))

        return results_df
    
    experiment_setup_and_save_csv_fixme(f, **kwargs)


def observation_processing(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    # could eventually be multiple paths
    logcat_directory_path: str = kwargs["logcat_directory_path"]

    results_df = results_df_from_benchmark_df(benchmark_df)
    results_df["Selected Log Errors"] = ""

    logcat_processing_strategy: LogcatProcessingStrategy = logcat_processing_strategy_factory(kwargs["logcat_processing_strategy"])

    observed_source_sink_directory_path: str = setup_additional_directories(experiment_dir_path, ["observed-source-sinks"])[0]
    source_sink_directory_path: str = setup_additional_directories(experiment_dir_path, ["augmented-source-sinks"])[0]
    observed_strings_directory_path: str = setup_additional_directories(experiment_dir_path, ["observation-details"])[0]

    original_source_sinks: SourceSinkSignatures = SourceSinkSignatures.from_file(kwargs["source_sink_list_path"])

    source_sink_path_column = "Source Sink Path"
    results_df[source_sink_path_column] = ""

    for i in benchmark_df.index:
        input_model = benchmark_df.loc[i, "Input Model"]

        # grab logcat files that match with the input_model
        # TODO: path function has support for apks that are a part of apk_groups
        possible_logcat_file_path = apk_logcat_output_path(logcat_directory_path, input_model)
        if not os.path.isfile(possible_logcat_file_path):
            msg = f"Log not found at {possible_logcat_file_path}, check previous experiment steps"
            results_df.loc[i, "Error Message"] += msg
            logger.error(msg)
            continue

        results_df.loc[i, "Selected Log Errors"] += get_selected_errors_from_logcat(possible_logcat_file_path)
        

        # TODO: this assumes all the inputs in benchmark_df are also present in the indicated logcat directory
        observed_source_sinks: SourceSinkSignatures = logcat_processing_strategy.sources_from_log(possible_logcat_file_path)

        logcat_model = LogcatLogFileModel(possible_logcat_file_path)
        instrumentation_report_tuples: List[InstrumentationReport] = logcat_model.scan_log_for_instrumentation_report_tuples()
        results_df.loc[i, "Instrumentation Reports"] = len(instrumentation_report_tuples)
        results_df.loc[i, "Discovered Sources"] = observed_source_sinks.source_count()
        source_sink_file = source_sink_file_path(observed_source_sink_directory_path, input_model)
        observed_source_sinks.write_to_file(source_sink_file)
        results_df.loc[i, "Observed Sources Path"] = source_sink_file

        harnessed_source_calls = logcat_model.scan_log_for_harnessed_source_calls()
        results_df.loc[i, "Harnessed Source Calls Count"] = len(harnessed_source_calls)
        harness_calls_path = text_file_path(observed_strings_directory_path, input_model)
        with open(harness_calls_path, 'w') as out_file:
            out_file.write(f"Instrumentation reports observing tainted strings {len(instrumentation_report_tuples)} times.\n")
            out_file.write("\n".join([f"String '{observed_string}' \nobserved at access path {access_path} \nby report {str(report)}" for report, access_path, observed_string in instrumentation_report_tuples]))
            out_file.write(f"\n\nObserved {len(harnessed_source_calls)} calls to harnessed sources:\n")
            out_file.write("\n".join([f"Log line {i}, {line.strip()}" for i, line in harnessed_source_calls]))

        augmented_source_sinks: SourceSinkSignatures = observed_source_sinks.union(original_source_sinks)
        source_sink_file = source_sink_file_path(source_sink_directory_path, input_model)
        augmented_source_sinks.write_to_file(source_sink_file)
        results_df.loc[i, source_sink_path_column] = source_sink_file

    return results_df




def _get_source_sink_factory(**kwargs) -> Callable[[pd.DataFrame, int], str]:
    unmodified_source_sink_list_path: str = kwargs["source_sink_list_path"]

    # Check if individual source/sinks will be used
    source_sink_path_column = "Source Sink Path"
    # use_individual_source_sinks = source_sink_path_column in benchmark_df.columns

    return lambda benchmark_df, i: (benchmark_df.loc[i, source_sink_path_column] if source_sink_path_column in benchmark_df.columns else unmodified_source_sink_list_path)

    # return lambda benchmark_df, i: unmodified_source_sink_list_path
        

def flowdroid_on_benchmark_df(experiment_dir_path: str, benchmark_df: pd.DataFrame, flowdroid_logs_directory_name: str="flowdroid-logs", **kwargs) -> pd.DataFrame:
    flowdroid_jar_path: str = kwargs["flowdroid_jar_path"]
    android_path: str = kwargs["android_path"]

    flowdroid_timeout_seconds = kwargs["timeout"] 
    flowdroid_args: FlowdroidArgs = kwargs["flowdroid_args"] 



    # TODO: should probably go back and actually add support for this
    ic3_model_column = "ic3_model"
    use_ic3 = ic3_model_column in benchmark_df.columns


    source_sink_list_path = kwargs["source_sink_list_path"]
    # Check if individual source/sinks will be used
    source_sink_path_column = "Source Sink Path"
    use_individual_source_sinks = source_sink_path_column in benchmark_df.columns

    get_source_sink = _get_source_sink_factory(**kwargs)
    
    # if "use_model_paths_csv" in kwargs.keys():
    #     icc_model_path_df = pd.read_csv("/home/calix/programming/ConDySta/data/benchmark-descriptions/gpbench-icc-model-paths.csv", header=0, index_col=False)
    #     icc_model_path_df = icc_model_path_df.set_index(icc_model_path_df["AppID"])
    
    # run fd on each app    
    # flowdroid_logs_directory_name = ("flowdroid-logs" if "flowdroid_output_directory_name" not in kwargs.keys() else kwargs["flowdroid_output_directory_name"])
    # flowdroid_logs_directory_name = kwargs["flowdroid_output_directory_name"]
    flowdroid_logs_directory_path = setup_additional_directories(experiment_dir_path, [flowdroid_logs_directory_name])[0]
        
    results_df = results_df_from_benchmark_df(benchmark_df)
    
    for i in benchmark_df.index:
        input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore
        
        # output_log_path = os.path.join(flowdroid_logs_directory_path, input_model.input_identifier() + ".log")
        output_log_path = flowdroid_logs_path(flowdroid_logs_directory_path, input_model)
        

        source_sink_list_path = get_source_sink(benchmark_df, i)

        try:
            t0 = time.time()
            run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, source_sink_list_path, flowdroid_args, output_log_path, flowdroid_timeout_seconds)
            time_elapsed_seconds = int(time.time() - t0)
        except TimeoutExpired as e:
            msg = f"Flowdroid timed out after {format_num_secs(flowdroid_timeout_seconds)} on apk {input_model.apk().apk_name}; details in " + output_log_path
            logger.error(msg)
            results_df.loc[i, "Error Message"] += msg

            output_time_path = time_path(flowdroid_logs_directory_path, input_model)
            time_seconds_to_file(output_time_path, flowdroid_timeout_seconds)
            continue

        output_time_path = time_path(flowdroid_logs_directory_path, input_model)
        time_seconds_to_file(output_time_path, time_elapsed_seconds)
        
    results_df = parse_flowdroid_results(experiment_dir_path, benchmark_df, flowdroid_logs_directory_path, results_df["Error Message"], **kwargs)
    return results_df

def parse_flowdroid_results(experiment_dir_path, benchmark_df, flowdroid_logs_directory_path, errors: pd.Series=None, **kwargs) -> pd.DataFrame:
    # TODO: this should/could get called parallel with flowdroid_on_benchmark_df, not by it. 

    results_df = results_df_from_benchmark_df(benchmark_df)

    if errors is not None:
        results_df["Error Message"] = errors
    # This should be broken out into it's own function

    if "ground_truth_xml_path" in kwargs.keys():
        ground_truth_xml_path = kwargs["ground_truth_xml_path"]
        ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)

        # only for testing augmented SS list
        if "Observed Sources Path" in benchmark_df.columns:
            observed_sources_details_directory = setup_additional_directories(experiment_dir_path, ["result-details"])[0]

    for i in benchmark_df.index:
        input_model = benchmark_df.loc[i, "Input Model"]

        output_log_path = flowdroid_logs_path(flowdroid_logs_directory_path, input_model)
        output_time_path = time_path(flowdroid_logs_directory_path, input_model)
        time_elapsed_seconds = time_seconds_from_file(output_time_path)

        process_fd_log_stats(results_df, i, time_elapsed_seconds, output_log_path)
        process_fd_log_reported_flows(results_df, i, output_log_path)

        if "ground_truth_xml_path" in kwargs.keys():
            # ground_truth_xml_path = kwargs["ground_truth_xml_path"]
            # ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)
            process_fd_log_ground_truth_comparison(results_df, i, output_log_path, input_model.apk().apk_path, ground_truth_flows_df)

            if "Observed Sources Path" in benchmark_df.columns:
                # TODO: this should get put into it's own function
                # 

                # Check if there are flows from observed sources to ground_truth sinks. 
                apk_observed_sources_path = benchmark_df.loc[i, "Observed Sources Path"]
                observed_sources: SourceSinkSignatures = SourceSinkSignatures.from_file(apk_observed_sources_path)

                # Don't bother printing this info out if there were no observed sources.
                if observed_sources.source_count() > 0:

                    try:
                        detected_flows = get_flowdroid_flows(output_log_path, input_model.apk().apk_path)
                    except FlowdroidLogException as e:
                        logger.error(e.msg)
                        results_df.loc[i, "Error Message"] += e.msg # type: ignore
                        continue

                    detected_flows = list(set(detected_flows))

                    apk_name = results_df.loc[i, 'APK Name']            
                    apk_name_mask = ground_truth_flows_df['APK Name'] == apk_name
                    ground_truth_flows_df[apk_name_mask]

                    observed_sources_details_path = text_file_path(observed_sources_details_directory, input_model)

                    with open(observed_sources_details_path, 'w') as file:
                        file.write(f"{apk_name}\n")
                        file.write(f"Detected Flows:\n")
                        file.write("\n".join([str(flow) for flow in detected_flows]))
                        file.write("\nGround Truth Flows matching the APK's name\n")
                        reordered_cols = ["APK Name", "Benchmark ID", "Ground Truth Value", "Source Signature", "Sink Signature", "Flow"]
                        file.write(ground_truth_flows_df[apk_name_mask][reordered_cols].to_string())
                        file.write("\nObserved Sources:\n")
                        file.write(str(observed_sources))
                        file.write("\n")

    return results_df


def process_fd_log_stats(results_df: pd.DataFrame, i: int, time_elapsed_seconds: int, log_path: str):

    if "Time Elapsed" not in results_df.columns:
        results_df["Time Elapsed"] = ""
    results_df.loc[i, "Time Elapsed"] = format_num_secs(time_elapsed_seconds)

    if "Max Reported Memory Usage" not in results_df.columns:
        results_df["Max Reported Memory Usage"] = ""
    results_df.loc[i, "Max Reported Memory Usage"] = get_flowdroid_memory(log_path)

    analysis_error = get_flowdroid_analysis_error(log_path)
    if analysis_error != "":
        results_df.loc[i, "Error Message"] += analysis_error # type: ignore
        logger.error(analysis_error)

def process_fd_log_reported_flows(results_df: pd.DataFrame, i: int, log_path: str):

    if "Reported Flowdroid Flows" not in results_df.columns:
        results_df["Reported Flowdroid Flows"] = ""
    try:
        reported_num_leaks = get_flowdroid_reported_leaks_count(log_path)
    except FlowdroidLogException as e:
        logger.error(e.msg)
        results_df.loc[i, "Error Message"] += e.msg # type: ignore
        return

    if reported_num_leaks is None:
        msg = "Flowdroid Irregularity, review log at " + log_path
        results_df.loc[i, "Error Message"] += msg
        logger.error(msg)
        return

    results_df.loc[i, "Reported Flowdroid Flows"] = reported_num_leaks

def process_fd_log_ground_truth_comparison(results_df: pd.DataFrame, i: int, log_path: str, apk_path: str, ground_truth_flows_df: pd.DataFrame):
    for col in ["TP", "FP", "TN", "FN", "Flows Not Evaluated"]:
        if col not in results_df.columns:
            results_df[col] = ""

    try:
        detected_flows = get_flowdroid_flows(log_path, apk_path)
    except FlowdroidLogException as e:
        logger.error(e.msg)
        results_df.loc[i, "Error Message"] += e.msg # type: ignore
        return


    # deduplicate FD flows
    original_length = len(detected_flows)
    detected_flows = list(set(detected_flows))
    if len(detected_flows) != original_length:
        logger.warn(f"Flowdroid reported {original_length - len(detected_flows)} duplicate flows for app {results_df.loc[i, 'APK Name']}")

    tp, fp, tn, fn, inconclusive = compare_flows(detected_flows, ground_truth_flows_df, results_df.loc[i, 'APK Name'])

    results_df.loc[i, "TP"] = tp
    results_df.loc[i, "FP"] = fp
    results_df.loc[i, "TN"] = tn
    results_df.loc[i, "FN"] = fn
    results_df.loc[i, "Flows Not Evaluated"] = inconclusive

def time_seconds_to_file(output_time_path: str, time_elapsed_seconds: int):
    with open(output_time_path, "w") as file:
        file.write(str(int(time_elapsed_seconds)))

def time_seconds_from_file(output_time_path: str) -> int:
    with open(output_time_path, "r") as file:
        line: str = file.readline()
        time_elapsed_seconds = int(line.strip())

    # TODO: implement
    return time_elapsed_seconds


def suffix_on_flowdroid_results(results_df: pd.DataFrame, suffix) -> pd.DataFrame:
    cols_to_skip = ["Benchmark ID", "APK Name"]

    f = lambda column_name: (column_name if column_name in cols_to_skip else column_name + suffix)    

    new_results_df = results_df.rename(columns=f)
    # Experiments expect an "Error Message" column with an empty string.
    new_results_df["Error Message"] = ""
    return new_results_df

def summary_df_for_fd_comparison(unmodified_results_df: pd.DataFrame, augmented_results_df: pd.DataFrame, count_discovered_sources: pd.Series) -> pd.DataFrame:
    # original columns for each df = [Error Message,Time Elapsed,Max Reported Memory Usage,Reported Flowdroid Flows,TP,FP,TN,FN,Flows Not Evaluated"]
    unmodified = "Unmodified "
    augmented = "Augmented "
    # summary_columns: List[str] = ["Benchmark ID", "APK Name"] 
    summary_columns: List[str] = ["APK Name"] 
    summary_columns += ["True Flows in Ground Truth", "False Flows in Ground Truth", "Count Discovered Sources"] 
    # TP + FN, FP + TN
    summary_columns += [unmodified + "Reported Flows", augmented + "Reported Flows"]
    # TP + FP + Flows Not Evaluated
    summary_columns += [unmodified + "TP Reported Flows", unmodified + "FP Reported Flows", unmodified + "Not Evaluated Reported Flows"]
    summary_columns += [augmented + "TP Reported Flows", augmented + "FP Reported Flows", augmented + "Not Evaluated Reported Flows"]
    summary_columns += [unmodified + "Time Elapsed", augmented + "Time Elapsed"]
    summary_columns += [unmodified + "Max Reported Memory Usage", augmented + "Max Reported Memory Usage"]
    summary_columns += [unmodified + "Error Message", augmented + "Error Message"]


    # dataframe with matching index/Benchmark ID & APK Name cols
    summary_df = results_df_from_benchmark_df(unmodified_results_df)

    summary_df["True Flows in Ground Truth"] = unmodified_results_df["TP"] + unmodified_results_df["FN"]
    summary_df["False Flows in Ground Truth"] = unmodified_results_df["FP"] + unmodified_results_df["TN"]

    # indices are expected to match
    summary_df["Count Discovered Sources"] = count_discovered_sources

    summary_df[unmodified + "Reported Flows"] = unmodified_results_df["TP"] + unmodified_results_df["FP"] + unmodified_results_df["Flows Not Evaluated"]
    summary_df[augmented + "Reported Flows"] = augmented_results_df["TP"] + augmented_results_df["FP"] + augmented_results_df["Flows Not Evaluated"]

    summary_df[unmodified + "TP Reported Flows"] = unmodified_results_df["TP"]
    summary_df[unmodified + "FP Reported Flows"] = unmodified_results_df["FP"]
    summary_df[unmodified + "Not Evaluated Reported Flows"] = unmodified_results_df["Flows Not Evaluated"]

    summary_df[augmented + "TP Reported Flows"] = augmented_results_df["TP"]
    summary_df[augmented + "FP Reported Flows"] = augmented_results_df["FP"]
    summary_df[augmented + "Not Evaluated Reported Flows"] = augmented_results_df["Flows Not Evaluated"]

    summary_df[unmodified + "Time Elapsed"] = unmodified_results_df["Time Elapsed"]
    summary_df[augmented + "Time Elapsed"] = augmented_results_df["Time Elapsed"]

    summary_df[unmodified + "Max Reported Memory Usage"] = unmodified_results_df["Max Reported Memory Usage"]
    summary_df[augmented + "Max Reported Memory Usage"] = augmented_results_df["Max Reported Memory Usage"]

    summary_df[unmodified + "Error Message"] = unmodified_results_df["Error Message"]
    summary_df[augmented + "Error Message"] = augmented_results_df["Error Message"]

    # Use the columns so the entries are in order
    return summary_df[summary_columns]


def groundtruth_df_from_xml(benchmark_df: pd.DataFrame, ground_truth_xml_path):
    tree = ET.parse(ground_truth_xml_path)
    ground_truth_root = tree.getroot()

    # assert ["Benchmark ID", "Input Model"] in benchmark_df.columns

    flow_elements = ground_truth_root.findall("flow")
    # df columns -> Flow, APK Name, APK Path, Source Signature, Sink Signature, Ground Truth Value
    flows = [Flow(element) for element in flow_elements]
    flows.sort()

    groundtruth_df = pd.DataFrame({"Flow": flows})
    # Index is set to the list index of flows
    groundtruth_df["APK Name"] = ""
    groundtruth_df["Benchmark ID"] = ""
    groundtruth_df["Source Signature"] = ""
    groundtruth_df["Sink Signature"] = ""
    groundtruth_df["Ground Truth Value"] = ""

    for i in groundtruth_df.index:
        flow: Flow = groundtruth_df.loc[i, "Flow"] # type: ignore
        groundtruth_df.loc[i, "APK Name"] = flow.get_file()

        # Match up the flow with the corresponding Benchmark ID
        mask = benchmark_df["Input Model"].apply(lambda model: model.apk().apk_name).values == groundtruth_df.loc[i, "APK Name"]

        assert sum(mask) <= 1
        if sum(mask) == 1:
            groundtruth_df.loc[i, "Benchmark ID"] = benchmark_df[mask]["Benchmark ID"].iloc[0]

            groundtruth_df.loc[i, "Source Signature"] = flow.get_source_statementgeneric()
            groundtruth_df.loc[i, "Sink Signature"] = flow.get_sink_statementgeneric()
            groundtruth_df.loc[i, "Ground Truth Value"] = flow.get_ground_truth_attribute()
        else:
            groundtruth_df.loc[i, "Benchmark ID"] = -1
    # Strip out ground truth flows not relevant to the apps in the benchmark_df
    groundtruth_df = groundtruth_df[groundtruth_df["Benchmark ID"] != -1]

    return groundtruth_df




