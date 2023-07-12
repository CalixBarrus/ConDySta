# decode
import copy
import os
# import commands
import subprocess

import intercept.intercept_config
from intercept import intercept_main, intercept_config

from util import logger
logger = logger.get_logger('intercept', 'decode')

# apkNameList = []

def decode(config: intercept_config.InterceptConfig):
    logger.info("Decoding input APKs...")

    input_apks = config.input_apks
    decoded_apks_path = config.decoded_apks_path
    output_files = os.listdir(decoded_apks_path)

    for input_apk in input_apks:

        if input_apk.apk_name in output_files:
            logger.debug(f"APK {input_apk.apk_name} already decompiled. Skipping.")
            continue
        else:
            # decompile to decoded_apks_path
            # Pull off the ".apk" of the name of the output file
            cmd = "apktool --quiet d '{}' -o '{}'".format(
                input_apk.apk_path,
                os.path.join(decoded_apks_path, input_apk.apk_name[:-4]))
            logger.debug(cmd)
            os.system(cmd)


if __name__ == '__main__':
    config = intercept_config.get_default_intercept_config()

    decode(config)


# move()
