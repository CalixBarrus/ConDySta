import os
import re
from typing import List
import xml.etree.ElementTree as ET

from hybrid.flow import Flow, create_flows_elements
from util import logger
import util.logger
logger = util.logger.get_logger(__name__)

def get_reported_num_leaks_in_flowdroid_log(flowdroid_log_path: str) -> int:
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
                num_leaks = int(re.search(r"Found (\d+) leaks", line).group(1))
                return num_leaks

    logger.error(f"Flowdroid did not execute as expected in log file"
            f" {flowdroid_log_path}")
    return None

def get_flows_in_flowdroid_log(flowdroid_log_path: str, apk_path: str) -> List[Flow]:

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


def get_analysis_error_in_flowdroid_log(flowdroid_log_path: str) -> str:
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
    These show up multiple times. Find them all, and return the max. (usually reported right before a cleanup). Note there 

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

                



class FlowdroidLogException(Exception):
    msg: str
    def __init__(self, msg):
        self.msg = msg