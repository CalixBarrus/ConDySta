
import os
from subprocess import CalledProcessError, TimeoutExpired
import time
from typing import Dict, List
import typing

import numpy as np

from experiment.common import benchmark_df_base_from_batch_input_model, format_num_secs, groundtruth_df_from_xml, process_results_from_fd_log_single, results_df_from_benchmark_df, setup_additional_directories, setup_dirs_with_ic3, setup_experiment_dir
import hybrid
from hybrid.flowdroid import FlowdroidArgs, run_flowdroid, run_flowdroid_help, run_flowdroid_paper_settings, run_flowdroid_with_fdconfig
from hybrid.ic3 import run_ic3_on_apk, run_ic3_script_on_apk
from hybrid.log_process_fd import get_reported_num_leaks_in_flowdroid_log
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import format_source_sink_signatures
from util.input import BatchInputModel, InputModel, input_apks_from_dir
from util.subprocess import run_command_direct

import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)

def gpbench_main():
    # benchmark_folder_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/gpbench/apks"
    benchmark_folder_path: str = "/home/calix/programming/benchmarks/wild-apps/data/gpbench/apks"

    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    # flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"

    # android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    android_path: str = "/home/calix/.android_sdk/platforms"
    

    gpbench_dir_path: str = "/home/calix/programming/benchmarks/ggplay/apks"

    # ic3_jar_path = "/home/calix/programming/ic3/target/ic3-0.2.1-full.jar"
    # ic3_jar_path: str = "/home/calix/programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"

    ic3_script_root_path: str = "/home/calix/programming/IC3"

    ground_truth_xml_path = "/home/calix/programming/benchmarks/wild-apps/gpbench_ground_truth.xml"
    gpbench_description_path = "data/benchmark-descriptions/gpbench-info.csv"

    # single_gpbench_experiment(flowdroid_jar_path=flowdroid_jar_path, android_path=android_path, gpbench_dir_path=benchmark_folder_path, ground_truth_xml_path=ground_truth_xml_path, gpbench_description_path=gpbench_description_path)
    gbpench_experiment_1hr_fd_configs(flowdroid_jar_path=flowdroid_jar_path, android_path=android_path, gpbench_dir_path=benchmark_folder_path, ground_truth_xml_path=ground_truth_xml_path, gpbench_description_path=gpbench_description_path)
    # flowdroid_on_gpbench_full(flowdroid_jar_path, android_path, gpbench_dir_path, ic3_path="", use_model_paths_csv=False, using_ic3_script=False, app_ids=range(1,20))


def single_gpbench_experiment(**file_paths):
    # experiment_args = gpbench_experiment_full_short_timeout(**file_paths)
    experiment_args = gpbench_experiment_setup_test(**file_paths)
    # experiment_args = gpbench_experiment_full_long_timeout(**file_paths)
    
    gpbench_experiment_generic(**experiment_args)


def gbpench_experiment_1hr_fd_configs(**file_paths):

    for name_suffix, settings_description_suffix, fd_settings in [("default", "default FD settings", FlowdroidArgs.default_settings), 
                                                           ("modified-zhang-settings", "modified settings from gpbench study", FlowdroidArgs.gpbench_experiment_settings_modified), 
                                                           ("best-mordahl-settings", "best settings from Mordahl study's droidbench trial", FlowdroidArgs.best_fossdroid_settings)]:
        
        experiment_args = gpbench_experiment_full_long_timeout(**file_paths)
        experiment_args["flowdroid_args"] = FlowdroidArgs(**fd_settings)
        experiment_args["experiment_name"] = f"fd-on-fossdroid-{name_suffix}"
        experiment_args["experiment_description"] = f"Run FlowDroid on the full Fossdroid dataset with {settings_description_suffix}"
        experiment_args["timeout"] = 60 * 60 * 60
        gpbench_experiment_generic(**experiment_args)

