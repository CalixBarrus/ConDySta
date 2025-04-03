
# report on observations to show how the count of instrumented sources should
# Count DA reports; count observations after processing; Breakdown of Access Path lvl (0 and 1), Count Observations When Combined by Disabling Field Sensitivity

from typing import List, Tuple

from hybrid.access_path import AccessPath
from hybrid.dynamic import ExecutionObservation
from intercept import instrumentation_report

import util.logger
logger = util.logger.get_logger(__name__)

def report_observations_profile(reports: List[Tuple[instrumentation_report, AccessPath, str]], observations) -> Tuple[int, int, int, int, int]:

    # da_results: List[Tuple] = log.scan_log_for_instrumentation_report_tuples()

    observation = ExecutionObservation()
    for da_result in reports:
        observation.parse_instrumentation_result(da_result)
    observations, _ = observation.get_tainting_invocation_contexts(with_observed_strings=True)

    count_reports = len(reports)


