import os
import intercept.intercept_config
from hybrid.hybrid_config import HybridAnalysisConfig

from util.subprocess import run_command, run_command_direct
from subprocess import CalledProcessError

from util import logger
logger = logger.get_logger('hybrid', 'flowdroid')



def run_flowdroid_config(config: HybridAnalysisConfig, apk_path: str,
                         source_and_sink_path: str,
                         output_log_path: str,
                         ):
    # Use the compiled version of flowdroid at the specified jar on the specified apk.
    # Write the logged results to the specified file.

    if not apk_path.endswith(".apk"):
        raise ValueError(f"Input apk_name {apk_path} needs to end with \".apk\"")

    flowdroid_jar = config.flowdroid_jar_path
    android_platform_path = config.android_platform_path

    # log_name = apk_name + ".log"

    cmd = ["java", "-jar", flowdroid_jar,
           "-a", apk_path,
           "-p", android_platform_path,
           "-s", source_and_sink_path,
           "--paths", "--pathspecificresults", "--outputlinenumbers",
           ]

    logger.debug(" ".join(cmd))
    run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True)
"""
       -cp,--paths                              
       Compute the taint propagation paths and not just source-to-sink connections.
"""

def run_flowdroid_paper_settings(flowdroid_jar_path: str, android_platform_path: str, apk_path: str,
                         source_and_sink_path: str,
                         icc_model_path: str,
                         output_log_path: str,
                         verbose_path_info: bool):
    if not apk_path.endswith(".apk"):
        raise ValueError(f"Input apk_name {apk_path} needs to end with \".apk\"")


    # log_name = apk_name + ".log"

    cmd = ["java", "-jar", flowdroid_jar_path,
           "-a", apk_path,
           "-p", android_platform_path,
           "-s", source_and_sink_path,
           "--enablereflection",
           "--noiccresultspurify",
           "--layoutmode", "NONE"
           ]
    if verbose_path_info:
        cmd += [
           "--paths", "--pathspecificresults",
           ]
    if icc_model_path != "":
        cmd.append("--iccmodel")
        cmd.append(icc_model_path)

    logger.debug(" ".join(cmd))
    run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True)

def run_flowdroid(flowdroid_jar_path: str, apk_path: str, android_platform_path: str, source_sink_path: str, icc_model_path: str = "", output_log_path: str = ""):

    if not apk_path.endswith(".apk"):
        raise ValueError(f"Input apk_name {apk_path} needs to end with \".apk\"")

    cmd = ["java", "-jar", flowdroid_jar_path,
           "-a", apk_path,
           "-p", android_platform_path,
           "-s", source_sink_path,
           "--enablereflection",
           "--noiccresultspurify",
        #    "--paths", "--pathspecificresults",
           "--layoutmode", "NONE"
           ]
    if icc_model_path != "":
        cmd.append("--iccmodel")
        cmd.append(icc_model_path)

    # If output_log_path is not "" redirect input to the provided file path, else print to stdout.
    if output_log_path != "":
        logger.debug(" ".join(cmd))
        run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True)
    else:
        logger.debug(" ".join(cmd))
        run_command_direct(cmd)






def get_flowdroid_callgraph(hybrid_analysis_config: HybridAnalysisConfig,
                            apk_path: str,
                            output_path: str
                            ) -> str:
    flowdroid_jar = hybrid_analysis_config.flowdroid_jar_path
    android_platform_path = hybrid_analysis_config.android_platform_path
    source_and_sink_path = hybrid_analysis_config.unmodified_source_sink_list_path

    cmd = ["java", "-jar", flowdroid_jar, ' -a ', apk_path, ' -p ', android_platform_path, ' -s ', source_and_sink_path, "--callgraphonly"]

    run_command(cmd)
    pass

def run_flowdroid_help(flowdroid_jar_path: str):
    args = ['java', '-jar', flowdroid_jar_path, '-help']
    run_command_direct(args)



# def run_flowdroid_batch(input_apks_path, source_and_sink_path,
#                         output_log_path, recursive=False):
#     if not os.path.isdir(input_apks_path):
#         raise FileNotFoundError(f"Directory {input_apks_path} not found.")
#
#     for item in os.listdir(input_apks_path):
#         if os.path.isfile(os.path.join(input_apks_path, item)) and item.endswith(
#                 ".apk"):
#             activate_flowdroid(input_apks_path, item, source_and_sink_path,
#                                output_log_path)
#
#         if recursive:
#             if os.path.isdir(os.path.join(input_apks_path, item)):
#                 run_flowdroid_batch(os.path.join(input_apks_path, item),
#                                     source_and_sink_path,
#                                     output_log_path, recursive)


if __name__ == '__main__':
    # apk_name = "FieldSensitivity3.apk"
    # apk_path = intercept.intercept_config.get_default_intercept_config().input_apks_path
    # output_path = os.path.join(
    #     intercept.intercept_config.get_default_intercept_config().logs_path,
    #     "droidbench-settings-experiments")
    # sources_and_sinks = "SourcesAndSinks.txt"  # The flowdroid default is in
    # # the root of this project
    #
    # activate_flowdroid(apk_path, apk_name, sources_and_sinks, output_path)

    flowdroid_help()

# #
# cmd_install = 'adb install ' + apk_signedPath + apk + '.apk'
# os.system(cmd_install)
#
# cmd_logcat_c = 'adb logcat -c'
# os.system(cmd_logcat_c)
#
#
# input_log_path = '/home/xueling/researchProjects/sourceDetection/input_log_path/'
# cmd_logcat_out = 'adb logcat > ' + input_log_path + apk
# os.system(cmd_logcat_out)


# cmd_taint_newSource = 'java -jar ' + jar + ' -a ' + apk_orgPath + apk + '.apk -p' + platformPath + ' -s ' + SourceAndSinks_newSources + ' > ' + analysis_newSources + apk + ' 2>&1'
# print cmd_taint_newSource
# os.system(cmd_taint_newSource)