import os
import importlib

# from "6_install" import getPackageName
import time
from subprocess import CalledProcessError
from typing import List

from hybrid.hybrid_config import HybridAnalysisConfig, signed_apk_path, apk_logcat_dump_path
from hybrid.results import HybridAnalysisResult
from intercept import install
from intercept.install import get_package_name, getApkMainIntent


from util import logger
from util.input import ApkModel, InputModel, BatchInputModel
from util.subprocess import run_command

logger = logger.get_logger('intercept', 'monkey')

def run_input_apks_model(config: HybridAnalysisConfig, input_apks_model: BatchInputModel):

    run_ungrouped_instrumented_apks(config, input_apks_model.ungrouped_apks)

    if len(input_apks_model.grouped_inputs) > 0:
        run_grouped_instrumented_apks(config, input_apks_model.grouped_inputs)

def run_ungrouped_instrumented_apks(config: HybridAnalysisConfig, apks: List[ApkModel]):
    for apk in apks:
        run_ungrouped_instrumented_apk(config, apk)

def run_ungrouped_instrumented_apk(config: HybridAnalysisConfig, apk: ApkModel):
    install.installApk(signed_apk_path(config, apk))

    # Clear logcat so the log dump will only consist of statements relevant to this test
    _clear_logcat()

    seconds_to_test = config.seconds_to_test_each_app
    if not config.use_monkey:
        test_apk_manual(signed_apk_path(config, apk), seconds_to_test)
    else:
        monkey_rng_seed = config.monkey_rng_seed
        test_apk_monkey(config, signed_apk_path(config, apk), seconds_to_test,
                        monkey_rng_seed)

    _dump_logcat(config, apk_logcat_dump_path(config, apk))

    _uninstall_apk(signed_apk_path(config, apk))

def run_grouped_instrumented_apks(config: HybridAnalysisConfig, apk_groups: List[InputModel]):
    """
    Grouped apks should all be installed, then each apk should get run. After each apk has been run, all apks in the
    group should be uninstalled
    """
    use_monkey = config.use_monkey

    for apk_group in apk_groups:
        # TODO: update
        for apk in apk_group.apks:
            install.installApk(signed_apk_path(config, apk))

        for apk in apk_group.apks:

            # Clear logcat so the log dump will only consist of statements relevant to this test
            _clear_logcat()

            seconds_to_test = config.seconds_to_test_each_app
            if not use_monkey:
                test_apk_manual(signed_apk_path(config, apk), seconds_to_test)
            else:
                monkey_rng_seed = config.monkey_rng_seed
                test_apk_monkey(config, signed_apk_path(config, apk), seconds_to_test,
                                monkey_rng_seed)

            _dump_logcat(config, apk_logcat_dump_path(config, apk, apk_group.input_id))

        for apk in apk_group.apks:
            _uninstall_apk(signed_apk_path(config, apk))

def _clear_logcat():
    cmd = ["adb", "logcat", "-c"]
    logger.debug(" ".join(cmd))
    run_command(cmd)

def _dump_logcat(config: HybridAnalysisConfig, output_path: str):

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

def test_apk_manual(apk_path: str, block_duration: int):
    """
    :param block_duration: Function will block for this number of seconds. The
    logs are collected after this function returns; this blocking behavior
    prevents the logs dump from grabbing the logs before it fills up from the
    testing.
    :return:
    """

    apk_package_name = get_package_name(apk_path)
    # apkPackageName = getPackageName(apkName, target_apks_path)
    apk_main_intent = getApkMainIntent(apk_package_name)

    # adb shell am start com.bignerdranch.android.buttonwithtoast/.MainActivity
    cmd = "adb shell am start {}".format(apk_main_intent)
    cmd = ["adb", "shell", "am", "start", apk_main_intent]
    logger.debug(" ".join(cmd))
    run_command(cmd)

    if block_duration > 0:
        time.sleep(block_duration)


def test_apk_monkey(config: HybridAnalysisConfig, apk_path: str, seconds_to_test: int,
                    seed: int=-1):
    # There is not explicit option to run monkey for n seconds, but a time delay
    # between events can be used.
    # As fast as possible on a toy app, monkey generated an event ~once every
    # 2.5 ms on average
    throttle_ms = 10

    num_events = int(seconds_to_test * 1000 / throttle_ms)

    apk_package_name = get_package_name(apk_path)

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
        error_msg = f"Error when running {apk_path}, check logcat dump"

        logger.error(error_msg)
        HybridAnalysisResult.report_error(config, apk_path.split("/")[-1], error_msg)


if __name__ == '__main__':
    # install.installApk("data/signed-apks/StaticInitialization1.apk")
    # test_apk_manual("data/signed-apks/StaticInitialization1.apk", 10)
    _uninstall_apk("data/signed-apks/StaticInitialization1.apk")
