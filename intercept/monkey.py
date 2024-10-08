import os
import importlib

# from "6_install" import getPackageName
import time
from subprocess import CalledProcessError
from typing import List

from hybrid.hybrid_config import HybridAnalysisConfig, signed_apk_path, apk_logcat_output_path
from intercept import install
from intercept.install import get_package_name, getApkMainIntent

from util.input import ApkModel, InputModel, BatchInputModel
from util.subprocess import run_command

import util.logger
logger = util.logger.get_logger(__name__)

def run_input_apks_model(config: HybridAnalysisConfig, input_apks_model: BatchInputModel):

    run_ungrouped_instrumented_apks(config, input_apks_model.ungrouped_apks)

    if len(input_apks_model.grouped_inputs) > 0:
        run_grouped_instrumented_apks(config, input_apks_model.grouped_inputs)

def run_ungrouped_instrumented_apks(config: HybridAnalysisConfig, apks: List[ApkModel]):
    for apk in apks:
        run_ungrouped_instrumented_apk(config, apk)

def run_ungrouped_instrumented_apk(config: HybridAnalysisConfig, apk: ApkModel):
    signed_apks_directory_path = config._signed_apks_path
    install.install_apk(signed_apk_path(signed_apks_directory_path, apk))

    apk_package_name = get_package_name(signed_apk_path(signed_apks_directory_path, apk))

    # Clear logcat so the log dump will only consist of statements relevant to this test
    _clear_logcat()

    seconds_to_test = config.seconds_to_test_each_app
    if not config.use_monkey:
        test_apk_manual(apk_package_name, seconds_to_test)
    else:
        monkey_rng_seed = config.monkey_rng_seed
        test_apk_monkey(apk_package_name, seconds_to_test,
                                seed=monkey_rng_seed)

    _dump_logcat(apk_logcat_output_path(config._logcat_dir_path, apk))

    _uninstall_apk(signed_apk_path(signed_apks_directory_path, apk))

def run_grouped_instrumented_apks(config: HybridAnalysisConfig, apk_groups: List[InputModel]):
    """
    Grouped apks should all be installed, then each apk should get run. After each apk has been run, all apks in the
    group should be uninstalled
    """
    use_monkey = config.use_monkey
    signed_apks_directory_path = config._signed_apks_path

    for apk_group in apk_groups:
        # TODO: update
        for apk in apk_group.apks:
            install.install_apk(signed_apk_path(signed_apks_directory_path, apk))

        for apk in apk_group.apks:

            # Clear logcat so the log dump will only consist of statements relevant to this test
            _clear_logcat()

            apk_package_name = get_package_name(signed_apk_path(signed_apks_directory_path, apk))
            logcat_output_path = apk_logcat_output_path(config._logcat_dir_path, apk, apk_group.input_id)

            seconds_to_test = config.seconds_to_test_each_app
            if not use_monkey:
                test_apk_manual(signed_apk_path(signed_apks_directory_path, apk), seconds_to_test)
            else:
                monkey_rng_seed = config.monkey_rng_seed
                test_apk_monkey(apk_package_name, seconds_to_test,
                                seed=monkey_rng_seed)

            _dump_logcat(logcat_output_path)

        for apk in apk_group.apks:
            _uninstall_apk(signed_apk_path(signed_apks_directory_path, apk))

def _clear_logcat():
    cmd = ["adb", "logcat", "-c"]
    logger.debug(" ".join(cmd))
    run_command(cmd)

def _dump_logcat(output_path: str):

    # dump logcat to a text file on the host machine
    # cmd = "adb logcat -d \"DySta-Instrumentation:I System.err:W *:S\" > {}" \
    #       "".format(log_file_name)
    cmd = ["adb", "logcat", "-d",
           # ">", output_path,
           ]
    logger.debug(" ".join(cmd))
    run_command(cmd, redirect_stdout=output_path)

    # simple dump to sout
    "adb logcat -d"

    # *:S silences all tags/levels except those specified.
    # DySta-Instrumentation:I Allows tags with DySta-Instrumentation up to Info level
    # System.err:W Allows tags with System.err up to Warning level
    "adb logcat -d \"DySta-Instrumentation:I System.err:W *:S\""

def _uninstall_apk(apk_path):
    # Todo: package_name should either get cached with the apk somehow, or this step of logic should be handled by install.unistall_apk
    package_name = get_package_name(apk_path)
    install.uninstall_apk(package_name)

def test_apk_manual(apk_package_name: str, block_duration: int, apk_main_intent: str="", logcat_output_path: str=""):
    """
    :param block_duration: Function will block for this number of seconds. The
    logs are collected after this function returns; this blocking behavior
    prevents the logs dump from grabbing the logs before it fills up from the
    testing.
    :return:
    """

    # apk_package_name = get_package_name(apk_path)
    # apkPackageName = getPackageName(apkName, target_apks_path)
    if not logcat_output_path == "":
        _clear_logcat()

    if apk_main_intent == "":
        apk_main_intent = getApkMainIntent(apk_package_name)

    # adb shell am start com.bignerdranch.android.buttonwithtoast/.MainActivity
    cmd = "adb shell am start {}".format(apk_main_intent)
    cmd = ["adb", "shell", "am", "start", apk_main_intent]
    logger.debug(" ".join(cmd))
    run_command(cmd)

    if block_duration > 0:
        time.sleep(block_duration)
    # if block_duration == -1: 
    #   input("Press enter when finished testing")

    # TODO: is there an adb command to quit/close the app? or notify the user?

    if not logcat_output_path == "":
        _dump_logcat(logcat_output_path)


def test_apk_monkey(apk_package_name: str, seconds_to_test: int, logcat_output_path: str="", seed: int=-1, force_stop_when_finished=False):
    # There is not explicit option to run monkey for n seconds, but a time delay
    # between events can be used.
    # As fast as possible on a toy app, monkey generated an event ~once every
    # 2.5 ms on average
    throttle_ms = 10

    num_events = int(seconds_to_test * 1000 / throttle_ms)

    # TODO: assert the target package is already installed

    # apk_package_name = get_package_name(apk_path)
    if not logcat_output_path == "":
        _clear_logcat()

    # This command will block for the duration that monkey runs.
    if seed == -1:
        cmd = ["adb", "shell", "monkey",
               "-p", apk_package_name,
               "--throttle", str(throttle_ms), str(num_events)]
    else:
        cmd = ["adb", "shell", "monkey",
               "-p", apk_package_name,
               "-s", str(seed),
               "--throttle", str(throttle_ms), str(num_events)]
    logger.debug(" ".join(cmd))

    try:
        run_command(cmd)
    except CalledProcessError as e:
        error_msg = f"Error when running {apk_package_name}, check logcat dump"

        logger.error(error_msg)

        logger.debug(f"Forcing app {apk_package_name} to stop")
        force_stop_app(apk_package_name)
        # HybridAnalysisResult.report_error(config, apk_path.split("/")[-1], error_msg)

    if force_stop_when_finished:
        logger.debug(f"Forcing app {apk_package_name} to stop")
        force_stop_app(apk_package_name)

    if not logcat_output_path == "":
        _dump_logcat(logcat_output_path)

def force_stop_app(package_name):
    "adb shell am force-stop {}"
    cmd = ["adb", "shell", "am", "force-stop", package_name]

    run_command(cmd)

if __name__ == '__main__':
    # install.installApk("data/signed-apks/StaticInitialization1.apk")
    # test_apk_manual("data/signed-apks/StaticInitialization1.apk", 10)
    _uninstall_apk("data/signed-apks/StaticInitialization1.apk")
