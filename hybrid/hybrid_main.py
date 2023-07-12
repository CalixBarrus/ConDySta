import os
import re
import shutil
from typing import List, Optional

import util
from hybrid import results
from hybrid.clean import clean
from hybrid.flowdroid import activate_flowdroid
from hybrid.hybrid_config import HybridAnalysisConfig, get_default_hybrid_analysis_config
from hybrid.results import HybridAnalysisResult
from intercept import intercept_main
from intercept.intercept_config import get_default_intercept_config

from util import logger, input


logger = logger.get_logger('hybrid', 'hybrid_main')

def main(hybrid_config, do_clean=True):
    if do_clean:
        clean(hybrid_config)

    results.HybridAnalysisResult.experiment_start(hybrid_config)

    dysta(hybrid_config, do_clean)

    results.HybridAnalysisResult.experiment_end(hybrid_config)


def dysta(hybrid_config: HybridAnalysisConfig, do_clean):
    unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
    flowdroid_first_pass_logs_path = hybrid_config.flowdroid_first_pass_logs_path
    flowdroid_second_pass_logs_path = hybrid_config.flowdroid_second_pass_logs_path

    # dynamic pass
    # TODO: I should setup the configs so that this step is unnecessary
    hybrid_config.intercept_config.logs_path = hybrid_config.dynamic_pass_logs_path
    # TODO: Should be able to skip specific APKs if there's already a result for them.
    intercept_main.main(hybrid_config.intercept_config, do_clean=do_clean)

    input_apks: List[input.InputApkModel] = hybrid_config.intercept_config.input_apks

    for input_apk in input_apks:

        apk_name = input_apk.apk_name

        apk_path = input_apk.apk_path

        # flowdroid 1st pass
        result_log_name = activate_flowdroid(hybrid_config, apk_path, apk_name,
                                             unmodified_source_and_sink_path,
                                             flowdroid_first_pass_logs_path)

        # create new sources/sinks file
        modified_source_and_sink_directory = hybrid_config.modified_source_sink_directory

        modified_source_and_sink_path = os.path.join(
            modified_source_and_sink_directory,
            apk_name + "source-and-sinks.txt")
        dynamic_log_path = os.path.join(hybrid_config.dynamic_pass_logs_path, result_log_name)

        if not os.path.isfile(dynamic_log_path):
            results.HybridAnalysisResult.report_error(hybrid_config, apk_name,
                                                      "No record of Dynamic Run")
            continue
        new_sources_count = process_dynamic_log_to_source_file(hybrid_config,
                                                               modified_source_and_sink_path,
                                                               dynamic_log_path)
        logger.info(f"Discovered {new_sources_count} new source(s) "
                    f"from {apk_name}.")

        results.HybridAnalysisResult.report_new_sources_count(hybrid_config, apk_name,
                                                              new_sources_count)

        # flowdroid 2nd pass
        activate_flowdroid(hybrid_config,
                           apk_path, apk_name,
                           modified_source_and_sink_path,
                           flowdroid_second_pass_logs_path)


def process_dynamic_log_to_source_file(hybrid_config: HybridAnalysisConfig,
                                       modified_source_and_sink_path: str,
                                       log_path: str) -> int:
    # Place any observed sources from "logs_to_process_directory/log_to_process_name)"
    # into a new source/sink file at "modified_source_and_sink_path"
    # return the number of discovered/added sources

    unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
    target_PII = hybrid_config.target_PII

    observed_sources: set[FlowdroidSourceModel] = set(
        get_sources_from_log(log_path, target_PII))

    existing_sources: set[FlowdroidSourceModel] = set(get_sources_from_file(
        unmodified_source_and_sink_path))

    # Set minus, only append new sources not in unmodified source/sink list.
    new_sources: set[FlowdroidSourceModel] = observed_sources - existing_sources

    # Copy over the source/sink file and append the new sources
    shutil.copyfile(unmodified_source_and_sink_path, modified_source_and_sink_path)
    with open(modified_source_and_sink_path, 'a') as result_file:
        result_file.writelines(list(map(lambda s: s.get_source_string(), new_sources)))

    return len(new_sources)


