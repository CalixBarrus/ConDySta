from abc import ABC
import os
import re
import shutil
from typing import Set, List, Optional, Dict, Tuple, Union

import pandas as pd

from experiment.common import modified_source_sink_path
from hybrid import results, sensitive_information
from hybrid.invocation_register_context import InvocationRegisterContext
from hybrid.source_sink import MethodSignature, SourceSink, SourceSinkSignatures, SourceSinkXML
from intercept.InstrumentationReport import InstrumentationReport
from intercept.smali import SmaliMethodInvocation

from hybrid.access_path import AccessPath


from util.input import InputModel

import util.logger
logger = util.logger.get_logger(__name__)


class LogcatToSourcesStrategy(ABC):
    """
    Class encapsulates different strategies for processing the logs produced by an instrumented dynamic run of an app.

    Different strategies correspond to different instrumentation schemes.
    """

    def sources_from_log(self, logcat_path: str) -> SourceSink:
        # Produce sources that have been identified as sensitive methods based on reports in the logs provided by log_path.
        raise NotImplementedError("Interface not implemented")

def logcat_to_sources_strategy_factory(
        logcat_to_sources_strategy: str) -> LogcatToSourcesStrategy:
    """
    Return the correct instantiation of a LogcatToSourcesStrategy.

    a_priori_personally_identifiable_information is pulled from sensitive_information by default.
    """
    # dynamic_log_processing_strategy = hybrid_config.dynamic_log_processing_strategy

    if logcat_to_sources_strategy == \
            "StringReturn":
        a_priori_personally_identifiable_information = sensitive_information.personally_identifiable_information
        return StringReturn(a_priori_personally_identifiable_information)
    elif logcat_to_sources_strategy == \
            "InstrReportReturnOnly":
        return InstrReportReturnOnly()
    elif logcat_to_sources_strategy == "InstrReportReturnAndArgs":
        return InstrReportReturnAndArgs()
    else:
        raise AssertionError("Unexpected strategy name: " + logcat_to_sources_strategy)


class StringReturn(LogcatToSourcesStrategy):
    def __init__(self, target_PII) -> None:
        super().__init__()
        self.target_PII = target_PII

    
    def sources_from_log(self, logcat_path: str) -> Set[MethodSignature]:

        target_PII = self.target_PII

        observed_sources: set[MethodSignature] = set(
            self._get_sources_from_log(logcat_path, target_PII))

        # existing_sources: set[MethodSignature] = set(self._get_sources_from_file(
        #     unmodified_source_sink_list_path))

        # Set minus, only append new sources not in unmodified source/sink list.
        # new_sources: set[MethodSignature] = observed_sources - existing_sources

        return SourceSinkSignatures(source_signatures=observed_sources)

    def _get_sources_from_log(self, log_path: str, target_PII: List[str]) -> List["MethodSignature"]:

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


class InstrReportReturnOnly(LogcatToSourcesStrategy):
    """
    Identify and deserialize InstrumentationReport python objects from the log
    All logging is done tagged.
    Only create sources from function returns.
    """

    
    def sources_from_log(self, logcat_path: str) -> Set[
        MethodSignature]:

        log = LogcatLogFileModel(logcat_path)

        instr_reports = log.scan_log_for_instrumentation_reports()

        observed_sources = self._instr_reports_to_sources(instr_reports)

        return SourceSinkSignatures(source_signatures=observed_sources)

    def _instr_reports_to_sources(self, instr_reports: List[InstrumentationReport]) -> Set[MethodSignature]:
        # But only grabs instr reports for function returns.

        post_invoke_arg_masks = dict()
        pre_invoke_arg_masks = dict()
        signatures_by_id = dict()

        # check for invocations with some arg/return tainted after the invocation
        for instr_report in instr_reports:

            # setup masks indicating if an arg/return value is/isn't tainted for a
            # given invocation
            if not post_invoke_arg_masks.keys().__contains__(instr_report.invoke_id):
                pre_invoke_arg_masks[instr_report.invoke_id] = []
                post_invoke_arg_masks[instr_report.invoke_id] = [False]
                signatures_by_id[instr_report.invoke_id] = instr_report.invocation_java_signature
            # The exact number of registers in an invoke is tricky to know. On the
            # fly, expand the arg masks so there is room for whatever arg registers
            # get reported as tainted.
            if instr_report.is_arg_register and (
                    instr_report.invocation_argument_register_index >= len(pre_invoke_arg_masks[instr_report.invoke_id])):
                additional_mask_length = (instr_report.invocation_argument_register_index + 1) - len(
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
                        instr_report.invocation_argument_register_index] = True

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
        return set([MethodSignature.from_java_style_signature(signature) for signature in source_signatures])


