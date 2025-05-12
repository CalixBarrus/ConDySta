
# report on observations to show how the count of instrumented sources should
# Count DA reports; count observations after processing; Breakdown of Access Path lvl (0 and 1), Count Observations When Combined by Disabling Field Sensitivity

from enum import Enum
import enum
import itertools
import os
from typing import List, Tuple

import pandas as pd

from experiment import common
from experiment.batch import ExperimentStepException, process_as_dataframe
from experiment.benchmark_name import BenchmarkName
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from experiment.report import save_to_file
from hybrid import hybrid_config
from hybrid.access_path import AccessPath
from hybrid.dynamic import ExecutionObservation, LogcatLogFileModel


from hybrid.invocation_register_context import InvocationRegisterContext, pretty_print_observation
from intercept import decode, decoded_apk_model
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from intercept.instrumentation_report import InstrumentationReport
from util.input import InputModel
import util.logger
logger = util.logger.get_logger(__name__)



def report_observations_profile_single(logcat_path: str) -> Tuple[int, int, int, int, int]:

    log = LogcatLogFileModel(logcat_path)
    report_tuples: List[Tuple[InstrumentationReport, AccessPath, str]] = log.scan_log_for_instrumentation_report_tuples()

    observation_parser = ExecutionObservation()
    for da_result in report_tuples:
        observation_parser.parse_instrumentation_result(da_result)
    observations: List[InvocationRegisterContext]
    observations, _ = observation_parser.get_tainting_invocation_contexts(with_observed_strings=True)

    count_reports = len(report_tuples)
    count_observations = len(observations)

    count_observations_lvl_0_ap = len([observation for observation in observations if len(observation[1].fields) == 1])
    count_observations_lvl_1_ap = len([observation for observation in observations if len(observation[1].fields) > 1])
    harness_observations = HarnessObservations(disable_field_sensitivity=True)
    harness_observations.set_observations(observations)
    count_observations_field_sensitivity_reduced = len(harness_observations.processed_observations)

    return count_reports, count_observations, count_observations_lvl_0_ap, count_observations_lvl_1_ap, count_observations_field_sensitivity_reduced

report_observations_profile_batch = process_as_dataframe(report_observations_profile_single, [True], [])

class DynamicResultsSpecifier(Enum):
    GPBENCH = ""
    FOSSDROID_SHALLOW = "shallow"
    FOSSDROID_INTERCEPT = "intercept"

def get_da_results_directory(benchmark_name: BenchmarkName, specifier: DynamicResultsSpecifier) -> str:
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            if specifier == DynamicResultsSpecifier.FOSSDROID_SHALLOW:
                # return "data/OneDrive_1_2-7-2025/2024-10-26-execution-full-fossdroid-extendedStrList-60s/logcat-output"
                return "data/uploads/2025-04-22_execution_fossdroid_0.1.1_shallow-args_monkey/logcat-output"
            elif specifier == DynamicResultsSpecifier.FOSSDROID_INTERCEPT:
                # return "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"
                return "data/uploads/2025-04-22_execution_fossdroid_0.1.1_intercept-args_monkey/logcat-output"

        case BenchmarkName.GPBENCH:
            # return "data/OneDrive_1_2-7-2025/initial-results-for-xiaoyin/2024-10-21-execution-full-gpbench-manual/logcat-output"
            return "data/uploads/2025-04-22_execution_gpbench_0.1.1_shallow-args_manual/logcat-output"
        
    raise NotImplementedError()        


def report_observations_profile_da_experiments_all():
    for benchmark_name, specifier in [
        (BenchmarkName.GPBENCH, DynamicResultsSpecifier.GPBENCH),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_SHALLOW),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_INTERCEPT)
    ]:
        report_observations_profile_da_experiments(benchmark_name, specifier)

