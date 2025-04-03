
from functools import reduce
import os
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from experiment import report
from experiment.batch import process_as_dataframe
from experiment.flow_mapping import get_observation_harness_to_string_set_map, get_observed_source_to_original_source_map, get_observation_harness_to_observed_source_map, get_observed_string_to_original_source_map, get_observed_string_to_original_source_map_batch_df_output
from experiment import flow_mapping
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.benchmark_name import BenchmarkName
from experiment.common import benchmark_df_from_benchmark_directory_path, flowdroid_setup_generic, get_experiment_name, get_flowdroid_file_paths, load_logcat_files_batch, setup_additional_directories, setup_experiment_dir
from experiment.flowdroid_experiment import flowdroid_on_benchmark_df, groundtruth_df_from_xml, parse_flowdroid_results
from experiment.instrument import instrument_observations_batch
from experiment.load_source_sink import get_default_source_sink_path, source_list_of_inserted_taint_function_batch
from hybrid import hybrid_config
from hybrid.dynamic import ExecutionObservation, LogcatLogFileModel, get_observations_from_logcat_batch, get_observations_from_logcat_single
from hybrid.flow import compare_flows, get_reported_fd_flows_as_df
from hybrid.flowdroid import FlowdroidArgs
from hybrid.hybrid_config import text_file_path
from hybrid.log_process_fd import flowdroid_time_path_from_log_path, get_count_found_sources, get_flowdroid_analysis_error, get_flowdroid_flows, get_flowdroid_memory, get_flowdroid_reported_leaks_count, get_flowdroid_time
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from util.input import InputModel

import util.logger
logger = util.logger.get_logger(__name__)

def get_da_results_directory(benchmark_name: BenchmarkName, specifier: str=""):
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            if specifier == "shallow":
                return "data/OneDrive_1_2-7-2025/2024-10-26-execution-full-fossdroid-extendedStrList-60s/logcat-output"
            elif specifier == "intercept":
                return "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"

        case BenchmarkName.GPBENCH:
            return "data/OneDrive_1_2-7-2025/initial-results-for-xiaoyin/2024-10-21-execution-full-gpbench-manual/logcat-output"
        

def test_hybrid_analysis_returns_only():
    setup_and_run_analysis_by_benchmark_name(BenchmarkName.GPBENCH)
    setup_and_run_analysis_by_benchmark_name(BenchmarkName.FOSSDROID, "shallow")
    setup_and_run_analysis_by_benchmark_name(BenchmarkName.FOSSDROID, "intercept")

def setup_and_run_analysis_by_benchmark_name(benchmark: BenchmarkName, da_results_specifier: str="", da_filter_specifier: str=""):
    
    params_in_name = [da_results_specifier] if da_results_specifier != "" else []
    experiment_name = get_experiment_name(benchmark.value, "SA-with-observations-harnessed", (0,1,1), params_in_name)
    experiment_description = """Static analysis with observations harnessed
    Doesn't reinstrument apks if already done in the experiment directory.
    """

    # pull out all the relevant keyword args    
    da_results_directory = get_da_results_directory(benchmark, da_results_specifier)
    default_ss_list = get_default_source_sink_path(benchmark)

    flowdroid_kwargs = get_flowdroid_file_paths() 
    flowdroid_kwargs["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
    flowdroid_kwargs["timeout"] = 3 * 60 # seconds

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    
    # Setup up workdir and documentation
    experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                                    {"da_results_directory": da_results_directory, 
                                                                     } | flowdroid_kwargs | df_file_paths)
    workdir = experiment_directory_path

    # actually construct dependencies
    df = LoadBenchmark(df_file_paths).execute()
    harness_observations = HarnessObservations()

    observation_harnessed_apks_column = "observation_harnessed_apks"

    dont_reinstrument_apks = True
    if dont_reinstrument_apks:
        df[observation_harnessed_apks_column] = df["Input Model"].apply(lambda model: hybrid_config.apk_path(os.path.join(workdir, "rebuilt_apks"), model.apk()))
        mask = ~df[observation_harnessed_apks_column].apply(os.path.exists)
        logger.debug(f"Skipping {sum(~mask)} apks that are already instrumented")
    else: 
        mask = [True] * len(df)

    harness_based_on_observations(workdir, df[mask], da_results_directory, harness_observations, observation_harnessed_apks_column)

    run_fd_on_apks(workdir, df, da_results_directory, default_ss_list, harness_observations, flowdroid_kwargs, observation_harnessed_apks_column)

def lookup_harnessed_apks(workdir, input_model) -> Tuple[str, bool]:
    path = hybrid_config.apk_path(os.path.join(workdir, "rebuilt_apks"), input_model.apk())
    return path, os.path.exists(path)

