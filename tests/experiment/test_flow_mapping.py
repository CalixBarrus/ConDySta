


import os
import shutil
import pandas as pd
import pytest
from experiment.flow_mapping import get_observation_harness_to_observed_source_map, get_observation_harness_to_string_set_map
from intercept.decoded_apk_model import DecodedApkModel
from intercept.instrument import HarnessObservations
from tests.sample_results import get_mock_invocation_register_context

@pytest.fixture
def decompiled_apk_copy_readonly():
    # copy smali dirs
    decompiled_apk = "tests/data/decompiledInstrumentableExample/app-debug"
    assert os.path.exists(decompiled_apk)

    copy_readonly = os.path.join("tests/data/decompiledInstrumentableExample_copyreadonly", "app-debug")
    
    if not os.path.exists(copy_readonly):
        shutil.copytree(decompiled_apk, copy_readonly, dirs_exist_ok=False)
    else: 
        # blithely assume the users actually treat is as readonly, so don't do the next two lines
        # shutil.rmtree(copy_readonly)
        # shutil.copytree(decompiled_apk, copy_readonly, dirs_exist_ok=False)
        pass

    yield copy_readonly
    
    # don't delete after


def test_get_observation_harness_to_observed_source_map_smoke(decompiled_apk_copy_readonly):
    
    harnesser = HarnessObservations(record_taint_function_mapping=True)
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy_readonly)
    observations = [get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-string", content="blackbox-call"), 
                    get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                    ]
    df = get_observation_harness_to_observed_source_map(harnesser, decoded_apk_model, observations)

    # Should be 4 rows, one per unique context
    assert len(df) == 4 
    # taint functions should all be different since these are all in the same enclosing class/method
    assert len(df[harnesser.mapping_key_cols[0]].unique()) == 4


def test_get_observation_harness_to_string_set_map_smoke(decompiled_apk_copy_readonly):
    harnesser = HarnessObservations(record_taint_function_mapping=True)
    decoded_apk_model = DecodedApkModel(decompiled_apk_copy_readonly)

    observations = [get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-string", content="blackbox-call"), 
                get_mock_invocation_register_context(is_arg=False, is_return=True, arg_register_index=-1, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                # get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-string", content="blackbox-call"), 
                get_mock_invocation_register_context(is_arg=True, is_return=False, arg_register_index=0, is_before=False, access_path="parent-child-string", content="blackbox-call"), 
                ]
    observed_strings = [
        set(["a"]),
        set(["b", "c"]),
        # set([]),
        set(["d"]),
    ]
    df = get_observation_harness_to_string_set_map(harnesser, decoded_apk_model, observations, observed_strings)


    # Should be 4 cols, 3 for key and 1 for the string sets
    assert len(df.columns) == 4 
    # Taint functions should be unique -> rows shouldn't have been reduced -> observed string sets should all be different like the test input
    # assert len(df[harnesser.mapping_str_observation_lookup_cols[0]].unique()) == 3
    assert df.at[0, harnesser.mapping_str_observation_lookup_cols[0]] == set(["a"])

    