class InstrReportReturnAndArgs(LogcatToSourcesStrategy):
    """
    Identify and deserialize InstrumentationReport python objects from the log
    All logging is done tagged.
    Create sources from function returns and args
    """
    
    def sources_from_log(self, logcat_path: str) -> SourceSink:

        log: LogcatLogFileModel = LogcatLogFileModel(logcat_path)

        instr_reports: List[InstrumentationReport] = log.scan_log_for_instrumentation_reports()

        # todo: what if there are reports from multiple runs? 
        source_sink: SourceSinkSignatures = self._instr_reports_to_source_sink(instr_reports)
        discovered_sources_count: int = source_sink.source_count

        return source_sink
    
    def _instr_reports_to_source_sink(self, instrumentation_reports: List[InstrumentationReport]) -> SourceSinkSignatures:

        observation = ExecutionObservation()
        for instrumentation_report in instrumentation_reports:
            observation.parse_instrumentation_result(instrumentation_report)

        tainting_invocation_ids: List[int] = observation.get_tainting_invocation_ids()

        tainting_signatures: List[MethodSignature] = [MethodSignature.from_java_style_signature(observation.invocation_java_signatures[id]) for id in tainting_invocation_ids]

        # TODO: we should output some frequency information about these tainting signatures; How many times each comes up

        return SourceSinkSignatures(source_signatures=set(tainting_signatures))

def get_selected_errors_from_logcat(logcat_path: str) -> str:
    logcat_file_model = LogcatLogFileModel(logcat_path)
    
    errors = []
    errors += logcat_file_model.get_lang_verify_errors()
    errors += logcat_file_model.get_fatal_exception_errors()
    errors += logcat_file_model.get_app_not_responding_errors()
    errors += logcat_file_model.get_class_not_found_errors()
    return ";".join(errors)
    
def log_to_tainting_invocation_register_context(logcat_path: str) -> 'InvocationRegisterContext':
    logcat_file_model = LogcatLogFileModel(logcat_path)
    # feed Observation Result all the instr reports (and access paths)
    # ask it for InvocationRegisterContexts and return
    raise NotImplementedError

class LogcatLogFileModel:
    path: str
    lines: List[str]

    # exceptions: List['ExceptionModel']

    def __init__(self, log_path):
        # Open the log and read the contents


        # Check if file has non utf-8 encoded letters and report if this is the case. For now, we'll ignore them.
        try:
            with open(log_path, 'r', encoding="utf-8") as log_file:
                _ = log_file.readlines()
        except UnicodeDecodeError as e:
            logger.warning(f"Non utf-8 chars are being ignored in file {log_path}")

        # ignore data with a bad encoding
        with open(log_path, 'r', errors="ignore") as log_file:
            self.lines = log_file.readlines()

        self.path = log_path

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
        return [report for report, _, _ in self.scan_log_for_instrumentation_report_tuples()]

    def scan_log_for_instrumentation_report_tuples(self) -> List[Tuple[InstrumentationReport, AccessPath, str]]:
        # Tuples are instr_report, access_path, private_string
        # "Example 07-21 12:46:10.902  7001  7001 D Snapshot: InstrumentationReport(invoke_signature='<Lc..."

        report_tag = " D Snapshot: "
        report_preamble = report_tag + "InstrumentationReport("
        instr_report_tuples = []

        for i, line in enumerate(self.lines):
            if report_preamble in line:
                log_content = line.split(report_tag)[1]

                # Parse the contents of the string according to the code written in Java
                re_result = re.search(r"(InstrumentationReport\(.+\));(.+);(.*)", log_content.strip())
                if re_result is None:
                    raise AssertionError("Log did not parse correctly")


                instr_report_string, access_path, private_string = re_result.group(1), re_result.group(
                    2), re_result.group(3)
                # instr_report_string should be a working constructor for an InstrumentationReport object.
                # access_path is the str representation of a List<FieldInfo> object, defined in Snapshot.Java
                # private_string is the listed string of PII that was detected by the Snapshot code

                if len(re.findall("InstrumentationReport", instr_report_string)) > 1:
                    logger.error(f"Instrumentation produced a bad string on line {i} of {os.path.basename(self.path)}; Tainted string was itself an Instrumentation Report! '{instr_report_string}'")
                    continue

                access_path: AccessPath = AccessPath(access_path)

                instr_report = eval(instr_report_string)
                instr_report_tuples.append((instr_report, access_path, private_string))

        return instr_report_tuples
    
    def scan_log_for_harnessed_source_calls(self) -> List[Tuple[int, str]]:
