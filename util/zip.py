import os
from util.subprocess import run_command

def zip_dir(target_dir_path, output_dir_path, output_file_name):
    cmd = ["zip", "-r", os.path.join(output_dir_path, output_file_name), target_dir_path]

    stdout = run_command(cmd)

