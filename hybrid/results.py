import os
import re
from typing import List, Union, Dict

from hybrid.hybrid_config import HybridAnalysisConfig, flowdroid_first_pass_logs_path, flowdroid_second_pass_logs_path
from util.input import InputApkModel, InputApkGroup, InputApksModel

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

        results_dict = hybrid_config.results_dict
        file.write(HybridAnalysisResult.label_row())
        for result in results_dict.values():
            file.write(result.as_row())
            file.write("\n")


class HybridAnalysisResult:
    """
    Each instance of HybridAnalysisResult should represent 1 line in a results spreadsheet.
    """
    # TODO: I still hate this data structure. Need to figure out a nicer framework/structure/interface.
    # Start Spreadsheet Entries
    # input_name: str
    # input_details: str
    # monkey_on: bool
    flowdroid_leaks: Union[int, None]
    # flowdroid_leaks_details: str
    number_added_sources: Union[int, None]
    # number_added_sources_details: str
    dysta_leaks: Union[int, None]
    # dysta_leaks_details: str
    # # time_to_run
    # # kloc_smali
    error_msg: Union[str, None]
    # End Spreadsheet Entries

    apk_model: Union[InputApkModel, None]

    apk_group: Union[InputApkGroup, None]
    group_apk_name_index: Union[Dict[str, int], None]
    group_flowdroid_leaks: Union[List[Union[int, None]], None]
    group_number_added_sources: Union[List[Union[int, None]], None]
    group_dysta_leaks: Union[List[Union[int, None]], None]
    group_error_msg: Union[List[str], None]

    def __init__(self):
        # self.apk_name = ""
        # self.number_added_sources = None
        # self.flowdroid_leaks = None
        # self.dysta_leaks = None
        # self.error_msg = ""
        self.apk_model = None
        self.flowdroid_leaks = None
        self.number_added_sources = None
        self.dysta_leaks = None
        self.error_msg = None

        self.apk_group = None
        self.group_apk_name_index = None
        self.group_flowdroid_leaks = None
        self.group_number_added_sources = None
        self.group_dysta_leaks = None
        self.group_error_msg = None

    @classmethod
    def _result_from_apk(cls, apk: InputApkModel) -> 'HybridAnalysisResult':
        new_result = HybridAnalysisResult()

        new_result.apk_model = apk
        new_result.error_msg = ""

        return new_result

    @classmethod
    def _result_from_group(cls, apk_group: InputApkGroup) -> 'HybridAnalysisResult':
        new_result = HybridAnalysisResult()

        new_result.apk_group = apk_group

        new_result.group_apk_name_index = {apk.apk_name:i for i, apk in enumerate(apk_group.apks)}
        apk_count = len(apk_group.apks)
        new_result.group_flowdroid_leaks = [None] * apk_count
        new_result.group_number_added_sources = [None] * apk_count
        new_result.group_dysta_leaks = [None] * apk_count
        new_result.group_error_msg = [""] * apk_count

        return new_result
    @classmethod
    def label_row(cls) -> str:
        """
        Return the label row of a csv generated from HybridAnalysisResults
        """
        return ",".join([
            "Apk Name(s) — Multiple names are separated with a semicolon",
            "Apk Path(s)",
            # "Monkey On",
            "Num Flowdroid Leaks",
            "Flowdroid Leaks Details",
            "Num Discovered Sources",
            "Discovered Sources Details",
            "Num Flowdroid Leaks with Augmented Sources/Sinks",
            "Augmented Flowdroid Leaks Details",
            "Error Msg(s)"
        ])

    def as_row(self) -> str:
        """
        Representation of this object as a row in a csv
        """
        if self.apk_model is None and self.apk_group is None:
            raise AssertionError("Both apk_model and apk_group can't be None")

        if self.apk_model is not None and self.apk_group is not None:
            raise AssertionError("Both apk_model and apk_group can't be filled out")

        if self.apk_model is not None:
            return ",".join([
                self.apk_model.apk_name,
                self.apk_model.apk_path,
                str(self.flowdroid_leaks) if self.flowdroid_leaks is not None else "",
                "",
                str(self.number_added_sources) if self.number_added_sources is not None else "",
                "",
                str(self.dysta_leaks) if self.dysta_leaks is not None else "",
                "",
                self.error_msg
            ])
        else:
            return ",".join([
                ";".join([apk.apk_name for apk in self.apk_group.apks]),
                ";".join([apk.apk_path for apk in self.apk_group.apks]),
                str(sum([i if i is not None else 0 for i in self.group_flowdroid_leaks])), # Add up all the leaks
                ";".join([str(i) for i in self.group_flowdroid_leaks]),
                str(sum([i if i is not None else 0 for i in self.group_number_added_sources])),  # Add up all the discovered sources
                ";".join([str(i) for i in self.group_number_added_sources]),
                str(sum([i if i is not None else 0 for i in self.group_dysta_leaks])),  # Add up all the discovered sources
                ";".join([str(i) for i in self.group_dysta_leaks]),
                ";".join(self.group_error_msg)
            ])

    @classmethod
    def _input_key(cls, apk_name: str, group_id: int=-1) -> str:
        if group_id == -1:
            return apk_name
        else:
            return str(group_id)

    @classmethod
    def experiment_start(cls, hybrid_config: HybridAnalysisConfig):
        hybrid_config.results_dict = dict()

        # Initialize result model objects in dictionary

        ungrouped_apks: List[InputApkModel] = hybrid_config.input_apks.ungrouped_apks
        for input_apk in ungrouped_apks:
            hybrid_config.results_dict[cls._input_key(input_apk.apk_name, -1)] = cls._result_from_apk(input_apk)

        apk_groups: List[InputApkGroup] = hybrid_config.input_apks.input_apk_groups
        for apk_group in apk_groups:
            hybrid_config.results_dict[cls._input_key("", apk_group.group_id)] = cls._result_from_group(apk_group)

    @classmethod
    def report_new_sources_count(cls, hybrid_config, apk_name, new_sources_count, group_id=-1):
        if group_id == -1:
            hybrid_config.results_dict[cls._input_key(apk_name, -1)].number_added_sources = new_sources_count
        else:
            result_instance: 'HybridAnalysisResult' = hybrid_config.results_dict[cls._input_key(apk_name, group_id)]
            result_instance.group_number_added_sources[result_instance.group_apk_name_index[apk_name]] = new_sources_count

    @classmethod
    def experiment_end(cls, hybrid_config: HybridAnalysisConfig):
        cls._parse_leak_counts(hybrid_config, hybrid_config.input_apks)

    @classmethod
    def _parse_leak_counts(cls, hybrid_config: HybridAnalysisConfig, input_apks: InputApksModel) -> None:
        # TODO: this method should get called at the tail end of all flowdroid invocations, then the flowdroid
        #  invocation should just return the result info (# of leaks or a result object of some kind)

        # Go through logs from flowdroid's first and second passes, and add the leak results
        # to the results dictionary.
        # results_dict should already be filled out with result models that will be mutated.

        results_dict = hybrid_config.results_dict

        for ungrouped_apk in input_apks.ungrouped_apks:
            try:
                first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_first_pass_logs_path(hybrid_config, ungrouped_apk))

                results_dict[cls._input_key(ungrouped_apk.apk_name, -1)].flowdroid_leaks = first_pass_leaks_count
            except FlowdroidLogException as e:
                results_dict[cls._input_key(ungrouped_apk.apk_name, -1)].error_msg += str(e)

            try:
                second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_second_pass_logs_path(hybrid_config, ungrouped_apk))

                results_dict[cls._input_key(ungrouped_apk.apk_name, -1)].dysta_leaks = \
                    second_pass_leaks_count
            except FlowdroidLogException as e:
                results_dict[
                    cls._input_key(ungrouped_apk.apk_name, -1)].error_msg += str(e)

        for apk_group in input_apks.input_apk_groups:
            for grouped_apk in apk_group.apks:
                try:
                    first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        flowdroid_first_pass_logs_path(hybrid_config, grouped_apk,
                                                       apk_group.group_id))

                    result_instance: HybridAnalysisResult = results_dict[cls._input_key(grouped_apk.apk_name, apk_group.group_id)]
                    result_instance.group_flowdroid_leaks[
                        result_instance.group_apk_name_index[grouped_apk.apk_name]] =first_pass_leaks_count

                except FlowdroidLogException as e:
                    result_instance: HybridAnalysisResult = results_dict[
                        cls._input_key(grouped_apk.apk_name,
                                       apk_group.group_id)]
                    result_instance.group_error_msg[
                        result_instance.group_apk_name_index[grouped_apk.apk_name]] =\
                        e.msg

                try:
                    second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(
                        flowdroid_second_pass_logs_path(hybrid_config, grouped_apk,
                                                       apk_group.group_id))

                    result_instance: HybridAnalysisResult = results_dict[
                        cls._input_key(grouped_apk.apk_name, apk_group.group_id)]
                    result_instance.group_dysta_leaks[
                        result_instance.group_apk_name_index[
                            grouped_apk.apk_name]] = second_pass_leaks_count

                except FlowdroidLogException as e:
                    result_instance: HybridAnalysisResult = results_dict[
                        cls._input_key(grouped_apk.apk_name,
                                       apk_group.group_id)]
                    result_instance.group_error_msg[
                        result_instance.group_apk_name_index[grouped_apk.apk_name]] = \
                        e.msg

        # Files in these directories should have path names matching hybrid_config.flowdroid_first_pass_logs_path()
        #   or hybrid_config.flowdroid_second_pass_logs_path()
        # That is, file names will be of the form [apk_name].log or group[id]_[apk_name].log
        # for item in os.listdir(hybrid_config.flowdroid_first_pass_logs_path):
        #     if item.endswith(".log"):
        #
        #         if item.startswith("group"):
        #             regex_result = re.search(r"group(\d+)_(.+).log", item)
        #             group_id = regex_result.group(1)
        #             apk_name = regex_result.group(2)
        #         else:
        #             regex_result = re.search(r"(.+).log", item)
        #             group_id = -1 # ungrouped
        #             apk_name = regex_result.group(1)
        #
        #         try:
        #             first_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_first_pass_logs_path(hybrid_config, apk_name, group_id))
        #             if group_id == -1:
        #                 results_dict[apk_name].flowdroid_leaks = first_pass_leaks_count
        #             else:
        #                 result: HybridAnalysisResult = results_dict[cls._input_key(apk_name, group_id)]
        #                 result.group_flowdroid_leaks[result.group_apk_name_index[apk_name]] = first_pass_leaks_count
        #         except FlowdroidLogException as e:
        #             if group_id == -1:
        #                 results_dict[apk_name].error_msg += str(e)
        #             else:
        #                 result_entry: HybridAnalysisResult = results_dict[cls._input_key(apk_name, group_id)]
        #                 result_entry.group_error_msg[result_entry.group_apk_name_index[apk_name]] = str(e)
        #
        #         try:
        #             second_pass_leaks_count = cls._count_leaks_in_flowdroid_log(flowdroid_second_pass_logs_path(hybrid_config, apk_name, group_id))
        #             if group_id == -1:
        #                 results_dict[apk_name].dysta_leaks = second_pass_leaks_count
        #             else:
        #                 result: HybridAnalysisResult = results_dict[cls._input_key(apk_name, group_id)]
        #                 result.group_dysta_leaks[result.group_apk_name_index[apk_name]] = second_pass_leaks_count
        #         except FlowdroidLogException as e:
        #             if group_id == -1:
        #                 results_dict[apk_name].error_msg += str(e)
        #             else:
        #                 result_entry: HybridAnalysisResult = results_dict[cls._input_key(apk_name, group_id)]
        #                 result_entry.group_error_msg[result_entry.group_apk_name_index[apk_name]] += str(e)


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
