
from functools import reduce
import os
from typing import Dict, List
import pandas as pd
from experiment import report
from experiment.LoadBenchmark import LoadBenchmark, get_wild_benchmarks
from experiment.benchmark_name import BenchmarkName
from experiment.common import benchmark_df_from_benchmark_directory_path, flowdroid_setup_generic, get_experiment_name, get_flowdroid_file_paths, load_logcat_files_batch, setup_additional_directories, setup_experiment_dir
from experiment.flowdroid_experiment import flowdroid_on_benchmark_df, get_default_source_sink_path, source_list_of_inserted_taint_function_batch
from experiment.instrument import instrument_observations_batch
from hybrid.dynamic import ExecutionObservation, LogcatLogFileModel, get_observations_from_logcat_batch
from hybrid.flowdroid import FlowdroidArgs
from hybrid.hybrid_config import text_file_path
from intercept.instrument import HarnessObservations
from util.input import InputModel

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

def setup_and_run_analysis_by_benchmark_name(benchmark: BenchmarkName, da_results_specifier: str=""):
    
    params_in_name = [da_results_specifier] if da_results_specifier != "" else []
    experiment_name = get_experiment_name(benchmark.value, "SA-with-observations-harnessed", (0,1,0), params_in_name)
    experiment_description = "Static analysis with observations harnessed"

    # pull out all the relvant keyword args    
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
    harness_observations = HarnessObservations([])

    analysis_with_da_observations_harnessed(workdir, df, da_results_directory, default_ss_list, harness_observations, flowdroid_kwargs)

def analysis_with_da_observations_harnessed(workdir: str, df: pd.DataFrame, da_results_directory: str, default_ss_list: str, harness_observations: HarnessObservations, flowdroid_kwargs: Dict):
    # # Prepare dataframe with base apk info
    # benchmark_df_from_benchmark_directory_path()

    # load DA results, 
    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    # analyze DA results to get observations
    get_observations_from_logcat_batch("logcat_file", df, output_col="da_observations")

        # create report on DA results & observations

    instrument_intermediate_directories = setup_additional_directories(workdir, ["decoded_apks", "rebuilt_apks"])
    df["APK Model"] = df["Input Model"].apply(lambda model: model.apk())
    instrument_observations_batch(harness_observations, "da_observations", "APK Model", instrument_intermediate_directories[0], instrument_intermediate_directories[1], 
                                  df, output_col="observation_harnessed_apks")

        # create report on instrumentations

    # create tweaked S/S lists
    modified_ss_list_directory = setup_additional_directories(workdir, ["modified_sources_and_sinks"])[0]
    # source_list_with_inserted_taint_function_batch(default_ss_list, modified_ss_list_directory, "Input Model", df, output_col="ss_list_with_taint_functions")
    source_list_of_inserted_taint_function_batch(default_ss_list, modified_ss_list_directory, "Input Model", df, output_col="ss_list_with_taint_functions")
    flowdroid_kwargs["source_sink_column"] = "ss_list_with_taint_functions"
    
    # run SA on instrumented apks and S/S lists
    # flowdroid_kwargs = get_flowdroid_file_paths()
    # flowdroid_kwargs["timeout"] = 15 * 60 # seconds
    flowdroid_on_benchmark_df(workdir, df, flowdroid_logs_directory_name="flowdroid-logs", **flowdroid_kwargs)

    # create report on SA results
    pass



def hybrid_analysis_results():
    # load hybrid fd result flows
    fd_results = ""

    
    # load ground truth flows

    # load taint-function to string mapping
    # load string to implicit source mapping
    # load DA analysis results to get source observation contexts

    # generate string to explicit source w/ or w/out context mapping, compare context of SA results to observation data used to instrument
    # recover context of SA results
        # how many different observations get instrumented in the same enclosing method/class?

    # apply implicit original source to intermediate source flows
    # apply explicit original source to intermediate source flows

    # Summary table by app, # of is -> si flows, # so -> si flows after mapping, # is with context, # so with context, # si with context
        # report how many of these have context (enclosing class & method) – expected to be 0 for shallow, 95% for intercept
        # detail tables by is -> si flow and so -> si flow

    # generously compare so -> si flow to ground truth so -> si flows; give detected TP, FP and Unclassified
        # use union of observed so contexts when possible context available in ground truth
        # don't use contexts if context not available in ground truth
        # need another column for context sensitivity of comparison??

    # load plain FD results

    # Make table with calculated Miss-to-find, miss-to-miss, find-to-find, find-to-miss for TP or TP/FP
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

def instrumentation_report():
    # # LOC bloat
    pass
