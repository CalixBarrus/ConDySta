import subprocess
from experiment import run
from experiment.benchmarks import icc_bench_linux
from experiment.fossdroid import fossdroid_main, fossdroid_validation_experiment
from experiment.gpbench import flowdroid_help, gpbench_main, ic3_linux, run_ic3_on_apk

from experiment.instrument import instrument_test_wild_benchmarks, instrument_test_wild_benchmarks_few, instrument_test_wild_benchmarks_full
from experiment.run import install_few_apps_for_integration_testing, record_manual_interactions, monkey_test_few_apps_for_verify_errors
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
    # install_few_apps_for_integration_testing()
    # monkey_test_few_apps_for_verify_errors()
    

    instrument_test_wild_benchmarks_full()
    run.monkey_test_all_apps_for_verify_errors()

    # instrument_test_wild_benchmarks_full()

    # fossdroid_validation_experiment()

    # record_manual_interactions()

    # adb install -r /home/calix/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks/eu.kanade.tachiyomi_41.apk
