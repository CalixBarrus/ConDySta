

import os
import shutil
import pytest
from experiment.benchmark_name import BenchmarkName
from experiment.instrument import InstrumentationApproach, setup_dynamic_value_analysis_strategies
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from hybrid import hybrid_config
from intercept import decode
from intercept.decoded_apk_model import DecodedApkModel
from util.input import InputModel


# TODO: this is copied from intercept.test_instrument.py
@pytest.fixture(scope='module')
def onxmaps_apk_model():
    df_file_paths = get_wild_benchmarks(BenchmarkName.GPBENCH)[0]
    df = LoadBenchmark(df_file_paths).execute()
    onx_input_model: InputModel
    onx_input_model = df.at[19, "Input Model"]

    return onx_input_model.apk()

# TODO: this is copied from intercept.test_instrument.py
# TODO: returns a file path not an ApkModel
@pytest.fixture
def decompiled_onxmaps_apk_copy(onxmaps_apk_model):
    # Decompile it once, since copying it is cheaper that decompiling it every time we want to modify it.
    test_data_directory = "tests/data/"
    onxmaps_identifier = "19.onxmaps.hunt"
    decompiled_onxmaps_apk = os.path.join(test_data_directory, onxmaps_identifier)

    if not os.path.isdir(decompiled_onxmaps_apk):
        # load up the apk, decompile into the target directory
        apk = onxmaps_apk_model
        decode.decode_apk(test_data_directory, apk, clean=True)

        assert decompiled_onxmaps_apk == hybrid_config.decoded_apk_path(test_data_directory, apk)


    copy_dir = "tests/data/copied_decompiled_apks"
    if os.path.isdir(os.path.join(copy_dir, onxmaps_identifier)):
        shutil.rmtree(os.path.join(copy_dir, onxmaps_identifier))

    shutil.copytree(decompiled_onxmaps_apk, os.path.join(copy_dir, onxmaps_identifier))
    yield os.path.join(copy_dir, onxmaps_identifier)

    # Let Client delete the copy if it's been modified
    # delete the copy since it's probably been modified
    # shutil.rmtree(os.path.join(copy_dir, onxmaps_identifier))



def test_instrument_schemes_instrument_different_code(decompiled_onxmaps_apk_copy):

    count_insertions_list = []
    for instrumentation_approach in [InstrumentationApproach.SHALLOW_ARGS, InstrumentationApproach.SHALLOW_RETURNS]:
        benchmark = BenchmarkName.GPBENCH
        instrumentation_strategies = setup_dynamic_value_analysis_strategies(instrumentation_approach, benchmark)


        # decoded_apk = DecodedApkModel(hybrid_config.decoded_apk_path(_decoded_apks_directory_path, _apk))
        # apk_path = ""
        decoded_apk = DecodedApkModel(decompiled_onxmaps_apk_copy)
        code_insertions = decoded_apk.get_code_insertions_for_files(instrumentation_strategies)

        count_insertions = sum(list(map(len, code_insertions)))
        count_insertions_list.append(count_insertions)

    print(list(zip(count_insertions_list, [InstrumentationApproach.SHALLOW_ARGS, InstrumentationApproach.SHALLOW_RETURNS])))
    assert count_insertions_list[0] != count_insertions_list[1]
    # assert count_insertions_list[1] != count_insertions_list[2]
    # assert count_insertions_list[2] != count_insertions_list[3]


    # decoded_apk.instrument(instrumentation_strategies)




