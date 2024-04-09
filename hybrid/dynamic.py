import os
import re
import shutil
from typing import Set, List, Optional, Dict

from hybrid import results
from hybrid.hybrid_config import HybridAnalysisConfig, modified_source_sink_path
from hybrid.source_sink import MethodSignature, SourceSinkXML
from intercept.instrument import InstrumentationReport, SmaliMethodInvocation

from util import logger

logger = logger.get_logger('hybrid', 'dynamic')


class AbstractDynamicLogProcessingStrategy:
    """
    Class encapsulates different strategies for processing the logs produced by an instrumented dynamic run of an app.

    Different strategies correspond with different instrumentation schemes.
    """

    def sources_from_log(self, hybrid_config: HybridAnalysisConfig, log_path: str, apk_name: str, group_id: int=-1):
        """
        Produce sources that have been identified as sensitive methods based on reports in the logs provided by log_path.
        """
        raise NotImplementedError("Interface not implemented")

    def source_sink_file_from_sources(self, hybrid_config: HybridAnalysisConfig,
                                      sources, apk_name: str, group_id: int=-1) -> str:
        """
        Create a new source sink file using the given sources. Returns a path to the
        created file. `
        """
        raise NotImplementedError("Interface not implemented")

    def _get_sources_from_file(self, source_and_sink_path: str) -> List[
        "MethodSignature"]:
        """
        Read in the source/sink text file, and produce a list of MethodSignatures.
        """
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
                if "'" in line:
                    continue
                if line.strip().endswith("-> _SOURCE_"):
                    resultSources.append(MethodSignature.from_source_string(line))

        return resultSources


def dynamic_log_processing_strategy_factory(
        hybrid_config: HybridAnalysisConfig) -> AbstractDynamicLogProcessingStrategy:
    """
    Return the correct instantiation of an AbstractDynamicLogProcessingStrategy based on the
    dynamic_log_processing_strategy field of the provided config.
    """

    if hybrid_config.dynamic_log_processing_strategy == \
            "StringReturnDynamicLogProcessingStrategy":
        return StringReturnDynamicLogProcessingStrategy()
    elif hybrid_config.dynamic_log_processing_strategy == \
            "InstrReportReturnOnlyDynamicLogProcessingStrategy":
        return InstrReportReturnOnlyDynamicLogProcessingStrategy()
    elif hybrid_config.dynamic_log_processing_strategy == "InstrReportReturnAndArgsDynamicLogProcessingStrategy":
        return InstrReportReturnAndArgsDynamicLogProcessingStrategy()
    else:
        raise AssertionError("Unexpected strategy name: " + hybrid_config.dynamic_log_processing_strategy)


class StringReturnDynamicLogProcessingStrategy(AbstractDynamicLogProcessingStrategy):
    def sources_from_log(self, hybrid_config: HybridAnalysisConfig, log_path: str, apk_name: str, group_id: int=-1) -> Set[MethodSignature]:
        unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path
        target_PII = hybrid_config.target_PII

        observed_sources: set[MethodSignature] = set(
            self._get_sources_from_log(log_path, target_PII))

        existing_sources: set[MethodSignature] = set(self._get_sources_from_file(
            unmodified_source_and_sink_path))

        # Set minus, only append new sources not in unmodified source/sink list.
        new_sources: set[MethodSignature] = observed_sources - existing_sources

        # Report new sources
        results.HybridAnalysisResult.report_new_sources_count(hybrid_config, apk_name,
                                                              len(new_sources), group_id)
        logger.info(f"Discovered {len(new_sources)} new source(s) "
                    f"from {apk_name}.")

        return new_sources

    def source_sink_file_from_sources(self, hybrid_config: HybridAnalysisConfig,
                                      sources: Set[MethodSignature], apk_name: str, group_id: int=-1) -> str:
        unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path

        modified_source_and_sink_path = modified_source_sink_path(hybrid_config, apk_name, group_id)

        shutil.copyfile(unmodified_source_and_sink_path, modified_source_and_sink_path)
        with open(modified_source_and_sink_path, 'a') as result_file:
            result_file.writelines(
                list(map(lambda s: s.get_source_string(), sources)))

        return modified_source_and_sink_path

    def _get_sources_from_log(self, log_path: str, target_PII: List[str]) -> List[
        "MethodSignature"]:
        # this behavior should depend on the instrumentation being used in the
        # intercept step

        # assuming we are using the simplest instrumentation, log the value and the
        # stack trace

        log = LogcatLogFileModel(log_path)
        exceptions = log.scan_lines_for_exception_blocks()
        filtered_exceptions = filter_exceptions_by_header(target_PII, exceptions)

        # sources_in_log = list(map(lambda e: from_exception(e),
        #                           filtered_exceptions))
        sources_in_log = list(
            map(lambda e: from_exception_containing_invocation(e),
                filtered_exceptions))

        return sources_in_log