# def process_dynamic_logs_to_source_file(unmodified_source_and_sink_path,
#                                         modified_source_and_sink_path,
#                                         logs_to_process_directory):
#     # lump all the observed sources from the log files into a new source/sink
#     # file.
#
#     # assume log files are not nested in additional directories; all relevant
#     # log files are just in logs_to_process_directory
#
#     mint_mobile_SIM_id = "8901240197155182897"
#     target_PII = [mint_mobile_SIM_id]
#
#     observed_sources = set()
#     for item in os.listdir(logs_to_process_directory):
#         item_path = os.path.join(logs_to_process_directory, item)
#         if os.path.isfile(item_path) and item_path.endswith(".log"):
#             sources = get_sources_from_log(item_path, target_PII)
#             observed_sources = observed_sources.union(set(sources))
#
#     existing_sources = set(get_sources_from_file(unmodified_source_and_sink_path))
#
#     new_sources = observed_sources - existing_sources
#
#     print(f"Discovered {len(new_sources)} new source(s).")
#
#     # Copy over the source/sink file and append the new sources
#     shutil.copyfile(unmodified_source_and_sink_path, modified_source_and_sink_path)
#     with open(modified_source_and_sink_path, 'a') as result_file:
#         result_file.writelines(map(lambda s: s.get_source_string(), new_sources))


def get_sources_from_log(log_path: str, target_PII: List[str]) -> List[
    "FlowdroidSourceModel"]:
    # this behavior should depend on the instrumentation being used in the
    # intercept step

    # assuming we are using the simplest instrumentation, log the value and the
    # stack trace

    log = LogcatLogFileModel(log_path)
    filtered_exceptions = log.filter_exceptions_by_header(target_PII)

    # sources_in_log = list(map(lambda e: FlowdroidSourceModel.from_exception(e),
    #                           filtered_exceptions))
    sources_in_log = list(map(lambda e: FlowdroidSourceModel.from_exception_containing_invocation(e),
                              filtered_exceptions))

    return sources_in_log


def get_sources_from_file(source_and_sink_path: str) -> List["FlowdroidSourceModel"]:
    # Open the file at the given path.
    # Iterate through each line. If a line ends with "-> _SOURCE_", it should
    # be a source.
    # Parse each source line and create a FlowdroidSourceModel object. Collect
    # all the model objects and return them in a list.

    with open(source_and_sink_path, 'r') as file:
        lines = file.readlines()
        resultSources = []
        for line in lines:
            """
Example line: 
<javax.servlet.ServletRequest: java.lang.String getParameter(java.lang.String)> -> _SOURCE_
            """
            if line.startswith('%'):
                # '%' are used as comments
                continue
            if line.strip().endswith("-> _SOURCE_"):
                resultSources.append(FlowdroidSourceModel.from_string(line))

    return resultSources


def flowdroid_on_apks(hybrid_config: HybridAnalysisConfig, input_apks: List[
    input.InputApkModel], use_individual_source_sink_file=False):

    for input_apk in input_apks:
        if use_individual_source_sink_file:
            source_and_sink_path = os.path.join(
                hybrid_config.modified_source_sink_directory,
                input_apk.apk_name + "source-and-sinks.txt"
            )
        else:
            source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
        result_log_name = activate_flowdroid(hybrid_config,
                                             input_apk.apk_path,
                                             input_apk.apk_name,
                                             source_and_sink_path,
                                             hybrid_config.flowdroid_misc_logs_path)


        num_leaks = HybridAnalysisResult._count_leaks_in_flowdroid_log(
            os.path.join(hybrid_config.flowdroid_misc_logs_path, result_log_name))

        if num_leaks is not None:
            logger.info(f"In apk {input_apk.apk_name} flowdroid found {num_leaks} leaks")
        else:
            pass


