
import os
import shutil
from typing import Dict, List
import pluggy
import pytest


from experiment.benchmark_name import BenchmarkName
from experiment.load_benchmark import LoadBenchmark, get_wild_benchmarks
from hybrid import hybrid_config
from hybrid.dynamic import get_observations_from_logcat_single
from hybrid.hybrid_config import apk_path
from hybrid.invocation_register_context import InvocationRegisterContext
from intercept import decode
from intercept.instrument import HarnessObservations, HarnessSources, extract_private_string
from intercept.rebuild import rebuild_apk
from intercept.decoded_apk_model import DecodedApkModel
from tests.experiment.test_experiments_2_10_25 import harness_observations
from tests.sample_results import get_mock_access_path, get_mock_instrumentation_report, get_mock_invocation_register_context, get_mock_result
from util.input import ApkModel, InputModel

# import util.logger
# logger = util.logger.get_logger(__name__)


@pytest.fixture
def rebuilt_apk_directory_path():
    # Delete APKs between tests

    directory = "tests/data/rebuiltInstrumentableExample"
    yield directory

    shutil.rmtree(directory)
    os.mkdir(directory)

@pytest.fixture
def apk_model():
    # # pytest complains about this import for some reason
    # from util.input import ApkModel

    # filename from android/decompile.py
    return ApkModel("tests/android/InstrumentableExample/app/build/outputs/apk/debug/app-debug.apk")

@pytest.fixture(scope='module')
def onxmaps_apk_model():
    df_file_paths = get_wild_benchmarks(BenchmarkName.GPBENCH)[0]
    df = LoadBenchmark(df_file_paths).execute()
    onx_input_model: InputModel
    onx_input_model = df.at[19, "Input Model"]

    return onx_input_model.apk()

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


@pytest.fixture(scope='module')
def passportcanada_apk_model():
    df_file_paths = get_wild_benchmarks(BenchmarkName.GPBENCH)[0]
    df = LoadBenchmark(df_file_paths).execute()
    onx_input_model: InputModel
    onx_input_model = df.at[6, "Input Model"]

    return onx_input_model.apk()


@pytest.fixture
def decompiled_passportcanada_apk_copy(passportcanada_apk_model):
        # Decompile it once, since copying it is cheaper that decompiling it every time we want to modify it.
    test_data_directory = "tests/data/"
    passportcanada_identifier = "6.ca.passportparking.mobile.passportcanada"
    decompiled_passportcanada_apk = os.path.join(test_data_directory, passportcanada_identifier)

    if not os.path.isdir(decompiled_passportcanada_apk):
        # load up the apk, decompile into the target directory
        apk = passportcanada_apk_model
        decode.decode_apk(test_data_directory, apk, clean=True)

        assert decompiled_passportcanada_apk == hybrid_config.decoded_apk_path(test_data_directory, apk)


    copy_dir = "tests/data/copied_decompiled_apks"
    if os.path.isdir(os.path.join(copy_dir, passportcanada_identifier)):
        shutil.rmtree(os.path.join(copy_dir, passportcanada_identifier))

    shutil.copytree(decompiled_passportcanada_apk, os.path.join(copy_dir, passportcanada_identifier))
    yield os.path.join(copy_dir, passportcanada_identifier)


@pytest.fixture
def example_apk_model():
    # depends on script tests/android/decompile.py
    instrumentable_example_apk_path = "tests/android/InstrumentableExample/app/build/outputs/apk/debug/app-debug.apk"

    return ApkModel(instrumentable_example_apk_path)


def test_decompiled_apk_copy_smoke(decompiled_apk_copy):
    assert os.path.exists(decompiled_apk_copy)
    smali_dir = os.path.join(decompiled_apk_copy, "smali")
    assert os.path.exists(smali_dir)

def mock_invocation_register_context() -> List[InvocationRegisterContext]:
    instr_report = get_mock_instrumentation_report(is_arg=True, is_return=False, arg_register_index=0, content="blackbox-call")
    access_path = get_mock_access_path("parent-string")
    

    return [(instr_report, access_path)]


def test_inject_field_accesses_smoke(decompiled_apk_copy_persistent):

    decoded_apk_model = DecodedApkModel(decompiled_apk_copy_persistent)
    mock_context: List[InvocationRegisterContext] = mock_invocation_register_context()
    instrumenters = [HarnessObservations(mock_context)]

    decoded_apk_model.instrument(instrumenters)

