import copy
import os
import shutil
import subprocess
from typing import List

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

def decode_apk(config: HybridAnalysisConfig, apk:ApkModel, clean:bool=False):

    # todo: fix test usages of this function
    if os.path.isdir(decoded_apk_path(config._decoded_apks_path, apk)):
        if not clean:
            logger.debug(f"APK {apk.apk_name} already decompiled. Skipping.")
            return
        else:
            shutil.rmtree(decoded_apk_path(config._decoded_apks_path, apk))
            logger.debug(f"APK {apk.apk_name} already decompiled. Deleting.")

    # decompile to decoded_apks_path
    # Pull off the ".apk" of the name of the output file
    apktool_path = "apktool" # TODO: move this to external_path
    cmd = [apktool_path, "--quiet", "d", apk.apk_path, "-o", decoded_apk_path(config._decoded_apks_path, apk)]

    logger.debug(" ".join(cmd))
    run_command(cmd)

def decode_batch(config: HybridAnalysisConfig, apks:List[ApkModel], clean: bool=False):
    for apk in apks:
        decode_apk(config, apk, clean)

if __name__ == '__main__':
    pass