# 10-21 11:40:27.756  8455  8455 D HarnessedSource: Source Method Landroid/widget/EditText; getText called in class and method <Lalc; onClick>. Return value was:;

        log_tag = "D HarnessedSource: "
        message_preamble = "Source Method "

        return self._get_log_messages(self.lines, log_tag, message_preamble)


    def scan_log_for_stack_traces(self):
        # TODO: not needed yet
        pass


    def get_app_not_responding_errors(self) -> List[str]:
        # Example line
        # 10-08 10:15:31.142  1124  1437 I InputDispatcher: Application is not responding: AppWindowToken{4c9da02 token=Token{8068ee4 ActivityRecord{6fd5277 u0 eu.kanade.tachiyomi/.ui.main.MainActivity t2558}}}.  It has been 5006.4ms since event, 5004.4ms since wait started.  Reason: Waiting because no window has focus but there is a focused application that may eventually add a window when it finishes starting up.
        log_tag = "I InputDispatcher: "
        error_preamble = "Application is not responding: "
        errors = [f"App Not Responding Error on line {i} in log {self.path}" for i, line in self._get_log_messages(self.lines, log_tag, error_preamble)]
        return errors

    def get_class_not_found_errors(self) -> List[str]:
        # Example line
        # 10-07 19:25:30.130  6540  6540 I art     : Caused by: java.lang.ClassNotFoundException: Didn't find class "android.os.ProxyFileDescriptorCallback" on path: DexPathList[[zip file "/data/app/com.google.android.gm-1/base.apk", zip file "/data/app/com.google.android.gm-1/split_config.armeabi_v7a.apk", zip file "/data/app/com.google.android.gm-1/split_config.en.apk", zip file "/data/app/com.google.android.gm-1/split_config.xxxhdpi.apk"],nativeLibraryDirectories=[/data/app/com.google.android.gm-1/lib/arm, /data/app/com.google.android.gm-1/base.apk!/lib/armeabi-v7a, /data/app/com.google.android.gm-1/split_config.armeabi_v7a.apk!/lib/armeabi-v7a, /data/app/com.google.android.gm-1/split_config.en.apk!/lib/armeabi-v7a, /data/app/com.google.android.gm-1/split_config.xxxhdpi.apk!/lib/armeabi-v7a, /system/lib, /vendor/lib]]
        log_tag = " I art     : "
        error_preamble = "Caused by: java.lang.ClassNotFoundException: Didn't find class "
        errors: List[Tuple[int, str]] = self._get_log_messages(self.lines, log_tag, error_preamble)
        return [f"Class Not Found Exceptions {len(errors)} times on lines [{",".join([str(i) for i, line in errors])}] of log."]
    
    def get_lang_verify_errors(self) -> List[str]:
        # 10-15 12:58:58.195 10477 10477 E ACRA    : Caused by: java.lang.VerifyError: Verifier rejected class android.support.v7.widget.RecyclerView$4: void android.support.v7.widget.RecyclerView$4.processPersistent(android.support.v7.widget.RecyclerView$ViewHolder, android.support.v7.widget.RecyclerView$ItemAnimator$ItemHolderInfo, android.support.v7.widget.RecyclerView$ItemAnimator$ItemHolderInfo) failed to verify: void android.support.v7.widget.RecyclerView$4.processPersistent(android.support.v7.widget.RecyclerView$ViewHolder, android.support.v7.widget.RecyclerView$ItemAnimator$ItemHolderInfo, android.support.v7.widget.RecyclerView$ItemAnimator$ItemHolderInfo): [0x4B] register v3 has type Boolean but expected Reference: java.lang.Object (declaration of 'android.support.v7.widget.RecyclerView$4' appears in /data/app/eu.kanade.tachiyomi-1/base.apk)
        log_tag = " E ACRA    : "
        error_preamble = "Caused by: java.lang.VerifyError: Verifier rejected class "
        errors = [f"Verify Error on line {i} in log {self.path}" for i, line in self._get_log_messages(self.lines, log_tag, error_preamble)]
        return errors

    def get_fatal_exception_errors(self) -> List[str]:
        # 10-17 12:02:27.954 23083 23104 E AndroidRuntime: FATAL EXCEPTION: Queue

        log_tag = " E AndroidRuntime: "
        error_preamble = "FATAL EXCEPTION: "
        errors = [f"Fatal Exception on line {i} in log." for i, line in self._get_log_messages(self.lines, log_tag, error_preamble)]
        return errors



    def _get_log_messages(self, lines: str, log_tag: str, message_preamble: str) -> List[Tuple[int, str]]:
        errors = []
        for i, line in enumerate(lines):
            if log_tag + message_preamble in line:
                errors.append((i, line.split(log_tag)[1]))

        return errors

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

