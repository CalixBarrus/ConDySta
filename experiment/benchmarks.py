import os
from typing import List

import numpy as np

from experiment.common import setup_additional_directories, setup_dirs_with_ic3, setup_experiment_dir
import hybrid.hybrid_config
from hybrid.flowdroid import run_flowdroid_paper_settings
from hybrid.ic3 import run_ic3_on_apk, run_ic3_on_apk_direct
from hybrid.log_process_fd import get_reported_num_leaks_in_flowdroid_log
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import format_source_sink_signatures
from util.input import BatchInputModel, input_apks_from_dir, InputModel
import pandas as pd

import util.logger
logger = util.logger.get_logger(__name__)

def icc_bench_mac():
    benchmark_folder_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/gpbench/apks"
    # benchmark_folder_path: str = "/home/calix/programming/benchmarks/gpbench"

    flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    # flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    # android_path: str = "/usr/lib/android-sdk/platforms/"

    source_sink_path: str = "/Users/calix/Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"
    # source_sink_path: str = "/home/calix/programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"

    icc_bench_dir_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/ICCBench20"

    ic3_jar_path = ""

    icc_bench(flowdroid_jar_path, android_path, icc_bench_dir_path, ic3_jar_path)

def icc_bench_linux():
    # benchmark_folder_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/gpbench/apks"
    benchmark_folder_path: str = "/home/calix/programming/benchmarks/gpbench"

    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    # android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    android_path: str = "/usr/lib/android-sdk/platforms/"

    # source_sink_path: str = "/Users/calix/Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"
    source_sink_path: str = "/home/calix/programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"

    icc_bench_dir_path: str = "/home/calix/programming/benchmarks/ICCBench20/benchmark/apks"

    ic3_jar_path = "/home/calix/programming/ic3/target/ic3-0.2.1-full.jar"
    # ic3_jar_path: str = "/home/calix/programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"

    icc_bench(flowdroid_jar_path, android_path, icc_bench_dir_path, ic3_jar_path)
    
# def setup_dirs(experiment_name, experiment_description):
#     date = str(pd.to_datetime('today').date())
#     # "YYYY-MM-DD"
#     experiment_id = date + "-" + experiment_name

#     # Setup experiment specific directories
#     experiment_dir_path = os.path.join("data", experiment_id)
#     results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
#     ic3_output_dir_path = os.path.join(experiment_dir_path, "ic3-output")
#     ic3_logs_dir_path = os.path.join(experiment_dir_path, "ic3-logs")
#     fd_output_dir_path = os.path.join(experiment_dir_path, "flowdroid-logs")
#     # Make sure each directory exists
#     for dir_path in [experiment_dir_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path]:
#         if not os.path.isdir(dir_path):
#             os.mkdir(dir_path)

#     # Record experiment description
#     readme_path = os.path.join(experiment_dir_path, "README.txt")
#     with open(readme_path, 'w') as file:
#         file.write(experiment_description)

#     return results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path

def droidbench_linux():
    benchmark_folder_path: str = "/home/calix/programming/benchmarks/DroidBenchExtended"

    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    android_path: str = "/usr/lib/android-sdk/platforms/"

    source_sink_path: str = "/home/calix/programming/ConDySta/data/sources-and-sinks/flowdroid-default-sources-and-sinks.txt"

    droidbench_dir_path: str = "/home/calix/programming/benchmarks/DroidBenchExtended/benchmark/apks"

    droidbench(flowdroid_jar_path, android_path, source_sink_path, droidbench_dir_path)

def icc_bench(flowdroid_jar_path: str, android_path: str, icc_bench_dir_path: str, ic3_jar_path):

    experiment_name = "fd-on-iccbench-compiled-ic3"
    experiment_description = """
Run Flowdroid on ICC Bench using same settings as zhang_2021_gpbench
"""

    results_df_path, ic3_output_dir_path, ic3_logs_dir_path, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)

    ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         icc_model_path,
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_reported_num_leaks_in_flowdroid_log(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)


