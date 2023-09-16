import subprocess
from typing import List



def run_command(args: List['str']) -> str:
    """
    Run the provided commandline command using the subprocess library.
    :param args: List of strings consisting of the desired command.
    :return: Any output of the command to stdout
    """

    completed_process: subprocess.CompletedProcess = subprocess.run(args,
                                                                    capture_output=True,
                                                                    check=True,
                                                                    # Raise a python exception if the process exits with exit code != 0
                                                                    text=True # Have output be captured as a string (not bytes)
                                                                    )

    return completed_process.stdout
