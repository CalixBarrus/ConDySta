import subprocess
from experiment import run
from experiment.benchmarks import full_observation_processing, icc_bench_linux, rebuild_fossdroid_apks_small, test_observation_processing
from experiment.fossdroid import fossdroid_main, fossdroid_validation_experiment
from experiment.gpbench import gpbench_main, run_ic3_on_apk

from experiment.instrument import instrument_test_wild_benchmarks, instrument_test_wild_benchmarks_few, instrument_test_wild_benchmarks_full, update_heap_snapshot_smali_files
from experiment.run import install_all_apps_for_integration_testing, install_few_apps_for_integration_testing, install_original_apps, monkey_test_all_apps_for_verify_errors, record_manual_interactions, monkey_test_few_apps_for_verify_errors, run_apps_for_integration_testing_generic, uninstall_all_3rd_party_apps
from hybrid.log_process_fd import get_flowdroid_analysis_error
from util import logger
logger = logger.get_logger(__name__)


if __name__ == '__main__':
    # icc_bench_linux()
    # run_ic3_on_apk()
    # gpbench_linux()
    # ic3_linux()
    # gpbench_main()
    # fossdroid_main()

    # update_heap_snapshot_smali_files()

    uninstall_all_3rd_party_apps()
    # instrument_test_wild_benchmarks_few()
    # install_few_apps_for_integration_testing()
    # run.monkey_test_few_apps_for_verify_errors()
    # test_observation_processing()
    

    # install_original_apps([0,1])
    # monkey_test_few_apps_for_verify_errors()

    # run_apps_for_integration_testing_generic("/home/calix/programming/ConDySta/data/experiments/2024-10-07-rebuilt-and-unmodified-apks/signed-apks", "execution-test-misc", "testing rebuilt apks", [0,1])


    # rebuild_fossdroid_apks_small()

    instrument_test_wild_benchmarks_full()
    install_all_apps_for_integration_testing()
    monkey_test_all_apps_for_verify_errors()
    full_observation_processing()    

    # instrument_test_wild_benchmarks_full()

    # fossdroid_validation_experiment()

    # record_manual_interactions("io.github.lonamiwebs.klooni_820.apk.log")

    # adb install -r /home/calix/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks/eu.kanade.tachiyomi_41.apk