def icc_bench_no_ic3(flowdroid_jar_path: str, android_path: str, icc_bench_dir_path: str, ic3_jar_path):

    date = str(pd.to_datetime('today').date())
    # "YYYY-MM-DD"

    experiment_name = "fd-on-iccbench-no-ic3"
    experiment_description = """
    Run Flowdroid on ICC Bench using same settings as zhang_2021_gpbench, less the icc model from ic3.
"""

    results_df_path, _, _, fd_output_dir_path = setup_dirs_with_ic3(experiment_name, experiment_description)

    ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        # ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        # icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         "",
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_reported_num_leaks_in_flowdroid_log(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)


def droidbench(flowdroid_jar_path: str, android_path: str, droidbench_dir_path: str, source_sink_path: str):

    experiment_name = "fd-on-droidbench-subset"
    experiment_description = """
Run Flowdroid on a subset of Droidbench apps
"""

    experiment_id, experiment_dir_path = setup_experiment_dir(experiment_name, experiment_description, {})
    results_df_path = os.path.join(experiment_dir_path, experiment_id + ".csv")
    fd_output_dir_path = setup_additional_directories(experiment_dir_path, ['flowdroid_logs'])[0]


    # ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = get_and_validate_icc_bench_apps(icc_bench_dir_path)

    # Setup results df
    results_df = setup_icc_bench_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        ic3_log_path = os.path.join(ic3_logs_dir_path, input.input_identifier() + ".log")
        icc_model_path = run_ic3_on_apk(ic3_jar_path, android_path, input, ic3_output_dir_path, record_logs=ic3_log_path)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         icc_model_path,
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = get_reported_num_leaks_in_flowdroid_log(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)
    results_df.to_csv(results_df_path)

def icc_bench_apk_names() -> List[str]:
    return [
        "icc_explicit_nosrc_nosink.apk",
        "icc_explicit_nosrc_sink.apk",
        "icc_explicit_src_nosink.apk",
        "icc_explicit_src_sink.apk",
        "icc_explicit1.apk",
        "icc_implicit_nosrc_nosink.apk",
        "icc_implicit_nosrc_sink.apk",
        "icc_implicit_src_nosink.apk",
        "icc_implicit_src_sink.apk",
        "icc_implicit_action.apk",
        "icc_intentservice.apk",
        "icc_stateful.apk",

        "icc_dynregister1.apk",
        "icc_dynregister2.apk",
        "icc_implicit_category.apk",
        "icc_implicit_data1.apk",
        "icc_implicit_data2.apk",
        "icc_implicit_mix1.apk",
        "icc_implicit_mix2.apk",

        "icc_rpc_comprehensive.apk",

        "rpc_localservice.apk",
        "rpc_messengerservice.apk",
        "rpc_remoteservice.apk",
        "rpc_returnsensitive.apk",
    ]

def icc_bench_apk_benchmark_ids():
    return [
        1,
        2,
        3,
        4,
        13,
        5,
        6,
        7,
        8,
        14,
        9,
        10,

        11,
        12,
        15,
        16,
        17,
        18,
        19,

        20,

        21,
        22,
        23,
        24,
    ]

def icc_bench_ubc_config_expected_flows():
    return [
        0,
        0,
        1,
        2,
        2,
        0,
        0,
        1,
        2,
        2,
        1,
        2,

        2,
        2,
        2,
        2,
        2,
        3,
        2,

        2,

        1,
        1,
        1,
        1,
    ]

# def icc_bench_designer_expected_flows():
#     return [
#         0,
#         0,
#         0,
#         1,
#         1,
#         0,
#         0,
#         1,
#         2,
#         2,
#         1,
#         3,

#         2,
#         2,
#         2,
#         2,
#         2,
#         3,
#         2,

#         3,

#         1,
#         1,
#         1,
#         1,
#     ]

def icc_bench_FDv2_7_1_ubc_results():
    return [
        0,
        0,
        1,
        2,
        2,
        0,
        0,
        1,
        2,
        2,
        0,
        1,

        1,
        1,
        2,
        1,
        1,
        3,
        2,

        0,

        0,
        0,
        0,
        0,
    ]

