import os
import re
from typing import List, Union, Dict

from hybrid.hybrid_config import HybridAnalysisConfig, flowdroid_first_pass_logs_path, flowdroid_second_pass_logs_path
from util.input import ApkModel, InputModel, BatchInputModel

from util.logger import get_logger
logger = get_logger("hybrid", "results")


def print_results_to_terminal(hybrid_config: HybridAnalysisConfig):
    results_dict = hybrid_config.results_dict
    for key in results_dict.keys():
        result_model: HybridAnalysisResult = results_dict[key]
        print(result_model.as_csv_row())


def print_csv_results_to_file(hybrid_config: HybridAnalysisConfig, outfile_path : str):
    # Todo: include today's date in the outfile name

    with open(outfile_path, 'w') as file:

        results_dict = hybrid_config.results_dict
        file.write(HybridAnalysisResult.csv_label_row())
        for result in results_dict.values():
            file.write(result.as_csv_row())
            file.write("\n")


class HybridAnalysisResult:
    """
    Each instance of HybridAnalysisResult should represent 1 line in a results spreadsheet.
    """
    input_model: InputModel

    # Start Spreadsheet Entries
    # input_name: str
    # input_details: str
    # monkey_on: bool
    first_pass_leaks: Union[int, None]
    number_added_sources: Union[int, None]
    second_pass_leaks: Union[int, None]
    # # time_to_run
    # # kloc_smali
    error_msg: str
    # End Spreadsheet Entries

    grouped_apk_first_pass_leaks: Union[Dict[str, int], None]
    grouped_apk_number_added_sources: Union[Dict[str, int], None]
    grouped_apk_second_pass_leaks: Union[Dict[str, int], None]
    grouped_apk_error_msg: Union[Dict[str, str], None]

    def __init__(self, input_model: InputModel):
        self.input_model = input_model

        self.first_pass_leaks = None
        self.number_added_sources = None
        self.second_pass_leaks = None
        self.error_msg = ""

        self.grouped_apk_first_pass_leaks = None
        self.grouped_apk_number_added_sources = None
        self.grouped_apk_second_pass_leaks = None
        self.grouped_apk_error_msg = None

        if input_model.is_group():
            self.grouped_apk_first_pass_leaks = dict()
            self.grouped_apk_number_added_sources = dict()
            self.grouped_apk_second_pass_leaks = dict()
            self.grouped_apk_error_msg = dict()

    @classmethod
    def csv_label_row(cls) -> str:
        """
        Return the label row of a csv generated from HybridAnalysisResults
        """
        return ",".join([
            "Input ID #"
            "Apk Name(s) — Multiple names are separated with a semicolon",
            "Apk Path(s)",
            "Num Flowdroid Leaks",
            "Num Discovered Sources",
            "Num Flowdroid Leaks with Augmented Sources/Sinks",
            "Error Msg(s)",
            "Flowdroid Leaks per Apk (Separated by semicolons)",
            "Discovered Sources per Apk",
            "Augmented Flowdroid Leaks per Apk",
            "Error Msg(s) by Apk"
        ])

    def as_csv_row(self) -> str:
        """
        Representation of this object as a row in a csv
        """

        if not self.input_model.is_group():
            return ",".join([
                self.input_model.input_id,
                self.input_model.apk().apk_name,
                self.input_model.apk().apk_path,
                str(self.first_pass_leaks) if self.first_pass_leaks is not None else "",
                str(self.number_added_sources) if self.number_added_sources is not None else "",
                str(self.second_pass_leaks) if self.second_pass_leaks is not None else "",
                self.error_msg,
                "",
                "",
                "",
                "",
            ])
        else:
            group_first_pass_leaks = []
            group_number_added_sources = []
            group_second_pass_leaks = []
            group_error_msgs = []

            for apk_idx, _ in self.input_model.apks():
                if self.input_model.input_identifier(apk_idx) in self.grouped_apk_first_pass_leaks.keys():
                     group_first_pass_leaks.append(str(self.grouped_apk_first_pass_leaks[self.input_model.input_identifier(apk_idx)]))
                if self.input_model.input_identifier(apk_idx) in self.grouped_apk_number_added_sources.keys():
                     group_number_added_sources.append(str(self.grouped_apk_number_added_sources[self.input_model.input_identifier(apk_idx)]))
                if self.input_model.input_identifier(apk_idx) in self.grouped_apk_second_pass_leaks.keys():
                     group_second_pass_leaks.append(str(self.grouped_apk_second_pass_leaks[self.input_model.input_identifier(apk_idx)]))
                if self.input_model.input_identifier(apk_idx) in self.grouped_apk_error_msg.keys():
                     group_error_msgs.append(str(self.grouped_apk_error_msg[self.input_model.input_identifier(apk_idx)]))

            return ",".join([
                self.input_model.input_id,
                ";".join(map(lambda _, apk_model: apk_model.apk_name, self.input_model.apks())),
                ";".join(map(lambda _, apk_model: apk_model.apk_path, self.input_model.apks())),
                str(self.first_pass_leaks) if self.first_pass_leaks is not None else "",
                str(self.number_added_sources) if self.number_added_sources is not None else "",
                str(self.second_pass_leaks) if self.second_pass_leaks is not None else "",
                self.error_msg,
                ";".join(group_first_pass_leaks),
                ";".join(group_number_added_sources),
                ";".join(group_second_pass_leaks),
                ";".join(group_error_msgs),
            ])

    @classmethod
    def experiment_start(cls, hybrid_config: HybridAnalysisConfig):
        hybrid_config.results_dict = dict()

        # Initialize result model objects in dictionary
        for input_model in hybrid_config.input_apks.all_input_models():
            hybrid_config.results_dict[input_model.input_identifier()] = HybridAnalysisResult(input_model)

    @classmethod
    def report_new_sources_count(cls, hybrid_config: HybridAnalysisConfig, new_sources_count: int, input_model: InputModel, grouped_apk_idx: int=-1):
        if not input_model.is_group():
            hybrid_config.results_dict[input_model.input_identifier()].number_added_sources = new_sources_count
        else:
            # number_added_sources can be incremented by different members of group
            result_instance: 'HybridAnalysisResult' = hybrid_config.results_dict[input_model.input_identifier()]
            if result_instance.number_added_sources is None:
                result_instance.number_added_sources = 0
            result_instance.number_added_sources += new_sources_count

            result_instance.grouped_apk_number_added_sources[input_model.input_identifier(grouped_apk_idx)] = new_sources_count



    @classmethod
    def experiment_end(cls, hybrid_config: HybridAnalysisConfig):
        cls._parse_leak_counts(hybrid_config, hybrid_config.input_apks)

    @classmethod
    def _parse_leak_counts(cls, hybrid_config: HybridAnalysisConfig, input_apks: BatchInputModel) -> None:
        # TODO: this method should get called at the tail end of all flowdroid invocations, then the flowdroid
        #  invocation should just return the result info (# of leaks or a result object of some kind)

        # Go through logs from flowdroid's first and second passes, and add the leak results
        # to the results dictionary.
        # results_dict should already be filled out with result models that will be mutated.

        results_dict = hybrid_config.results_dict

        for ungrouped_input in input_apks.ungrouped_inputs:
            try:
                first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_first_pass_logs_path(hybrid_config, ungrouped_input))

                results_dict[ungrouped_input.input_identifier()].first_pass_leaks = first_pass_leaks_count
            except FlowdroidLogException as e:
                results_dict[ungrouped_input.input_identifier()].error_msg += str(e)

            try:
                second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_second_pass_logs_path(hybrid_config, ungrouped_input))

                results_dict[ungrouped_input.input_identifier()].second_pass_leaks = second_pass_leaks_count
            except FlowdroidLogException as e:
                results_dict[ungrouped_input.input_identifier()].error_msg += str(e)

        for grouped_input in input_apks.grouped_inputs:
            result_instance: HybridAnalysisResult = results_dict[grouped_input.input_identifier()]

            for grouped_apk_index, _ in grouped_input.apks():
                try:
                    first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        flowdroid_first_pass_logs_path(hybrid_config, grouped_input,
                                                       grouped_apk_index))

                    if result_instance.first_pass_leaks is None:
                        result_instance.first_pass_leaks = 0
                    result_instance.first_pass_leaks += first_pass_leaks_count
                    result_instance.grouped_apk_first_pass_leaks[grouped_input.input_identifier(grouped_apk_index)] = first_pass_leaks_count

                except FlowdroidLogException as e:
                    if grouped_input.input_identifier(grouped_apk_index) not in result_instance.grouped_apk_error_msg.keys():
                        result_instance.grouped_apk_error_msg[grouped_input.input_identifier(grouped_apk_index)] = ""
                    result_instance.grouped_apk_error_msg[grouped_input.input_identifier(grouped_apk_index)] += e.msg

                try:
                    second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        flowdroid_second_pass_logs_path(hybrid_config, grouped_input, grouped_apk_index))

                    if result_instance.second_pass_leaks is None:
                        result_instance.second_pass_leaks = 0
                    result_instance.second_pass_leaks += second_pass_leaks_count
                    result_instance.grouped_apk_second_pass_leaks[grouped_input.input_identifier(grouped_apk_index)] = second_pass_leaks_count

                except FlowdroidLogException as e:
                    if grouped_input.input_identifier(grouped_apk_index) not in result_instance.grouped_apk_error_msg.keys():
                        result_instance.grouped_apk_error_msg[grouped_input.input_identifier(grouped_apk_index)] = ""
                    result_instance.grouped_apk_error_msg[grouped_input.input_identifier(grouped_apk_index)] += e.msg

            # Note in error_msg field if any apks in a group had an error
            if len(result_instance.grouped_apk_error_msg.values()) > 0:
                result_instance.error_msg += "Apks in group had errors."


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

    # TODO: set this to the droidbench directory. Should probably figure out a better testing infrastructure in general
    # hybrid_analysis_configuration.input_apks_path = ""
    hybrid_analysis_configuration.is_recursive_on_input_apks_path = True

    HybridAnalysisResult.experiment_start(hybrid_analysis_configuration)

    # There are 118 apks in this Droidbench directory
    assert len(hybrid_analysis_configuration.results_dict) == 118

class FlowdroidLogException(Exception):
    msg: str
    def __init__(self, msg):
        self.msg = msg

if __name__ == '__main__':
    test_initialize_results_dict_entries_works_recursively()