def count_lines_in_file(path: str) -> int:

    with open(path, "r") as file:
        # skip blank lines
        return len(list(filter(lambda line: line.strip() != "", file.readlines())))

def test_inject_field_accesses_lines_added(decompiled_apk_copy):

    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)
    mock_context: List[InvocationRegisterContext] = mock_invocation_register_context()
    instrumenters = [HarnessObservations(mock_context)]
    
    main_file_path = os.path.join(decompiled_apk_copy, "smali_classes3/com/example/instrumentableexample/MainActivity.smali")

    lines_in_main_before = count_lines_in_file(main_file_path)
    decoded_apk_model.instrument(instrumenters)
    lines_in_main_after = count_lines_in_file(main_file_path)

    assert lines_in_main_after > lines_in_main_before


def test_no_modification_recompile_successfully(decompiled_apk_copy, rebuilt_apk_directory_path, apk_model):
    # integration test
    
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)
    # mock_context: List[InvocationRegisterContext] = [("instr report", "access path")]
    # instrumenters = [HarnessObservations(mock_context)]
    # decoded_apk_model.instrument(instrumenters)

    # recompile the apk
    # rebuilt_apk_directory_path = "tests/data/rebuiltInstrumentableExample"
    rebuild_apk(os.path.dirname(decoded_apk_model.apk_root_path), rebuilt_apk_directory_path, apk_model, clean=True)
    
    assert os.path.exists(apk_path(rebuilt_apk_directory_path, apk_model))
    

def test_inject_field_accesses_recompile_successfully(decompiled_apk_copy, rebuilt_apk_directory_path, apk_model):
    # integration test

    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)
    mock_context: List[InvocationRegisterContext] = mock_invocation_register_context() 
    instrumenters = [HarnessObservations(mock_context)]
    decoded_apk_model.instrument(instrumenters)

    # recompile the apk
    # rebuilt_apk_directory_path = "tests/data/rebuiltInstrumentableExample"
    rebuild_apk(os.path.dirname(decoded_apk_model.apk_root_path), rebuilt_apk_directory_path, apk_model, clean=True)
    
    assert os.path.exists(apk_path(rebuilt_apk_directory_path, apk_model))

def test_HarnessObservations_onxmaps_case(decompiled_onxmaps_apk_copy, onxmaps_apk_model, rebuilt_apk_directory_path):
    decoded_apk_model = DecodedApkModel(decompiled_onxmaps_apk_copy)

    onxmaps_da_log = "tests/data-persistent/19.19.onxmaps.hunt.apk.log"
    tainted_contexts = get_observations_from_logcat_single(onxmaps_da_log, False)

    instrumenters = [HarnessObservations(observations=tainted_contexts)]

    decoded_apk_model.instrument(instrumenters)

    # Experiments have revealed 18 bad reports in the test input
    assert instrumenters[0].report_mismatch_exceptions == 15
    # All of the mismatches are on returns, we try to repair 
    assert instrumenters[0].report_mismatch_repair_attempted == 15

    rebuild_apk(os.path.dirname(decompiled_onxmaps_apk_copy), rebuilt_apk_directory_path, onxmaps_apk_model, True)
    
    assert os.path.exists(apk_path(rebuilt_apk_directory_path, onxmaps_apk_model))


    # Only delete if there weren't errors
    shutil.rmtree(decompiled_onxmaps_apk_copy)


def test_HarnessObservations_passportcanada_case(decompiled_passportcanada_apk_copy, passportcanada_apk_model, rebuilt_apk_directory_path):
    decoded_apk_model = DecodedApkModel(decompiled_passportcanada_apk_copy)

    passportcanada_da_log = "tests/data-persistent/6.6.ca.passportparking.mobile.passportcanada.apk.log"
    tainted_contexts = get_observations_from_logcat_single(passportcanada_da_log, False)

    instrumenters = [HarnessObservations(observations=tainted_contexts)]

    decoded_apk_model.instrument(instrumenters)

    rebuild_apk(os.path.dirname(decompiled_passportcanada_apk_copy), rebuilt_apk_directory_path, passportcanada_apk_model, True)
    
    assert os.path.exists(apk_path(rebuilt_apk_directory_path, passportcanada_apk_model))


    print(instrumenters[0].report_mismatch_exceptions) # 44 of these, yikes
    print(instrumenters[0].report_mismatch_repair_attempted)

    # We experimentally found 1 case where there wasn't a move-result when expected.
    assert instrumenters[0].report_mismatch_exceptions - instrumenters[0].report_mismatch_repair_attempted == 1 

    # Only delete if there weren't errors
    shutil.rmtree(decompiled_passportcanada_apk_copy)
    
