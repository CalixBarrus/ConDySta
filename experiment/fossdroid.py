import os
from subprocess import TimeoutExpired
import time
from typing import Dict, List
import typing
import xml.etree.ElementTree as ET

import pandas as pd

from experiment.common import format_num_secs, setup_dirs_with_dependency_info
from hybrid.flow import Flow
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig
from hybrid.log_process_fd import FlowdroidLogException, get_reported_num_leaks_in_flowdroid_log, get_analysis_error_in_flowdroid_log, get_flowdroid_memory, get_flows_in_flowdroid_log
from hybrid.source_sink import format_source_sink_signatures
from util import logger
from util.input import BatchInputModel, InputModel, find_apk_paths_in_dir_recursive, input_apks_from_dir
logger = logger.get_logger_revised(__name__)

def fossdroid_main():
    # File names only in this layer

    # flowdroid_jar_path = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_jar_path = "/home/calix/programming/flowdroid-jars/fossdroid-vm/soot-infoflow-cmd-jar-with-dependencies.jar"
    android_platforms_dir_path = "/usr/lib/android-sdk/platforms"
    fossdroid_benchmark_dir_path = "/home/calix/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks"
    fossdroid_ground_truth_xml_path = "/home/calix/programming/benchmarks/wild-apps/fossdroid_ground_truth.xml"

    # This rewrites the source sink list
    source_sink_list_from_df(df_from_groundtruth_xmls(fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path), get_fossdroid_source_sink_list_path())

    single_fossdroid_experiment(flowdroid_jar_path=flowdroid_jar_path, android_path=android_platforms_dir_path, fossdroid_dir_path=fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path=fossdroid_ground_truth_xml_path)

def single_fossdroid_experiment(**file_paths):
    experiment_args = fossdroid_experiment_setup_misc(**file_paths)
    # experiment_args = fossdroid_experiment_setup_default_fd_full(**file_paths)
    
    fossdroid_experiment_generic(**experiment_args)

def fossdroid_experiment_setup_base(**file_paths) -> Dict[str, typing.Any]:
    # No file names in this layer, but I want this function to eventually allow wierd automation of tweaking some experiment args. (test experiments, run different FD versions/SS lists in serial, etc.)
    # This should NOT be called by fossdroid_main, rather right some functions to handle these
    assert list(file_paths.keys()) == ["flowdroid_jar_path", "android_path", "fossdroid_dir_path", "fossdroid_ground_truth_xml_path"]
    
    experiment_args = file_paths.copy()
    # experiment_name = "fd-on-fossdroid-best-fdmini2"
    # experiment_args["experiment_name"] = experiment_name

    timeout = 1 * 60
    # timeout = 15 * 60
    # timeout = 2 * 60 * 60
    experiment_args["timeout"] = timeout


    ids_subset = pd.Series([0,1])
    # ids_subset = None
    experiment_args["ids_subset"] = ids_subset

    flowdroid_args = FlowdroidArgs(**FlowdroidArgs.default_settings)
    # flowdroid_args = FlowdroidArgs.best_fossdroid_settings
    experiment_args["flowdroid_args"] = flowdroid_args

    experiment_args["always_new_experiment_directory"] = False

    return experiment_args

def fossdroid_experiment_setup_misc(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([27])
    experiment_args["experiment_name"] = "fd-on-fossdroid-temp"
    experiment_args["experiment_description"] = ""
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["always_new_experiment_directory"] = False
    return experiment_args

def fossdroid_experiment_setup_test(**file_paths):
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    experiment_args["experiment_name"] = "fd-on-fossdroid-test"
    experiment_args["experiment_description"] = """
Integration test on a handful of apps.
"""

    experiment_args["ids_subset"] = pd.Series([0,1])

    experiment_args["timeout"] = 1 * 60
    return experiment_args

def fossdroid_experiment_setup_best_fd_longtimeout(**file_paths):
    pass
def fossdroid_experiment_setup_default_fd_full(**file_paths):
    experiment_args = fossdroid_experiment_setup_base(**file_paths)
    # experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = None
    experiment_args["experiment_name"] = "fd-on-fossdroid-default-fd-short-timeout"
    experiment_args["experiment_description"] = "Run FlowDroid on the full Fossdroid dataset with default FD settings"
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.default_settings)
    experiment_args["always_new_experiment_directory"] = True
    return experiment_args


