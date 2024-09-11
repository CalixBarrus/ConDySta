import subprocess
from experiment.benchmarks import icc_bench_linux
from experiment.fossdroid import fossdroid_main
from experiment.gpbench import flowdroid_help, gpbench_main, ic3_linux, run_ic3_on_apk

from hybrid.log_process_fd import get_analysis_error_in_flowdroid_log
from util import logger
logger = logger.get_logger(__name__)


if __name__ == '__main__':
    # icc_bench_linux()
    # run_ic3_on_apk()
    # gpbench_linux()
    # ic3_linux()
    gpbench_main()
    # fossdroid_main()

