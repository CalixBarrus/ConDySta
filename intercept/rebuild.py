
import os
import subprocess
from typing import List

import sys

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path, apk_path

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

def rebuild_apk(decoded_apk_directory_path: str, rebuilt_apk_directory_path: str, apk: ApkModel, clean: bool):
    # TODO: refactor to take a decoded_apk_path, instead of directory + apkModel.
    
    # decoded_apks_directory_path = config._decoded_apks_path
    # rebuilt_apks_directory_path = config._rebuilt_apks_path
    
    if os.path.isfile(apk_path(rebuilt_apk_directory_path, apk)):
        if not clean:
            logger.debug(f"Instrumented APK {apk.apk_name} already present, skipping.")
            return
        else: 
            os.remove(apk_path(rebuilt_apk_directory_path, apk))
            logger.debug(f"Instrumented APK {apk.apk_name} already present, deleting.")

    java_heap_size = ""
    java_heap_size = "1g"
    java_heap_size = "8g"
    java_heap_arg = ["-JXmx" + java_heap_size] if java_heap_size != "" else []

    cmd = ["apktool"] + java_heap_arg + [
           "b", decoded_apk_path(decoded_apk_directory_path, apk),
           "-o", apk_path(rebuilt_apk_directory_path, apk),
           "--use-aapt2"]

    logger.debug(" ".join(cmd))
    apk_tool_message = run_command(cmd)
    logger.debug(apk_tool_message)

if __name__ == '__main__':
    pass