def test_extract_private_string_regex_sanity_check():
    test = 'Error reading file: ***000000186130***'

    assert extract_private_string(test) == set(["***000000186130***"])

def test_HarnessObservations_disable_field_sensitivity_rebuilds(decompiled_apk_copy, rebuilt_apk_directory_path, example_apk_model):
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)

    
    mock_context: List[InvocationRegisterContext] = [get_mock_invocation_register_context(is_arg=False, is_return=True, content="blackbox-call", access_path="parent-child-string")]
    instrumenters = [HarnessObservations(mock_context, disable_field_sensitivity=True)]
    decoded_apk_model.instrument(instrumenters)

    rebuild_apk(os.path.dirname(decompiled_apk_copy), rebuilt_apk_directory_path, example_apk_model, True)

    assert True


def test_HarnessObservations_disable_field_sensitivity_fewer_lines(decompiled_apk_copy, decompiled_apk_copy2):
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)
    mock_context: List[InvocationRegisterContext] = [get_mock_invocation_register_context(is_arg=False, is_return=True, content="blackbox-call", access_path="parent-child-string")]
    instrumenters = [HarnessObservations(mock_context)]
    decoded_apk_model.instrument(instrumenters)
    
    main_file_path = os.path.join(decompiled_apk_copy, "smali_classes3/com/example/instrumentableexample/MainActivity.smali")

    lines_in_main_with_field_sensitivity = count_lines_in_file(main_file_path)

    decoded_apk_model2 = DecodedApkModel(decompiled_apk_copy2)
    instrumenters = [HarnessObservations(mock_context, disable_field_sensitivity=True)]
    decoded_apk_model2.instrument(instrumenters)

    lines_in_main_without_field_sensitivity = count_lines_in_file(os.path.join(decompiled_apk_copy2, "smali_classes3/com/example/instrumentableexample/MainActivity.smali"))

    assert lines_in_main_with_field_sensitivity > lines_in_main_without_field_sensitivity

def test_HarnessObservations_disable_field_sensitivity_observations_get_combined(decompiled_apk_copy, decompiled_apk_copy2):
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy)
    mock_context: List[InvocationRegisterContext] = [get_mock_invocation_register_context(is_arg=False, is_return=True, content="blackbox-call", access_path="parent-child-string")]
    instrumenters = [HarnessObservations(mock_context, disable_field_sensitivity=True)]
    decoded_apk_model.instrument(instrumenters)
    
    main_file_path = os.path.join(decompiled_apk_copy, "smali_classes3/com/example/instrumentableexample/MainActivity.smali")

    lines_in_main_single_observation = count_lines_in_file(main_file_path)

    decoded_apk_model2 = DecodedApkModel(decompiled_apk_copy2)
    mock_context2 = [get_mock_invocation_register_context(is_arg=False, is_return=True, content="blackbox-call", access_path="parent-child-string"),
                    get_mock_invocation_register_context(is_arg=False, is_return=True, content="blackbox-call", access_path="parent-string"),]
    instrumenters = [HarnessObservations(mock_context2, disable_field_sensitivity=True)]
    decoded_apk_model2.instrument(instrumenters)

    lines_in_main_2_observations = count_lines_in_file(os.path.join(decompiled_apk_copy2, "smali_classes3/com/example/instrumentableexample/MainActivity.smali"))

    assert lines_in_main_single_observation == lines_in_main_2_observations

def test_HarnessObservations_settings_reduce_count_leaks():

    observations = [
        get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="length1", content="placeholder"), # lvl 0 a.p.
        get_mock_invocation_register_context(access_path="a"), # lvl 1 a.p. but different base than previous
        get_mock_invocation_register_context(access_path="b"), # lvl 1 a.p. which would get combined with the previous when field sensitivity is disabled
    ]

    harness_observations = HarnessObservations(filter_to_length1_access_paths=True)
    harness_observations.set_observations(observations)
    assert len(harness_observations.processed_observations) == 1

    harness_observations = HarnessObservations(disable_field_sensitivity=True)
    harness_observations.set_observations(observations)
    assert len(harness_observations.processed_observations) == 2

    harness_observations = HarnessObservations()
    harness_observations.set_observations(observations)
    assert len(harness_observations.processed_observations) == 3


