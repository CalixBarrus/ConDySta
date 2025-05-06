# postprocess some flows, 
# 
# 
# reconstruct hybrid flows

# Compare with g.t. flows 

#     

import os

import pandas as pd

from experiment import common
from experiment.batch import process_as_dataframe
from experiment.benchmark_name import BenchmarkName, lookup_benchmark_name
from experiment.experiments_4_3_25 import get_readonly_decoded_apk_models, harness_observations_from_constraints, lookup_AnalysisConstraints
from experiment.flow_mapping import apply_flow_mapping, get_observation_harness_to_observed_source_map, get_observation_harness_to_string_set_map, get_observed_source_to_original_source_map, get_observed_string_to_original_source_map
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.load_flowdroid_logs import load_flowdroid_logs_batch
from hybrid.dynamic import get_observations_from_logcat_single
from hybrid.log_process_fd import get_flowdroid_flows
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from util.input import InputModel
import util.logger
logger = util.logger.get_logger(__name__)

def reconstruct_hybrid_flows():

    sa_results_directory = "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY"
    sa_results_directory = os.path.join(sa_results_directory, "flowdroid-logs")

    da_results_directory = "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"

    benchmark = lookup_benchmark_name(sa_results_directory)

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    input_df = LoadBenchmark(df_file_paths).execute()

    # load fd log paths
    load_flowdroid_logs_batch(sa_results_directory, input_df, "fd_log_path")
    harnesser = get_corresponing_harnesser(sa_results_directory)

    # load logcat paths
    input_df["Input Model Identifier"] = input_df["Input Model"].apply(lambda x: x.input_identifier())
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", input_df=input_df, output_col="logcat_file")
    input_df.drop(columns=["Input Model Identifier"], inplace=True)

    # load decoded_apk_model
    get_readonly_decoded_apk_models(benchmark, input_df=input_df, output_col="readonly_decoded_apk_model")

    # get flows from logs
    # pass blank apk_path since it's only used for some tag deep in the XML flow objects
    process_as_dataframe(get_flowdroid_flows, [True, False], [])("fd_log_path", "", input_df=input_df, output_col="flows_list")
    
    # get_observations_from_logcat_single(logcat_path: str, with_observed_strings: bool)
    process_as_dataframe(get_observations_from_logcat_single, [True, False], [])("logcat_file", True, input_df=input_df, output_col=["observations_list", "observed_strings_list"])
    
    # get flow mappings
    # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]])
    def reconstruct_flows_single(harnesser, readonly_decoded_apk_model: DecodedApkModel, observations, observed_string_sets, benchmark_name: BenchmarkName, logcat_file):
        # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]])

        """harnesser.mapping_key_cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
            harnesser.mapping_observation_lookup_cols = ["Invocation Java Signature", "Argument Register Index", "Access Path"]
            harnesser.mapping_str_observation_lookup_cols = ["Observed Strings"]"""
        observation_harness_to_string_set: pd.DataFrame = get_observation_harness_to_string_set_map(harnesser, readonly_decoded_apk_model, observations, observed_string_sets)
        # explode string sets
        observation_harness_to_string = observation_harness_to_string_set.explode(harnesser.mapping_str_observation_lookup_cols[0], ignore_index=True)
        # get_observed_string_to_original_source_map(benchmark_name: BenchmarkName, logcat_file: str="", columns: List[str]=[])
        columns = ["string_value", "scenario", "source-method-signature", "enclosing_class", "enclosing_method"]
        string_to_original_source = get_observed_string_to_original_source_map(benchmark_name, logcat_file, columns)

        observation_harness_to_original_source = apply_flow_mapping(observation_harness_to_string, string_to_original_source, harnesser.mapping_str_observation_lookup_cols, ["string_value"])

        # result_cols = []
        return observation_harness_to_original_source

    process_as_dataframe(reconstruct_flows_single, [False, True, True, True, False, True], [])(
        harnesser, "readonly_decoded_apk_model", "observations_list", "observed_strings_list", benchmark, "logcat_file", input_df=input_df, output_col="flow_dfs")
    
    sa_results_abbreviated = get_sa_results_abbreviated(sa_results_directory)
    experiment_name = common.get_experiment_name(benchmark.value, "flow_reconstruct_details", (0,1,0), params=[sa_results_abbreviated])

    experiment_id, experiment_directory_path = common.setup_experiment_dir(experiment_name, "", dependency_dict=
                                                                {"da_results_directory": da_results_directory, 
                                                                  "sa_results_directory": sa_results_directory,  })

    report_path = os.path.join(experiment_directory_path, "summary.csv")
    # report result for each app flows 
    input_df["Flow Count"] = input_df["flow_dfs"].apply(lambda x: len(x))
    input_df["App Name"] = input_df["Input Model"].apply(lambda model: model.apk().apk_name)
    summary_columns = ["App Name", "Flow Count"]
    input_df[summary_columns].to_csv(report_path)    

    # save each df to a file
    details_directory = os.path.join(experiment_directory_path, "flow_details")
    os.makedirs(details_directory, exist_ok=True)
    input_df["details_path"] = input_df["App Name"].apply(lambda x: os.path.join(details_directory, f"{x}.csv"))

    input_df.apply(lambda row: row["flow_dfs"].to_csv(row["details_path"]), axis=1)
    

def get_corresponing_harnesser(sa_results_directory) -> HarnessObservations:

    analysis_constraints = lookup_AnalysisConstraints(sa_results_directory)
    harnesser = harness_observations_from_constraints(analysis_constraints)
    harnesser.set_record_taint_function_mapping(True)
    
    return harnesser

def get_sa_results_abbreviated(sa_results_directory: str) -> str: 
    # example: "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY/flowdroid-logs"

    # Use after the benchmark name and forward.

    benchmark = lookup_benchmark_name(sa_results_directory)

    experiment_directory = os.path.basename(sa_results_directory) if benchmark.value in os.path.basename(sa_results_directory) else os.path.dirname(sa_results_directory)

    return "SA" + os.path.basename(experiment_directory).split(benchmark.value)[1]




    