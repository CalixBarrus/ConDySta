
import os
import subprocess
from typing import List

import sys

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path, rebuilt_apk_path
# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)

from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

def rebuild_batch(config: HybridAnalysisConfig, apks: List[ApkModel], clean: bool=False):
    logger.info("Rebuilding instrumented smali code...")

    for apk in apks:
        try:
            rebuild_apk(config, apk, clean=clean)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rebuilding apk {apk.apk_name} with message: " + e.stderr)

def rebuild_apk(config: HybridAnalysisConfig, apk: ApkModel, clean: bool):
    
    if os.path.isfile(rebuilt_apk_path(config, apk)):
        if not clean:
            logger.debug(f"Instrumented APK {apk.apk_name} already present, skipping.")
            return
        else: 
            os.remove(rebuilt_apk_path(config, apk))
            logger.debug(f"Instrumented APK {apk.apk_name} already present, deleting.")

    cmd = ["apktool",  "-JXmx1g", "--quiet",
           "b", decoded_apk_path(config._decoded_apks_path, apk),
           "-o", rebuilt_apk_path(config, apk),
           "--use-aapt2"]

    logger.debug(" ".join(cmd))
    run_command(cmd)

if __name__ == '__main__':
    pass