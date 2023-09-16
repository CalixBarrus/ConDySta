import os
import re

from hybrid.hybrid_config import HybridAnalysisConfig

from util.logger import get_logger
logger = get_logger("hybrid", "results")


def print_results_to_terminal(hybrid_config: HybridAnalysisConfig):
    results_dict = hybrid_config.results_dict
    for key in results_dict.keys():
        result_model: HybridAnalysisResult = results_dict[key]
        print(f"APK Name: {result_model.apk_name}, Flowdroid Leaks: "
              f"{result_model.flowdroid_leaks}, Sources "
              f"added: {result_model.number_added_sources}, DySTa Leaks: "
              f"{result_model.dysta_leaks}")


def print_csv_results_to_file(hybrid_config: HybridAnalysisConfig, outfile_path : str):
    # Todo: include today's date in the outfile name

    with open(outfile_path, 'w') as file:

        col_headers = ["APK Name", "Flowdroid Leaks", "Sources Added", "DySTa Leaks",
                       "Error Message"]
        file.write(",".join(col_headers) + "\n")

        results_dict = hybrid_config.results_dict
        for result in results_dict.values():
            file.write(",".join([result.apk_name,
                                 str(result.flowdroid_leaks if
                                     result.flowdroid_leaks is not None else ""),
                                 str(result.number_added_sources if
                                     result.number_added_sources is not None else ""),
                                 str(result.dysta_leaks if
                                     result.dysta_leaks is not None else ""),
                                 str(result.error_msg),
                                 ]) + "\n")


class HybridAnalysisResult:
    apk_name: str
    number_added_sources: int
    flowdroid_leaks: int
    dysta_leaks: int
    error_msg: str

    def __init__(self, apk_name):
        self.apk_name = apk_name
        self.number_added_sources = None
        self.flowdroid_leaks = None
        self.dysta_leaks = None
        self.error_msg = ""

    @classmethod
    def experiment_start(cls, hybrid_config: HybridAnalysisConfig):
        hybrid_config.results_dict = dict()

        # Initialize result model objects in dictionary
        for input_apk in hybrid_config.intercept_config.input_apks:
            hybrid_config.results_dict[input_apk.apk_name] = HybridAnalysisResult(
                input_apk.apk_name)


    @classmethod
    def report_new_sources_count(cls, hybrid_config, apk_name, new_sources_count):
        hybrid_config.results_dict[apk_name].number_added_sources = new_sources_count

    @classmethod
    def experiment_end(cls, hybrid_config: HybridAnalysisConfig):
        cls._parse_leak_counts(hybrid_config)

    @classmethod
    def _parse_leak_counts(cls, hybrid_config: HybridAnalysisConfig) -> None:
        # Go through logs from flowdroid's first and second passes, and add the leak results
        # to the results dictionary.
        # results_dict should already be filled out with result models that will be mutated.

        flowdroid_first_pass_logs_path = hybrid_config.flowdroid_first_pass_logs_path
        flowdroid_second_pass_logs_path = hybrid_config.flowdroid_second_pass_logs_path
        results_dict = hybrid_config.results_dict

        # Assume files in these two directories all have names that match up
        for item in os.listdir(flowdroid_first_pass_logs_path):
            if item.endswith(".log"):
                # Pull ".log" off of "[apk_name].log"
                apk_name = item.split(".")[:-1]
                apk_name = ".".join(apk_name)

                first_pass_log_path = os.path.join(flowdroid_first_pass_logs_path,
                                                   item)
                try:
                    first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        first_pass_log_path)
                    results_dict[apk_name].flowdroid_leaks = first_pass_leaks_count
                except FlowdroidLogException as e:
                    results_dict[apk_name].error_msg = str(e)

                second_pass_log_path = os.path.join(flowdroid_second_pass_logs_path,
                                                    item)
                try:
                    second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        second_pass_log_path)
                    results_dict[apk_name].dysta_leaks = second_pass_leaks_count
                except FlowdroidLogException as e:
                    results_dict[apk_name].error_msg = str(e)

    @classmethod
    def _count_leaks_in_flowdroid_log(cls, flowdroid_log_path: str) -> int:
        if not os.path.isfile(flowdroid_log_path):
            logger.error(f"Flowdroid did not execute; log file"
                         f" {flowdroid_log_path} does not exist.")
            raise FlowdroidLogException(f"Flowdroid did not execute; log file"
                         f" {flowdroid_log_path} does not exist.")

        with open(flowdroid_log_path, 'r') as file:
            for line in file.readlines():

                # looking for lines such as
                """
    [main] INFO soot.jimple.infoflow.android.SetupApplication - Found 1 leaks
                """
                if " - Found " in line:
                    # Pull number from phrase "Found n leaks"
                    num_leaks = int(re.search("Found (\d+) leaks", line).group(1))
                    return num_leaks

        logger.error(f"Flowdroid did not execute as expected in log file"
               f" {flowdroid_log_path}")
        return None


    @classmethod
    def report_error(cls, hybrid_config, apk_name, error_msg):
        hybrid_config.results_dict[apk_name].error_msg = error_msg


def test_initialize_results_dict_entries_works_recursively():
    from intercept import intercept_config
    intercept_configuration = intercept_config.get_default_intercept_config()
    from hybrid.hybrid_config import get_default_hybrid_analysis_config
    hybrid_analysis_configuration = get_default_hybrid_analysis_config(
        intercept_configuration)

    hybrid_analysis_configuration.input_apks_path = "/Users/calix/Documents/programming/research-programming/DroidBench/apk"
    hybrid_analysis_configuration.is_recursive_on_input_apks_path = True

    HybridAnalysisResult.experiment_start(hybrid_analysis_configuration)

    # There are 118 apks in this Droidbench directory
    assert len(hybrid_analysis_configuration.results_dict) == 118

class FlowdroidLogException(Exception):
    pass

if __name__ == '__main__':
    test_initialize_results_dict_entries_works_recursively()
