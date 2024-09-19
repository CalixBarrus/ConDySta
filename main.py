import subprocess
from experiment.benchmarks import icc_bench_linux
from experiment.fossdroid import fossdroid_main, fossdroid_validation_experiment
from experiment.gpbench import flowdroid_help, gpbench_main, ic3_linux, run_ic3_on_apk

from experiment.instrument import instrument_test_wild_benchmarks, instrument_test_wild_benchmarks_few, instrument_test_wild_benchmarks_full
from experiment.run import install_apps_for_integration_testing, run_apps_for_integration_testing
from hybrid.log_process_fd import get_analysis_error_in_flowdroid_log
from util import logger
logger = logger.get_logger(__name__)


if __name__ == '__main__':
    # icc_bench_linux()
    # run_ic3_on_apk()
    # gpbench_linux()
    # ic3_linux()
    # gpbench_main()
    # fossdroid_main()
    
    # instrument_test_wild_benchmarks_few()
    # instrument_test_wild_benchmarks_full()
    # install_apps_for_integration_testing()
    run_apps_for_integration_testing()

    # fossdroid_validation_experiment()
