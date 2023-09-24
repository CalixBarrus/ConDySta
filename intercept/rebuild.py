
import os
import subprocess
from typing import List

import pexpect
import sys

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path, rebuilt_apk_path
# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)
from intercept import intercept_config

from util import logger
from util.input import InputApkModel
from util.subprocess import run_command

logger = logger.get_logger('intercept', 'rebuild')

def rebuild_batch(config: HybridAnalysisConfig, apks: List[InputApkModel]):
    logger.info("Rebuilding instrumented smali code...")

    for apk in apks:
        try:
            rebuild_apk(config, apk)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error rebuilding apk {apk.apk_name} with message: " + e.stderr)

def rebuild_apk(config: HybridAnalysisConfig, apk: InputApkModel):
    if apk.apk_name in os.listdir(config.rebuilt_apks_path):
        logger.debug(f"Instrumented APK {apk.apk_name} already in {config.rebuilt_apks_path}, skipping.")
        return

    cmd = ["apktool", "--quiet",
           "b", decoded_apk_path(config, apk),
           "-o", rebuilt_apk_path(config, apk),
           "--use-aapt2"]

    logger.debug(" ".join(cmd))
    run_command(cmd)

if __name__ == '__main__':
    pass