class InstrReportReturnOnlyDynamicLogProcessingStrategy(AbstractDynamicLogProcessingStrategy):
    """
    Identify and deserialize InstrumentationReport python objects from the log
    All logging is done tagged.
    Only create sources from function returns.
    """

    def sources_from_log(self, hybrid_config: HybridAnalysisConfig, log_path: str, apk_name: str, group_id: int=-1) -> Set[
        MethodSignature]:

        log = LogcatLogFileModel(log_path)

        instr_reports = log.scan_log_for_instrumentation_reports()

        observed_sources = self._instr_reports_to_sources(instr_reports)

        existing_sources: set[MethodSignature] = set(self._get_sources_from_file(
            hybrid_config.unmodified_source_sink_list_path))

        # Set minus, only append new sources not in unmodified source/sink list.
        new_sources: set[MethodSignature] = observed_sources - existing_sources

        # Report new sources
        results.HybridAnalysisResult.report_new_sources_count(hybrid_config, apk_name,
                                                              len(new_sources), group_id)
        logger.info(f"Discovered {len(new_sources)} new source(s) "
                    f"from {apk_name}.")

        return new_sources

    def source_sink_file_from_sources(self, hybrid_config: HybridAnalysisConfig,
                                      sources: Set[MethodSignature], apk_name: str, group_id: int=-1):

        unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path

        modified_source_and_sink_path = modified_source_sink_path(hybrid_config, apk_name, group_id)

        shutil.copyfile(unmodified_source_and_sink_path, modified_source_and_sink_path)
        with open(modified_source_and_sink_path, 'a') as result_file:
            result_file.writelines(
                list(map(lambda s: s.get_source_string(), sources)))

        return modified_source_and_sink_path

        # raise NotImplementedError("Interface not implemented")

    def _instr_reports_to_sources(self, instr_reports: List[InstrumentationReport]) -> Set[MethodSignature]:
        post_invoke_arg_masks = dict()
        pre_invoke_arg_masks = dict()
        signatures_by_id = dict()

        # check for invocations with some arg/return tainted after the invoke
        for instr_report in instr_reports:

            # setup masks indicating if an arg/return value is/isn't tainted for a
            # given invocation
            if not post_invoke_arg_masks.keys().__contains__(instr_report.invoke_id):
                pre_invoke_arg_masks[instr_report.invoke_id] = []
                post_invoke_arg_masks[instr_report.invoke_id] = [False]
                signatures_by_id[instr_report.invoke_id] = instr_report.invoke_signature
            # The exact number of registers in an invoke is tricky to know. On the
            # fly, expand the arg masks so there is room for whatever arg registers
            # get reported as tainted.
            if instr_report.is_arg_register and (
                    instr_report.register_index >= len(pre_invoke_arg_masks[instr_report.invoke_id])):
                additional_mask_length = (instr_report.register_index + 1) - len(
                    pre_invoke_arg_masks[instr_report.invoke_id])
                pre_invoke_arg_masks[instr_report.invoke_id] = ([False] * additional_mask_length) + \
                                                               pre_invoke_arg_masks[instr_report.invoke_id]
                post_invoke_arg_masks[instr_report.invoke_id] = ([False] * additional_mask_length) + \
                                                                post_invoke_arg_masks[instr_report.invoke_id]

            if not instr_report.is_before_invoke:
                # return value
                if not instr_report.is_arg_register:
                    post_invoke_arg_masks[instr_report.invoke_id][-1] = True
                else:
                    pass
            else:
                if not instr_report.is_arg_register:
                    raise AssertionError("Case should not occur, can't have a return "
                                         "value before the invocation")
                else:
                    pre_invoke_arg_masks[instr_report.invoke_id][
                        instr_report.register_index] = True

        source_signatures: Set[str] = set()
        for invocation_id in post_invoke_arg_masks.keys():

            # Invocation is only a leak if return was tainted, or if a given arg is
            # tainted after, but wasn't tainted before.

            # Was the return value tainted?
            if post_invoke_arg_masks[invocation_id][-1]:
                source_signatures.add(signatures_by_id[invocation_id])
            # Was an arg tainted after, but not before, the invocation?
            else:
                # Don't check args
                pass
                # for arg_index in range(len(pre_invoke_arg_masks[invocation_id])):
                #     if post_invoke_arg_masks[invocation_id][arg_index]:
                #         if not pre_invoke_arg_masks[invocation_id][arg_index]:
                #             source_signatures.add(signatures_by_id[invocation_id])
                #             break

        # Change collected source_signatures to source models
        return set([MethodSignature.from_signature_string(signature) for signature in source_signatures])