class FlowdroidSourceModel:
    # Stores a string of the form
    # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
    full_package_name: str
    return_type: str
    method_name: str
    arg_types: List[str]

    def __init__(self):
        self.full_package_name = ""
        self.return_type = ""
        self.method_name = ""
        self.arg_types = []

    def __eq__(self, other):
        """Overrides the default implementation"""
        if not isinstance(other, FlowdroidSourceModel):
            return False

        if len(self.arg_types) != len(other.arg_types):
            return False

        return (all([self.arg_types[i] == other.arg_types[i]
            for i in range(len(self.arg_types))])
                and self.full_package_name == other.full_package_name
                and self.return_type == other.return_type
                and self.method_name == other.method_name)


    def __hash__(self):
        arg_types_hash_sum = sum([hash(item) for item in self.arg_types])
        return hash((self.full_package_name, self.return_type, self.method_name,
                          arg_types_hash_sum))

    def get_source_string(self):
        # Assumes string should be of the form
        # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
        return f"<{self.full_package_name}: {self.return_type} " \
               f"{self.method_name}({','.join(self.arg_types)})> -> _SOURCE_\n"

    @classmethod
    def from_exception(cls, exception: "ExceptionModel") -> "FlowdroidSourceModel":
        # Assume we are making a source with no context out of the top
        # function in the stacktrace

        # Assuming an exception to be of the form
        """
        04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897
        04-25 10:44:05.274  7232  7232 W System.err: 	at de.ecspride.Datacontainer.getSecret(Datacontainer.java:9)
        ...
        """
        top_function_of_stack_trace = exception.lines[1]

        result_model = FlowdroidSourceModel()

        # Get the remainder of the string after "\tat "
        prefix = "\tat "
        index = top_function_of_stack_trace.index(prefix) + len(prefix)
        suffix = top_function_of_stack_trace[index:].strip()

        # Pull out the package name and the method name
        result_model.method_name = suffix.split("(")[0].split(".")[-1]
        package_elements = suffix.split("(")[0].split(".")[:-1]
        result_model.full_package_name = ".".join(package_elements)

        # Assume the return type to be "java.lang.String" as that is the only
        # type of function the simple instrumentation looks at
        result_model.return_type = "java.lang.String"

        # getting the arg types programatically will be complicated. For now,
        # we assume no arguments (which will be accurate for getters, at least)

        result_model.arg_types = []
        return result_model

    @classmethod
    def from_exception_containing_invocation(cls, exception: "ExceptionModel") -> "FlowdroidSourceModel":
        # TODO: need to tie methods like this structurally to different
        #  instrumentation strategies. What scope does this need to be done?
        invocation_str, value = exception.parse_invocation_string_return_with_stacktrace()

        re_result = re.search(r"<L(.+);: L(.+); (.+)\((.*)\)>", invocation_str)
        if re_result is None:
            raise AssertionError(f"Invocation report '{invocation_str}' did not parse "
                                 f"correctly.")
        result = FlowdroidSourceModel()

        # Need to replace '/' with '.' to change from smali convention to flowdroid
        # source convention
        result.full_package_name = re_result.group(1).replace("/", ".")
        result.return_type = re_result.group(2).replace("/", ".")
        result.method_name = re_result.group(3).replace("/", ".")
        arg_types = re_result.group(4).split(",")
        for i in range(len(arg_types)):
            # Pull L and ; off beginning and end of string, if necessary.
            if re.search(r"L(.+);", arg_types[i]) is not None:
                arg_types[i] = re.search(r"L(.+);", arg_types[i]).group(1).replace("/", ".")
        result.arg_types = arg_types
        return result

    @classmethod
    def from_string(cls, line: str) -> "FlowdroidSourceModel":
        """
        Parse the given string into a Source Model Object, and return the
        model object.
        :param line: String from sources/sinks file containing source
        :return: FlowdroidSourceModel
        """
        # Assumes string should be of the form
        # <[full package name]: [return type] [method name]([arg types,])> -> _SOURCE_
        # Example:
        # <javax.servlet.ServletRequest: java.lang.String getParameter(java.lang.String)> -> _SOURCE_

        line = line.strip()
        line_chunks = line.split(" -> ")
        assert len(line_chunks) == 2
        assert line_chunks[1] == "_SOURCE_"

        function_chunks = line_chunks[0]
        # a small handful of lines break the above pattern. Example:
        # <android.telephony.TelephonyManager: java.lang.String getDeviceId()> android.permission.READ_PHONE_STATE -> _SOURCE_
        if function_chunks.strip().endswith("android.permission.READ_PHONE_STATE"):
            # TODO: need to look into flowdroid to see why this case comes up/if it
            #  has important semantics.
            function_chunks = function_chunks.strip()[:-len(
                "android.permission.READ_PHONE_STATE")].strip()
        function_chunks = function_chunks[1:-1]  # take off the enclosing '<' and '>'
        full_package_name, return_type, signature = function_chunks.split()
        full_package_name = full_package_name[:-1]  # take off the ':' at the end
        method_name = signature.split(')')[0]
        # get the string after the '(' and take off the ')' at the end
        if '(' in signature:
            signature_args = signature.split('(')[1]
            if signature_args.endswith(')'):
                signature_args = signature_args[:-1]
            signature_args = signature_args.split(',')
        else:
            # Case where function name just has ')' after, but no '()'
            # this may be a bug from flowdroid? If there are semantics associated
            # with this case, they are not capture here.
            signature_args = []

        # put results in model object
        result = FlowdroidSourceModel()
        result.full_package_name = full_package_name
        result.return_type = return_type
        result.method_name = method_name
        result.arg_types = signature_args

        return result