def report_observations_profile_da_experiments(benchmark_name: BenchmarkName, specifier: DynamicResultsSpecifier):

    df_file_paths = get_wild_benchmarks(benchmark_name)[0]
    df = LoadBenchmark(df_file_paths).execute()

    da_results_directory = get_da_results_directory(benchmark_name, specifier)
    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    # report_df = pd.DataFrame({"App Name": df["Input Model"].apply(lambda model: model.apk().apk_name), "logcat_file": df["logcat_file"]})

    result_cols = ["count_reports", "count_observations", "count_observations_lvl_0_ap", "count_observations_lvl_1_ap", "count_observations_field_sensitivity_reduced"]
    report_observations_profile_batch("logcat_file", input_df=df, output_col=result_cols)

    report_name = common.get_experiment_name(benchmark_name.value, "sep24-da-observations-report", (0,1,0), params=[specifier.value])
    
    reports_dir = os.path.join("data", "experiments", "apr25-da-observations-reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"{report_name}.csv")

    df["App Name"] = df["Input Model"].apply(lambda model: model.apk().apk_name)

    df[["App Name"] + result_cols].to_csv(report_path)

def report_observation_details_single(logcat_path: str):
    # print all the observations

    log = LogcatLogFileModel(logcat_path)
    report_tuples: List[Tuple[InstrumentationReport, AccessPath, str]] = log.scan_log_for_instrumentation_report_tuples()

    observation_parser = ExecutionObservation()
    for da_result in report_tuples:
        observation_parser.parse_instrumentation_result(da_result)
    observations: List[InvocationRegisterContext]
    observations, string_sets = observation_parser.get_tainting_invocation_contexts(with_observed_strings=True)

    count_reports, count_observations, count_observations_lvl_0_ap, count_observations_lvl_1_ap, count_observations_field_sensitivity_reduced = report_observations_profile_single(logcat_path)
    report = f"count_reports: {count_reports}, count_observations: {count_observations}, count_observations_lvl_0_ap: {count_observations_lvl_0_ap}, count_observations_lvl_1_ap: {count_observations_lvl_1_ap}, count_observations_field_sensitivity_reduced: {count_observations_field_sensitivity_reduced}\n"
    
    for observation, observed_strings in zip(observations, string_sets):
        report += f"{pretty_print_observation(observation, observed_strings)}\n"

    return report

report_observation_details_batch = process_as_dataframe(report_observation_details_single, [True], [])

def report_instrumentation_locations_single(logcat_path: str, decoded_apk_root_path: str, harness_observation: HarnessObservations) -> str:
    decoded_apk_model = DecodedApkModel(decoded_apk_root_path)

    log = LogcatLogFileModel(logcat_path)
    report_tuples: List[Tuple[InstrumentationReport, AccessPath, str]] = log.scan_log_for_instrumentation_report_tuples()

    observation_parser = ExecutionObservation()
    for da_result in report_tuples:
        observation_parser.parse_instrumentation_result(da_result)
    observations: List[InvocationRegisterContext]
    observations, string_sets = observation_parser.get_tainting_invocation_contexts(with_observed_strings=True)

    harness_observation.set_observations(observations)
    harness_observation.set_observed_strings(string_sets)

    class_names = map(lambda f: f.class_name, itertools.chain(*decoded_apk_model.smali_directories))
    code_insertions_lists = decoded_apk_model.get_code_insertions_for_files([harness_observation])
    report = f"total code insertions: {sum(map(len, code_insertions_lists))}\n"
    count_code_insertions = 0
    for class_name, code_insertion_list in zip(class_names, code_insertions_lists):
        for code_insertion in code_insertion_list:
            count_code_insertions += 1
            report += f"at class: {class_name}, line index: {code_insertion.line_number}, code inserted: {code_insertion.code_to_insert}\n"

    report = f"total code insertions: {count_code_insertions}\n" + report

    # print all the instrumentation locations
    # by hand, compare the two, compare instr locations with decompiled apks from previous experiment
    return report

report_instrumentation_locations_batch = process_as_dataframe(report_instrumentation_locations_single, [True, True, False], [])


def get_readonly_decoded_apk_models(benchmark_name: BenchmarkName, input_df, output_col):
    # Places path to decoded apk on output_col
    # apks are not decoded if they are already decoded; clients should treat them as readonly

    decoded_apks_directory_path = os.path.join("data", "readonly-decoded-apks", benchmark_name.value )
    os.makedirs(decoded_apks_directory_path, exist_ok=True)

    decoded_apk_path_col = output_col
    input_df[decoded_apk_path_col] = input_df["Input Model"].apply(lambda model: hybrid_config.decoded_apk_path(decoded_apks_directory_path, model.apk()))

    not_already_decoded_mask = ~input_df[decoded_apk_path_col].apply(lambda path: os.path.exists(path))
    if not_already_decoded_mask.any():
        # decode.decode_apk(decoded_apks_directory_path, apk, clean=True)
        batch_decode = process_as_dataframe(decode.decode_apk, [False, True], [False])

        # paths generated as    
        # decoded_apk_path = hybrid_config.decoded_apk_path(decoded_apks_directory_path, apk)
        input_df["Apk Model"] = input_df["Input Model"].apply(lambda model: model.apk())
        batch_decode(decoded_apks_directory_path, "Apk Model", clean=False, input_df=input_df[not_already_decoded_mask], output_col="")
        input_df.drop(columns=["Apk Model"], inplace=True)


    # Get DecodedApkModels for result
    def _error_wrapper(model: InputModel):
        decoded_apk_root_path = hybrid_config.decoded_apk_path(decoded_apks_directory_path, model.apk())
        if not os.path.exists(decoded_apk_root_path):
            raise ExperimentStepException(f"Readonly decoded apk not found at {decoded_apk_root_path}")
        
        return DecodedApkModel(decoded_apk_root_path)
        
    return process_as_dataframe(_error_wrapper, [True], [])("Input Model", input_df=input_df, output_col=output_col)


save_to_file_batch = process_as_dataframe(save_to_file, [True, True], [])

class AnalysisConstraints(Enum):
    DEPTH_0_DA_RESULTS_ONLY = enum.auto() # imitate context sensitive ConDySTA
    DISABLE_FIELD_SENSITIVITY = enum.auto() # Base objects should be tainted. Expected to have more FP than enabled field sensitivity
    FULL_CONTEXT_AND_FIELD_SENSITIVITY = enum.auto()  


def harness_observations_from_constraints(constraints: AnalysisConstraints) -> HarnessObservations:
    match constraints:
        case AnalysisConstraints.DEPTH_0_DA_RESULTS_ONLY:
            return HarnessObservations(filter_to_length1_access_paths=True)
        case AnalysisConstraints.DISABLE_FIELD_SENSITIVITY:
            return HarnessObservations(disable_field_sensitivity=True)
        case AnalysisConstraints.FULL_CONTEXT_AND_FIELD_SENSITIVITY:
            return HarnessObservations()
        
def lookup_AnalysisConstraints(path: str) -> AnalysisConstraints:
    if "DEPTH_0_DA_RESULTS_ONLY" in path:
        return AnalysisConstraints.DEPTH_0_DA_RESULTS_ONLY
    elif "DISABLE_FIELD_SENSITIVITY" in path:
        return AnalysisConstraints.DISABLE_FIELD_SENSITIVITY
    elif "FULL_CONTEXT_AND_FIELD_SENSITIVITY" in path:
        return AnalysisConstraints.FULL_CONTEXT_AND_FIELD_SENSITIVITY
    else:
        raise NotImplementedError(f"Unknown analysis constraints: {path}")


def report_instrumentation_location_details_all():
    # we want instr details for the 9 settings.
    for benchmark_name, specifier in [
        (BenchmarkName.GPBENCH, DynamicResultsSpecifier.GPBENCH),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_SHALLOW),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_INTERCEPT)
        ]:
        for constraints in AnalysisConstraints:

            df_file_paths = get_wild_benchmarks(benchmark_name)[0]
            df = LoadBenchmark(df_file_paths).execute()

            harness_observations = harness_observations_from_constraints(constraints)
            da_results_directory = get_da_results_directory(benchmark_name, specifier)            

            report_details_directory = os.path.join("data", "experiments", "sep24-da-observations-reports", f"{benchmark_name.value}_{specifier.value}_{constraints.name}_instrumentation-location-details")
            if not os.path.exists(report_details_directory):
                os.makedirs(report_details_directory)
            report_instrumentation_location_details(df, benchmark_name, harness_observations, da_results_directory, report_details_directory)
            # report_instrumentation_locations_single(logcat_path: str, decoded_apk_root_path: str, harness_observation: HarnessObservations)