class InstrReportReturnAndArgsDynamicLogProcessingStrategy(AbstractDynamicLogProcessingStrategy):
    """
    Identify and deserialize InstrumentationReport python objects from the log
    All logging is done tagged.
    Create sources from function returns and args
    """

    def sources_from_log(self, hybrid_config: HybridAnalysisConfig, log_path: str,
                         apk_name: str, group_id: int=-1) -> SourceSinkXML:

        log: LogcatLogFileModel = LogcatLogFileModel(log_path)

        instr_reports: List[InstrumentationReport] = log.scan_log_for_instrumentation_reports()

        source_sink_xml: SourceSinkXML = self._instr_reports_to_source_sink(instr_reports)
        discovered_sources_count: int = source_sink_xml.source_count

        existing_sources: Set[MethodSignature] = set(self._get_sources_from_file(
            hybrid_config.unmodified_source_sink_list_path))

        # only append new sources not in unmodified source/sink list.
        source_sink_xml.remove_return_sources(list(existing_sources))
        duplicate_sources_count = discovered_sources_count - source_sink_xml.source_count

        # Report new sources
        results.HybridAnalysisResult.report_new_sources_count(hybrid_config, apk_name,
                                                              source_sink_xml.source_count, group_id)
        logger.info(f"Discovered {str(source_sink_xml.source_count)} new source(s) "
                    f"from {apk_name}.")

        return source_sink_xml

    def source_sink_file_from_sources(self, hybrid_config: HybridAnalysisConfig,
                                      sourceSinks: SourceSinkXML, apk_name: str, group_id: int=-1) -> str:

        unmodified_source_and_sink_path = hybrid_config.unmodified_source_sink_list_path

        modified_source_and_sink_path = modified_source_sink_path(hybrid_config, apk_name, group_id, is_xml=True)

        sourceSinks.add_sinks_from_file(unmodified_source_and_sink_path)

        sourceSinks.write_to_file(modified_source_and_sink_path)

        return modified_source_and_sink_path

    def _instr_reports_to_source_sink(self, instr_reports: List[InstrumentationReport]) -> SourceSinkXML:

        # Create data structures to note what was tainted before and after a given function.
        # For each dict the key is the invocation ID.
        base_tainted_before_dict: Dict[int, bool] = dict()
        base_tainted_after_dict: Dict[int, bool] = dict()
        args_tainted_before_dict: Dict[int, List[bool]] = dict()
        args_tainted_after_dict: Dict[int, List[bool]] = dict()
        return_tainted_after_dict: Dict[int, bool] = dict()
        signatures_by_id: Dict[int, MethodSignature] = dict()

        # before_invoke_arg_masks = dict()
        # after_invoke_arg_masks = dict()

        # check for invocations with some base/arg/return tainted after the invoke
        for instr_report in instr_reports:

            ### Start interpret instr_report
            is_base = instr_report.register_index == 0 and (not instr_report.is_static)
            is_return = (not instr_report.is_before_invoke) and instr_report.is_return_register
            is_arg = not (is_base or is_return)

            signature_model = MethodSignature.from_signature_string(instr_report.invoke_signature)
            if not (instr_report.invoke_id in signatures_by_id.keys()):
                signatures_by_id[instr_report.invoke_id] = signature_model

            if is_arg:
                arg_index = SmaliMethodInvocation.register_index_to_arg_index(instr_report.is_static,
                                                                              instr_report.register_index,
                                                                              signature_model.arg_types)
                if is_arg and arg_index is None:
                    raise AssertionError("Unable to determine index of argument")
            ### End interpret instr_report

            if instr_report.is_before_invoke:
                if is_base:
                    base_tainted_before_dict[instr_report.invoke_id] = True
                elif is_arg:
                    if not instr_report.invoke_id in args_tainted_before_dict.keys():
                        args_tainted_before_dict[instr_report.invoke_id] = [False] * len(signature_model.arg_types)
                    args_tainted_before_dict[instr_report.invoke_id][arg_index]
                elif is_return:
                    raise AssertionError("Unexpected Case, shouldn't have return report before invoke. Examine earlier checks for logic errors.")
                else:
                    raise AssertionError("Unexpected Case. One of is_base, is_arg, or is_return should be true.")

            else:  # After invoke
                if is_base:
                    base_tainted_after_dict[instr_report.invoke_id] = True
                elif is_arg:
                    if not instr_report.invoke_id in args_tainted_before_dict.keys():
                        args_tainted_before_dict[instr_report.invoke_id] = [False] * len(signature_model.arg_types)
                    args_tainted_before_dict[instr_report.invoke_id][arg_index]
                elif is_return:
                    return_tainted_after_dict[instr_report.invoke_id] = True
                else:
                    raise AssertionError("Unexpected Case. One of is_base, is_arg, or is_return should be true.")

        base_source_signatures: List[MethodSignature] = []
        arg_source_signatures: List[MethodSignature] = []
        arg_source_indices: List[int] = []
        return_source_signatures: List[MethodSignature] = []

        # Go through base dicts
        for invocation_id in base_tainted_after_dict.keys():
            # Invocation is a leak if the method name is "<init>" and the base is tainted after the invoke,
            # or if the base was not tainted before the invoke, and is tainted after the invoke.
            signature_model = signatures_by_id[invocation_id]
            if signature_model.method_name == "<init>":
                base_source_signatures.append(signature_model)
            else:
                if invocation_id not in base_tainted_before_dict.keys():
                    base_source_signatures.append(signature_model)
                else:
                    if not base_tainted_before_dict[invocation_id]:
                        base_source_signatures.append(signature_model)

        # Go through args dicts
        for invocation_id in args_tainted_after_dict.keys():
            # Invocation is only a leak if arg was tainted and the specified arg was not tainted before

            signature_model = signatures_by_id[invocation_id]
            args_tainted_after = args_tainted_after_dict[invocation_id]

            if invocation_id not in args_tainted_before_dict:
                for arg_index in range(len(args_tainted_after)):
                    if args_tainted_after[arg_index]:
                        arg_source_signatures.append(signature_model)
                        arg_source_indices.append(arg_index)
            else:
                args_tainted_before = args_tainted_before_dict[invocation_id]

                for arg_index in range(len(args_tainted_after)):
                    if args_tainted_after[arg_index] and not args_tainted_before[arg_index]:
                        arg_source_signatures.append(signature_model)
                        arg_source_indices.append(arg_index)

        # Go through return dict
        for invocation_id in return_tainted_after_dict:
            signature_model = signatures_by_id[invocation_id]
            return_source_signatures.append(signature_model)

            # # Was the return value tainted?
            # if after_invoke_arg_masks[invocation_id][-1]:
            #     return_source_signatures.append(signatures_by_id[invocation_id])
            # # Was an arg tainted after, but not before, the invocation?
            # else:
            #     for arg_index in range(len(before_invoke_arg_masks[invocation_id])):
            #         if after_invoke_arg_masks[invocation_id][arg_index]:
            #             if not before_invoke_arg_masks[invocation_id][arg_index]:
            #                 arg_source_signatures.append(signatures_by_id[invocation_id])
            #                 arg_source_indices.append(arg_index)

        result_source_sinks = SourceSinkXML()

        for base_source_signature in base_source_signatures:
            result_source_sinks.add_base_source(base_source_signature)

        for arg_source_signature, arg_source_index in zip(arg_source_signatures, arg_source_indices):
            result_source_sinks.add_arg_source(MethodSignature.from_signature_string(arg_source_signature),
                                               arg_source_index)

        for return_source_signature in return_source_signatures:
            result_source_sinks.add_return_source(return_source_signature)

        return result_source_sinks


