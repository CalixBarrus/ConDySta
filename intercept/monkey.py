import os
import importlib

# from "6_install" import getPackageName
import time
from subprocess import CalledProcessError
from typing import Callable, Dict, List

from hybrid.hybrid_config import HybridAnalysisConfig, apk_path, apk_logcat_output_path
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
    install.install_apk(apk_path(signed_apks_directory_path, apk))

    apk_package_name = get_package_name(apk_path(signed_apks_directory_path, apk))
    apk.apk_package_name = apk_package_name

    # Clear logcat so the log dump will only consist of statements relevant to this test
    _clear_logcat()

    seconds_to_test = config.seconds_to_test_each_app
    if not config.use_monkey:
        test_apk_manual(apk, seconds_to_test)
    else:
        monkey_rng_seed = config.monkey_rng_seed
        test_apk_monkey(apk, seconds_to_test,
                                seed=monkey_rng_seed)

    _dump_logcat(apk_logcat_output_path(config._logcat_dir_path, apk))

    _uninstall_apk(apk_path(signed_apks_directory_path, apk))

def run_grouped_instrumented_apks(config: HybridAnalysisConfig, apk_groups: List[InputModel]):
    """
    Grouped apks should all be installed, then each apk should get run. After each apk has been run, all apks in the
    group should be uninstalled
    """
    use_monkey = config.use_monkey
    signed_apks_directory_path = config._signed_apks_path

    for apk_group in apk_groups:
        # TODO: update
        for apk in apk_group.apks():
            install.install_apk(apk_path(signed_apks_directory_path, apk))

        for apk in apk_group.apks():

            # Clear logcat so the log dump will only consist of statements relevant to this test
            _clear_logcat()

            apk_package_name = get_package_name(apk_path(signed_apks_directory_path, apk))
            apk.apk_package_name = apk_package_name
            logcat_output_path = apk_logcat_output_path(config._logcat_dir_path, apk, apk_group.input_id)

            seconds_to_test = config.seconds_to_test_each_app
            if not use_monkey:
                test_apk_manual(apk, seconds_to_test)
            else:
                monkey_rng_seed = config.monkey_rng_seed
                test_apk_monkey(apk, seconds_to_test,
                                seed=monkey_rng_seed)

            _dump_logcat(logcat_output_path)

        for apk in apk_group.apks():
            _uninstall_apk(apk_path(signed_apks_directory_path, apk))

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


def test_apk_method_factory(execution_input_approach: str, monkey_kwargs: Dict[str, str]) -> Callable[[ApkModel, str], None]:
    """
    execution_input_approach: "monkey" or "manual"
    monkey_kwargs: dictionary of kwargs to pass to the monkey test method
    """
    default_seconds_to_test = 60
    default_force_stop_when_finished = True

    seconds_to_test = default_seconds_to_test

    if "seconds_to_test" in monkey_kwargs.keys():
        seconds_to_test = monkey_kwargs["seconds_to_test"]

    if execution_input_approach == "monkey": 
        # seconds_to_test = 60

        f = lambda apk_model, logcat_output_path: test_apk_monkey(apk_model, seconds_to_test=seconds_to_test, logcat_output_path=logcat_output_path, force_stop_when_finished=default_force_stop_when_finished)
    elif execution_input_approach == "manual":
        f = lambda apk_model, logcat_output_path: test_apk_manual(apk_model, seconds_to_test=seconds_to_test, logcat_output_path=logcat_output_path, force_stop_when_finished=default_force_stop_when_finished)
    else: 
        assert False

    return f

def test_apk_monkey(apk_model: ApkModel, seconds_to_test: int, logcat_output_path: str="", seed: int=-1, force_stop_when_finished=False):
    apk_package_name = apk_model.apk_package_name
    if apk_package_name is None:
        raise ValueError()
    # There is not explicit option to run monkey for n seconds, but a time delay
    # between events can be used.
    # As fast as possible on a toy app, monkey generated an event ~once every
    # 2.5 ms on average


    # TODO: assert the target package is already installed

    # apk_package_name = get_package_name(apk_path)
    # if not logcat_output_path == "":
    #     _clear_logcat()

    throttle_ms = 10

    num_events = int(seconds_to_test * 1000 / throttle_ms)


    def temp_monkey_command():
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

            logger.error(error_msg.splitlines())

            logger.debug(f"Forcing app {apk_package_name} to stop")
            force_stop_app(apk_package_name)
            # HybridAnalysisResult.report_error(config, apk_path.split("/")[-1], error_msg)
        else:
            if force_stop_when_finished:
                logger.debug(f"Forcing app {apk_package_name} to stop")
                force_stop_app(apk_package_name)

    _dump_logcat_around_command(logcat_output_path, temp_monkey_command)
    # if not logcat_output_path == "":
    #     _dump_logcat(logcat_output_path)    

def test_apk_manual(apk_model: ApkModel, seconds_to_test: int, logcat_output_path: str="", force_stop_when_finished=False):
    apk_application_label: str = apk_model.apk_application_label
    apk_package_name: str = apk_model.apk_package_name
    assert apk_application_label != ""  # client needs to use optional param of get_package_name so this is filled out.

    def temp_manual_command():
        # if apk_main_intent == "":
        #     apk_main_intent = getApkMainIntent(apk_package_name)

        # # adb shell am start com.bignerdranch.android.buttonwithtoast/.MainActivity
        # cmd = "adb shell am start {}".format(apk_main_intent)
        # cmd = ["adb", "shell", "am", "start", apk_main_intent]
        # logger.debug(" ".join(cmd))
        # run_command(cmd)

        logger.info(f"Please Open App {apk_application_label} and test. Sleeping for {seconds_to_test} seconds.")
        time.sleep(seconds_to_test)
        logger.info("Testing finished. Please close app and press any key to continue. ")
        input()
        if force_stop_when_finished:
            force_stop_app(apk_package_name)

    _dump_logcat_around_command(logcat_output_path, temp_manual_command)


def _dump_logcat_around_command(logcat_output_path, command):
    if not logcat_output_path == "":
        _clear_logcat()

    command()

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