def get_and_validate_icc_bench_apps(icc_bench_dir_path: str) -> BatchInputModel:

    # Expected apps and id's
    apk_names = icc_bench_apk_names()
    apk_benchmark_ids = icc_bench_apk_benchmark_ids()


    if len(apk_names) != len(apk_benchmark_ids):
        raise AssertionError(f"Mismatch between ICCBench ID's and apk names")

    input_apks = input_apks_from_dir(icc_bench_dir_path)

    # Validate results from input_apks_from_dir, and assign apks their id's.
    if len(input_apks.unique_apks) != len(apk_names):
        raise AssertionError(f"Expected {len(apk_names)} apks but found {len(input_apks.unique_apks)} in directory {icc_bench_dir_path}")

    def scan_for_apk(input_apks, apk_name) -> InputModel:
        result = None
        for model in input_apks.ungrouped_inputs:
            if model.apk().apk_name == apk_name:
                if result is not None:
                    raise AssertionError(f"Duplicate apk found {apk_name}")
                result = model
        if result is None:
            raise AssertionError(f"Apk not found {apk_name}")
        return result

    for i in range(len(apk_names)):
        # make sure an apk of this name is present, and assign that InputModel its benchmark ID
        input_model = scan_for_apk(input_apks, apk_names[i])
        input_model.benchmark_id = apk_benchmark_ids[i]

    return input_apks





def setup_icc_bench_df() -> pd.DataFrame:

    apk_benchmark_ids = icc_bench_apk_benchmark_ids()
    apk_names = icc_bench_apk_names()

    df = pd.DataFrame({"apk_name": pd.Series(apk_names, apk_benchmark_ids)})
    df.rename_axis('AppID')

    expected_flows = icc_bench_ubc_config_expected_flows()
    df["UBC Expected Flows"] = pd.Series(expected_flows, apk_benchmark_ids)

    df["Detected Flows"] = pd.Series([np.nan] * len(apk_benchmark_ids), apk_benchmark_ids)

    ubc_experiment_flows = icc_bench_FDv2_7_1_ubc_results()
    df["UBC FlowDroid v2.7.1 Detected Flows"] = pd.Series(ubc_experiment_flows, apk_benchmark_ids)

    return df



def check_ss_bench_list() -> str:
    """ Generate the file path where SS-Bench.txt is expected. Generate it if it's not present."""
    sources_sinks_dir_path = hybrid.hybrid_config.source_sink_dir_path()
    ss_bench_list_path = os.path.join(sources_sinks_dir_path, "SS-Bench.txt")

    if not os.path.isfile(ss_bench_list_path):
        create_source_sink_file_ssbench(ss_bench_list_path)

    return ss_bench_list_path

def create_source_sink_file_ssbench(file_path):
    contents = source_sink_file_ssbench_string()
    with open(file_path, 'w') as file:
        file.write(contents)

def source_sink_file_ssbench_string() -> str:
    sources = ["android.telephony.TelephonyManager: java.lang.String getDeviceId()",
               "android.telephony.TelephonyManager: java.lang.String getSimSerialNumber()",
               "android.location.Location: double getLatitude()",
               "android.location.Location: double getLongitude()",
               "android.telephony.TelephonyManager: java.lang.String getSubscriberId()"
               ]

    sinks = ["android.telephony.SmsManager: void sendTextMessage(java.lang.String,java.lang.String,java.lang.String, android.app.PendingIntent,android.app.PendingIntent)",
             "android.util.Log: int i(java.lang.String,java.lang.String)",
             "android.util.Log: int e(java.lang.String,java.lang.String)",
             "android.util.Log: int v(java.lang.String,java.lang.String)",
             "android.util.Log: int d(java.lang.String,java.lang.String)",
             "java.lang.ProcessBuilder: java.lang.Process start()",
             "android.app.Activity: void startActivityForResult(android.content.Intent,int)",
             "android.app.Activity: void setResult(int,android.content.Intent)",
             "android.app.Activity: void startActivity(android.content.Intent)",
             "java.net.URL: java.net.URLConnection openConnection()",
             "android.content.ContextWrapper: void sendBroadcast(android.content.Intent)",
             ]

    return format_source_sink_signatures(sources, sinks)

