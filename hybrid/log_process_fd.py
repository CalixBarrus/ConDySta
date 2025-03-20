import os
import re
from typing import List, Tuple
import xml.etree.ElementTree as ET

from experiment.common import format_num_secs
from hybrid.flow import Flow, create_flows_elements
from util import logger
import util.logger
logger = util.logger.get_logger(__name__)

def get_flowdroid_reported_leaks_count(flowdroid_log_path: str) -> int:
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
                reported_leaks_count = int(re.search(r"Found (\d+) leaks", line).group(1))
                return reported_leaks_count

    logger.error(f"Flowdroid did not execute as expected in log file"
            f" {flowdroid_log_path}")
    return None

def get_flowdroid_flows(flowdroid_log_path: str, apk_path: str) -> List[Flow]:
    # flowdroid_log_path: Path to flowdroid log file
    # apk_path: Used so a reference (part of a flow) can indicate what APK it's from. For now, only the basename of the path is used.
    # 
    # Throws FlowdroidLogException if file doesn't exist, or if for whatever reason flowdroid didn't exit normally. 


    """
    Expecting log to contain section like 

[main] INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - The sink staticinvoke <android.util.Log: int i(java.lang.String,java.lang.String)>("DroidBench", $r3) in method <edu.mit.icc_componentname_class_constant.IsolateActivity: void onCreate(android.os.Bundle)> was called with values from the following sources:
[main] INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - - $r5 = virtualinvoke $r4.<android.telephony.TelephonyManager: java.lang.String getDeviceId()>() in method <edu.mit.icc_componentname_class_constant.OutFlowActivity: void onCreate(android.os.Bundle)>
...
[main] INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - Data flow solver took 19 seconds. Maximum memory consumption: 25 MB
[main] INFO soot.jimple.infoflow.android.SetupApplication - Found 3 leaks
    """

    if not os.path.isfile(flowdroid_log_path):
        logger.error(f"Flowdroid did not execute; log file"
                        f" {flowdroid_log_path} does not exist.")
        raise FlowdroidLogException(f"Flowdroid did not execute; log file"
                        f" {flowdroid_log_path} does not exist.")



    flows = []

    with open(flowdroid_log_path, 'r') as file:
        lines = file.readlines()

        # Check if flowdroid finished executing correctly by looking for a line like this: 
        """
[main] INFO soot.jimple.infoflow.android.SetupApplication - Found 1 leaks
        """
        flowdroid_finished = False
        for line in lines:
            if " - Found " in line:
                flowdroid_finished = True
        if not flowdroid_finished:
            raise FlowdroidLogException(f"Flowdroid did not execute succesfully, please see log file at {flowdroid_log_path}.")

        flows = []
        for i, line in enumerate(lines):
            if " was called with values from the following sources:" in line:
                match = re.search(r" - The sink (.+) in method (<(.+): .+>) was called with values from the following sources:", line)
                sink_statement_full = match.group(1)
                sink_method = match.group(2)
                sink_class_name = match.group(3)

                # Check following lines for one or more sources
                source_tuples = []
                for j in range(i+1, len(lines)):
                    possible_source_line = lines[j]
                    match = re.search(r"- - (.+) in method (<(.+): .+>)", possible_source_line)
                    if match is None:
                        break
                    source_statement_full = match.group(1)
                    source_method = match.group(2)
                    source_class_name = match.group(3)

                    source_tuples.append((source_statement_full, source_method, source_class_name))

                flows += create_flows_elements(sink_statement_full, sink_method, sink_class_name, source_tuples, apk_path)

    return flows


def get_flowdroid_analysis_error(flowdroid_log_path: str) -> str:
    """
    Flowdroid errors often include an entry such as 
[main] ERROR soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - Exception during data flow analysis
java.lang.RuntimeException: There were exceptions during IFDS analysis. Exiting.
...
Caused by: java.lang.ClassCastException: soot.IntType cannot be cast to soot.ArrayType

    where the specific error that cause the failure is this first "Caused by: " line. 
    """
    with open(flowdroid_log_path, 'r') as file:
        lines = file.readlines()
        for i, line in enumerate(lines):
            if "java.lang.RuntimeException: There were exceptions during IFDS analysis. Exiting.\n" == line:
                # Scan the following lines for the next "Caused by: " line
                for j in range(i+1, len(lines)):
                    if "Caused by: " in lines[j]:
                        return f"Exception during Flowdroid {lines[j].strip()}"

    return ""

def get_flowdroid_memory(flowdroid_log_path: str) -> str:
    """
    Lines look like:
    memory consumption: 216 MB
    These show up multiple times. Find them all, and return the max. (usually reported right before a cleanup).

    Returns highest reported memory consumption as a string
    """
    with open(flowdroid_log_path, 'r') as file:
        lines = file.readlines()

        reported_mem = []
        for line in lines:
            if "memory consumption" in line:
                pattern = r": (\d+) MB"
                reported_mem.append(int(re.search(pattern, line).group(1)))
        
        if len(reported_mem) == 0:
            return ""
        else: 
            return f"{max(reported_mem)} MB"

                
def get_count_found_sources(flowdroid_log_path: str) -> List[int]:
    """
    Were the source/sinks loaded from the source/sink list correctly?

    Were source/sinks found in the code? 
    """

    """ Example:
[main] INFO soot.jimple.infoflow.android.source.AccessPathBasedSourceSinkManager - Created a SourceSinkManager with 1 sources, 11 sinks, and 302 callback methods.

[main] INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - Looking for sources and sinks...
[main] ERROR soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - No sources found, aborting analysis
or 
[main] INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - Source lookup done, found 98 sources and 2 sinks.
    """
    with open(flowdroid_log_path, 'r') as file:
        lines = file.readlines()

        # messages = _get_log_messages(lines, "", "Created a SourceSinkManager with ")
        # if len(messages) > 0:
        #     count_loaded_sources = ""
        #     count_loaded_sinks = ""
        #     pass

        count_found_sources = 0
        count_found_sinks = 0

        messages = _get_log_messages(lines, "ERROR soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - ", "No sources found, aborting analysis")
        if len(messages) > 0:
            count_found_sources = 0
            count_found_sinks = 0

        messages = _get_log_messages(lines, "INFO soot.jimple.infoflow.android.SetupApplication$InPlaceInfoflow - ", "Source lookup done, found ")
        if len(messages) > 0:
            matches = re.findall(r"Source lookup done, found (\d+) sources and (\d+) sinks.", messages[0][1])
            count_found_sources, count_found_sinks = matches[0]


    # return count_loaded_sources, count_loaded_sinks, count_found_sources, count_found_sinks
    return int(count_found_sources), int(count_found_sinks)



def _get_log_messages(lines: str, log_tag: str, message_preamble: str) -> List[Tuple[int, str]]:
    messages = []
    for i, line in enumerate(lines):
        if log_tag + message_preamble in line:
            messages.append((i, line.split(log_tag)[1]))

    return messages

def flowdroid_time_path_from_log_path(flowdroid_log_path: str) -> str:
    return flowdroid_log_path.replace(".log", ".time")

def get_flowdroid_time(flowdroid_time_path: str) -> str:
    with open(flowdroid_time_path, 'r') as file:
        return format_num_secs(int(file.read().strip()))

class FlowdroidLogException(Exception):
    msg: str
    def __init__(self, msg):
        self.msg = msg