def gpbench_experiment_setup_base(**file_paths) -> Dict[str, typing.Any]:
    # assert list(file_paths.keys()) == ["flowdroid_jar_path", "android_path", "fossdroid_dir_path", "fossdroid_ground_truth_xml_path"]
    
    experiment_args = file_paths.copy()

    timeout = 1 * 60
    experiment_args["timeout"] = timeout

    ids_subset = pd.Series([0,1])
    experiment_args["ids_subset"] = ids_subset

    flowdroid_args = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified) 
    # flowdroid_args = FlowdroidArgs.best_fossdroid_settings
    experiment_args["flowdroid_args"] = flowdroid_args

    experiment_args["always_new_experiment_directory"] = False

    return experiment_args

def gpbench_experiment_setup_test(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = gpbench_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 1 * 60
    experiment_args["ids_subset"] = pd.Series([0, 1])
    experiment_args["experiment_name"] = "fd-on-gpbench-test"
    experiment_args["experiment_description"] = "Run Flowdroid on a few Google Play Bench apps"
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
    experiment_args["always_new_experiment_directory"] = False
    return experiment_args

def gpbench_experiment_full_long_timeout(**file_paths) -> Dict[str, typing.Any]:
    experiment_args = gpbench_experiment_setup_base(**file_paths)
    experiment_args["timeout"] = 60 * 60
    experiment_args["ids_subset"] = pd.Series(range(1,20))
    experiment_args["experiment_name"] = "fd-on-gpbench-login"
    experiment_args["experiment_description"] = "Run Flowdroid on Google Play Bench Login Scenario"
    experiment_args["flowdroid_args"] = FlowdroidArgs(**FlowdroidArgs.gpbench_experiment_settings_modified)
    experiment_args["always_new_experiment_directory"] = False
    return experiment_args

def ic3_linux():
    android_path: str = "/usr/lib/android-sdk/platforms/"
    gpbench_dir_path: str = "/home/calix/programming/benchmarks/ggplay/apks"
    ic3_script_root_path: str = "/home/calix/programming/IC3"
    ic3_on_gpbench(android_path, gpbench_dir_path, ic3_script_root_path)
    
def ic3_on_gpbench(android_path: str, gpbench_dir_path: str, ic3_path: str):
    experiment_name = "ic3-on-gpbench-long-timeouts"
    experiment_description = f"""{str(pd.to_datetime('today').date())}-{experiment_name}

Run ic3 on Google Play Bench (gpbench), login scenario.

Using ic3 script from Junbin Zhang (UBC).
"""
    
    results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)

    # Setup experiment df
    gpbench_description_path = "data/benchmark-descriptions/gpbench-info.csv"
    df = pd.read_csv(gpbench_description_path, header=0, index_col=False)
    df = df.set_index(df["AppID"])
    df["Detected Flows"] = None
    df["Error Message"] = None
    df["IC3 Time"] = None
    df["Time Elapsed"] = None
    benchmark_df = df

    # Get apps from icc_bench
    input_apks: BatchInputModel = apps_from_gpbench(gpbench_dir_path, benchmark_df)
    benchmark_df["Input Model"] = None
    for input_model in input_apks.ungrouped_inputs:
        mask = benchmark_df["AppName"].apply(lambda x: x in input_model.apk().apk_name) # type: ignore
        # only one result should be found 
        if mask.sum() > 1:
            raise AssertionError("Apk Name " + input_model.apk().apk_name + " found in multiple df rows: \n" + str(benchmark_df[mask]))
        app_id = benchmark_df[mask]["AppID"].iloc[0]
        input_model.benchmark_id = app_id
        benchmark_df.loc[app_id, "Input Model"] = input_model # type: ignore
    # assign_input_gpbench_benchmark_ids(input_apks, results_df)


    # Only use a subset of inputs
    mask = benchmark_df["AppID"].isin(range(1,20))
    mask = benchmark_df["AppID"].isin([3,6,8,9,10,15,19])
    results_df = benchmark_df[mask]
    

    # run ic3 on each app
    for input_model in input_apks.ungrouped_inputs:
        # only run apps in dataframe
        if not input_model.benchmark_id in results_df["AppID"]:
            continue

        # Run ic3 to get model for app, need to record resulting model filename
        # ic3_timeout = 4 * 60 * 60
        ic3_timeout = 72 *  60 * 60
        # ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")

        android_jar_path = os.path.join(android_path, f"android-{str(results_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")

        try:
            t0 = time.time()
            # icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
            icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
            results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
        except CalledProcessError as e:
            logger.error("Exception by ic3; details in " + ic3_path + "for apk " + input_model.apk().apk_name)
            results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
            # skip the rest of the experiment; Can't run FD properly without the ICC model
            continue
        except TimeoutExpired as e:
            logger.error(f"ic3 timed out after {ic3_timeout} seconds; details in " + ic3_path)
            results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {ic3_timeout} seconds"
            # skip the rest of the experiment; Can't run FD properly without the ICC model
            continue
        except ValueError as e:
            logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
            results_df.loc[input_model.benchmark_id, "Error Message"] = f"Can't find icc model: {str(e)}"
            continue

    print(results_df)
    results_df.to_csv(results_df_path)


