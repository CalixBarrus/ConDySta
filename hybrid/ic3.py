import os
from typing import List

from util.input import InputModel
from util.subprocess import run_command_direct, run_command


def run_ic3_on_apk_direct(ic3_jar_path: str, android_path: str, apk_path, output_dir_path):

    cmd = ["java", "-jar", ic3_jar_path, "-a", apk_path, "-cp", android_path, "-protobuf", output_dir_path]

    run_command_direct(cmd)

    """
    Results file name example
    org.arguslab.icc_explicit_nosrc_nosink_1.txt
    
    They seem to be named [apk file name, less ".apk"]_n, where n is some integer
    """


def run_ic3_on_apk(ic3_jar_path: str, android_path: str, input_model: InputModel, output_dir_path, record_logs: str="") -> str:
    cmd = ["java", "-jar", ic3_jar_path, "-a", input_model.apk().apk_path, "-cp", android_path, "-protobuf", output_dir_path]

    # I'm not sure exactly the naming convention used by ic3 for its outputs, so we will do some detective work.
    orig_filenames: List[str] = os.listdir(output_dir_path)

    if record_logs != "":
        run_command(cmd, redirect_stdout=record_logs, redirect_stderr_to_stdout=True)
    else:
        run_command(cmd)
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
            if input_model.apk().apk_name in filename:
                if result_filename is not None:
                    raise AssertionError("More than 1 file found containing apk name " + input_model.apk().apk_name + " in directory " + output_dir_path)
                result_filename = filename
        if result_filename is None:
            raise AssertionError("No file created nor matching file found in directory " + output_dir_path)
        return os.path.join(output_dir_path, result_filename)