def harness_based_on_observations(workdir: str, df: pd.DataFrame, da_results_directory: str, harness_observations: HarnessObservations, output_apks_column: str):
    # load DA results, 
    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    # analyze DA results to get observations
    get_observations_from_logcat_batch("logcat_file", False, df, output_col="da_observations")

        # create report on DA results & observations

    instrument_intermediate_directories = setup_additional_directories(workdir, ["decoded_apks", "rebuilt_apks"])
    df["APK Model"] = df["Input Model"].apply(lambda model: model.apk())
    
    instrument_observations_batch(harness_observations, "da_observations", "APK Model", instrument_intermediate_directories[0], instrument_intermediate_directories[1], 
                                  df, output_col=output_apks_column)

        # create report on instrumentations

def run_fd_on_apks(workdir: str, df: pd.DataFrame, da_results_directory: str, default_ss_list: str, harness_observations: HarnessObservations, flowdroid_kwargs: Dict, apks_column: str):

    # create tweaked S/S lists
    modified_ss_list_directory = setup_additional_directories(workdir, ["modified_sources_and_sinks"])[0]
    # source_list_with_inserted_taint_function_batch(default_ss_list, modified_ss_list_directory, "Input Model", df, output_col="ss_list_with_taint_functions")
    source_list_of_inserted_taint_function_batch(default_ss_list, modified_ss_list_directory, "Input Model", df, output_col="ss_list_with_taint_functions")
    flowdroid_kwargs["source_sink_column"] = "ss_list_with_taint_functions"
    
    # run SA on instrumented apks and S/S lists
    # flowdroid_kwargs = get_flowdroid_file_paths()
    # flowdroid_kwargs["timeout"] = 15 * 60 # seconds
    flowdroid_on_benchmark_df(workdir, df, flowdroid_logs_directory_name="flowdroid-logs", apk_path_column=apks_column, **flowdroid_kwargs)

    # create report on SA results
    pass



def hybrid_flow_postprocessing_single(flowdroid_log_path: str, original_apk_path: str, harnesser: HarnessObservations, decoded_apk_path: str, benchmark_name: BenchmarkName, logcat_file: str) -> pd.DataFrame:
    """
    flowdroid_log_path 
    original_apk_path: kinda optional; used for metadata in Flow objects
    harnesser: should have the same settings as when app was fed to SA was instrumented; expects record_taint_mapping to be true; expects a fresh copy of the harnesser
    decoded_apk_path 
    benchmark_name 
    logcat_file 
    result: TODO make a test in order to figure out column filtering
    """

    
    # load hybrid fd result flows
    reported_fd_flows = get_flowdroid_flows(flowdroid_log_path, original_apk_path) # TODO: add deduplicate_on="signature_in_enclosing_method" as kwarg to this? 

    observations, observed_strings = get_observations_from_logcat_single(logcat_file, with_observed_strings=True)
    decoded_apk_model = DecodedApkModel(decoded_apk_path)


    cols = ["source_function", "source_enclosing_method", "source_enclosing_class", "", "", ""]
    df_sa_observation: pd.DataFrame = get_reported_fd_flows_as_df(reported_fd_flows, col_names=cols)

    # cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method", "Observed Strings"] # cols are determined by harnesser, filtered by get_observation_harness_to_string_set_map
    sa_observation_to_observed_string_set_map: pd.DataFrame = flow_mapping.get_observation_harness_to_string_set_map(harnesser, decoded_apk_model, observations, observed_strings)
    # Explode string sets so there is a row per string
    sa_observation_to_observed_string_map = sa_observation_to_observed_string_set_map.explode(harnesser.mapping_str_observation_lookup_cols[0], ignore_index=True)

    cols = ["observed_string", "original_source_method", "scenario", "original_source_enclosing_method", "original_source_enclosing_class"]
    observed_string_to_original_source_map: pd.DataFrame = get_observed_string_to_original_source_map(benchmark_name, logcat_file, columns=cols)


    df_mapped_flows = df_sa_observation.merge(
            sa_observation_to_observed_string_map, how="left", 
            left_on=["source_function", "source_enclosing_method", "source_enclosing_class"], 
            right_on=["Taint Function Name", "Enclosing Method", "Enclosing Class"]
        ).merge(
            observed_string_to_original_source_map, how="left", 
            left_on="Observed Strings", 
            right_on="observed_string")
    # Intermediately, the reported static flows themselves that don't map succesfully; they should theoretically all be mapped to some string and scenario

    # TODO: No doubt need to filter down columns and possibly deduplicate; will need to test this probably

    return df_mapped_flows

