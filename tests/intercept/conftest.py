
import os
import shutil
from typing import Dict
from pytest import StashKey, CollectReport
import pytest

# import util.logger
# logger = util.logger.get_logger(__name__)

phase_report_key = StashKey[Dict[str, CollectReport]]()



@pytest.fixture
def decompiled_apk_copy(request):
    # TODO: instead of getting fancy with this, just have separate fixture where clients are responsible for deleting it (or not)

    # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample/app-debug"
    assert os.path.exists(decompiled_apk), "Run scripts in build and decompile scripts in tests/android/"

    # decompiled_apk_copy = "tests/data/decompiledInstrumentableExample_copy"

    # DECOMPILED_APK_COPY = os.path.join("tests/data/decompiledInstrumentableExample_copy")
    DECOMPILED_APK_COPY = os.path.join("tests/data/decompiledInstrumentableExample_copy", "app-debug")
    
    if os.path.exists(DECOMPILED_APK_COPY):
        shutil.rmtree(DECOMPILED_APK_COPY)
    shutil.copytree(decompiled_apk, DECOMPILED_APK_COPY, dirs_exist_ok=False)

    yield DECOMPILED_APK_COPY

    # Check if test failed. If so, save off the decompiled apk copy for inspection.
    # print("checking result")
    # print("Stash object contents2: " + str(request.node.stash))
    # report = request.node.stash[phase_report_key]
    # # print(report)
    # # for item in report:
    # #     print(item)
    # assert "call" in report
    # did_test_fail = report["call"].outcome == 'failed'

    # if did_test_fail: 
    #     # TODO: Save off the decompiled apk copy for inspection.
    #     print("failed!")
        
    
    # Clean up the copied directory
    shutil.rmtree(DECOMPILED_APK_COPY)

@pytest.fixture
def decompiled_apk_copy2():
    # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample/app-debug"
    assert os.path.exists(decompiled_apk)

    copy2 = os.path.join("tests/data/decompiledInstrumentableExample_copy2", "app-debug")
    
    if os.path.exists(copy2):
        shutil.rmtree(copy2)
    shutil.copytree(decompiled_apk, copy2, dirs_exist_ok=False)

    yield copy2
    
    # Clean up the copied directory
    shutil.rmtree(copy2)

@pytest.fixture
def decompiled_apk_copy_persistent(request):
    # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample/app-debug"
    assert os.path.exists(decompiled_apk)

    # decompiled_apk_copy = "tests/data/decompiledInstrumentableExample_copy"

    # DECOMPILED_APK_COPY = os.path.join("tests/data/decompiledInstrumentableExample_copy")
    DECOMPILED_APK_COPY = os.path.join("tests/data/decompiledInstrumentableExample_persistent-copy", "app-debug")
    
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
    # shutil.rmtree(DECOMPILED_APK_COPY)