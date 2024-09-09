import os
from typing import List

from intercept.install import get_package_name
from util.input import InputModel
from util.subprocess import run_command_direct, run_command

from util import logger
logger = logger.get_logger('hybrid', 'ic3')


def run_ic3_on_apk_direct(ic3_jar_path: str, android_path: str, input_model: InputModel, output_dir_path):

    cmd = ["java", "-jar", ic3_jar_path, "-a", input_model.apk().apk_path, "-cp", android_path, "-protobuf", output_dir_path]

    run_command_direct(cmd)

    """
    Results file name example
    org.arguslab.icc_explicit_nosrc_nosink_1.txt
    
    They seem to be named [apk file name, less ".apk"]_n, where n is some integer
    """


def run_ic3_on_apk(ic3_jar_path: str, android_path: str, input_model: InputModel, output_dir_path, record_logs: str="", timeout: int=None) -> str:
    cmd = ["java", "-jar", ic3_jar_path, "-a", input_model.apk().apk_path, "-cp", android_path, "-protobuf", output_dir_path]

    # I'm not sure exactly the naming convention used by ic3 for its outputs, so we will do some detective work.
    orig_filenames: List[str] = os.listdir(output_dir_path)

    logger.debug(" ".join(cmd))

    if record_logs != "":
        run_command(cmd, redirect_stdout=record_logs, redirect_stderr_to_stdout=True, timeout=timeout)
    else:
        run_command(cmd, timeout=timeout)
    """
    Results file name example
    org.arguslab.icc_explicit_nosrc_nosink_1.txt

    They seem to be named [apk file name, less ".apk"]_n, where n is some integer
    """

    # check if a file was added. If none, check for a file name containing the apk's name. Raise an error otherwise
    new_filenames: List[str] = os.listdir(output_dir_path)
    difference = list(set(new_filenames) - set(orig_filenames))
    if len(difference) == 1:
        return os.path.join(output_dir_path, difference[0])
    elif len(difference) > 1:
        raise AssertionError("Unexpected behavior, ic3 produced >1 files: " + str(difference))
    else:
        result_filename = None
        for filename in new_filenames:

            if input_model.apk().apk_package_name is None:
                input_model.apk().apk_package_name = get_package_name(input_model.apk().apk_path)

            if input_model.apk().apk_package_name in filename:
                if result_filename is not None:
                    raise AssertionError("More than 1 file found containing apk name " + input_model.apk().apk_name + " in directory " + output_dir_path)
                result_filename = filename
        if result_filename is None:
            raise AssertionError("No file created nor matching file found in directory " + output_dir_path)
        return os.path.join(output_dir_path, result_filename)

def run_ic3_script_on_apk(ic3_script_root_path: str, apk_path: str, android_path: str, timeout:int=None)-> str:
    """
    Wrapper for script from zhang_2021_gpbench authors

    android_path must be the path to the correct version of the android sdk

    Returns the path of the created ICC_Model (throws error if none)
    """

    logger.debug(f"For IC3 logs for apk at {apk_path}, see {ic3_script_root_path}")

    # Find name of created 
    orig_filenames: List[str] = os.listdir(os.path.join(ic3_script_root_path, "dir_iccmodel"))

    cmd = ["./runIC3.sh", apk_path, android_path]
    run_command(cmd, timeout=timeout, cwd=ic3_script_root_path)

    new_filenames: List[str] = os.listdir(os.path.join(ic3_script_root_path, "dir_iccmodel"))
    difference = list(set(new_filenames) - set(orig_filenames))
    if len(difference) == 1:
        return os.path.join(ic3_script_root_path, "dir_iccmodel", difference[0])
    else:
        raise ValueError(f"Unexpected behavior, ic3 produced {len(difference)} files: " + str(difference))
    
    