def report_hybrid_flow_postprocessing():
    # Summary tables for flows, mappings, and flow transformations; row per app, 
            # of harness source -> sink flows, # of intermediate source -> sink flows, # orig. source -> sink flows after mapping, 
                # this is mostly to observe how intense the multiplication of flows is
            # count of harness source with context, intermediate source with context, # orig source with context, # sink with context
                # This is more for debugging, also being aware of if implicit/explicit expectations are being met
                # e.g., for the original sources, the # of expected contexts to be 0 for shallow, 95% for intercept
        # detail tables for each app (different for each of these)
        #   harness_ref to intermediate_source map
        #   intermediate_ref_to str set map
        #   str to original source map
        #   harness source -> sink flows (flow count, then pretty print each flow)
        #   intermediate source -> sink flows (flow count, then pretty print each flow)
        #   original source -> sink flows (flow count, then pretty print each flow)

    reported_fd_flows = get_flowdroid_flows(flowdroid_log_path, apk_path)
    cols = ["source_function", "source_enclosing_method", "source_enclosing_class", "", "", ""]
    df_sa_observation: pd.DataFrame = get_reported_fd_flows_as_df(reported_fd_flows, col_names=cols)

    df_mapped_flows = hybrid_flow_postprocessing_single(flowdroid_log_path, apk_path, harnesser, decoded_apk_path, benchmark_name, logcat_file)

    cols = ["App Name",
            "Count FD Flows", # (harness source -> sink) 
            "Count Mapped Flows", 
            "Count Unmapped Flows", ]
    cols_flow_mapping_stepwise = ["Count Intermediate Source to Sink Flows", 
                                  "Count Distinct Detected String to Sink Flows",
                                  "Count Original Source to Sink Flows"]
    cols_flows_context_summary = ["FD Flows with sink context", 
            "FD Flows with source context", 
            "Count Original Source to Sink Flows", 
            "Count mapped original source flows with enclosing class/method context", 
            "Count mapped original source flows with function"
            ]


    df_summary_of_flows = ""

def report_hybrid_against_groundtruth():
    # load ground truth flows
    ground_truth_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)

    compare_flows()
    # generously compare so -> si flow to ground truth so -> si flows; give detected TP, FP and Unclassified
        # use union of observed so contexts when possible context available in ground truth
        # don't use contexts if context not available in ground truth
        # need another column for context sensitivity of comparison??
    pass
    
def report_groundtruth():
    # Summary table: Row per app
        # Count True Positive, Count False Positive, Count Source contexts, Count Sink contexts, Source func names, Sink func names
    # Detail table per app
        # Count True flows and False flows
        # Pretty print true flows, then false flows
    pass

def report_hybrid_vs_static_against_groundtruth():
    # load up results of regular fd
    # Make table with calculated Miss-to-find, miss-to-miss, find-to-find, find-to-miss for TP or TP/FP

    # report_miss_to_find_etc(hybrid_flows, static_flows, ground_truth_df, apk_name)
    # tp_flows, fp_flows, tn_flows, fn_flows, inconclusive_flows = compare_flows(detected_flows: List[Flow], ground_truth_flows_df: pd.DataFrame, apk_name: str)

        # tp_flows, fp_flows, tn_flows, fn_flows, inconclusive_flows = compare_flows(plain_fd_detected_flows: List[Flow], ground_truth_flows_df: pd.DataFrame, apk_name: str)
    # hybrid/regular_fd_vs_groundtruth_summary(reglar flows, hybrid flows, ground truth_df) -> table with the 4 or 8 miss-to-find, etc. flows

    # supporting details table with a row per G.T. flow (found by fd original?, found by hybrid?)

    # Detail table on unclassified flows, both is -> si and so -> si
        # summary table with a row per string, # flows observing the string led to, relevant methods in implicit mapping
        # summary table by apk, # of unclassified flows, strings observed that led to the flows
    pass

def run_all_da_observation_reports():
    
    for benchmark, da_results_specifier in [
        (BenchmarkName.GPBENCH, ""),
        (BenchmarkName.FOSSDROID, "shallow"),
        (BenchmarkName.FOSSDROID, "intercept"),
        ]:

        params_in_name = [da_results_specifier] if da_results_specifier != "" else []
        experiment_name = get_experiment_name(benchmark.value, "da-observations-report", (0,1,0), params_in_name)
        experiment_description = "Static analysis with observations harnessed"

        da_results_directory = get_da_results_directory(benchmark, da_results_specifier)

        experiment_id, experiment_directory_path = setup_experiment_dir(experiment_name, experiment_description, dependency_dict=
                                                                    {"da_results_directory": da_results_directory, 
                                                                        })

        df_file_paths = get_wild_benchmarks(benchmark)[0]
        df = LoadBenchmark(df_file_paths).execute()

        da_observation_report(da_results_directory, df, experiment_directory_path)




