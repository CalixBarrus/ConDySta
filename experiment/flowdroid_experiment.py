

import os
from subprocess import TimeoutExpired
import time
from typing import Dict, Tuple
import xml.etree.ElementTree as ET
import pandas as pd
from experiment.common import benchmark_df_base_from_batch_input_model, benchmark_df_from_benchmark_directory_path, format_num_secs, logger, results_df_from_benchmark_df, setup_additional_directories, setup_experiment_dir
from hybrid.dynamic import LogcatLogFileModel, LogcatProcessingStrategy, logcat_processing_strategy_factory
from hybrid.flow import Flow, compare_flows
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid_with_fdconfig

from hybrid.hybrid_config import apk_logcat_output_path, source_sink_file_path
from hybrid.log_process_fd import FlowdroidLogException, get_flowdroid_analysis_error, get_flowdroid_flows, get_flowdroid_memory, get_flowdroid_reported_leaks_count
from hybrid.source_sink import SourceSink, SourceSinkSignatures
from util.input import input_apks_from_dir
import util.logger
logger = util.logger.get_logger(__name__)

#### Start External File Paths Settings

def flowdroid_file_paths() -> Dict[str, str]:
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    android_path: str = "/home/calix/.android_sdk/platforms"
    return {
            "flowdroid_jar_path":flowdroid_jar_path,
            "android_path":android_path,
            }

#### End External File Paths Settings

def experiment_setup_and_teardown_temp(experiment_runnable, **kwargs):
    experiment_id, experiment_dir_path, benchmark_df = experiment_setup(**kwargs)

    # passing all relevant kwargs to setup_experiment_dir only works if this runnable only takes stuff produced in setup + kwargs.
    results_df = experiment_runnable(experiment_dir_path, benchmark_df, **kwargs)

    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)

def experiment_setup(**kwargs) -> Tuple[str, str, pd.DataFrame]:
    experiment_name = kwargs["experiment_name"] 
    experiment_description = kwargs["experiment_description"] 
    always_new_experiment_directory = kwargs["always_new_experiment_directory"] 

    ids_subset = kwargs["ids_subset"] 
    benchmark_dir_path: str = kwargs["benchmark_dir_path"]
    benchmark_description_path = (kwargs["benchmark_description_path"] if "benchmark_description_path" in kwargs.keys() else "")

    logger.info(f"Starting experiment {experiment_name}")

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

    benchmark_df = benchmark_df_from_benchmark_directory_path(benchmark_dir_path, benchmark_description_csv_path=benchmark_description_path, ids_subset=ids_subset)

    return experiment_id, experiment_dir_path, benchmark_df



