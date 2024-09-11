import copy
import os
import subprocess
from typing import List

from hybrid.hybrid_config import HybridAnalysisConfig, decoded_apk_path
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

def decode_apk(config: HybridAnalysisConfig, apk:ApkModel):
    decoded_apks_path = config.decoded_apks_path
    output_files = os.listdir(decoded_apks_path)

    # todo: fix test usages of this function

    if apk.apk_name[:-4] in output_files:
        logger.debug(f"APK {apk.apk_name} already decompiled. Skipping.")
    else:
        # decompile to decoded_apks_path
        # Pull off the ".apk" of the name of the output file
        cmd = ["apktool", "--quiet", "d", apk.apk_path, "-o", decoded_apk_path(config, apk)]

        logger.debug(" ".join(cmd))
        run_command(cmd)

def decode_batch(config: HybridAnalysisConfig, apks:List[ApkModel]):
    for apk in apks:
        decode_apk(config, apk)

if __name__ == '__main__':
    pass

