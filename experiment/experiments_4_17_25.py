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
from hybrid.flow import Flow, get_reported_fd_flows_as_df
from hybrid.hybrid_config import apk_path
from hybrid.log_process_fd import deduplicate_flows, get_flowdroid_flows, get_flowdroid_flows_from_df
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from util.input import InputModel
import util.logger
logger = util.logger.get_logger(__name__)

def reconstruct_hybrid_flows_spot_check():
    sa_results_directory = "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY"
    sa_results_directory = "data/experiments/2025-04-23_SA-with-observations-harnessed_gpbench_0.1.7_DEPTH_0_DA_RESULTS_ONLY"

    reconstruct_hybrid_flows(sa_results_directory)

def reconstruct_hybrid_flows_all_SA_0_1_7():
    experiments_subdirectory = "flow_reconstruction_SA_0.1.7"

    experiments_directory = "data/experiments" 
    filtered_items = list(filter(lambda x: "SA-with-observations-harnessed" in x and "0.1.7" in x, os.listdir(experiments_directory)))
    for i, item in enumerate(filtered_items):
        logger.info(f"Reconstructing hybrid flows for {i+1}/{len(filtered_items)}: {item}")
        
        sa_results_directory = os.path.join(experiments_directory, item)
        reconstruct_hybrid_flows(sa_results_directory, experiments_subdirectory=experiments_subdirectory)