def da_observation_report(da_results_directory: str, df: pd.DataFrame, workdir: str):
        
    # Summary Table by app:
        # app name
        # was relevant DA successful?
        # # of instrumentation reports
        # # of taint observations (1 or 2 instr reports -> taint observation)
        # Union of String values observed for taint observations
        # # Harnessed source calls

    # By app, Detail Tables:
        # Instrumentation reports
        # Harnessed source calls 
        # ** Taint observations with relevant string values

    
    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    summary_table = pd.DataFrame({"App Name": df["Input Model Identifier"]}, index=df.index)

    
    logcat_available = (df["logcat_file"] != "")
    summary_table["DA Available"] = logcat_available

    instrumentation_report_details_directory, observed_intermediate_sources_details_directory, harness_source_calls_details_directory = setup_additional_directories(workdir, ["instrumentation_report_details", "observed_intermediate_sources_details", "harnessed_source_calls_details"])    

    for i in df[logcat_available].index:
        logcat_model = LogcatLogFileModel(df.at[i, "logcat_file"])
        

        instrumentation_report_tuples: List = logcat_model.scan_log_for_instrumentation_report_tuples()        
        summary_table.at[i, "Instrumentation Reports"] = len(instrumentation_report_tuples)

        observation = ExecutionObservation()
        list(map(observation.parse_instrumentation_result, instrumentation_report_tuples))
        tainting_invocation_contexts, contexts_strings = observation.get_tainting_invocation_contexts(with_observed_strings=True)

        summary_table.at[i, "Intermediate Sources"] = len(tainting_invocation_contexts)
        summary_table.at[i, "Intermediate Source Observed Strings"] = str(reduce(lambda x, y: x.union(y), contexts_strings)) if len(contexts_strings) > 0 else ""

        harnessed_source_calls = logcat_model.scan_log_for_harnessed_source_calls()
        summary_table.at[i, "Observed Harnessed Source Calls"] = len(harnessed_source_calls)

        # For each app, what is the max # of different intermediate sources in a given context? (enclosing method/class)
            # This will determine the feasibility of differentiating these with separate taint functions
        max_in_context_col = "Max Intermediate Sources in Same Context (Enclosing Class/Method)"
        context_table = observation.get_tainting_invocation_contexts_as_table(enclosing_class_col="enclosing_class", enclosing_method_col="enclosing_method")
        summary_table.at[i, max_in_context_col] = max(context_table[["enclosing_class", "enclosing_method"]].value_counts()) if len(contexts_strings) > 0 else ""
        

        # Save details on Instrumentation Reports, Observed intermediate sources, and harnessed source calls
        input_model = df.at[i, "Input Model"]
        instrumentation_report_details_path = text_file_path(instrumentation_report_details_directory, input_model)
        observed_intermediate_sources_details_path = text_file_path(observed_intermediate_sources_details_directory, input_model)
        harness_source_calls_details_path = text_file_path(harness_source_calls_details_directory, input_model)

        report.save_to_file(instrumentation_report_details_path, report.instrumentation_reports_details(instrumentation_report_tuples))
        report.save_to_file(observed_intermediate_sources_details_path, report.observed_intermediate_sources_details(tainting_invocation_contexts, contexts_strings))
        report.save_to_file(harness_source_calls_details_path, report.harnessed_source_calls_details(harnessed_source_calls))


    summary_path = os.path.join(workdir, "summary.txt")
    report.save_to_file(summary_path, summary_table.to_string())

def save_all_observed_string_to_source_maps():
    for benchmark, da_results_specifier in [
        (BenchmarkName.GPBENCH, ""),
        (BenchmarkName.FOSSDROID, "shallow"),
        (BenchmarkName.FOSSDROID, "intercept"),
        ]:
        path = os.path.join("data/experiments", "2025-03-02-expected-string-mappings", f"mapping_{benchmark.value}_{da_results_specifier}.csv")
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))

        df_mapping = get_each_observed_string_to_source_maps(benchmark, da_results_specifier)
        report.save_to_file(path, df_mapping.to_string())

def get_each_observed_string_to_source_maps(benchmark_name: BenchmarkName, specifier: str) -> pd.DataFrame:
    da_results_directory = get_da_results_directory(benchmark_name, specifier)


    df_file_paths = get_wild_benchmarks(benchmark_name)[0]
    df = LoadBenchmark(df_file_paths).execute()

    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")
    df_mapping = get_observed_string_to_original_source_map_batch_df_output(benchmark_name, "logcat_file", df, "Benchmark ID")

    return df_mapping

def instrumentation_report():
    # # LOC bloat
    pass
