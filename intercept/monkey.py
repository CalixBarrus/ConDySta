import os
import importlib

# from "6_install" import getPackageName
import time

from intercept import intercept_config, install
from intercept.install import getPackageName, getApkMainIntent


def run_apk(config):
    target_apks_path = config.signed_apks_path

    use_monkey = config.use_monkey

    for apkName in os.listdir(target_apks_path):
        # Only run apks
        if not apkName.endswith(".apk"):
            continue

        log_file_path = os.path.join(config.logs_path, apkName + ".log")

        install.installApk(apkName, config.signed_apks_path)

        # Clear logcat so the log dump will only consist of statements
        # relevant to this test
        cmd = "adb logcat -c"
        print(cmd)
        os.system(cmd)

        seconds_to_test = config.seconds_to_test_each_app
        if not use_monkey:
            test_apk_manual(target_apks_path, apkName, seconds_to_test)
        else:
            monkey_rng_seed = config.monkey_rng_seed
            test_apk_monkey(target_apks_path, apkName, seconds_to_test,
                            monkey_rng_seed)

        # dump logcat to a text file on the host machine
        # cmd = "adb logcat -d \"DySta-Instrumentation:I System.err:W *:S\" > {}" \
        #       "".format(log_file_name)
        cmd = "adb logcat -d > '{}'".format(log_file_path)
        print(cmd)
        os.system(cmd)

        # simple dump to sout
        "adb logcat -d"

        # *:S silences all tags/levels except those specified.
        # DySta-Instrumentation:I Allows tags with DySta-Instrumentation up to Info level
        # System.err:W Allows tags with System.err up to Warning level
        "adb logcat -d \"DySta-Instrumentation:I System.err:W *:S\""

        packageName = getPackageName(apkName, config.signed_apks_path)
        install.uninstall_apk(packageName)

    # cmd = "adb shell monkey -p {} -v 500".format(apkPackageName)


def test_apk_manual(target_apks_path, apkName: str, block_duration):
    """
    :param apkName:
    :param block_duration: Function will block for this number of seconds. The
    logs are collected after this function returns; this blocking behavior
    prevents the logs dump from grabbing the logs before it fills up from the
    testing.
    :return:
    """

    apkPackageName = getPackageName(apkName, target_apks_path)
    apkMainIntent = getApkMainIntent(apkPackageName)

    # adb shell am start com.bignerdranch.android.buttonwithtoast/.MainActivity
    cmd = "adb shell am start {}".format(apkMainIntent)
    print(cmd)
    os.system(cmd)

    if block_duration > 0:
        time.sleep(block_duration)


def test_apk_monkey(target_apks_path, apkName: str, seconds_to_test, seed=-1):
    # There is not explicit option to run monkey for n seconds, but a time delay
    # between events can be used.

    # As fast as possible on a toy app, monkey generated an event ~once every
    # 2.5 ms on average
    throttle_ms = 3

    num_events = int(seconds_to_test * 1000 / throttle_ms)

    apkPackageName = getPackageName(apkName, target_apks_path)
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
    configuration = intercept_config.get_default_intercept_config()

    run_apk(configuration)
    pass
