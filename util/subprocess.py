import os
import subprocess
from typing import List

import util.logger
logger = util.logger.get_logger(__name__)


def run_command(args: List['str'], redirect_stdout: str = "",
                redirect_stderr_to_stdout=True, timeout=None, cwd=None, verbose=False) -> str:
    """
    Run the provided commandline command using the subprocess library.
    :param args: List of strings consisting of the desired command.
    :param redirect_stdout: str, file name to which stdout should be redirected. No redirect if empty string.
    :param redirect_stderr_to_stdout: bool
    :param timeout: int, No timeout if None. Timeout is in seconds. Timeout produces TimeoutExpired exception
    :return: Any output of the command to stdout
    """

    debug_cmd = " ".join(args)
    if verbose:
        logger.debug(debug_cmd)

    try:
        if redirect_stdout == "":
            completed_process = subprocess.run(args,
                                            capture_output=True,
                                            check=True,
                                            # Raise a python exception if the process exits with exit code != 0
                                            text=True,
                                            # Have output be captured as a string (not bytes)
                                            timeout=timeout,
                                            cwd=cwd,
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
                                                    timeout=timeout,
                                                    cwd=cwd,
                                                    )
                return ""
            else:
                with open(redirect_stdout, 'w') as out_file:
                    completed_process = subprocess.run(args,
                                                        stderr=subprocess.STDOUT,
                                                        stdout=out_file,
                                                        check=True,
                                                        timeout=timeout,
                                                        cwd=cwd,
                                                        )
                return ""
    except subprocess.CalledProcessError as e:
        logger.error("Error running command: " + debug_cmd)
        if str(e.stderr) != "":
            debug_stderr = str(e.stderr)
            msg = "STDERR First Line: " + debug_stderr.splitlines()[0]
            logger.error(msg)
        if str(e.stdout) != "":
            debug_stdout = str(e.stdout)
            msg = "STDOUT First Line: " + debug_stdout.splitlines()[0]
            logger.error(msg)
        raise e

def run_command_direct(args: List['str']) -> None:
    """
    Run the command, but just in whatever current shell is running
    """

    print(" ".join(args))
    os.system(" ".join(args))
