import os
from typing import List

import numpy as np

import hybrid.hybrid_config
from hybrid.flowdroid import run_flowdroid_paper_settings
from hybrid.ic3 import run_ic3_on_apk_direct
from hybrid.results import HybridAnalysisResult
from hybrid.source_sink import format_source_sink_signatures
from util import logger
from util.input import BatchInputModel, input_apks_from_dir, InputModel
import pandas as pd

logger = logger.get_logger('hybrid', 'dynamic')


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

    # ic3_jar_path = "/home/calix/programming/ic3/target/ic3-0.2.1-full.jar"
    ic3_jar_path: str = "/home/calix/programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"

    icc_bench(flowdroid_jar_path, android_path, icc_bench_dir_path, ic3_jar_path)


def icc_bench(flowdroid_jar_path: str, android_path: str, icc_bench_dir_path: str, ic3_jar_path):

    ss_bench_path: str = check_ss_bench_list()

    # Get apps from icc_bench
    input_apks: BatchInputModel = apps_from_icc_bench(icc_bench_dir_path)

    # Setup results df
    results_df = setup_experiment_df()

    # run fd on each app
    for input in input_apks.ungrouped_inputs:
        ic3_output_dir = hybrid.hybrid_config.ic3_output_dir_path()
        icc_model_path = run_ic3_on_apk_direct(ic3_jar_path, android_path, input, ic3_output_dir)

        # Run ic3 to get model for app, get file for FD
            # Save file for review & comparison
        fd_output_dir_path = "data/logs/flowdroid-iccbench"
        fd_log_path = os.path.join(fd_output_dir_path, input.input_identifier() + ".log")
        run_flowdroid_paper_settings(flowdroid_jar_path, android_path, input.apk().apk_path,
                         ss_bench_path,
                         icc_model_path,
                         fd_log_path,
                         verbose_path_info=True)

        leaks_count = HybridAnalysisResult.count_leaks_in_flowdroid_log(fd_log_path)
        results_df.loc[input.benchmark_id, "Detected Flows"] = leaks_count


    print(results_df)




def icc_bench_apk_names() -> List[str]:
    return [
        "icc_explicit_nosrc_nosink.apk",
        "icc_explicit_nosrc_sink.apk",
        "icc_explicit_src_nosink.apk",
        "icc_explicit_src_sink.apk",
        "icc_implicit_nosrc_nosink.apk",
        "icc_implicit_nosrc_sink.apk",
        "icc_implicit_src_nosink.apk",
        "icc_implicit_src_sink.apk",
        "icc_intentservice.apk",
        "icc_stateful.apk",

        "icc_implicit_mix2.apk",
        "icc_dynregister1.apk",
        "icc_dynregister2.apk",
        "icc_explicit1.apk",
        "icc_implicit_action.apk",
        "icc_implicit_category.apk",
        "icc_implicit_data1.apk",
        "icc_implicit_data2.apk",
        "icc_implicit_mix1.apk",

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

def icc_bench_expected_flows():
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
def apps_from_icc_bench(icc_bench_dir_path: str) -> BatchInputModel:

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
        for model in input_apks:
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

    return input_model





def setup_experiment_df() -> pd.DataFrame:

    apk_benchmark_ids = icc_bench_apk_benchmark_ids()
    apk_names = icc_bench_apk_names()

    df = pd.DataFrame({"apk_name": pd.Series(apk_names, apk_benchmark_ids)})

    expected_flows = icc_bench_expected_flows()
    df["Expected Flows"] = pd.Series(expected_flows, apk_benchmark_ids)

    df["Detected Flows"] = pd.Series([np.nan] * len(apk_benchmark_ids), apk_benchmark_ids)

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
