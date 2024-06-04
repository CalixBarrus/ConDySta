import os
import subprocess
from typing import List

from util import logger

logger = logger.get_logger('intercept', 'rebuild')


def run_command(args: List['str'], redirect_stdout: str = "",
                redirect_stderr_to_stdout=False) -> str:
    """
    Run the provided commandline command using the subprocess library.
    :param args: List of strings consisting of the desired command.
    :return: Any output of the command to stdout
    """

    debug_cmd = " ".join(args)

    if redirect_stdout == "":
        # TODO: how to view stderr with the exception that gets thrown?
        completed_process = subprocess.run(args,
                                           capture_output=True,
                                           check=True,
                                           # Raise a python exception if the process exits with exit code != 0
                                           text=True
                                           # Have output be captured as a string (not bytes)
                                           )
        if completed_process.stderr != "":
            logger.error(completed_process.stderr)

        return completed_process.stdout
    else:
        if not redirect_stderr_to_stdout:
            with open(redirect_stdout, 'w') as out_file:
                completed_process = subprocess.run(args,
                                                   stdout=out_file,
                                                   check=True,
                                                   )
            return ""
        else:
            with open(redirect_stdout, 'w') as out_file:
                completed_process = subprocess.run(args,
                                                   stderr=subprocess.STDOUT,
                                                   stdout=out_file,
                                                   check=True,
                                                   )
            return ""

def run_command_direct(args: List['str']) -> None:
    """
    Run the command, but just in whatever current shell is running
    """

    print(" ".join(args))
    os.system(" ".join(args))
