import copy
import os
import shutil
import subprocess
from typing import List

from hybrid.hybrid_config import HybridAnalysisConfig
from hybrid import hybrid_config
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

# def decode_apk(config: HybridAnalysisConfig, apk:ApkModel, clean:bool=False):
def decode_apk(decoded_apks_directory_path: HybridAnalysisConfig, apk:ApkModel, clean:bool=False):
    # decoded_apk_path = hybrid_config.decoded_apk_path(config._decoded_apks_path, apk)
    decoded_apk_path = hybrid_config.decoded_apk_path(decoded_apks_directory_path, apk)

    # todo: fix test usages of this function
    if os.path.isdir(decoded_apk_path):
        if not clean:
            logger.debug(f"APK {apk.apk_name} already decompiled. Skipping.")
            return
        else:
            shutil.rmtree(decoded_apk_path)
            logger.debug(f"APK {apk.apk_name} already decompiled. Deleting.")

    # decompile to decoded_apks_path
    # Pull off the ".apk" of the name of the output file
    apktool_path = "apktool" # TODO: move this to external_path
    cmd = [apktool_path, "--quiet", "d", apk.apk_path, "-o", decoded_apk_path]
    cmd = [apktool_path, "d", apk.apk_path, "-o", decoded_apk_path]

    logger.debug(" ".join(cmd))
    apk_tool_message = run_command(cmd)
    logger.debug(apk_tool_message)

# def decode_batch(config: HybridAnalysisConfig, apks:List[ApkModel], clean: bool=False):
def decode_batch(decoded_apks_directory_path: str, apks:List[ApkModel], clean: bool=False):
    
    for apk in apks:
        decode_apk(decoded_apks_directory_path, apk, clean)

if __name__ == '__main__':
    pass