def reconstruct_hybrid_flows(sa_results_directory: str, experiments_subdirectory: str=""):
    sa_results_fd_logs_directory = os.path.join(sa_results_directory, "flowdroid-logs")

    da_results_directory = common.lookup_experiment_parameter(sa_results_directory, "da_results_directory")
    assert os.path.exists(da_results_directory), f"DA results directory {da_results_directory} does not exist"
    # da_results_directory = "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"

    # sa_results_directory = "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_shallow_FULL_CONTEXT_AND_FIELD_SENSITIVITY/flowdroid-logs"

    # # todo: lookup da_results_directory from readme
    # da_results_directory = "data/OneDrive_1_2-7-2025/2024-10-26-execution-full-fossdroid-extendedStrList-60s/logcat-output"
    

    benchmark = lookup_benchmark_name(sa_results_fd_logs_directory)

    df_file_paths = get_wild_benchmarks(benchmark)[0]
    input_df = LoadBenchmark(df_file_paths).execute()

    # load fd log paths
    load_flowdroid_logs_batch(sa_results_fd_logs_directory, input_df, "fd_log_path")
    harnesser: HarnessObservations = get_corresponding_reconstruct_harnesser(sa_results_fd_logs_directory)

    # load logcat paths
    input_df["Input Model Identifier"] = input_df["Input Model"].apply(lambda x: x.input_identifier())
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", input_df=input_df, output_col="logcat_file")
    input_df.drop(columns=["Input Model Identifier"], inplace=True)

    # get flows from logs
    apk_path = ""   # pass blank apk_path since it's only used for some tag deep in the XML flow objects
    get_flowdroid_flows_from_df("fd_log_path", apk_path, input_df=input_df, output_col="flows_list")

    # load decoded_apk_model
    get_readonly_decoded_apk_models(benchmark, input_df=input_df, output_col="readonly_decoded_apk_model")
    
    # deduplicate flows
    no_errors_mask = input_df["last_error"] == ""
    input_df["flows_list"] = input_df[no_errors_mask]["flows_list"].apply(deduplicate_flows)
    
    # get_observations_from_logcat_single(logcat_path: str, with_observed_strings: bool)
    process_as_dataframe(get_observations_from_logcat_single, [True, False], [])("logcat_file", True, input_df=input_df, output_col=["observations_list", "observed_strings_list"])
    
    sa_results_abbreviated = get_sa_results_abbreviated(sa_results_fd_logs_directory)
    experiment_name = common.get_experiment_name(benchmark.value, "flow_reconstruct_details", (0,1,0), params=[sa_results_abbreviated])

    experiment_id, experiment_directory_path = common.setup_experiment_dir(experiment_name, "", dependency_dict=
                                                                {"da_results_directory": da_results_directory, 
                                                                  "sa_results_directory": sa_results_fd_logs_directory,  }, specify_experiments_subdirectory=experiments_subdirectory)
    logger.debug(f"Experiment directory path: {experiment_directory_path}")

    #### get flow mappings

    def reconstruct_flows_single(harnesser: HarnessObservations, readonly_decoded_apk_model: DecodedApkModel, observations, observed_string_sets, benchmark_name: BenchmarkName, logcat_file, flows_list):
        # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]])

        """harnesser.mapping_key_cols = ["Taint Function Signature", "Enclosing Class", "Enclosing Method Name"]
            harnesser.mapping_observation_lookup_cols = ["Invocation Java Signature", "Argument Register Index", "Access Path"]
            harnesser.mapping_str_observation_lookup_cols = ["Observed Strings"]"""
        observation_harness_to_string_set: pd.DataFrame = get_observation_harness_to_string_set_map(harnesser, readonly_decoded_apk_model, observations, observed_string_sets)

        # explode string sets
        observation_harness_to_string = observation_harness_to_string_set.explode(harnesser.mapping_str_observation_lookup_cols[0], ignore_index=True)
        observation_harness_to_string.drop_duplicates(inplace=True)        

        columns = ["string_value", "scenario", "orig_source-method-signature", "orig_enclosing_class", "orig_enclosing_method"]
        string_to_original_source = get_observed_string_to_original_source_map(benchmark_name, logcat_file, columns)
        string_to_original_source.drop_duplicates(inplace=True)        


        # apply the mapping to the flows and save the results
        flows_column_names = ["flow", "source_method", "source_enclosing_method", "source_enclosing_class", "sink_method", "sink_enclosing_method", "sink_enclosing_class"]
        flows_df = get_reported_fd_flows_as_df(flows_list, flows_column_names)
        # ["Taint Function Name", "Enclosing Class", "Enclosing Method"]

        # make "source_enclosing_method" to be "source_enclosing_method_name"
        flows_df["source_enclosing_method_name"] = flows_df["flow"].apply(lambda flow: flow.get_source_method_name())

        flows_df.drop(columns=["flow"], inplace=True) # for readability when printing this out

        flows_source_key_columns = ["source_method", "source_enclosing_class", "source_enclosing_method_name"]
        # self.mapping_key_cols = ["Taint Function Signature", "Enclosing Class", "Enclosing Method Name"]
        flow_sink_to_string = apply_flow_mapping(flows_df, observation_harness_to_string, flows_source_key_columns, harnesser.mapping_key_cols)

        flow_sink_to_original_source = apply_flow_mapping(flow_sink_to_string, string_to_original_source, harnesser.mapping_str_observation_lookup_cols, ["string_value"])

        return flow_sink_to_original_source

    process_as_dataframe(reconstruct_flows_single, [False, True, True, True, False, True, True], [])(
        harnesser, "readonly_decoded_apk_model", "observations_list", "observed_strings_list", benchmark, "logcat_file", "flows_list", input_df=input_df, output_col="reconstructed_flows_dfs")
    

    report_path = os.path.join(experiment_directory_path, "summary.csv")
    # report result for each app flows 
    input_df["Reconstructed Flow Count"] = input_df["reconstructed_flows_dfs"].apply(lambda x: len(x))
    input_df["App Name"] = input_df["Input Model"].apply(lambda model: model.apk().apk_name)

    # Since the mappings are left joined, unmapped values will be null
    no_errors_mask = input_df["last_error"] == ""
    input_df["count_recovered_scenario"] = input_df[no_errors_mask]["reconstructed_flows_dfs"].apply(lambda x: x["scenario"].isnull().sum())
    input_df["recovered_scenarios"] = input_df[no_errors_mask]["reconstructed_flows_dfs"].apply(lambda x: str(x["scenario"].unique().tolist()))
    input_df["count_recovered_orig_source_signature"] = input_df[no_errors_mask]["reconstructed_flows_dfs"].apply(lambda x: (~x["orig_source-method-signature"].isnull()).sum()) 
    input_df["count_recovered_orig_source_enclosing_method"] = input_df[no_errors_mask]["reconstructed_flows_dfs"].apply(lambda x: (~x["orig_enclosing_method"].isnull()).sum()) 
    summary_columns = ["App Name", "Reconstructed Flow Count", "count_recovered_scenario", "recovered_scenarios", "count_recovered_orig_source_signature", "count_recovered_orig_source_enclosing_method", "last_error"]
    input_df[summary_columns].to_csv(report_path)    

    # save each df to a file
    details_directory = os.path.join(experiment_directory_path, "flow_mapping_details")
    os.makedirs(details_directory, exist_ok=True)
    input_df["details_path"] = input_df["App Name"].apply(lambda x: os.path.join(details_directory, f"{x}.csv"))

    no_errors_mask = input_df["last_error"] == ""
    input_df[no_errors_mask].apply(lambda row: row["reconstructed_flows_dfs"].to_csv(row["details_path"]), axis=1)

    # get more details
    flows_details_directory = os.path.join(experiment_directory_path, "fd_flows_details")
    os.makedirs(flows_details_directory, exist_ok=True)

    observation_harness_to_string_set_details_directory = os.path.join(experiment_directory_path, "obs2str_details")
    os.makedirs(observation_harness_to_string_set_details_directory, exist_ok=True)
    # observation_harness_to_string_set_details_path = ""

    str2origsrc_details_directory = os.path.join(experiment_directory_path, "str2origsrc_details")
    os.makedirs(str2origsrc_details_directory, exist_ok=True)

    def report_mapping_details(harnesser, readonly_decoded_apk_model: DecodedApkModel, observations, observed_string_sets, benchmark_name: BenchmarkName, logcat_file, app_name, flows_list):
        # get_observation_harness_to_string_set_map(harnesser, decoded_apk_model: DecodedApkModel, observations: List[InvocationRegisterContext], observed_strings: List[Set[str]])

        flows_column_names = ["flow", "source_method", "source_enclosing_method", "source_enclosing_class", "sink_method", "sink_enclosing_method", "sink_enclosing_class"]
        flows_df = get_reported_fd_flows_as_df(flows_list, flows_column_names)
        fd_flows_details_path = os.path.join(flows_details_directory, f"{app_name}.csv")
        flows_df.drop(columns=["flow"], inplace=True) # for readability when printing this out
        flows_df.to_csv(fd_flows_details_path)

        """harnesser.mapping_key_cols = ["Taint Function Name", "Enclosing Class", "Enclosing Method"]
            harnesser.mapping_observation_lookup_cols = ["Invocation Java Signature", "Argument Register Index", "Access Path"]
            harnesser.mapping_str_observation_lookup_cols = ["Observed Strings"]"""
        observation_harness_to_string_set: pd.DataFrame = get_observation_harness_to_string_set_map(harnesser, readonly_decoded_apk_model, observations, observed_string_sets)
        observation_harness_to_string_set_details_path = os.path.join(observation_harness_to_string_set_details_directory, f"{app_name}.csv")
        observation_harness_to_string_set.to_csv(observation_harness_to_string_set_details_path)
        
        # explode string sets
        # observation_harness_to_string = observation_harness_to_string_set.explode(harnesser.mapping_str_observation_lookup_cols[0], ignore_index=True)
        # get_observed_string_to_original_source_map(benchmark_name: BenchmarkName, logcat_file: str="", columns: List[str]=[])
        columns = ["string_value", "scenario", "source-method-signature", "enclosing_class", "enclosing_method"]
        string_to_original_source = get_observed_string_to_original_source_map(benchmark_name, logcat_file, columns)
        string_to_original_source_details_path = os.path.join(str2origsrc_details_directory, f"{app_name}.csv")
        string_to_original_source.to_csv(string_to_original_source_details_path)

        # observation_harness_to_original_source = apply_flow_mapping(observation_harness_to_string, string_to_original_source, harnesser.mapping_str_observation_lookup_cols, ["string_value"])

        # result_cols = []
        # return observation_harness_to_original_source

    process_as_dataframe(report_mapping_details, [False, True, True, True, False, True, True, True], [])(
        harnesser, "readonly_decoded_apk_model", "observations_list", "observed_strings_list", benchmark, "logcat_file", "App Name", "flows_list", input_df=input_df, output_col="")
    

def get_corresponding_reconstruct_harnesser(sa_results_directory) -> HarnessObservations:

    analysis_constraints = lookup_AnalysisConstraints(sa_results_directory)
    harnesser = harness_observations_from_constraints(analysis_constraints)
    harnesser.set_record_taint_function_mapping(True)
    
    return harnesser

def get_sa_results_abbreviated(sa_results_directory: str) -> str: 
    # example: "data/experiments/2025-04-15_SA-with-observations-harnessed_fossdroid_0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY/flowdroid-logs"

    # Use after the benchmark name and forward.
    # e.g. "0.1.6_intercept_DEPTH_0_DA_RESULTS_ONLY"

    benchmark = lookup_benchmark_name(sa_results_directory)

    experiment_directory = os.path.basename(sa_results_directory) if benchmark.value in os.path.basename(sa_results_directory) else os.path.dirname(sa_results_directory)

    return "SA" + os.path.basename(experiment_directory).split(benchmark.value)[1]




    