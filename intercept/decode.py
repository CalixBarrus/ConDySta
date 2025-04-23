import copy
import os
import shutil
import subprocess
from typing import List, Tuple

import pandas as pd

from experiment.paths import StepInfoInterface
from hybrid.hybrid_config import HybridAnalysisConfig
from hybrid import hybrid_config
from util.input import ApkModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

class DecodeApk(StepInfoInterface):
    apktool_path: str

    def __init__(self):
        self.apktool_path = "apktool" # TODO: move this to external_path

    @property
    def step_name(self) -> str:
        return "decode"

    @property
    def version(self) -> Tuple[int, int, int]:
        return (0, 1, 0)

    @property
    def concise_params(self) -> List[str]:
        return []

    def execute(self, input_df: pd.DataFrame):
        # Input: df with columns "Input APK Path", "Decompiled Path"
        # Output: in paths indicated by "Decompiled Path"

        for i in input_df.index:
            _decode_apk(self.apktool_path, input_df.loc[i, "Input APK Path"], input_df.loc[i, "Decompiled Path"])


# def decode_apk(config: HybridAnalysisConfig, apk:ApkModel, clean:bool=False):
def decode_apk(decoded_apks_directory_path: str, apk: ApkModel, clean:bool=False):
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
    apk_path = apk.apk_path

    _decode_apk(apktool_path, apk_path, decoded_apk_path)

def _decode_apk(apktool_path, input_apk_path, decoded_apk_path):
    # ApkToolSettings
    java_heap_size = ""
    java_heap_size = "8g"
    java_heap_arg = ["-JXmx" + java_heap_size] if java_heap_size != "" else []

    cmd = [apktool_path, "--quiet", "d", input_apk_path, "-o", decoded_apk_path]
    # cmd = [apktool_path, "d", input_apk_path, "-o", decoded_apk_path]
    cmd = [apktool_path] + java_heap_arg + ["d", input_apk_path, "-o", decoded_apk_path]

    logger.debug(" ".join(cmd))
    apk_tool_message = run_command(cmd)
    logger.debug(apk_tool_message)

# def decode_batch(config: HybridAnalysisConfig, apks:List[ApkModel], clean: bool=False):
def decode_batch(decoded_apks_directory_path: str, apks:List[ApkModel], clean: bool=False):
    
    for apk in apks:
        decode_apk(decoded_apks_directory_path, apk, clean)

if __name__ == '__main__':
    pass