def fossdroid_experiment_setup_best_fd_full(**file_paths):
    pass

def fossdroid_experiment_setup(**file_paths) -> Dict[str, typing.Any]:
    # No file names in this layer, but I want this function to eventually allow wierd automation of tweaking some experiment args. (test experiments, run different FD versions/SS lists in serial, etc.)
    assert file_paths.keys == ["flowdroid_jar_path", "android_path", "fossdroid_dir_path", "fossdroid_ground_truth_xml_path"]
    
    experiment_args = file_paths.copy()
    experiment_name = "fd-on-fossdroid-best-fdmini2"
    experiment_args["experiment_name"] = experiment_name

    # flowdroid_args = FlowdroidArgs.default_settings
    flowdroid_args = FlowdroidArgs.best_fossdroid_settings

    timeout = 1 * 60
    # timeout = 15 * 60
    # timeout = 2 * 60 * 60
    experiment_args["timeout"] = timeout


    ids_subset = pd.Series([0,1])
    # ids_subset = None
    experiment_args["ids_subset"] = ids_subset

    experiment_description = f"""
Run Flowdroid on FossDroid apps. 

Timeout: {format_num_secs(timeout)}
Flowdroid run with the following args: {str(flowdroid_args)}
"""
    flowdroid_args = FlowdroidArgs(**flowdroid_args)
    experiment_args["experiment_description"] = experiment_description    
    experiment_args["flowdroid_args"] = flowdroid_args

    return experiment_args


    
