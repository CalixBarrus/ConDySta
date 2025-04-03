
# report on observations to show how the count of instrumented sources should
# Count DA reports; count observations after processing; Breakdown of Access Path lvl (0 and 1), Count Observations When Combined by Disabling Field Sensitivity

from enum import Enum
import enum
import os
from typing import List, Tuple

import pandas as pd

from experiment import common
from experiment.batch import process_as_dataframe
from experiment.benchmark_name import BenchmarkName
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from hybrid.access_path import AccessPath
from hybrid.dynamic import ExecutionObservation, LogcatLogFileModel


from hybrid.invocation_register_context import InvocationRegisterContext
from intercept.instrument import HarnessObservations
from intercept.instrumentation_report import InstrumentationReport
from tests.experiment.test_experiments_2_10_25 import harness_observations
from util.input import InputModel
import util.logger
logger = util.logger.get_logger(__name__)



def report_observations_profile(logcat_path: str) -> Tuple[int, int, int, int, int]:

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

report_observations_profile_batch = process_as_dataframe(report_observations_profile, [True], [])

class DynamicResultsSpecifier(Enum):
    GPBENCH = ""
    FOSSDROID_SHALLOW = "shallow"
    FOSSDROID_INTERCEPT = "intercept"

def get_da_results_directory(benchmark_name: BenchmarkName, specifier: DynamicResultsSpecifier) -> str:
    match benchmark_name:
        case BenchmarkName.FOSSDROID:
            if specifier == DynamicResultsSpecifier.FOSSDROID_SHALLOW:
                return "data/OneDrive_1_2-7-2025/2024-10-26-execution-full-fossdroid-extendedStrList-60s/logcat-output"
            elif specifier == DynamicResultsSpecifier.FOSSDROID_INTERCEPT:
                return "data/OneDrive_1_2-7-2025/2024-10-28-execution-full-fossdroid-intercept-replace-60s/logcat-output"

        case BenchmarkName.GPBENCH:
            return "data/OneDrive_1_2-7-2025/initial-results-for-xiaoyin/2024-10-21-execution-full-gpbench-manual/logcat-output"
        
    raise ValueError()


def report_observations_profile_feb_experiments_all():
    for benchmark_name, specifier in [
        (BenchmarkName.GPBENCH, DynamicResultsSpecifier.GPBENCH),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_SHALLOW),
        (BenchmarkName.FOSSDROID, DynamicResultsSpecifier.FOSSDROID_INTERCEPT)
    ]:
        report_observations_profile_sep24_experiments(benchmark_name, specifier)

def report_observations_profile_sep24_experiments(benchmark_name: BenchmarkName, specifier: DynamicResultsSpecifier):

    df_file_paths = get_wild_benchmarks(benchmark_name)[0]
    df = LoadBenchmark(df_file_paths).execute()

    da_results_directory = get_da_results_directory(benchmark_name, specifier)
    df["Input Model Identifier"] = df["Input Model"].apply(lambda model: model.input_identifier())
    common.load_logcat_files_batch(da_results_directory, "Input Model Identifier", df, output_col="logcat_file")

    report_df = pd.DataFrame({"App Name": df["Input Model"].apply(lambda model: model.apk().apk_name), "logcat_file": df["logcat_file"]})

    result_cols = ["count_reports", "count_observations", "count_observations_lvl_0_ap", "count_observations_lvl_1_ap", "count_observations_field_sensitivity_reduced"]
    report_observations_profile_batch("logcat_file", input_df=df, output_col=result_cols)

    report_name = common.get_experiment_name(benchmark_name.value, "sep24-da-observations-report", (0,1,0), params=[specifier.value])
    
    reports_dir = os.path.join("data", "experiments", "sep24-da-observations-reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"{report_name}.csv")

    df["App Name"] = df["Input Model"].apply(lambda model: model.apk().apk_name)

    df[["App Name"] + result_cols].to_csv(report_path)