class LogcatLogFileModel:
    def __init__(self, log_path):
        # Open the log and read the contents
        with open(log_path, 'r') as log_file:
            self.lines = log_file.readlines()

        self.exceptions = self.scan_lines_for_exception_blocks()

    def scan_lines_for_exception_blocks(self) -> List["ExceptionModel"]:
        """
        :return: Returns a list of exception blocks where each block is a list
        of the strings that make up the exception.
        """
        # Assuming an exception to be of the form
        """
        04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897
        04-25 10:44:05.274  7232  7232 W System.err: 	at de.ecspride.Datacontainer.getSecret(Datacontainer.java:9)
        """
        # with the second line being repeated one or more times.
        exceptions = []
        block_in_progress = []
        scanning_exception = False
        for line in self.lines:
            if not scanning_exception and line.__contains__(
                    "W System.err: java.lang.Exception:"):
                scanning_exception = True
                block_in_progress.append(line)
            elif scanning_exception and line.__contains__(
                    "W System.err: java.lang.Exception:"):
                # this case would occur if there are two relevant exceptions
                # back to back.
                exceptions.append(ExceptionModel(block_in_progress))
                block_in_progress = []
                block_in_progress.append(line)
                # leave scanning_exception as True
            elif line.__contains__("W System.err:"):
                block_in_progress.append(line)
            elif scanning_exception and not line.__contains__("W System.err:"):
                scanning_exception = False
                exceptions.append(ExceptionModel(block_in_progress))
                block_in_progress = []

        return exceptions

    def filter_exceptions_by_header(self, target_strings: List[str]) -> List[
        "ExceptionModel"]:
        result_exceptions = []
        for exception in self.exceptions:

            # From older instrumentation approach
            # header_value = exception.get_header_value()

            if not exception.is_from_instrumentation():
                continue
            _, value = exception.parse_invocation_string_return_with_stacktrace()

            if value in target_strings:
                result_exceptions.append(exception)

        return result_exceptions


class ExceptionModel:
    lines: List[str]

    def __init__(self, lines):
        self.lines = lines

    def get_header_value(self) -> Optional[str]:
        """
        Return the string value that the exception was created with, if any.
        Returns None if there is no value.
        """

        # Assuming an exception to be of the form
        """
        04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897
        04-25 10:44:05.274  7232  7232 W System.err: 	at de.ecspride.Datacontainer.getSecret(Datacontainer.java:9)
        ...
        """
        header_line = self.lines[0]
        # Take white space of sides
        header_line = header_line.strip()
        prefix = "java.lang.Exception:"
        # We expect the header value to follow the prefix, separated by
        # a space.
        if header_line.find(prefix) == -1:
            # If prefix not found, then this is not the exception we are looking for.
            return None
        prefix_index = header_line.index(prefix)
        # the index after the prefix and a space
        value_index = prefix_index + len(prefix) + 1

        # there may not be a value
        if value_index >= len(header_line):
            return None
        value = header_line[value_index:]
        value.strip()
        if value == "":
            return None
        else:
            return value

    def parse_invocation_string_return_with_stacktrace(self):
        """
        Parse a header value that was written by code from
        log_invocation_string_return_with_stacktrace in instrument.py.
        """

        # Example exception header:
        "06-29 20:11:54.507  8840  8840 W System.err: java.lang.Exception: At method <<Lmod/ndk/ActMain;: Ljava/lang/String; cFuncGetIMEI(Landroid/content/Context;)>> value returned: 355458061189396"

        # Client should have checked that this will parse
        # TODO: this whole parsing thingdepends really heavily on
        #  the instrumentation impl
        result = re.search(r"W System\.err: java\.lang\.Exception: At method (<.+>) value returned: (.*)$", self.lines[0])
        invoked_method = result.group(1)
        value = result.group(2)
        return invoked_method, value

    def is_from_instrumentation(self):
        result = re.search(
            r"W System\.err: java\.lang\.Exception: At method (<.+>) value returned: (.*)$", self.lines[0])
        return result is not None


def test_exception_parsing():
    log = LogcatLogFileModel("../data/test-resources/FieldSensitivity3.apk.log")
    exceptions = log.filter_exceptions_by_header(["8901240197155182897"])
    assert len(exceptions) == 1
    assert exceptions[0].lines[
               0] == "04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897\n"


def test_file_source_parsing():
    file_path = "../data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    sources = get_sources_from_file(file_path)
    print(list(map(lambda s: s.get_source_string(), sources)))


if __name__ == '__main__':
    print(len(input.input_apks_from_list(
        "data/input-apk-lists/common-false-neg-RP.txt")))