# def fossdroid_experiment(flowdroid_jar_path: str, android_path: str, fossdroid_dir_path: str, fossdroid_ground_truth_xml_path: str, default_fd_config: bool=False, best_fossdroid_fd_config: bool=False):
def fossdroid_experiment_generic(**kwargs):
    flowdroid_jar_path = kwargs["flowdroid_jar_path"]
    android_path = kwargs["android_path"]
    fossdroid_dir_path = kwargs["fossdroid_dir_path"]
    fossdroid_ground_truth_xml_path = kwargs["fossdroid_ground_truth_xml_path"]
    timeout = kwargs["timeout"]
    ids_subset = kwargs["ids_subset"]
    experiment_name = kwargs["experiment_name"]
    experiment_description = kwargs["experiment_description"]
    flowdroid_args = kwargs["flowdroid_args"]
    always_new_experiment_directory = kwargs["always_new_experiment_directory"]
    
    # Things below here don't need tweaking between experiments???

    dir_names = ["flowdroid-logs"]
    result_df_path, dir_paths = setup_dirs_with_dependency_info(experiment_name, experiment_description, dir_names, kwargs, always_new_experiment_directory)
    flowdroid_logs_dir_path = dir_paths[0]

    source_sink_list_path = get_fossdroid_source_sink_list_path()

    
    ground_truth_flows_df = df_from_groundtruth_xmls(fossdroid_dir_path, fossdroid_ground_truth_xml_path)

    # TODO: This isn't a general way at all to setup the results_df/apps_df
    inputs_model: BatchInputModel = input_apks_from_dir(fossdroid_dir_path)
    # For benchmark/app 'id's, take the apps alphabetically from the directory 
    apk_names = os.listdir(fossdroid_dir_path)
    apk_names.sort()
    apps_df = pd.DataFrame({
                    "Benchmark ID": [""]*len(apk_names),
                    "Input Model": [""]*len(apk_names),
                    "APK Name": [""]*len(apk_names), 
                    "APK Path": [""]*len(apk_names), 
                    "Reported Flowdroid Flows": [""]*len(apk_names),
                    "TP": [""]*len(apk_names), 
                    "FP": [""]*len(apk_names), 
                    "TN": [""]*len(apk_names), 
                    "FN": [""]*len(apk_names), 
                    "Flows Not Evaluated": [""]*len(apk_names), 
                    "Time Elapsed": [""]*len(apk_names), 
                    "Max Reported Memory Usage": [""]*len(apk_names), 
                    "Error Message": [""]*len(apk_names), 
                    })
                    
    for i, apk_name in enumerate(apk_names):
        matching_input_model: InputModel = next((input_model for input_model in inputs_model.ungrouped_inputs if input_model.apk().apk_name == apk_name), None)
        assert matching_input_model is not None
        matching_input_model.benchmark_id = i

        apps_df.loc[i, 'Benchmark ID'] = i
        apps_df.loc[i, 'Input Model'] = matching_input_model
        apps_df.loc[i, 'APK Name'] = matching_input_model.apk().apk_name
        apps_df.loc[i, 'APK Path'] = matching_input_model.apk().apk_path
    
    if ids_subset is not None:
        apps_df = apps_df.iloc[ids_subset]

    for i in apps_df.index:
        output_log_path = os.path.join(flowdroid_logs_dir_path, apps_df.loc[i, 'Input Model'].input_identifier() + ".log")

        # TODO: do i need to pass specific android paths, or just the android platforms dir?
        try: 
            t0 = time.time()
            run_flowdroid_with_fdconfig(flowdroid_jar_path, apps_df.loc[i, 'APK Path'], android_path, source_sink_list_path, flowdroid_args, output_log_path, timeout)
            time_elapsed = time.time() - t0
        except TimeoutExpired as e:
            msg = f"Flowdroid timed out after {format_num_secs(timeout)} on apk {apps_df.loc[i, 'APK Name']}; details in " + output_log_path
            logger.error(msg)
            apps_df.loc[i, "Error Message"] += msg
            continue

        apps_df.loc[i, "Time Elapsed"] = format_num_secs(time_elapsed)

        apps_df.loc[i, "Max Reported Memory Usage"] = get_flowdroid_memory(output_log_path)
        analysis_error = get_analysis_error_in_flowdroid_log(output_log_path)
        if analysis_error != "":
            apps_df.loc[i, "Error Message"] += analysis_error
            logger.error(analysis_error)

        try: 
            reported_num_leaks = get_reported_num_leaks_in_flowdroid_log(output_log_path)
            detected_flows = get_flows_in_flowdroid_log(output_log_path, apps_df.loc[i, 'APK Path'])

        except FlowdroidLogException as e:
            logger.error(e.msg)
            apps_df.loc[i, "Error Message"] = e.msg
            # raise e
            continue

        apps_df.loc[i, "Reported Flowdroid Flows"] = reported_num_leaks

        # deduplicate FD flows
        original_length = len(detected_flows)
        detected_flows = list(set(detected_flows))
        if len(detected_flows) != original_length:
            logger.warn(f"Flowdroid reported {original_length - len(detected_flows)} duplicate flows for app {apps_df.loc[i, 'APK Name']}")

        tp, fp, tn, fn, inconclusive = compare_flows(detected_flows, ground_truth_flows_df, apps_df.loc[i, 'APK Name'])

        apps_df.loc[i, "TP"] = tp
        apps_df.loc[i, "FP"] = fp
        apps_df.loc[i, "TN"] = tn
        apps_df.loc[i, "FN"] = fn
        apps_df.loc[i, "Flows Not Evaluated"] = inconclusive

    # Save the results
    cols = ["Benchmark ID","Input Model","APK Name","APK Path","TP","FP","TN","FN","Flows Not Evaluated","Time Elapsed","Max Reported Memory Usage","Error Message"]
    cols = ["Benchmark ID","APK Name","TP","FP","TN","FN","Flows Not Evaluated","Time Elapsed","Max Reported Memory Usage","Error Message"]
    apps_df[cols].to_csv(result_df_path)



def get_fossdroid_source_sink_list_path() -> str:
    project_root = os.path.dirname(os.path.dirname(__file__)) # Go back a directory
    return os.path.join(project_root, "data", "sources-and-sinks", "SS-from-fossdroid-ground-truth.txt")