def gpbench_experiment_generic(**kwargs):
    flowdroid_jar_path: str = kwargs["flowdroid_jar_path"]
    android_path: str = kwargs["android_path"]
    gpbench_dir_path: str = kwargs["gpbench_dir_path"]
    ground_truth_xml_path = kwargs["ground_truth_xml_path"]
    gpbench_description_path = kwargs["gpbench_description_path"]
    # ground_truth_xml_path = ""
    # gpbench_description_path = "data/benchmark-descriptions/gpbench-info.csv"

    flowdroid_timeout = kwargs["timeout"] 
    ids_subset = kwargs["ids_subset"] 
    experiment_name = kwargs["experiment_name"] 
    experiment_description = kwargs["experiment_description"] 
    flowdroid_args = kwargs["flowdroid_args"] 
    always_new_experiment_directory = kwargs["always_new_experiment_directory"] 

    # ic3_timeout = 4 * 60 * 60
    ic3_timeout = 15 * 60

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, kwargs, always_new_experiment_directory)

    ss_gpl_path: str = check_ssgpl_list()


    # Setup experiment df
    #TODO: more general would be to merge in a given benchmark description
    # ground_truth_xml_path = ""
    # gpbench_description_path = "data/benchmark-descriptions/gpbench-info.csv"
    # benchmark_df = pd.read_csv(gpbench_description_path, header=0, index_col=False)
    # benchmark_df = benchmark_df.set_index(benchmark_df["AppID"])
    # benchmark_df["Detected Flows"] = None
    # benchmark_df["Error Message"] = None
    # # results_df["IC3 Time"] = None
    # benchmark_df["Time Elapsed"] = None

    # Get apps from gp_bench
    # input_apks: BatchInputModel = apps_from_gpbench(gpbench_dir_path, benchmark_df)

    inputs_model = input_apks_from_dir(gpbench_dir_path)

    # #TODO: reconcile this impl with the one in fossdroid.py. 
    # benchmark_df["Input Model"] = None
    # for input_model in input_apks.ungrouped_inputs:
    #     mask = benchmark_df["AppName"].apply(lambda x: x in input_model.apk().apk_name) # type: ignore
    #     # only one result should be found 
    #     if mask.sum() > 1:
    #         raise AssertionError("Apk Name " + input_model.apk().apk_name + " found in multiple df rows: \n" + str(benchmark_df[mask]))
    #     app_id = benchmark_df[mask]["AppID"].iloc[0]
    #     input_model.benchmark_id = app_id
    #     benchmark_df.loc[app_id, "Input Model"] = input_model # type: ignore

    benchmark_df = benchmark_df_base_from_batch_input_model(inputs_model, benchmark_description_csv_path=gpbench_description_path)

    if ids_subset is not None:
        benchmark_df = benchmark_df.iloc[ids_subset]

    """
    ic3_path: str = kwargs["ic3_path"]
    use_model_paths_csv: bool = kwargs["use_model_paths_csv"]
    using_ic3_script: bool = kwargs["using_ic3_script"]
    """
    
    if "use_model_paths_csv" in kwargs.keys():
        icc_model_path_df = pd.read_csv("/home/calix/programming/ConDySta/data/benchmark-descriptions/gpbench-icc-model-paths.csv", header=0, index_col=False)
        icc_model_path_df = icc_model_path_df.set_index(icc_model_path_df["AppID"])
    
    # run fd on each app
    fd_output_dir_path = setup_additional_directories(experiment_dir_path, ["flowdroid-logs"])[0]
    if "use_model_paths_csv" in kwargs.keys():
        ic3_logs_dir_path, ic3_output_dir_path = setup_additional_directories(experiment_dir_path, ["ic3-logs", "ic3_output"])

    ground_truth_flows_df = groundtruth_df_from_xml(benchmark_df, ground_truth_xml_path)
    results_df = results_df_from_benchmark_df(benchmark_df)
    
    for i in benchmark_df.index:
    # for input_model in input_apks.ungrouped_inputs:
        input_model: InputModel = benchmark_df.loc[i, "Input Model"] # type: ignore

        # Run ic3 to get model for app, get file for FD
        if "use_model_paths_csv" in kwargs.keys() and kwargs["use_model_paths_csv"]:
            icc_model_path = icc_model_path_df.loc[input_model.benchmark_id, "ICC Model Path"]
            if not os.path.isfile(str(icc_model_path)):
                results_df.loc[input_model.benchmark_id, "Error Message"] = "No ICC Model"
                continue

        elif "ic3_path" in kwargs.keys():
            ic3_path = kwargs["ic3_path"]
            using_ic3_script = kwargs["using_ic3_script"]
            if not using_ic3_script:
                ic3_log_path = os.path.join(ic3_logs_dir_path, input_model.input_identifier() + ".log")
                try:
                    t0 = time.time()
                    icc_model_path = run_ic3_on_apk(ic3_path, android_path, input_model, ic3_output_dir_path, record_logs=ic3_log_path, timeout=ic3_timeout)
                    
                    results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
                except CalledProcessError as e:
                    logger.error("Exception by ic3; details in " + ic3_log_path + " for apk " + input_model.apk().apk_name)
                    results_df.loc[input_model.benchmark_id, "Error Message"] = "IC3 Exception"
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except TimeoutExpired as e:
                    logger.error(f"ic3 timed out after {ic3_timeout} seconds; details in " + ic3_log_path)
                    results_df.loc[input_model.benchmark_id, "Error Message"] = f"IC3 Timed Out after {format_num_secs(ic3_timeout)} "
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except ValueError as e:
                    logger.error(f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e))
                    continue
            else: 
                android_jar_path = os.path.join(android_path, f"android-{str(benchmark_df.loc[input_model.benchmark_id, "APILevel"])}", "android.jar")
                try:
                    t0 = time.time()
                    icc_model_path = run_ic3_script_on_apk(ic3_path, input_model.apk().apk_path, android_jar_path, ic3_timeout)
                    results_df.loc[input_model.benchmark_id, "IC3 Time"] = time.time() - t0
                except CalledProcessError as e:
                    logger.error("Exception by ic3; details in " + ic3_path + " for apk " + input_model.apk().apk_name)
                    results_df.loc[i, "Error Message"] = "IC3 Exception"
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except TimeoutExpired as e:
                    msg = f"ic3 timed out after {format_num_secs(ic3_timeout)} seconds; details in " + ic3_path
                    logger.error(msg)
                    results_df.loc[i, "Error Message"] = msg
                    # skip the rest of the experiment; Can't run FD properly without the ICC model
                    continue
                except ValueError as e:
                    msg = f"Some value error on apk " + input_model.apk().apk_name + " with msg: " + str(e)
                    logger.error(msg)
                    results_df.loc[i, "Error Message"] += msg # type: ignore
                    continue
        else: 
            # ic3_path is ""
            icc_model_path = ""
            pass

        fd_log_path = os.path.join(fd_output_dir_path, input_model.input_identifier() + ".log")

        try:
            t0 = time.time()
            # run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input_model.apk().apk_path,
            #                 ss_gpl_path,
            #                 icc_model_path, # type: ignore
            #                 fd_log_path,
            #                 verbose_path_info=True,
            #                 timeout=flowdroid_timeout)
            run_flowdroid_with_fdconfig(flowdroid_jar_path, input_model.apk().apk_path, android_path, ss_gpl_path, flowdroid_args, fd_log_path, flowdroid_timeout)
            time_elapsed = time.time() - t0
        except TimeoutExpired as e:
            logger.error(f"Flowdroid timed out after {flowdroid_timeout} seconds; details in " + fd_log_path)
            results_df.loc[i, "Error Message"] = f"Flowdroid Timed Out after {format_num_secs(flowdroid_timeout)} "
            continue

        process_results_from_fd_log_single(results_df, i, time_elapsed, fd_log_path, apk_path=input_model.apk().apk_path, ground_truth_flows_df=ground_truth_flows_df)

        # leaks_count = get_reported_num_leaks_in_flowdroid_log(fd_log_path)
        # if leaks_count is None:
        #     benchmark_df.loc[input_model.benchmark_id, "Error Message"] = "Flowdroid Irregularity, review log at " + fd_log_path
        # benchmark_df.loc[input_model.benchmark_id, "Detected Flows"] = leaks_count

    # print(results_df)
    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    results_df.to_csv(results_df_path)

