import os
from typing import Dict, List
import intercept.intercept_config
from hybrid.hybrid_config import HybridAnalysisConfig

from util.subprocess import run_command, run_command_direct
from subprocess import CalledProcessError

import util.logger
logger = util.logger.get_logger(__name__)



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

    logger.debug(" ".join(cmd)) # type: ignore
    run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True)
"""
       -cp,--paths                              
       Compute the taint propagation paths and not just source-to-sink connections.
"""

def run_flowdroid_paper_settings(flowdroid_jar_path: str, android_platform_path: str, apk_path: str,
                         source_and_sink_path: str,
                         icc_model_path: str,
                         output_log_path: str,
                         verbose_path_info: bool,
                         timeout: int=None):
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
    run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True, timeout=timeout)

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


def run_flowdroid_with_fdconfig(flowdroid_jar_path: str, apk_path: str, android_platform_path: str, source_sink_path: str, flowdroid_args: "FlowdroidArgs", output_log_path: str = "", timeout: int=None):
    cmd = ["java", "-jar", flowdroid_jar_path, '-a', apk_path, '-p', android_platform_path, '-s', source_sink_path] + flowdroid_args.additional_args_list()

    run_command(cmd, redirect_stdout=output_log_path, redirect_stderr_to_stdout=True, timeout=timeout)

class FlowdroidArgs:
    """
    --aliasalgo LAZY --aplength 4 --callbackanalyzer DEFAULT --codeelimination NONE --cgalgo RTA --dataflowsolver FLOWINSENSITIVE --analyzeframeworks --implicit NONE --maxcallbackspercomponent 80 --maxcallbacksdepth 0 --noexceptions --pathalgo CONTEXTSENSITIVE --onesourceatatime --pathspecificresults --singlejoinpointabstraction --staticmode CONTEXTFLOWSENSITIVE --taintwrapper DEFAULTFALLBACK
    """
    best_fossdroid_settings: Dict = {'aliasalgo': 'LAZY', 'aplength': 4, 'callbackanalyzer': 'DEFAULT', 'codeelimination': 'NONE', 'cgalgo': 'RTA', 'dataflowsolver': 'FLOWINSENSITIVE', 'analyzeframeworks': None, 'implicit': 'NONE', 'maxcallbackspercomponent': 80, 'maxcallbacksdepth': 0, 'noexceptions': None, 'pathalgo': 'CONTEXTSENSITIVE', 'onesourceatatime': None, 'pathspecificresults': None, 'singlejoinpointabstraction': None, 'staticmode': 'CONTEXTFLOWSENSITIVE', 'taintwrapper': 'DEFAULTFALLBACK'}
    default_settings: Dict[str, str] = {}
    gpbench_experiment_settings_modified: Dict = {"enablereflection": None, "noiccresultspurify": None, "layoutmode": "NONE", }
    gpbench_experiment_settings: Dict = {"enablereflection": None, "noiccresultspurify": None, "layoutmode": "NONE", "iccmodel": "placeholder for path to icc_model"}

    # Options with only an empty list [] do not take any argument
    available_options: Dict = {'aliasalgo': ['LAZY'], 'aplength': range(1,10), 'callbackanalyzer': ['DEFAULT'], 'codeelimination': ['NONE'], 'cgalgo': ['RTA'], 'dataflowsolver': ['FLOWINSENSITIVE'], 'analyzeframeworks': [None], 'implicit': ['NONE'], 'maxcallbackspercomponent': range(0,1000), 'maxcallbacksdepth': range(-1, 10), 'noexceptions': [None], 'pathalgo': ['CONTEXTSENSITIVE'], 'onesourceatatime': [None], 'pathspecificresults': [None], 'singlejoinpointabstraction': [None], 'staticmode': ['CONTEXTFLOWSENSITIVE'], 'taintwrapper': ['DEFAULTFALLBACK'], 'enablereflection': [None], 'noiccresultspurify': [None], 'layoutmode': ["NONE"], 'iccmodel': ['any']}
    
    args: Dict[str, str]

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key not in FlowdroidArgs.available_options.keys():
                raise AssertionError(f'Option {key} not documented.')
            if value not in FlowdroidArgs.available_options[key] and FlowdroidArgs.available_options[key] not in ['iccmodel']:
                raise AssertionError(f'Option {value} not documented, documented options for {key} are {str(FlowdroidArgs.available_options[key])}')
            
        self.args = kwargs

    def additional_args_list(self) -> List[str]:
        additional_args = []
        for key, value in self.args.items():
            additional_args.append(f"--{str(key)}")
            if value is not None:
                additional_args.append(str(value))

        return additional_args


if __name__ == '__main__':
    pass