def compare_flows(detected_flows: List[Flow], ground_truth_flows_df: pd.DataFrame, apk_name: str) -> List[int]:
    apk_name_mask = ground_truth_flows_df['APK Name'] == apk_name
    
    # Keep track of specific flows since I'll probably need to look at them specifically later.
    tp_flows = []
    fp_flows = []
    # Flows not in ground truth, or annotated in ground truth as UNKNOWN or MISMATCH
    inconclusive_flows = []

    tn_flows = []
    fn_flows = []
    has_flow_been_detected = pd.Series([False] * len(ground_truth_flows_df[apk_name_mask]), index=ground_truth_flows_df[apk_name_mask].index)
    for detected_flow in detected_flows:
        # does it match a ground truth flow?
        detected_flow_mask = ground_truth_flows_df[apk_name_mask]['Flow'] == detected_flow
        if sum(detected_flow_mask) == 0:
            # Flow is not in ground_truth
            inconclusive_flows.append(detected_flow)
        elif sum(detected_flow_mask) == 1:
            detected_flow_row = ground_truth_flows_df[apk_name_mask][detected_flow_mask].iloc[0]
            has_flow_been_detected[detected_flow_row.name] = True #TODO test to see if name actually pulls the index of the row
            ground_truth_value = detected_flow_row['Ground Truth Value']
            if ground_truth_value == "TRUE":
                tp_flows.append(detected_flow)
            elif ground_truth_value == "FALSE": 
                fp_flows.append(detected_flow)
            else: 
                # Value must have been UNKNOWN or MISMATCH or NATIVE
                inconclusive_flows.append(detected_flow)
        else: 
            raise AssertionError("Detected flow is not expected to match with more than 1 ground truth flow.")

    # count the known flows that were not hit to get TN/FN, Unknown Negative
    for i in has_flow_been_detected[has_flow_been_detected == False].index:
        # These flows were NOT hit, so if ground truth is FALSE -> true negative, and vice versa
        if ground_truth_flows_df.loc[i, 'Ground Truth Value'] == 'FALSE':
            tn_flows.append(ground_truth_flows_df.loc[i, 'Flow'])
        elif ground_truth_flows_df.loc[i, 'Ground Truth Value'] == 'TRUE':
            fn_flows.append(ground_truth_flows_df.loc[i, 'Flow'])
        else: 
            # We don't really care if uncategorized flows are detected or not.
            pass


    # Debug
    ground_truth_flows_df[apk_name_mask].to_csv(os.path.join("/home/calix/programming/ConDySta/data/temp", "app_flows.csv"))

    # tree = ET.ElementTree(inconclusive_flows[0].element)
    # ET.indent(tree) # Pretty print the result, requires python 3.9
    # tree.write(os.path.join("/home/calix/programming/ConDySta/data/temp", "detected_leak.xml"))
    for flow in inconclusive_flows:
        logger.debug(str(flow))
        

    # element = inconclusive_flows[0].element
    # references = element.findall("reference")
    # logger.debug(references)
    # source = [r for r in references if r.get("type") == "to"][0]
    # logger.debug(source)
    # for child in source:
    #     logger.debug(child)
    #     logger.debug(child.text)
    #     logger.debug(len(child))
    # logger.debug(source.find("statement").find("statementgeneric").text)
    
    # End Debug

    return len(tp_flows), len(fp_flows), len(tn_flows), len(fn_flows), len(inconclusive_flows)

def df_from_groundtruth_xmls(fossdroid_benchmark_dir_path, fossdroid_ground_truth_xml_path):

    tree = ET.parse(fossdroid_ground_truth_xml_path)
    fossdroid_ground_truth_root = tree.getroot() 
    
    apk_paths = find_apk_paths_in_dir_recursive(fossdroid_benchmark_dir_path)

    flow_elements = fossdroid_ground_truth_root.findall("flow")
    # df columns -> Flow, APK Name, APK Path, Source Signature, Sink Signature, Ground Truth Value
    # for gpBench, will want API level too
    df = pd.DataFrame({'Flow': [""]*len(flow_elements), 
                       "APK Name": [""]*len(flow_elements), 
                       "APK Path": [""]*len(flow_elements), 
                       "Source Signature": [""]*len(flow_elements), 
                       "Sink Signature": [""]*len(flow_elements), 
                       "Ground Truth Value": [""]*len(flow_elements), })
    
    flows = [Flow(element) for element in flow_elements]
    flows.sort()

    for i, flow in enumerate(flows):
        df.loc[i, "Flow"] = flow
        df.loc[i, "APK Name"] = flow.get_file()

        apk_path = ""
        for path in apk_paths:
            if os.path.basename(path) == flow.get_file():
                apk_path = path
                break
        assert apk_path != ""
        df.loc[i, "APK Path"] = apk_path

        df.loc[i, "Source Signature"] = flow.get_source_statementgeneric()
        df.loc[i, "Sink Signature"] = flow.get_sink_statementgeneric()
        df.loc[i, "Ground Truth Value"] = flow.get_ground_truth_attribute()

    return df

def source_sink_list_from_df(df, output_file):
    # df["Source Signature"].unique().list()

    source_sink_list = format_source_sink_signatures(df["Source Signature"].unique().tolist(), df["Sink Signature"].unique().tolist())

    with open(output_file, 'w') as file:
        file.write(source_sink_list)