def dysta_experiment(**kwargs):

    def f(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
        source_sink_files = observation_processing_experiment(experiment_dir_path, benchmark_df, **kwargs)

        unmodified_source_sink_results = flowdroid_experiment(experiment_dir_path, benchmark_df, **kwargs)

        benchmark_df["source_sink_path"] = source_sink_files["source_sink_path"]
        augmented_source_sink_results = flowdroid_experiment(experiment_dir_path, benchmark_df, **kwargs)

        return pd.merge(suffix_on_flowdroid_results(unmodified_source_sink_results, " Original Source/Sink"), 
                        suffix_on_flowdroid_results(augmented_source_sink_results, " Augmented Source/Sink"))
    
    experiment_setup_and_teardown_temp(f, **kwargs)


def observation_processing_experiment(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    # could eventually be multiple paths
    logcat_directory_path: str = kwargs["logcat_directory_path"]
    always_new_output_directory = kwargs["always_new_output_directory"] 

    results_df = results_df_from_benchmark_df(benchmark_df)

    logcat_processing_strategy: LogcatProcessingStrategy = logcat_processing_strategy_factory(kwargs["logcat_processing_strategy"])

    source_sink_directory_path: str = setup_additional_directories(experiment_dir_path, ["augmented-source-sinks"], always_new_output_directory)[0]

    source_sink_path_column = "Source Sink Path"
    results_df[source_sink_path_column] = ""

    for i in benchmark_df.index:
        input_model = benchmark_df.loc[i, "Input Model"]

        # grab logcat files that match with the input_model
        # TODO: path function has support for apks that are a part of apk_groups
        possible_logcat_file_path = apk_logcat_output_path(logcat_directory_path, input_model)

        # TODO: this assumes all the inputs in benchmark_df are also present in the indicated logcat directory
        source_sink: SourceSinkSignatures = logcat_processing_strategy.sources_from_log(possible_logcat_file_path)

        results_df.loc[i, "Instrumentation Reports"] = len(LogcatLogFileModel(possible_logcat_file_path).scan_log_for_instrumentation_reports())

        source_sink_file = source_sink_file_path(source_sink_directory_path, input_model)

        source_sink.write_to_file(source_sink_file)

        results_df.loc[i, "Discovered Sources"] = source_sink.source_count()

        results_df.loc[i, source_sink_path_column] = source_sink_file

    return results_df






def flowdroid_experiment(experiment_dir_path: str, benchmark_df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    flowdroid_jar_path: str = kwargs["flowdroid_jar_path"]
    android_path: str = kwargs["android_path"]

    flowdroid_timeout_seconds = kwargs["timeout"] 
    flowdroid_args: FlowdroidArgs = kwargs["flowdroid_args"] 

    source_sink_list_path = kwargs["source_sink_list_path"]

    # TODO: should probably go back and actually add support for this
    ic3_model_column = "ic3_model"
    use_ic3 = ic3_model_column in benchmark_df.columns

    # Check if individual source/sinks will be used
    source_sink_path_column = "Source Sink Path"
    use_individual_source_sinks = source_sink_path_column in benchmark_df.columns
    
    # if "use_model_paths_csv" in kwargs.keys():
    #     icc_model_path_df = pd.read_csv("/home/calix/programming/ConDySta/data/benchmark-descriptions/gpbench-icc-model-paths.csv", header=0, index_col=False)
    #     icc_model_path_df = icc_model_path_df.set_index(icc_model_path_df["AppID"])
    
    # run fd on each app
    flowdroid_logs_directory_path = setup_additional_directories(experiment_dir_path, ["flowdroid-logs"], always_new_directory=True)[0]

    ground_truth_provided = "ground_truth_xml_path" in kwargs.keys
    if ground_truth_provided:
        ground_truth_xml_path = kwargs["ground_truth_xml_path"]
        ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)
    else: 
        ground_truth_flows_df = None

        
    results_df = results_df_from_benchmark_df(benchmark_df)
    
    for i in benchmark_df.index:
        input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore
        

    #     # Run ic3 to get model for app, get file for FD
    #     # it makes an ic3 model, or fails to do so. The resulting path needs to get passed to FD (if this thang is being used)
    #     # These file paths are different, depending on the input. 
    #     # inputs: params for ic3 behavior, specific input model (plus group_id, i guess, though this should only be done once per apk)
    #     # dataframe with columns that will be used
    #     # output: dataframe with the outputs corresponding to the input dataframe
    #     if "use_model_paths_csv" in kwargs.keys() and kwargs["use_model_paths_csv"]:
    #         icc_model_path = icc_model_path_df.loc[input_model.benchmark_id, "ICC Model Path"]
    #         if not os.path.isfile(str(icc_model_path)):
    #             results_df.loc[input_model.benchmark_id, "Error Message"] = "No ICC Model"
    #             continue

    #     elif "ic3_path" in kwargs.keys():
    #         ic3_path = kwargs["ic3_path"]
    #         using_ic3_script = kwargs["using_ic3_script"]
    #         if not using_ic3_script:
    #             ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")
    #             try:
    #                 t0 = time.time()
    #                 icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
                    
    #                 results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
    #             except CalledProcessError as e:
    #                 logger.error("Exception by ic3; details in " + ic3_log_path + " for apk " + input_model.apk().apk_name)
    #                 results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
    #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
    #                 continue
    #             except TimeoutExpired as e:
    #                 logger.error(f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_log_path)
    #                 results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {format_num_secs(ic3_timeout)} "
    #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
    #                 continue
    #             except ValueError as e:
    #                 logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
    #                 continue
    #         else: 
    #             android_jar_path = os.path.join(android_path, f"android-{str(benchmark_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")
    #             try:
    #                 t0 = time.time()
    #                 icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
    #                 results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
    #             except CalledProcessError as e:
    #                 logger.error("Exception by ic3; details in " + ic3_path + " for apk " + input_model.apk().apk_name)
    #                 results_df.loc[i, "Error Message"] = "IC3 Exception"
    #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
    #                 continue
    #             except TimeoutExpired as e:
    #                 msg = f"ic3 timed out after {format_num_secs(ic3_timeout)}; details in " + ic3_path
    #                 logger.error(msg)
    #                 results_df.loc[i, "Error Message"] = msg
    #                 # skip the rest of the experiment; Can't run FD properly without the ICC model
    #                 continue
    #             except ValueError as e:
    #                 msg = f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e)
    #                 logger.error(msg)
    #                 results_df.loc[i, "Error Message"] += msg # type: ignore
    #                 continue
    #     else: 
    #         # ic3_path is ""
    #         icc_model_path = ""
    #         pass

        output_log_path = os.path.join(flowdroid_logs_directory_path, input_model.input_identifier() + ".log")
        # # debug
        # flowdroid_args.set_arg("outputfile", os.path.join(fd_xml_output_dir_path, input_model.input_identifier() + ".xml"))
        # # end debug
        

        try:
            t0 = time.time()
            run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, source_sink_list_path, flowdroid_args, output_log_path, flowdroid_timeout_seconds)
            time_elapsed_seconds = time.time() - t0
        except TimeoutExpired as e:
            msg = f"Flowdroid timed out after {format_num_secs(flowdroid_timeout_seconds)} on apk {input_model.apk().apk_name}; details in " + output_log_path
            logger.error(msg)
            results_df.loc[i, "Error Message"] += msg
            continue

        process_results_from_fd_log_single(results_df, i, time_elapsed_seconds, output_log_path, apk_path=input_model.apk().apk_path, ground_truth_flows_df=ground_truth_flows_df)

        # # debug
        # ground_truth_flows_df.to_csv(os.path.join(experiment_dir_path, "groundtruth_df.csv"))
        # # end debug
    return results_df
    # results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    # results_df.to_csv(results_df_path)


def process_results_from_fd_log_single(results_df: pd.DataFrame, i: int, time_elapsed_seconds: int, output_log_path, apk_path, ground_truth_flows_df=None):



    if "Time Elapsed" not in results_df.columns:
        results_df["Time Elapsed"] = ""
    results_df.loc[i, "Time Elapsed"] = format_num_secs(time_elapsed_seconds)

    if "Max Reported Memory Usage" not in results_df.columns:
        results_df["Max Reported Memory Usage"] = ""
    results_df.loc[i, "Max Reported Memory Usage"] = get_flowdroid_memory(output_log_path)

    analysis_error = get_flowdroid_analysis_error(output_log_path)
    if analysis_error != "":
        results_df.loc[i, "Error Message"] += analysis_error # type: ignore
        logger.error(analysis_error)

    if "Reported Flowdroid Flows" not in results_df.columns:
        results_df["Reported Flowdroid Flows"] = ""
    try:
        reported_num_leaks = get_flowdroid_reported_leaks_count(output_log_path)
    except FlowdroidLogException as e:
        logger.error(e.msg)
        results_df.loc[i, "Error Message"] += e.msg # type: ignore
        return

    if reported_num_leaks is None:
        msg = "Flowdroid Irregularity, review log at " + output_log_path
        results_df.loc[i, "Error Message"] += msg
        logger.error(msg)
        return

    results_df.loc[i, "Reported Flowdroid Flows"] = reported_num_leaks

    if ground_truth_flows_df is None:
        return

    for col in ["TP", "FP", "TN", "FN", "Flows Not Evaluated"]:
        if col not in results_df.columns:
            results_df[col] = ""

    detected_flows = get_flowdroid_flows(output_log_path, apk_path)

    # deduplicate FD flows
    original_length = len(detected_flows)
    detected_flows = list(set(detected_flows))
    if len(detected_flows) != original_length:
        logger.warn(f"Flowdroid reported {original_length - len(detected_flows)} duplicate flows for app {results_df.loc[i, 'APK Name']}")

    tp, fp, tn, fn, inconclusive = compare_flows(detected_flows, ground_truth_flows_df, results_df.loc[i, 'APK Name'])

    results_df.loc[i, "TP"] = tp
    results_df.loc[i, "FP"] = fp
    results_df.loc[i, "TN"] = tn
    results_df.loc[i, "FN"] = fn
    results_df.loc[i, "Flows Not Evaluated"] = inconclusive

def suffix_on_flowdroid_results(results_df: pd.DataFrame, suffix) -> pd.DataFrame:
    cols_to_skip = ["Benchmark ID", "APK Name"]

    f = lambda column_name: (column_name if column_name in cols_to_skip else column_name + suffix)    

    new_results_df = results_df.rename(columns=f)
    # Experiments expect an "Error Message" column with an empty string.
    new_results_df["Error Message"] = ""
    return new_results_df

def groundtruth_df_from_xml(benchmark_df: pd.DataFrame, ground_truth_xml_path):
    tree = ET.parse(ground_truth_xml_path)
    ground_truth_root = tree.getroot()

    # assert ["Benchmark ID", "Input Model"] in benchmark_df.columns

    flow_elements = ground_truth_root.findall("flow")
    # df columns -> Flow, APK Name, APK Path, Source Signature, Sink Signature, Ground Truth Value
    flows = [Flow(element) for element in flow_elements]
    flows.sort()

    groundtruth_df = pd.DataFrame({"Flow": flows})
    # Index is set to the list index of flows
    groundtruth_df["APK Name"] = ""
    groundtruth_df["Benchmark ID"] = ""
    groundtruth_df["Source Signature"] = ""
    groundtruth_df["Sink Signature"] = ""
    groundtruth_df["Ground Truth Value"] = ""

    for i in groundtruth_df.index:
        flow: Flow = groundtruth_df.loc[i, "Flow"] # type: ignore
        groundtruth_df.loc[i, "APK Name"] = flow.get_file()

        # Match up the flow with the corresponding Benchmark ID
        mask = benchmark_df["Input Model"].apply(lambda model: model.apk().apk_name).values == groundtruth_df.loc[i, "APK Name"]

        assert sum(mask) <= 1
        if sum(mask) == 1:
            groundtruth_df.loc[i, "Benchmark ID"] = benchmark_df[mask]["Benchmark ID"].iloc[0]

            groundtruth_df.loc[i, "Source Signature"] = flow.get_source_statementgeneric()
            groundtruth_df.loc[i, "Sink Signature"] = flow.get_sink_statementgeneric()
            groundtruth_df.loc[i, "Ground Truth Value"] = flow.get_ground_truth_attribute()
        else:
            groundtruth_df.loc[i, "Benchmark ID"] = -1
    # Strip out ground truth flows not relevant to the apps in the benchmark_df
    groundtruth_df = groundtruth_df[groundtruth_df["Benchmark ID"] != -1]

    return groundtruth_df