def check_ssgpl_list():
    """ Generate the file path where SS-GooglePlayLogin.txt is expected. Generate it if it's not present."""
    sources_sinks_dir_path = hybrid.hybrid_config.source_sink_dir_path() # type: ignore
    ssgpl_list_path = os.path.join(sources_sinks_dir_path, "SS-GooglePlayLogin.txt")

    if not os.path.isfile(ssgpl_list_path):
        create_source_sink_file_ssgpl(ssgpl_list_path)

    return ssgpl_list_path


# TODO: This nonsense needs to be broken out into it's own file. 
def source_sink_file_ssgpl_string() -> str:
    sources = ["android.widget.EditText: android.text.Editable getText()"]
    sinks = ["com.squareup.okhttp.Call: com.squareup.okhttp.Response execute()",
             "cz.msebera.android.httpclient.client.HttpClient: cz.msebera.android.httpclient.HttpResponse execute (cz.msebera.android.httpclient.client.methods.HttpUriRequest)",
             "java.io.OutputStreamWriter: void write(java.lang.String)",
             "java.io.PrintWriter: void write(java.lang.String)",
             "java.net.HttpURLConnection: int getResponseCode()",
             "java.util.zip.GZIPOutputStream: void write(byte[])",
             "okhttp3.Call: okhttp3.Response execute()",
             "okhttp3.Call: void enqueue(okhttp3.Callback)",
             "org.apache.http.client.HttpClient: org.apache.http.HttpResponse execute(org.apache.http.client.methods.HttpUriRequest)",
             "org.apache.http.client.HttpClient: org.apache.http.HttpResponse execute(org.apache.http.client.methods.HttpUriRequest, org.apache.http.protocol.HttpContext)",
             "org.apache.http.impl.client.DefaultHttpClient: org.apache.http.HttpResponse execute(org.apache.http.client. methods.HttpUriRequest)"
             ]

    return format_source_sink_signatures(sources, sinks)




def create_source_sink_file_ssgpl(file_path):
    contents = source_sink_file_ssgpl_string()
    with open(file_path, 'w') as file:
        file.write(contents)


def apps_from_gpbench(gpbench_dir_path, df: pd.DataFrame):
    inputs_model = input_apks_from_dir(gpbench_dir_path)

    # Verify that each apk in the dataframe is in the input_apks object
    # files are saved as [AppID].[AppName].apk
    # Use sets to ignore ordering
    app_file_names_from_df = set(((df["AppID"].astype(str) + ".") + df["AppName"].astype(str)) + ".apk")
    app_file_names_from_dir = set(map(lambda input_model: input_model.apk().apk_name, inputs_model.ungrouped_inputs))
    
    if app_file_names_from_df != app_file_names_from_dir:
        raise AssertionError("Mismatch between apks and expected apks:" + str(app_file_names_from_df) + str(app_file_names_from_dir))

    return inputs_model


def flowdroid_help():
    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    run_flowdroid_help(flowdroid_jar_path)