class LogcatLogFileModel:
    lines: List[str]

    # exceptions: List['ExceptionModel']

    def __init__(self, log_path):
        # Open the log and read the contents
        with open(log_path, 'r') as log_file:
            self.lines = log_file.readlines()

        # self.exceptions = self._scan_lines_for_exception_blocks()

    def scan_lines_for_exception_blocks(self) -> List['ExceptionModel']:
        """
        :return: Returns a list of exception models where each block is a list
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

    def scan_log_for_instrumentation_reports(self) -> List['InstrumentationReport']:
        # "Example 07-21 12:46:10.902  7001  7001 D Snapshot: InstrumentationReport(invoke_signature='<Lc..."

        report_preamble = " D Snapshot: "
        instr_reports = []

        for line in self.lines:
            if report_preamble in line:
                log_content = line.split(report_preamble)[1]

                # Parse the contents of the string according to the code written in Java
                re_result = re.search(r"(InstrumentationReport\(.+\));(.+);(.+)", log_content.strip())
                if re_result is None:
                    raise AssertionError("Log did not parse correctly")

                instr_report_string, access_path, private_string = re_result.group(1), re_result.group(
                    2), re_result.group(3)
                # instr_report_string should be a working constructor for an
                # InstrumentationReport object.
                instr_report = eval(instr_report_string)
                instr_reports.append(instr_report)

        return instr_reports

def filter_exceptions_by_header(target_strings: List[str], exceptions) -> \
        List["ExceptionModel"]:
    result_exceptions = []
    for exception in exceptions:

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
        result = re.search(r"W System\.err: java\.lang\.Exception: At method (<.+>) value returned: (.*)$",
                           self.lines[0])
        invoked_method = result.group(1)
        value = result.group(2)
        return invoked_method, value

    def is_from_instrumentation(self):
        result = re.search(
            r"W System\.err: java\.lang\.Exception: At method (<.+>) value returned: (.*)$", self.lines[0])
        return result is not None


def from_exception(exception: "ExceptionModel") -> "MethodSignature":
    # Assume we are making a source with no context out of the top
    # function in the stacktrace

    # Assuming an exception to be of the form
    """
    04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897
    04-25 10:44:05.274  7232  7232 W System.err: 	at de.ecspride.Datacontainer.getSecret(Datacontainer.java:9)
    ...
    """
    top_function_of_stack_trace = exception.lines[1]

    result_model = MethodSignature()

    # Get the remainder of the string after "\tat "
    prefix = "\tat "
    index = top_function_of_stack_trace.index(prefix) + len(prefix)
    suffix = top_function_of_stack_trace[index:].strip()

    # Pull out the package name and the method name
    result_model.method_name = suffix.split("(")[0].split(".")[-1]
    package_elements = suffix.split("(")[0].split(".")[:-1]
    result_model.base_type = ".".join(package_elements)

    # Assume the return type to be "java.lang.String" as that is the only
    # type of function the simple instrumentation looks at
    result_model.return_type = "java.lang.String"

    # getting the arg types programatically will be complicated. For now,
    # we assume no arguments (which will be accurate for getters, at least)

    result_model.arg_types = []
    return result_model


def from_exception_containing_invocation(exception: "ExceptionModel") -> "MethodSignature":
    # TODO: need to tie methods like this structurally to different
    #  instrumentation strategies. What scope does this need to be done?
    invocation_str, value = exception.parse_invocation_string_return_with_stacktrace()

    re_result = re.search(r"<L(.+);: L(.+); (.+)\((.*)\)>", invocation_str)
    if re_result is None:
        raise AssertionError(
            f"Invocation report '{invocation_str}' did not parse "
            f"correctly.")
    result = MethodSignature()

    # Need to replace '/' with '.' to change from smali convention to flowdroid
    # source convention
    result.base_type = re_result.group(1).replace("/", ".")
    result.return_type = re_result.group(2).replace("/", ".")
    result.method_name = re_result.group(3).replace("/", ".")
    arg_types = re_result.group(4).split(",")
    for i in range(len(arg_types)):
        # Pull L and ; off beginning and end of string, if necessary.
        if re.search(r"L(.+);", arg_types[i]) is not None:
            arg_types[i] = re.search(r"L(.+);", arg_types[i]).group(
                1).replace("/", ".")
    result.arg_types = arg_types
    return result


def test_exception_parsing():
    log = LogcatLogFileModel("../data/test-resources/FieldSensitivity3.apk.log")
    exceptions = log.filter_exceptions_by_header(["8901240197155182897"])
    assert len(exceptions) == 1
    assert exceptions[0].lines[
               0] == "04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897\n"


def test_file_source_parsing():
    file_path = "../data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"
    sources = StringReturnDynamicLogProcessingStrategy()._get_sources_from_file(
        file_path)
    print(list(map(lambda s: s.get_source_string(), sources)))


def test_instr_report_parsing():
    file_path = "data/test-resources/OnlyTelephony.apk.log"

    log_model = LogcatLogFileModel(file_path)

    instr_reports = log_model.scan_log_for_instrumentation_reports()

    print(instr_reports)


if __name__ == '__main__':
    test_instr_report_parsing()