def get_observations_from_logcat_batch(logcat_path: str, input_df: pd.DataFrame, output_col="") -> pd.Series:
    assert logcat_path in input_df.columns

    if output_col != "":
        if not output_col in input_df.columns:
            input_df[output_col] = "" # or some other null value? 
        else:
            result_series = pd.Series(index=input_df.index)

    for i in input_df.index:
        result = get_observations_from_logcat_single(input_df.loc[i, logcat_path])
        if output_col != "":
            input_df.loc[i, output_col] = result
        else:
            result_series.loc[i] = result

    if output_col != "":
        return None
    else:
        return result_series
            
    

def get_observations_from_logcat_single(logcat_path: str) -> List[InvocationRegisterContext]:
    log: LogcatLogFileModel = LogcatLogFileModel(logcat_path)

    da_results: List[Tuple] = log.scan_log_for_instrumentation_report_tuples()

    # TODO: move this function to ExecutionObservation. Change clients so they use this end point instead of replicating the functionality.
    # TODO: will need to restrict depth & args analysis either here or in HarnessObservations.
    observation = ExecutionObservation()
    for da_result in da_results:
        observation.parse_instrumentation_result(da_result)
    
    return observation.get_tainting_invocation_contexts()


class ExecutionObservation:
    # Parses all the instrumentation reports hashing related results by invocation_id. 
    # Keeps track of what return/arg registers have been observed to have tainted values before/after the invocation

    # information for a given invocation that was observed to result in tainted values on 1 or more access paths

    def __init__(self) -> None:
        self._observed_invocation_ids: Set[int] = set()

        self.argument_register_tainted_before: Dict[int, Dict[int, bool]] = dict()
        self.argument_register_tainted_after: Dict[int, Dict[int, bool]] = dict()
        self.argument_register_newly_tainted: Dict[int, Dict[int, bool]] = dict()

        self.return_tainted_after: Dict[int, bool] = dict()

        self.argument_access_path_tainted_before: Dict[int, Dict[int, Dict[AccessPath, bool]]] = dict()
        self.argument_access_path_tainted_after: Dict[int, Dict[int, Dict[AccessPath, bool]]] = dict()
        self.argument_access_path_instrumentation_report: Dict[int, Dict[int, Dict[AccessPath, InstrumentationReport]]] = dict()
        self.argument_access_path_newly_tainted: Dict[int, Dict[int, Dict[AccessPath, bool]]] = dict()

        self.return_access_path_tainted_after: Dict[int, Dict[AccessPath, bool]] = dict()
        self.return_access_path_instrumentation_report: Dict[int, Dict[AccessPath, InstrumentationReport]] = dict()

        self.invocation_java_signatures: Dict[int, str] = dict()


    Result = Union[InstrumentationReport, Tuple[InstrumentationReport, AccessPath, str]]
    def parse_instrumentation_result(self, instrumentation_result: Result) -> None:
        # To be called on each instrumentation result from a parsed by a LogcatFileModel. 
        # Keeps track of information to be later queried through other functions.

        if not isinstance(instrumentation_result, InstrumentationReport):
            instrumentation_report, access_path, private_string = instrumentation_result
            invocation_id = instrumentation_report.invoke_id

            self._try_initialize_invocation_id(invocation_id, instrumentation_report)                        

            self._update_register_taints(invocation_id, instrumentation_report)
            self._update_access_path_taints(invocation_id, instrumentation_report, access_path)
        else:
            instrumentation_report = instrumentation_result
            invocation_id: int = instrumentation_report.invoke_id

            self._try_initialize_invocation_id(invocation_id, instrumentation_report)

            self._update_register_taints(invocation_id, instrumentation_report)
    
    def _try_initialize_invocation_id(self, invocation_id: int, instrumentation_report: InstrumentationReport) -> None:
            # If this is the first time seeing a particular invocation_id, initialize the internal dictionaries for that id.
            if invocation_id not in self._observed_invocation_ids:
                self._observed_invocation_ids.add(invocation_id)
                self.invocation_java_signatures[invocation_id] = instrumentation_report.invocation_java_signature

                for dictionary in [self.argument_register_tainted_before, self.argument_register_tainted_after, self.argument_register_newly_tainted]:
                    if invocation_id not in dictionary.keys():
                        dictionary[invocation_id] = dict()
                # For the access_paths too, though they won't be used for plain InstrumentationReports.
                for dictionary in [self.argument_access_path_tainted_before, self.argument_access_path_tainted_after, self.argument_access_path_instrumentation_report, self.argument_access_path_newly_tainted]:
                    if invocation_id not in dictionary.keys():
                        dictionary[invocation_id] = dict()

    def _update_register_taints(self, invocation_id: int, instrumentation_report: InstrumentationReport) -> None:


        # update observation data structures
        if instrumentation_report.is_arg_register:    
            invocation_argument_register_index = instrumentation_report.invocation_argument_register_index

            if instrumentation_report.is_before_invoke:
                self.argument_register_tainted_before[invocation_id][invocation_argument_register_index] = True

            else: # report is from after invoke
                self.argument_register_tainted_after[invocation_id][invocation_argument_register_index] = True

            # If the register not observed to be tainted before, but is observed to be tainted after, then the register is newly tainted.
            # If the register is observed to be tainted before, and is observed to be tainted after, then the register is not newly tainted. 
            # If the register is not observed after, then we don't make conclusions.
            ######################## tainted before |                    | no observation before
            # tainted after        | False          |                    | True
            # no observation after | Blank          |                    | Blank

            # We assume here that all non-blank entries in the before/after dictionary are True.
            if invocation_argument_register_index in self.argument_register_tainted_after[invocation_id].keys():

                if invocation_argument_register_index in self.argument_register_tainted_before[invocation_id].keys():
                    self.argument_register_newly_tainted[invocation_id][invocation_argument_register_index] = False
                else:
                    self.argument_register_newly_tainted[invocation_id][invocation_argument_register_index] = True

        elif instrumentation_report.is_return_register:
            self.return_tainted_after[invocation_id] = True
        else: 
            assert False

    def _update_access_path_taints(self, invocation_id: int, instrumentation_report: InstrumentationReport, access_path: AccessPath) -> None:
        # Similar to _update_register_taints, but extra steps for extra layer of dictionaries

        # update observation data structures
        if instrumentation_report.is_arg_register:
            invocation_argument_register_index = instrumentation_report.invocation_argument_register_index

            if instrumentation_report.is_before_invoke:
                if invocation_argument_register_index not in self.argument_access_path_tainted_before[invocation_id].keys():
                    self.argument_access_path_tainted_before[invocation_id][invocation_argument_register_index] = dict()
                if invocation_argument_register_index not in self.argument_access_path_instrumentation_report[invocation_id].keys():
                    self.argument_access_path_instrumentation_report[invocation_id][invocation_argument_register_index] = dict()

                self.argument_access_path_tainted_before[invocation_id][invocation_argument_register_index][access_path] = True
                # Save off or overwrite instrumentation report for this access path; 
                # don't use before/after invoke info
                self.argument_access_path_instrumentation_report[invocation_id][invocation_argument_register_index][access_path] = instrumentation_report

            else:  # report is from after invoke
                if invocation_argument_register_index not in self.argument_access_path_tainted_after[invocation_id].keys():
                    self.argument_access_path_tainted_after[invocation_id][invocation_argument_register_index] = dict()
                if invocation_argument_register_index not in self.argument_access_path_instrumentation_report[invocation_id].keys():
                    self.argument_access_path_instrumentation_report[invocation_id][invocation_argument_register_index] = dict()

                self.argument_access_path_tainted_after[invocation_id][invocation_argument_register_index][access_path] = True
                self.argument_access_path_instrumentation_report[invocation_id][invocation_argument_register_index][access_path] = instrumentation_report

        elif instrumentation_report.is_return_register:
            for dictionary in [self.return_access_path_tainted_after, self.return_access_path_instrumentation_report]:
                if not invocation_id in dictionary.keys():
                    dictionary[invocation_id] = dict()

            self.return_access_path_tainted_after[invocation_id][access_path] = True
            self.return_access_path_instrumentation_report[invocation_id][access_path] = instrumentation_report
        else: 
            assert False

        
        # Update argument_access_path_newly_tainted
        if instrumentation_report.is_arg_register:
            invocation_argument_register_index = instrumentation_report.invocation_argument_register_index

            if (invocation_argument_register_index in self.argument_access_path_tainted_after[invocation_id].keys()
                and access_path in self.argument_access_path_tainted_after[invocation_id][invocation_argument_register_index].keys()):

                if invocation_argument_register_index not in self.argument_access_path_newly_tainted[invocation_id].keys():
                    self.argument_access_path_newly_tainted[invocation_id][invocation_argument_register_index] = dict()

                self.argument_access_path_newly_tainted[invocation_id][invocation_argument_register_index][access_path] = True

                # if Access path also tainted before
                if (invocation_argument_register_index in self.argument_access_path_tainted_before[invocation_id].keys()
                    and access_path in self.argument_access_path_tainted_before[invocation_id][invocation_argument_register_index].keys()):

                    self.argument_access_path_newly_tainted[invocation_id][invocation_argument_register_index][access_path] = False


    def get_tainting_invocation_ids(self) -> Set[int]:
        # Returns ids for every invocation in which an argument became tainted, or the return was observed to be tainted.

        tainting_invocation_ids = set()

        for invocation_id, value in self.return_tainted_after.items():
            if value:
                tainting_invocation_ids.add(invocation_id)
        
        for invocation_id, arguments in self.argument_register_newly_tainted.items():
            for invocation_argument_register_index, value in arguments.items():
                if value:
                    tainting_invocation_ids.add(invocation_id)
        
        return tainting_invocation_ids
    
    def get_tainting_invocation_contexts(self) -> List[InvocationRegisterContext]:
        # Return True entries in argument_access_path_newly_tainted and return_tainted_after
        register_contexts = []

        for invocation_id, access_path_mapping in self.return_access_path_tainted_after.items():
            for access_path, value in access_path_mapping.items():
                if value:
                    relevent_instrumentation_report = self.return_access_path_instrumentation_report[invocation_id][access_path]
                    register_contexts.append((relevent_instrumentation_report, access_path))


        for invocation_id, arguments in self.argument_access_path_newly_tainted.items():
            for invocation_argument_register_index, access_path_mapping in arguments.items():
                for access_path, value in access_path_mapping.items():
                    if value:
                        relevent_instrumentation_report = self.argument_access_path_instrumentation_report[invocation_id][invocation_argument_register_index][access_path]
                        register_contexts.append((relevent_instrumentation_report, access_path))

        return register_contexts
        
    def signature_from_invocation_id(self, invocation_id) -> str:
        return self.invocation_signatures[invocation_id]



    # class ReturnObservation: -> information for a given function return that saw a tainted value (as in original ConDySTA approach)

    # function signature -> so FD s/s list can be augmented
    # observed private string -> could eventually be mapped to a source function or smthng
    # 
    # could be subclassed into invocation observation vs return observation vs heap observation
    # call stack context -> for condysta type filtering
    # access chain information (a.f.g.h) -> for field sensitive tainting
    # arg vs.return
    #
    # TODO: this should be an intermediate between log processing, and using the info in the static analysis.
    

# TODO: get tests to actually work. Setup a test dir and move them there.
def test_exception_parsing():
    log = LogcatLogFileModel("../data/test-resources/FieldSensitivity3.apk.log")
    exceptions = log.filter_exceptions_by_header(["8901240197155182897"])
    assert len(exceptions) == 1
    assert exceptions[0].lines[
               0] == "04-25 10:44:05.273  7232  7232 W System.err: java.lang.Exception: 8901240197155182897\n"



def test_instr_report_parsing():
    file_path = "data/test-resources/OnlyTelephony.apk.log"

    log_model = LogcatLogFileModel(file_path)

    instr_reports = log_model.scan_log_for_instrumentation_reports()

    print(instr_reports)


if __name__ == '__main__':
    test_instr_report_parsing()
