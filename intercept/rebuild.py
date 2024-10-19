
import os
import subprocess
from typing import List

import sys

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path, apk_path
# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)

from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

def rebuild_batch(decoded_apks_directory_path: str, rebuilt_apks_directory_path: str, apks: List[ApkModel], clean: bool=False):
    logger.info("Rebuilding instrumented smali code...")

    # decoded_apks_directory_path = config._decoded_apks_path
    # rebuilt_apks_directory_path = config._rebuilt_apks_path

    for apk in apks:
        try:
            rebuild_apk(decoded_apks_directory_path, rebuilt_apks_directory_path, apk, clean=clean)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rebuilding apk {apk.apk_name} with message: " + e.stderr)

def rebuild_apk(decoded_apks_directory_path: str, rebuilt_apks_directory_path: str, apk: ApkModel, clean: bool):
    # decoded_apks_directory_path = config._decoded_apks_path
    # rebuilt_apks_directory_path = config._rebuilt_apks_path
    
    if os.path.isfile(apk_path(rebuilt_apks_directory_path, apk)):
        if not clean:
            logger.debug(f"Instrumented APK {apk.apk_name} already present, skipping.")
            return
        else: 
            os.remove(apk_path(rebuilt_apks_directory_path, apk))
            logger.debug(f"Instrumented APK {apk.apk_name} already present, deleting.")

    cmd = ["apktool",  "-JXmx1g",
           "b", decoded_apk_path(decoded_apks_directory_path, apk),
           "-o", apk_path(rebuilt_apks_directory_path, apk),
           "--use-aapt2"]

    logger.debug(" ".join(cmd))
    apk_tool_message = run_command(cmd)
    logger.debug(apk_tool_message)

if __name__ == '__main__':
    pass