def report_instrumentation_location_details(df, benchmark_name, harness_observations, da_results_directory, report_details_directory):

    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    get_readonly_decoded_apk_models(benchmark_name, df, "decoded_apk_path")

    report_instrumentation_locations_batch("logcat_file", "decoded_apk_path", harness_observations, input_df=df, output_col="instrumentation-location-report")

    df["instrumentation-location-report-path"] = df["Input Model Identifier"] + "-instrumentation-location-report.txt"
    df["instrumentation-location-report-path"] = df["instrumentation-location-report-path"].apply(lambda path: os.path.join(report_details_directory, path))

    save_to_file_batch("instrumentation-location-report-path", "instrumentation-location-report", input_df=df, output_col="")


    

def report_observation_details():
    # we want observation details from the 3 experiments

    base_observation_details_report_directory = os.path.join("data", "experiments", "sep24-da-observations-reports")
    

    for benchmark_name, specifier in [
    (BenchmarkName.GPBENCH, DynamicResultsSpecifier.GPBENCH),
    (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_SHALLOW),
    (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_INTERCEPT)
        ]:

        observation_details_report_directory = os.path.join(base_observation_details_report_directory ,f"{benchmark_name.value}-{specifier.value}-observation-details")
        if not os.path.exists(observation_details_report_directory):
            os.makedirs(observation_details_report_directory)

        df_file_paths = get_wild_benchmarks(benchmark_name)[0]
        df = LoadBenchmark(df_file_paths).execute()

        da_results_directory = get_da_results_directory(benchmark_name, specifier)
        df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
        common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")
        

        report_observation_details_batch("logcat_file", input_df=df, output_col="observation-details-report")

        df["observation-details-report-path"] = df["Input Model Identifier"] + "-observation-details-report.txt"
        df["observation-details-report-path"] = df["observation-details-report-path"].apply(lambda path: os.path.join(observation_details_report_directory, path))


        save_to_file_batch("observation-details-report-path", "observation-details-report", input_df=df, output_col="")