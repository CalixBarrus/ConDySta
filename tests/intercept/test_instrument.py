
import os
import shutil
from typing import Dict, List
import pluggy
import pytest


from hybrid.hybrid_config import apk_path
from hybrid.invocation_register_context import InvocationRegisterContext
from intercept.instrument import HarnessObservations, HarnessSources
from intercept.rebuild import rebuild_apk
from intercept.decoded_apk_model import DecodedApkModel
from tests.sample_results import get_mock_access_path, get_mock_instrumentation_report, get_mock_result
from util.input import ApkModel

# import util.logger
# logger = util.logger.get_logger(__name__)


@pytest.fixture
def rebuilt_apk_directory_path():
    # Delete APK between tests
    yield "tests/data/rebuiltInstrumentableExample"
    
    # TODO: delete the rebuilt apk

@pytest.fixture
def apk_model():
    # # pytest complains about this import for some reason
    # from util.input import ApkModel

    # filename from android/decompile.py
    return ApkModel("tests/android/InstrumentableExample/app/build/outputs/apk/debug/app-debug.apk")



# DECOMPILED_APK_COPY = "tests/data/decompiledInstrumentableExample_copy"


# @pytest.fixture
# def setup_teardown(did_test_fail):
#     # Code to run before each test
#     # logger.info("Setup for test")

#     # copy smali dirs
#     decompiled_apk = "tests/data/decompiledInstrumentableExample"
#     assert os.path.exists(decompiled_apk)

#     decompiled_apk_copy = "tests/data/decompiledInstrumentableExample_copy"

    
#     shutil.copytree(decompiled_apk, DECOMPILED_APK_COPY, dirs_exist_ok=False)


#     yield 



#     logger.info("Teardown for test")
#     shutil.rmtree(DECOMPILED_APK_COPY)
#     print("checking result")
#     print(did_test_fail)
#     if did_test_fail: 
        
#         print("failed!")

        

# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item: pytest.Function, call: pytest.CallInfo):
#     outcome: pluggy.Result = yield
#     rep: pytest.TestReport = outcome.get_result()
#     setattr(item, "rep_" + rep.when, rep)
#     return rep

def test_passing(decompiled_apk_copy):
    assert True


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
    mock_context: List[InvocationRegisterContext] = [("instr report", "access path")]
    instrumenters = [HarnessObservations(mock_context)]
    decoded_apk_model.instrument(instrumenters)

    # recompile the apk
    # rebuilt_apk_directory_path = "tests/data/rebuiltInstrumentableExample"
    rebuild_apk(decoded_apk_model.apk_root_path, rebuilt_apk_directory_path, apk_model, clean=True)
    
    assert os.path.exists(apk_path(rebuilt_apk_directory_path, apk_model))

def test_inject_field_accesses_recompile_successfully_many_subfields():

    # when test fails, save off the modified smali 
    pass

def test_inject_field_accesses_recompile_successfully_restricted_fields():
    # try to access private & protected fields
    # try to access a private field from a class in a different modules

    # when test fails, save off the modified smali 
    pass

    