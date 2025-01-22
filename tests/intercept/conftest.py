
import os
import shutil
from typing import Dict
from pytest import StashKey, CollectReport
import pytest

# import util.logger
# logger = util.logger.get_logger(__name__)

phase_report_key = StashKey[Dict[str, CollectReport]]()



@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    # Code not well understood. Pulled from https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures

    # execute all other hooks to obtain the report object
    rep = yield

    # store test results for each phase of a call, which can
    # be "setup", "call", "teardown"
    print("rep.when: " + rep.when)   
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep

    return rep

@pytest.fixture
def decompiled_apk_copy(request):

        # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample"
    assert os.path.exists(decompiled_apk)

    # decompiled_apk_copy = "tests/data/decompiledInstrumentableExample_copy"

    DECOMPILED_APK_COPY = "tests/data/decompiledInstrumentableExample_copy"
    
    if os.path.exists(DECOMPILED_APK_COPY):
        shutil.rmtree(DECOMPILED_APK_COPY)
    shutil.copytree(decompiled_apk, DECOMPILED_APK_COPY, dirs_exist_ok=False)

    yield DECOMPILED_APK_COPY

    # Check if test failed. If so, save off the decompiled apk copy for inspection.
    # print("checking result")
    # print("Stash object contents2: " + str(request.node.stash))
    report = request.node.stash[phase_report_key]
    # print(report)
    # for item in report:
    #     print(item)
    assert "call" in report
    did_test_fail = report["call"].outcome == 'failed'

    if did_test_fail: 
        # TODO: Save off the decompiled apk copy for inspection.
        print("failed!")
        
    
    # Clean up the copied directory
    shutil.rmtree(DECOMPILED_APK_COPY)

