import subprocess
from experiment import run
from experiment.benchmarks import test_full_flowdroid_comparison_wild_benchmarks, test_full_flowdroid_on_wild_benchmarks, test_full_observation_processing, icc_bench_linux, test_rebuild_fossdroid_apks_small, test_rebuild_wild_benchmarks_full, test_rebuild_wild_benchmarks_several, test_small_flowdroid_comparison_wild_benchmarks, test_small_flowdroid_on_wild_benchmarks, test_small_observation_processing, test_spot_check_flowdroid_comparison, test_spot_check_flowdroid_output_processing, test_spotcheck_observation_processing
from experiment.common import get_fossdroid_files, get_gpbench_files
from experiment.fossdroid import test_fossdroid_validation_experiment
from experiment.gpbench import run_ic3_on_apk

from experiment.instrument import instrument_test_wild_benchmarks, instrument_test_wild_benchmarks_few, instrument_test_wild_benchmarks_full, update_heap_snapshot_smali_files
from experiment.run import install_all_apps_for_integration_testing, install_few_apps_for_integration_testing, install_original_fossdroid_apps, manual_test_all_apps_recording_output, manual_test_few_apps_recording_output, monkey_test_all_apps_recording_output, monkey_test_few_apps_recording_output, test_apps_spot_check, uninstall_all_3rd_party_apps
from hybrid.log_process_fd import get_flowdroid_analysis_error
from util import logger
logger = logger.get_logger(__name__)


if __name__ == '__main__':
    # icc_bench_linux()
    # run_ic3_on_apk()
    # gpbench_linux()
    # ic3_linux()

    # test_small_flowdroid_on_wild_benchmarks()
    # test_full_flowdroid_on_wild_benchmarks()

    # update_heap_snapshot_smali_files()

    # uninstall_all_3rd_party_apps()
    # instrument_test_wild_benchmarks_few()
    # run.monkey_test_few_apps_recording_output()
    # manual_test_few_apps_recording_output()

    # test_small_observation_processing("h5")
    # test_small_flowdroid_comparison_wild_benchmarks()
    # test_spot_check_flowdroid_output_processing("/home/calix/programming/ConDySta/data/experiments/2024-10-23-flowdroid-comparison-small-gpbench/augmented-flowdroid-logs")

    # recursion depth of 3 on gpbench w/ monkey
    # test_spotcheck_observation_processing(get_gpbench_files(), "/home/calix/programming/ConDySta/data/experiments/2024-10-09-execution-full-gpbench0/logcat-output")
    # recursion depth of 1 on gpbench w/ monkey
    # test_spotcheck_observation_processing(get_gpbench_files(), "/home/calix/programming/ConDySta/data/experiments/2024-10-10-execution-full-gpbench/logcat-output")

    # # This fossdroid run had 1 discovered source for app with id 1
    # test_spot_check_flowdroid_comparison(get_fossdroid_files(), "/home/calix/programming/ConDySta/data/experiments/2024-10-08-execution-test-full-fossdroid/logcat-output", [1])

    # The recursion depth of 1 and 3, had discovered sources on apps 4,5,19,20 and 13,21, respectively
    # test_spot_check_flowdroid_comparison(get_gpbench_files(), "/home/calix/programming/ConDySta/data/experiments/2024-10-10-execution-full-gpbench/logcat-output", [4,5,19,20])
    # test_spot_check_flowdroid_comparison(get_gpbench_files(), "/home/calix/programming/ConDySta/data/experiments/2024-10-09-execution-full-gpbench0/logcat-output", [13,21])
    # No dice. These FD runs didn't detect any additional flows. 



    # install_original_apps([0,1])
    # monkey_test_few_apps_for_verify_errors()
    # test_apps_spot_check(get_gpbench_files(), "several", "/home/calix/programming/benchmarks/wild-apps/data/gpbench/apks")
    # test_apps_spot_check(get_fossdroid_files(), "several", "/home/calix/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks")
    # test_spotcheck_observation_processing(get_gpbench_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-execution-spotcheck-several-gpbench-orig5s/logcat-output")
    # test_spotcheck_observation_processing(get_fossdroid_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-execution-spotcheck-several-fossdroid-orig5s/logcat-output")


    # run_apps_for_integration_testing_generic("/home/calix/programming/ConDySta/data/experiments/2024-10-07-rebuilt-and-unmodified-apks/signed-apks", "execution-test-misc", "testing rebuilt apks", [0,1])


    # test_rebuild_fossdroid_apks_small()
    # test_rebuild_wild_benchmarks_full()
    # test_rebuild_wild_benchmarks_several()
    # test_apps_spot_check(get_gpbench_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-plain-rebuild-several-on-gpbench/signed-apks")
    # test_apps_spot_check(get_fossdroid_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-plain-rebuild-several-on-fossdroid/signed-apks")
    # test_spotcheck_observation_processing(get_gpbench_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-execution-spotcheck-several-gpbench/logcat-output")
    # test_spotcheck_observation_processing(get_fossdroid_files(), "several", "/home/calix/programming/ConDySta/data/experiments/2024-10-17-execution-spotcheck-several-fossdroid/logcat-output")

    # instrument_test_wild_benchmarks_full()
    # install_all_apps_for_integration_testing()
    # monkey_test_all_apps_recording_output()
    # manual_test_all_apps_recording_output()
    # test_full_observation_processing()    

    test_full_flowdroid_comparison_wild_benchmarks()


    

    

    # fossdroid_validation_experiment()

    # record_manual_interactions("io.github.lonamiwebs.klooni_820.apk.log")

    # adb install -r /home/calix/programming/benchmarks/wild-apps/data/fossdroid/fossdroid_apks/eu.kanade.tachiyomi_41.apk

