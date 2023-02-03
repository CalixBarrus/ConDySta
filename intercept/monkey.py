import os
import importlib

# from "6_install" import getPackageName
import time

install_script = importlib.import_module("6_install")

def main():

    for apkName in os.listdir(target_apks_path):

        # Only run apks
        if not apkName.endswith(".apk"):
            continue


        cmd = "adb logcat -c"
        print(cmd)
        os.system(cmd)

        runApk(apkName)


        cmd = "adb logcat -d > {}".format(log_file_name)
        print(cmd)
        os.system(cmd)

        # *:S silences all tags/levels except those specified.
        # DySta-Instrumentation:I Allows tags with DySta-Instrumentation up to Info level
        # System.err:W Allows tags with System.err up to Warning level
        "adb logcat -d \"DySta-Instrumentation:I System.err:W *:S\""

def runApk(apkName: str):
    seconds_to_test = 5

    # runApkManual(apkName, seconds_to_test)
    monkey_rng_seed = 42
    runApkMonkey(apkName, seconds_to_test, monkey_rng_seed)

    # cmd = "adb shell monkey -p {} -v 500".format(apkPackageName)

def runApkManual(apkName: str, block_duration):
    """

    :param apkName:
    :param block_duration: Function will block for this number of seconds. The
    logs are collected after this function returns; this blocking behavior
    prevents the log dump from grabbing the log before it fills up from the
    testing.
    :return:
    """

    apkPackageName = install_script.getPackageName(apkName, target_apks_path)
    apkMainIntent = install_script.getApkMainIntent(apkPackageName)

    # adb shell am start com.bignerdranch.android.buttonwithtoast/.MainActivity
    cmd = "adb shell am start {}".format(apkMainIntent)
    print(cmd)
    os.system(cmd)

    if block_duration > 0:
        time.sleep(block_duration)

def runApkMonkey(apkName: str, seconds_to_test, seed = -1):
    # There is not explicit option to run monkey for n seconds, but a time delay
    # between events can be used.

    # As fast as possible on a toy app, monkey generated an event ~once every
    # 2.5 ms
    throttle_ms = 3

    num_events = int(seconds_to_test * 1000 / throttle_ms)

    apkPackageName = install_script.getPackageName(apkName, target_apks_path)
    if seed == -1:
        cmd = "adb shell monkey -p {} -v --throttle {} {}".format(
            apkPackageName, throttle_ms, num_events)
    else:
        cmd = "adb shell monkey -p {} -v -s {} --throttle {} {}".format(
            apkPackageName, seed, throttle_ms, num_events)

    print(cmd)
    # This command will block for the duration that monkey runs.
    os.system(cmd)

if __name__ == '__main__':
    target_apks_path = "signed-apks/"
    log_file_name = "../logs/test_monkey_run.log"
    main()
    pass