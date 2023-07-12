
import os
import pexpect
import sys


# for line in open("/home/xueling/apkAnalysis/invokeDetection/apkName_1007").readlines():
#     line = line.strip() + ".apk"
#     apkNameList.append(line)
# print len(apkNameList)
from intercept import intercept_config

from util import logger
logger = logger.get_logger('intercept', 'rebuild')

def rebuild(config):
    logger.info("Rebuilding instrumented smali code...")

    decoded_apks_path = config.decoded_apks_path
    rebuilt_apks_path = config.rebuilt_apks_path

    for apkName in os.listdir(decoded_apks_path):
        apk_name_with_suffix = apkName + ".apk"

        if apk_name_with_suffix in os.listdir(rebuilt_apks_path):
            logger.debug(f"Instrumented APK {apk_name_with_suffix} already in "
                  f"{rebuilt_apks_path}, skipping.")
            continue

        else:
            cmd = "apktool --quiet b '{}' -o '{}' --use-aapt2".format(
                os.path.join(decoded_apks_path, apkName),
                os.path.join(rebuilt_apks_path, apk_name_with_suffix))
            logger.debug(cmd)
            os.system(cmd)

if __name__ == '__main__':
    configuration = intercept_config.get_default_intercept_config()

    rebuild(configuration)