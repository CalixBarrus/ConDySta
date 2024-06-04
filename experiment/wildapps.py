
import os
from typing import List

from hybrid.flowdroid import run_flowdroid, run_flowdroid_help
from hybrid.source_sink import format_source_sink_signatures
from util.subprocess import run_command_direct

logger = logger.get_logger('hybrid', 'dynamic')


def flowdroid_on_gpbench():
    # benchmark_folder_path: str = "/Users/calix/Documents/programming/research-programming/benchmarks/gpbench/apks"
    benchmark_folder_path: str = "/home/calix/programming/benchmarks/gpbench"

    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    # android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    android_path: str = "/usr/lib/android-sdk/platforms/"

    # source_sink_path: str = "/Users/calix/Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"
    source_sink_path: str = "/home/calix/programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"

    # apk path, apk id,
    """
1.com.echangecadeaux.apk
2.com.rtp.livepass.android.apk
3.com.tripadvisor.tripadvisor.apk
4.ca.intact.mydrivingdiscount.apk
5.com.asiandate.apk
6.ca.passportparking.mobile.passportcanada.apk
7.com.aldiko.android.apk
8.com.passportparking.mobile.parkvictoria.apk
9.com.passportparking.mobile.toronto.apk
10.tc.tc.scsm.phonegap.apk
11.com.onetapsolutions.morneau.activity.apk
12.net.fieldwire.app.apk
13.com.ackroo.mrgas.apk
14.com.airbnb.android.apk
15.com.bose.gd.events.apk
16.com.phonehalo.itemtracker.apk
17.com.viagogo.consumer.viagogo.playstore.apk
18.com.yelp.android.apk
19.onxmaps.hunt.apk
"""
    """
21.com.monitor.phone.s0ft.phonemonitor.apk
22.com.mobistartapp.win7imulator.apk
    """

    apk3_path = os.path.join(benchmark_folder_path, "3.com.tripadvisor.tripadvisor.apk")
    apk13_path = os.path.join(benchmark_folder_path, "13.com.ackroo.mrgas.apk")

    icc_bench_apk_path = "/home/calix/programming/benchmarks/ICCBench20/benchmark/apks/IccHandling/icc_explicit_nosrc_nosink.apk"

    icc_bench_icc_model = "/home/calix/programming/ic3_results/org.arguslab.icc_explicit_nosrc_nosink_1.txt"
    apk13_icc_model_path = "/home/calix/programming/ic3_results/com.ackroo.mrgas_2.txt"
    

    run_flowdroid(flowdroid_jar_path, apk13_path, android_path, source_sink_path, apk13_icc_model_path)

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




def create_source_sink_file_ssgpl():
    file_path = "/Users/calix/Documents/programming/research-programming/ConDySta/data/sources-and-sinks/ss-gpl.txt"
    contents = source_sink_file_ssgpl_string()
    with open(file_path, 'w') as file:
        file.write(contents)


def flowdroid_help():
    # flowdroid_jar_path: str = "/Users/calix/Documents/programming/research-programming/flowdroid-jars/fd-2.13.0/soot-infoflow-cmd-2.13.0-jar-with-dependencies.jar"
    flowdroid_jar_path: str = "/home/calix/programming/flowdroid-jars/fd-2.7.1/soot-infoflow-cmd-jar-with-dependencies.jar"

    run_flowdroid_help(flowdroid_jar_path)

def run_ic3_on_apk():
    # ic3_jar_path = "/Users/calix/Documents/programming/research-programming/ic3/target/ic3-0.2.0-full.jar"
    # ic3_jar_path = "/home/calix/programming/ic3/target/ic3-0.2.1-full.jar"
    ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-tools/ic3.jar"
    # ic3_jar_path = "/home/calix/programming/ic3-jars/jordansamhi-raicc/ic3-raicc.jar"
    
    

    # classpath = "/Users/calix/.m2/repository/com/jcraft/jsch/0.1.51/jsch-0.1.51.jar:/Users/calix/.m2/repository/mysql/mysql-connector-java/5.1.31/mysql-connector-java-5.1.31.jar:/Users/calix/.m2/repository/org/slf4j/slf4j-api/1.7.7/slf4j-api-1.7.7.jar:/Users/calix/.m2/repository/org/slf4j/slf4j-log4j12/1.7.7/slf4j-log4j12-1.7.7.jar:/Users/calix/.m2/repository/log4j/log4j/1.2.17/log4j-1.2.17.jar:/Users/calix/.m2/repository/commons-cli/commons-cli/1.3.1/commons-cli-1.3.1.jar:/Users/calix/.m2/repository/edu/psu/cse/siis/coal/0.1.7/coal-0.1.7.jar:/Users/calix/.m2/repository/edu/psu/cse/siis/coal-strings/0.1.2/coal-strings-0.1.2.jar:/Users/calix/.m2/repository/soot/soot/20150607/soot-20150607.jar:/Users/calix/.m2/repository/infoflow/infoflow/20150607/infoflow-20150607.jar:/Users/calix/.m2/repository/infoflow-android/infoflow-android/20150607/infoflow-android-20150607.jar:/Users/calix/.m2/repository/com/google/protobuf/protobuf-java/2.5.0/protobuf-java-2.5.0.jar"
    # android_path: str = "/Users/calix/Library/Android/sdk/platforms/"
    android_path: str = "/usr/lib/android-sdk/platforms"
    

    benchmark_folder_path: str = "/home/calix/programming/benchmarks/gpbench/"
    apk13_path = os.path.join(benchmark_folder_path, "13.com.ackroo.mrgas.apk")

    icc_bench_apk_path = "/home/calix/programming/benchmarks/ICCBench20/benchmark/apks/IccHandling/icc_explicit_nosrc_nosink.apk"
    output_dir_path = "/home/calix/programming/ic3_results"

    cmd = ["java", "-jar", ic3_jar_path, "-a", apk13_path, "-cp", android_path, "-protobuf", output_dir_path]

    run_command_direct(cmd)






